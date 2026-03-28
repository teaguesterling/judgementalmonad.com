# Kibitzer Coaching Observations from Experiments

*Concrete patterns observed during ~250 experimental runs that Kibitzer's coach should detect and address.*

## Read first

- `drafts/kibitzer-implementor-prompt.md` — The build prompt for Kibitzer
- `drafts/toolcraft-coordinator-design.md` — The plugin architecture
- `blog/patterns/08-the-coach.md` — The Coach pattern

## Observation 1: Repeated file_edit failures (whitespace mismatch)

**What happens:** The agent calls `file_edit` with an `old_string` that doesn't match the file content. Usually the logic is correct but the indentation or whitespace is wrong. The agent retries with a slightly different string, fails again, retries again. Each cycle costs 2-3 turns (failed edit → re-read file → retry edit).

**How to detect (PostToolUse):**
```python
# Track consecutive file_edit failures on the same file
if tool_name == "file_edit" and not success:
    state["consecutive_edit_failures"] = state.get("consecutive_edit_failures", 0) + 1
    state["last_failed_edit_file"] = tool_input.get("file_path", "")
elif tool_name == "file_edit" and success:
    state["consecutive_edit_failures"] = 0
```

**When to intervene:** After 2 consecutive file_edit failures on the same file.

**What to say:**
```
[kibitzer] file_edit failed twice on {file}. The old_string may have
wrong indentation. Try file_read({file}) first to see the exact
current content, then copy the string precisely.
```

**Why this matters:** In Haiku/N experiments, agents with 9+ failed edits exhausted their turn budget and failed the task. Agents with ≤3 failed edits recovered and passed. Early intervention at the 2-failure mark could prevent the spiral.

**Model dependency:** Critical for Haiku (generates bad old_strings frequently). Occasionally useful for Sonnet. Rare for Opus.

## Observation 2: Sequential file_read calls (should batch or use semantic tools)

**What happens:** The agent reads files one at a time: `file_read("src/tokenizer.py")`, then next turn `file_read("src/parser.py")`, then `file_read("src/evaluator.py")`. Each call is a separate turn with full context re-send.

**How to detect (PostToolUse):**
```python
if tool_name == "file_read":
    state["consecutive_reads"] = state.get("consecutive_reads", 0) + 1
else:
    state["consecutive_reads"] = 0
```

**When to intervene:** After 3 consecutive file_read calls.

**What to say (if file_read_batch available):**
```
[kibitzer] You've read 3 files one at a time. file_read_batch can
read multiple files in one call:
file_read_batch(["src/tokenizer.py", "src/parser.py", "src/evaluator.py"])
```

**What to say (if find_definitions available):**
```
[kibitzer] You've read 3 files sequentially. find_definitions()
shows all function and class definitions across the codebase in
one call — it may give you the overview you're building manually.
```

**Why this matters:** Sonnet/A averaged 4.4 file_read calls per run. Sonnet/E averaged 4.0 but combined with batch reads. The round-trip overhead of sequential reads was a major cost driver — it's why A ($1.35) cost more than E ($0.98).

## Observation 3: Editing without testing (long edit streaks)

**What happens:** The agent makes multiple edits without running tests in between. It fixes what it thinks are all the bugs, then runs tests and discovers some edits were wrong or introduced new failures. Then it has to debug its own fixes.

**How to detect (PostToolUse):**
```python
if tool_name in ("file_edit", "file_edit_batch"):
    state["edits_since_test"] = state.get("edits_since_test", 0) + 1
elif tool_name == "run_tests":
    state["edits_since_test"] = 0
```

**When to intervene:** After 5 edits without a test run (configurable).

**What to say:**
```
[kibitzer] You've made {n} edits without running tests. Consider
run_tests() to verify your changes before continuing.
```

**Why this matters:** The principle instruction "understand before editing" addressed this partially — agents front-loaded understanding. But some agents (especially with bash) make many edits in a batch script and only test at the end. Early testing catches cascading errors before they compound.

**Model dependency:** Most useful for Haiku (which edits impulsively without the principle). Less critical for Sonnet/Opus which test more naturally.

## Observation 4: Ignoring available semantic tools

**What happens:** The agent has find_definitions, find_callers, code_structure available in its tool set but never calls them. It uses file_read and file_search (or grep via bash) to find code instead. The semantic tools provide AST-aware results but the agent doesn't discover them.

