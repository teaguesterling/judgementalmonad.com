# Build Kibitzer

*You are building kibitzer — a Claude Code extension that watches how agents use tools and suggests better alternatives.*

## What kibitzer is

A kibitzer is the person watching your chess game who can't help offering opinions. This extension watches an agent's tool calls and offers structured alternatives — "you just ran `git add && git commit` through bash; `jetsam save` does that with plan tracking and confirmation."

Kibitzer coordinates three existing tools:
- **Fledgling** (code intelligence, level 0 — read-only DuckDB queries over ASTs and conversation logs)
- **blq** (build/test capture, level 1-2 — structured event capture with optional sandbox enforcement)
- **jetsam** (git workflow, level 1-2 — atomic saves, syncs, plans, mode state)

Kibitzer itself is level 1 — specified rules over structured data. No LLM in the decision loop. Every decision traces to config.toml.

## Before you start

Read these files. They contain the design, the evidence, and the integration contracts.

### The design (read first)
1. `drafts/toolcraft-coordinator-design.md` — **The full architecture.** Plugin system, path guard, mode controller, coach, interception modes, PostToolUse validation. Your blueprint.
2. `drafts/toolcraft-extension-prompt.md` — File structure, implementation details, state management, testing plan.

### The patterns (read for context)
3. `blog/patterns/index.md` — Patterns for Toolcraft overview. Kibitzer implements patterns 1, 2, 4, 7, and 8.
4. `blog/patterns/01-the-quartermaster.md` — Session-start configuration. Kit manifests, model profiles.
5. `blog/patterns/02-the-strategy-instruction.md` — ~50 token principles. Model-dependent: essential for Haiku, harmful for Opus.
6. `blog/patterns/04-write-execute-separation.md` — Path guard enforces this. Tests read-only during implementation.
7. `blog/patterns/07-the-mode-controller.md` — Failure-driven transitions. Counters + thresholds.
8. `blog/patterns/08-the-coach.md` — Periodic suggestions. Integration with Fledgling/blq/jetsam.

### The evidence (read to understand why)
9. `experiments/pilot-findings.md` — ~200 experimental runs. Sections 8-11 are most relevant.
10. `drafts/the-experiment-that-proved-us-wrong.md` — The narrative. Why these patterns exist.

### Integration contracts (read to understand each tool's role)
11. `~/Projects/lq/main/docs/plans/patterns-integration-prompt.md` — blq: sandbox specs, test events
12. `~/Projects/source-sextant/main/docs/plans/patterns-integration-prompt.md` — Fledgling: level 0 intelligence, kits, coaching queries
13. `~/Projects/jetsam/main/docs/superpowers/plans/patterns-integration-prompt.md` — jetsam: mode state, workflow transitions

## What to build

### Core (build first, test independently)

```
kibitzer/
├── __init__.py
├── config.py              # Load config.toml
├── state.py               # Read/write .kibitzer/state.json
├── hooks/
│   ├── pre_tool_use.py    # Entry point: path guard + interceptors
│   └── post_tool_use.py   # Entry point: mode controller + coach
└── config.toml            # Default policies
```

The hooks are the product. Everything else serves them.

**pre_tool_use.py** receives on stdin:
```json
{"tool_name": "Edit", "tool_input": {"file_path": "tests/foo.py", ...}, "session_id": "..."}
```

It chains:
1. Path guard — check if the file is writable in the current mode
2. Interceptors — check if a bash command has a structured alternative

Output (deny):
```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}
```

Output (suggest without blocking):
```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[kibitzer] jetsam save does this with plan tracking."}}
```

Output (allow): exit 0 with no output.

**post_tool_use.py** receives the tool result. It chains:
1. Update counters (failure count, turns in mode, total calls)
2. Check mode transitions (3+ failures → debug mode)
3. Every N calls: run coach queries, suggest if pattern matches

### Guards (build second)

```
kibitzer/guards/
└── path_guard.py
```

Reads mode from `.kibitzer/state.json` (or `.jetsam/state.json` if jetsam is available). Checks write tool paths against mode policy. Denies with a reason that tells the agent how to switch modes.