**How to detect (PostToolUse):**
```python
# Track whether semantic tools have been used this session
semantic_tools = {"find_definitions", "find_callers", "code_structure", "find_imports"}
if tool_name in semantic_tools:
    state["semantic_tools_used"] = True

# After N tool calls, if no semantic tools used:
if state.get("total_calls", 0) > 10 and not state.get("semantic_tools_used"):
    # Check if the agent has been searching for code
    search_count = state.get("search_or_read_count", 0)
    if search_count > 5:
        suggest_semantic = True
```

**When to intervene:** After 10+ tool calls with 5+ file_read/file_search calls and zero semantic tool calls.

**What to say:**
```
[kibitzer] You've been searching through files manually.
find_definitions() shows all functions and classes across the
codebase with their types and locations — one call instead of
searching file by file.
```

**Why this matters:** In Haiku/L experiments (semantic tools available, generic principle), the agent made ZERO semantic tool calls across all 5 runs. With the semantic-focused principle (Haiku/N), it used find_definitions once per run and pass rate improved. The tool exists but is invisible without either the principle or the Coach.

## Observation 5: Using bash for git operations

**What happens:** The agent runs `git add -A && git commit -m "fix"` through bash when jetsam is available. The bash command works but bypasses jetsam's plan tracking, confirmation step, and audit trail.

**How to detect (PreToolUse on Bash):**
```python
if tool_name == "Bash":
    cmd = tool_input.get("command", "")
    if "git add" in cmd or "git commit" in cmd or "git push" in cmd:
        suggest_jetsam = True
```

**What to say:**
```
[kibitzer] jetsam save does git add + commit with plan tracking
and a confirmation step. Consider: jetsam save "description"
```

**Interception mode:** Start in OBSERVE (log it). Graduate to SUGGEST (show the alternative). This is the JetsamPlugin from the coordinator design.

## Observation 6: Using bash for test execution

**What happens:** The agent runs `python -m pytest tests/` through bash when run_tests or blq is available.

**How to detect (PreToolUse on Bash):**
```python
if tool_name == "Bash":
    cmd = tool_input.get("command", "")
    if "pytest" in cmd or "python -m pytest" in cmd:
        suggest_structured = True
```

**What to say (if run_tests available):**
```
[kibitzer] run_tests() provides structured test output and prevents
test file modification. Consider using it instead of bash pytest.
```

**What to say (if blq available):**
```
[kibitzer] blq run test captures structured output queryable via
blq errors. Consider: blq run test
```

**Caveat from experiments:** In Sonnet/E, using bash for pytest was actually the most efficient approach ($0.98). The suggestion should be OBSERVE or SUGGEST mode, not REDIRECT. The structured alternative is safer and more auditable, but the agent may have good reasons for using bash directly.

## Observation 7: Agent stuck in analysis loop (Opus pattern)

**What happens:** The agent reads files, searches, analyzes — but never edits. Turn count climbs. No file_edit or file_write calls after 15+ turns. The agent is understanding endlessly without acting.

**How to detect (PostToolUse):**
```python
if tool_name in ("file_edit", "file_write", "file_edit_batch"):
    state["last_edit_turn"] = state.get("total_calls", 0)

turns_since_edit = state.get("total_calls", 0) - state.get("last_edit_turn", 0)
```

**When to intervene:** After 15 turns with no edits.

**What to say:**
```
[kibitzer] You've spent {n} turns reading without making changes.
Consider starting with the most confident fix — you can verify
with run_tests and adjust.
```

**Model dependency:** Primarily Opus. The principle instruction "understand before editing" can trigger this in Opus — it interprets "understand" as "analyze exhaustively." For Opus, this coaching nudge toward action is more appropriate than the principle instruction itself.

**This is the Coach compensating for a harmful principle.** Rather than removing the principle (which helps Haiku and Sonnet), the Coach detects when the principle has over-corrected and nudges back toward action.

## Implementation priority for Kibitzer

1. **Observation 1 (edit failures)** — Highest impact for Haiku. Simple counter. Directly addresses the #1 cause of Haiku task failures.
2. **Observation 3 (edit without test)** — Simple counter, broadly useful.
3. **Observation 4 (ignored semantic tools)** — Makes tools visible that are otherwise unused.
4. **Observation 2 (sequential reads)** — Cost optimization, not reliability.
5. **Observation 7 (analysis loop)** — Opus-specific, important for model-aware coaching.
6. **Observations 5-6 (bash for git/tests)** — Ratchet data collection, lower urgency.

## How this connects to the ratchet

Each observation is a ratchet candidate. The Coach detects the pattern. Over time:
- High-frequency observations → bake into the principle instruction
- Observations the agent consistently follows → the tool or principle becomes default
- Observations the agent ignores → the tool may not be the right intervention

The Coach's suggestion log IS the ratchet's observation phase, running continuously.