Mode policies in config.toml:
```toml
[modes.debug]
writable = []
strategy = "Identify all failures before proposing fixes."

[modes.implement]
writable = ["src/"]

[modes.test_dev]
writable = ["tests/"]

[modes.review]
writable = []
```

### Interceptors (build third)

```
kibitzer/interceptors/
├── base.py
├── blq_plugin.py
├── jetsam_plugin.py
└── fledgling_plugin.py
```

Each plugin:
- Declares trigger patterns (bash command substrings)
- Returns a Suggestion (tool name, reason, grade change) or None
- Has a mode: observe / suggest / redirect (from config.toml)

The interceptor only fires on Bash tool calls.

### Coach (build fourth)

```
kibitzer/coach/
├── observer.py
└── suggestions.py
```

Fires every N calls (configurable). Queries:
- Recent tool call patterns (from state or conversation log)
- Repeated searches (suggest semantic alternative)
- Edit-without-test streaks (suggest running tests)

If Fledgling is available, uses `fledgling query` for richer analysis. If not, works from the state file alone.

### Quartermaster (build fifth)

```
kibitzer/quartermaster/
├── profiles.py
└── selector.py
```

Runs at session start (or on first tool call). Detects model, selects strategy instruction, configures mode. Writes initial state to `.kibitzer/state.json`.

Model profiles:
```python
PROFILES = {
    "haiku": {"strategy_required": True, "max_tools": 5, "coach_frequency": 3},
    "sonnet": {"strategy_required": False, "max_tools": 15, "coach_frequency": 5},
    "opus": {"strategy_required": False, "max_tools": 15, "coach_frequency": 10},
}
```

### Install

```
kibitzer/install.py
```

Adds hooks to `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [{"command": "python3 -m kibitzer.hooks.pre_tool_use"}],
    "PostToolUse": [{"command": "python3 -m kibitzer.hooks.post_tool_use"}]
  }
}
```

## Key design principles

1. **No LLM in the loop.** Every decision is a specified rule in config.toml. Counters, thresholds, pattern matches. If you catch yourself writing "ask the model," stop.

2. **Graceful degradation.** blq not installed? Skip BlqPlugin. Jetsam not installed? Use `.kibitzer/state.json` for mode state. Fledgling not installed? Coach works from state file only.

3. **Observe before enforce.** Default interception mode is "observe" for all plugins. Log everything. Enforce nothing. Graduate to "suggest" then "redirect" via config changes.

4. **The agent sees the reason.** Every deny includes the reason AND how to change the situation. "Implementation mode: tests/ is protected. Use `jetsam mode test_dev` to edit tests." Transparency principle.

5. **Hooks are fast.** Read a JSON file, check a condition, output JSON. No network calls, no database queries (except the optional Fledgling coach queries, which are local DuckDB). Target: <100ms per hook invocation.

## Testing

Use the synthetic codebase from the experiments:
```
experiments/synthetic/codebase-beta/
```

Test scenarios:
1. **Path guard**: Set mode to "implement", try to Edit a test file → should deny
2. **Mode switch**: Set mode to "debug", make 4 failing edits → should auto-switch to debug
3. **Interceptor**: Run `Bash("git add -A && git commit -m 'fix'")` → should suggest `jetsam save`
4. **Coach**: Make 3 identical `file_search` calls → should suggest `FindDefinitions`
5. **Quartermaster**: Start session as Haiku → should inject strategy instruction

## What NOT to build

- Don't reimplement Claude Code's built-in tools
- Don't use an LLM for any decision
- Don't make kibitzer required — agent works without it
- Don't build the Calibration Probe yet (follow-up)
- Don't integrate with blq's sandbox specs yet (follow-up)
- Don't over-engineer the config format — TOML is fine, start simple

## The name

Kibitzer: the person watching your chess game who can't help offering opinions. Three modes of kibitzing: observe (silent notes), suggest (whispered alternatives), redirect (moving the piece back). `pip install kibitzer`.
