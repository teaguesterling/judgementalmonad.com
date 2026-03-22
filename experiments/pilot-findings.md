# Experimental Findings

*Observations from infrastructure development and experimental runs, March 2026.*

---

## Methodological note

This document records an *exploratory* experimental program, not a pre-registered hypothesis test. The pre-registered experiments (Experiments 1-12 in `drafts/experiment-designs.md` and `drafts/experiment-statistics.md`) are the formal program. This document records what happened when we built the infrastructure to run them — and what we discovered along the way that changed the experimental design.

The sequence:
1. Built infrastructure to run the pre-registered Experiment 3 (computation channel phase transition)
2. Ran pilot tests to validate the infrastructure
3. Discovered that the original condition design (A/B/C as a gradient) was confounded — tool parity, run_tests dominance, cognitive fit
4. Explored the confounds through focused experiments (H5, A-vs-D, G/H/I)
5. These explorations will inform the design of the formal experiment

This is legitimate pre-experimental exploration — the kind of piloting that should happen before committing to 90+ runs on a pre-registered design. The findings here are descriptive (n=5-10 per cell, not powered for inferential claims). The formal experiment will be designed after this exploration converges.

**What changed from the original plan:**
- Conditions expanded from A/B/C (gradient) to A-F (2×2×2 factorial)
- `run_tests` identified as the dominant variable, not bash availability
- D (bash-only) became the comparison target, not C (bash + structured)
- Three ratchet experiments (G/H/I) designed to decompose D's advantage
- The formal experiment will test whichever variable the ratchet experiments identify

---

## 0. Framing: The Harness Matters, But How?

Crandall's ["Same Model, 78% vs 42%"](https://natesnewsletter.substack.com/p/same-model-78-vs-42-the-harness-made) documents at practitioner scale what the Ma framework formalizes: the harness determines the system's behavior more than the model does. The same model in different harnesses is a different system. The LangChain finding (52.8% → 66.5%) showed this on a benchmark. Crandall shows it in production, with compounding lock-in as accumulated configuration makes the choice increasingly irreversible.

Our pilot tests a more specific question: **within a well-engineered harness, does additional tool capability help?** Crandall compares designed harnesses (Claude Code's open environment vs Codex's sealed sandbox). We compare tool configurations within a single harness design (same MCP server, same permission model, same scope construction — just different tools available).

The results are complementary:
- **Crandall**: A well-engineered open harness beats a poorly-engineered closed one. (World coupling matters; the collar harness vs throat harness from post 1.)
- **Our pilot**: Within a well-engineered harness, fewer tools can produce better outcomes. (Restriction has returns; the supermodularity claim from post 2.)
- **The reconciliation**: Today's open harness is tomorrow's specified harness. The ratchet converts exploration into specification. The 78% harness earned its capability through accumulated configuration layers — each one a crystallized piece of exploratory behavior. The openness was necessary for discovery; the specification is what made it reliable.

This framing — "start open, crystallize what works, restrict the solved parts" — is the ratchet applied to experimental design itself. We built the experiment infrastructure with the full Claude Code harness. We observed what tools the agent actually used. We built an MCP server with specific tools. We found the specific tools were sufficient — and more efficient. One turn of the ratchet, performed on our own infrastructure.

---

## 1. Infrastructure Summary

### What was built

- **Experiment MCP server** (`tools/experiment-server/server.py`): Serves condition-specific tool sets. Logs every tool call to JSONL. Auto-commits file changes for sandbox diffing. Supports `--allowed-dirs` for restricted file access experiments.
- **Runner script** (`tools/run-experiment.sh`): Creates git worktrees for isolation, runs `claude -p` non-interactively, captures conversation JSON and summaries. Supports `--dry-run`, `--model`, `--max-turns`, `--max-budget`, `--cleanup`.
- **Bubblewrap sandboxing**: Both bash tools run inside bwrap with filesystem isolation (workspace only), no network, PID namespace isolation. `bash_readonly` mounts workspace read-only; `bash_sandboxed` mounts read-write.
- **Trust gap experiment tooling** (`tools/run-trust-experiment.sh`, `tools/setup-trust-tasks.sh`): Plants bait files, runs the agent, analyzes tool logs for constraint violations.
- **Synthetic codebase** (`synthetic/codebase-beta/`): Python expression language (tokenizer + parser + evaluator, ~600 lines) with 13 planted bugs across 3 files and 48 tests.
- **`run_tests` tool**: Available in ALL conditions. Runs pytest on original test files. Refuses to run if test files were modified. Data channel (level 1).

### Tool sets per condition

| Tool | Condition A | Condition B | Condition C |
|------|:-----------:|:-----------:|:-----------:|
| file_read | ✓ | ✓ | ✓ |
| file_read_batch | ✓ | ✓ | ✓ |
| file_search | ✓ | ✓ | ✓ |
| file_search_context | ✓ | ✓ | ✓ |
| file_glob | ✓ | ✓ | ✓ |
| file_list | ✓ | ✓ | ✓ |
| file_count | ✓ | ✓ | ✓ |
| file_edit | ✓ | ✓ | ✓ |
| file_write | ✓ | ✓ | ✓ |
| run_tests | ✓ | ✓ | ✓ |
| bash_readonly | | ✓ | |
| bash_sandboxed | | | ✓ |

---

## 2. Pilot Results: Synthetic Bug-Fixing Task

### Setup

- **Task**: Fix all bugs in codebase-beta to make 48 tests pass. Source files only — test files read-only.
- **Codebase**: 3 Python files (~600 lines), 13 bugs, 48 tests (13 failing).
- **Bug comments removed**: Agent must discover bugs from test failures, not from code comments.
- **Model**: claude-sonnet-4-6 (Sonnet)
- **n=1 per condition** (pilot, not powered for statistical claims)

### Results

| | Cond A (data channel) | Cond B (readonly bash) | Cond C (computation channel) |
|---|---|---|---|
| **Outcome** | 48/48 passed | 48/48 passed | 48/48 passed |
| **Duration** | **395s** (6.6 min) | 997s (16.6 min) | 659s (11.0 min) |
| **Turns** | **14** | 26 | 20 |
| **Tool calls** | **11** | 23 | 18 |
| **Tool call success** | 91% | **74%** | 83% |
| **File edits** | 5 | 8 | 7 |
| **run_tests calls** | 2 | 4 | 3 |
| **Bash calls** | 0 | **5** | **0** |
| **Output tokens** | **24,255** | 60,086 | 37,187 |
| **Context (cache read)** | **389,824** | 1,263,389 | 672,644 |
| **Cost** | **$0.67** | $1.63 | $1.00 |

### Observations

**1. All conditions succeeded.** The task was solvable regardless of tool set. No condition-dependent failures. This means the task is below the difficulty threshold for condition differentiation.

**2. Condition A was most efficient on every metric.** Fewest turns, fewest tool calls, fastest, cheapest. It read the code, read the test output, reasoned about the bugs, fixed them, and verified — in two iterations (run tests → fix → run tests → done).

**3. Condition B was worst on every metric.** Despite having "more tools" (readonly bash on top of everything A has), it was 2.4x the cost and 2.5x the time. The readonly bash was used 5 times — all for investigation (`cat -A`, `grep` on test files, `git` history) that didn't improve diagnosis. The exploration was counterproductive.

**4. Condition C had bash_sandboxed but didn't use it.** Zero bash calls. With `run_tests` available as a structured verification tool, the computation channel was unnecessary. The agent had no reason to run arbitrary Python when it could just run the test suite.

**5. Condition B's bash_readonly was used for investigation, not verification.** The 5 bash calls were: `cd` (failed — read-only), `cat -A` (checking whitespace), `grep` (searching test files), `grep -c` (counting), `git` (checking history). All of these are investigation tools the agent reached for when it was uncertain. Conditions A and C didn't have this uncertainty — they read the code and reasoned correctly on the first attempt.

### Interpretation

**Why A won:** The task has a small search space (3 files, ~600 lines). Sonnet can hold the entire codebase in context and reason about all bugs in one pass. The `run_tests` tool provides a clean verification loop. No exploration is needed — the bugs are findable by reading.

**Why B lost:** `bash_readonly` gave the agent more ways to look at the problem without helping it *think* about the problem. The investigation calls (checking whitespace, searching for patterns in tests) were symptoms of uncertainty that A and C resolved through reasoning alone. More tools → more exploration → more turns → more cost → same outcome.

**Why C didn't use bash:** `run_tests` is strictly better than `bash_sandboxed` for verification — it's faster, gives structured output, and is always available. The only advantage of bash_sandboxed would be interactive exploration (adding print statements, running code snippets), which the agent didn't need for this task.

### What this doesn't tell us

- Whether results hold at n>1 (could be a fluke of sampling)
- Whether results hold for harder tasks (where reasoning alone isn't sufficient)
- Whether results hold for larger codebases (where the search space exceeds context)
- Whether the failure *mode* distribution differs (no failures occurred)
- Whether the supermodularity interaction exists (need W-axis variation)

---

## 3. Other Pilot Observations

### sitting_duck tasks (hard-1, hard-2, trap-1 through trap-3)

Ran 5 tasks × 3 conditions = 15 runs on real sitting_duck codebase, 25-turn limit.

**Key finding: Turn limit was the dominant factor.** All hard tasks hit the 25-turn cap. Condition C was more *efficient* (fewer tool calls per unit of progress) because `bash_sandboxed` allowed multi-file grep in a single call. But no condition completed the hard tasks.

**Condition C used bash for 47% of its tool calls on hard-1** (14 of 30). It did things like `grep -rn 'PATTERN' src/language_configs/*.def` — one command scanning all config files simultaneously. Condition A did the same search as 10+ sequential `file_read` calls.

**Before enhanced file tools were added**, this was a confound: Condition A was handicapped by not having batch-read and context-search tools, not by lacking computation channels. After adding `file_read_batch`, `file_search_context`, and `file_count`, the confound was addressed for future runs.

### Trust gap tasks (trust-1 through trust-3)

9 runs (3 tasks × 3 conditions). Every run respected the "do not read" constraints. Zero violations, zero attempts.

**Sonnet's instruction-following is robust across all conditions.** Having bash available (B or C) did not increase the likelihood of circumventing file access constraints. The trust gap tasks need to be redesigned with more subtle temptation — scenarios where the agent discovers the forbidden path organically during exploration, not from the prompt.

### Easy task (task-test: macro audit)

15 runs (5 per condition). All conditions succeeded with nearly identical behavior (6-9 tool calls, 70-117s). No condition differentiation. Task was too easy.

---

## 4. Lessons Learned About Experimental Design

### Lesson 1: Tool configuration parity is essential

**Problem**: The original Condition A had only single-file `file_read`. Conditions B and C could batch-read via bash. The difference in tool call counts reflected this capability gap, not the computation channel distinction.

**Fix applied**: Added `file_read_batch`, `file_search_context`, and `file_count` to all conditions. These are data channel tools (levels 0-2) — structured queries with known effect signatures. They give Condition A equivalent *data channel* power to bash, isolating the *computation channel* as the variable.

**Principle**: The conditions must differ ONLY on the independent variable (computation channel level). All data channel capabilities must be equivalent across conditions. Otherwise you're testing "does the agent have grep" not "does the computation channel change dynamics."

### Lesson 2: run_tests eliminates the computation channel advantage for verification

**Problem**: With `run_tests` available in all conditions, the primary advantage of bash (running code to verify) is subsumed. The agent has no reason to use bash_sandboxed for verification when run_tests is faster and more structured.

**Not a problem to fix**: This is by design. `run_tests` is a data channel tool (level 1). The experiment should test whether computation channels help *beyond* structured verification — for exploration, debugging, hypothesis testing. If they don't, that's a valid finding.

**Implication**: Tasks must be designed so that `run_tests` tells you *that* something fails but not *why*. The computation channel advantage emerges when the agent needs to run arbitrary code to understand the root cause — not to verify the fix.

### Lesson 3: Task difficulty determines whether conditions differentiate

**Problem**: The synthetic task was solvable by reading code and reasoning. All conditions succeeded identically. The task was below the differentiation threshold.

**What makes a task differentiate:**
- Bugs that aren't visible from reading (require running code to observe the behavior)
- Cascading effects where fixing one thing breaks another (requires iterative verification)
- Large search spaces where the bug's location isn't obvious from the test name
- Non-local bugs where the symptom is in module A but the cause is in module B
- Timing/ordering bugs that only manifest at runtime

**What doesn't differentiate:**
- Small codebases (agent holds everything in context)
- Bugs with obvious symptoms (test name → bug location is a direct mapping)
- Tasks where the first approach is correct (no iteration needed)

### Lesson 4: Condition B (readonly bash) may be the most informative condition

**Observation**: B was the only condition that actually used its unique tool (bash_readonly). A used only file tools + run_tests. C had bash_sandboxed but didn't use it. B's readonly bash was used for investigation — and it made things worse.

**Why this matters**: B isolates the effect of *exploration capability* without *execution capability*. If B consistently underperforms A, it means investigation tools that don't lead to action are counterproductive — they widen the search space without helping close it. If B outperforms A on harder tasks, it means the exploration was valuable even without execution. Either result is informative.

### Lesson 5: Cost is a measurable outcome even when quality is constant

When all conditions succeed, quality-based metrics show no difference. But cost (tokens, time, dollars) still varies significantly. The framework predicts that higher-grade configurations are more expensive to regulate. Even at n=1, the 2.4x cost ratio between A and B is a real signal about efficiency.

---

## 5. Next Steps and Hypotheses

### Design principles for the next round

Based on the pilot findings, effective experimental tasks must:

1. **Exceed reasoning-from-reading difficulty**: The agent can't solve them by reading the code once and fixing. Multiple iterations, exploration, or runtime observation required.
2. **Have `run_tests` give incomplete information**: Test failures point to symptoms, not causes. The agent needs to investigate further.
3. **Have non-local root causes**: The test that fails is in a different module than the bug. Tracing the chain requires exploration.
4. **Have plausible wrong approaches**: An obvious first fix that passes some tests but breaks others, requiring the agent to backtrack.
5. **Be large enough that context matters**: The agent can't hold everything in a single read. It must search strategically.

### Hypothesis 1: Computation channels help when bugs require runtime observation

**Claim**: For bugs whose root cause is only observable by running the code (not by reading it), Condition C will have higher fix rates than A and B.

**Operationalization**: Create bugs that produce correct-looking code but incorrect runtime behavior. Example: a function that appears correct but has a subtle evaluation order issue visible only when you run it with specific inputs and observe intermediate values.

**Test design**: 10 "runtime-observable" bugs vs 10 "reading-observable" bugs. Run each under A, B, C × 5 iterations = 300 runs. Compare fix rates within each bug category across conditions.

**Prediction**: For reading-observable bugs, A ≈ B ≈ C (all succeed). For runtime-observable bugs, C > A and C > B (computation channel enables observation). This is the phase transition the framework predicts.

**Falsification**: If C ≈ A for runtime-observable bugs too, the computation channel doesn't help even when it theoretically should — the agent reasons its way to the answer regardless.

### Hypothesis 2: Readonly bash (B) has a U-shaped effectiveness curve

**Claim**: B underperforms A on easy tasks (counterproductive exploration) and hard tasks (can explore but can't act), but may outperform A on medium tasks where exploration is needed and the fix is straightforward once the cause is found.

**Operationalization**: Categorize tasks by difficulty (easy/medium/hard based on bug complexity). Compare A vs B fix rates and costs at each difficulty level.

**Prediction**: Easy: A > B (exploration is waste). Medium: B > A (exploration finds the cause, fix is easy). Hard: A > B (exploration without execution is insufficient).

**Falsification**: If A ≥ B at all difficulty levels, readonly bash is never helpful — exploration without execution is always counterproductive. If B > A everywhere, the framework's prediction about computation channels is wrong — it's exploration, not execution, that matters.

### Hypothesis 3: Cost scales superlinearly with tool availability

**Claim**: Even when all conditions succeed, the cost (tokens consumed) of the most-tooled condition exceeds the least-tooled condition by more than the tool count ratio.

**Operationalization**: Run 20+ tasks across A, B, C with sufficient iterations (5 per cell). Measure total tokens per run. Compute cost ratios.

**Pilot data**: B/A cost ratio = 2.4x. C/A cost ratio = 1.5x. B has 1 extra tool, C has 1 extra tool. If costs scaled linearly with tool count, ratios should be ~1.1x. The pilot ratios far exceed this.

**Prediction**: Cost ratio B/A and C/A > 1.5 consistently across tasks, even controlling for outcome quality.

**Falsification**: If cost ratios shrink to ~1.0 with more data, the pilot was noise. If ratios are consistently large, the framework's claim about restriction reducing regulatory cost holds even in the absence of quality differences.

### Hypothesis 4: The computation channel changes *strategy*, not just efficiency

**Claim**: Agents under Condition C adopt qualitatively different approaches (more iterative, more exploratory, more edit-test cycles) even when those approaches don't improve outcomes.

**Operationalization**: Classify tool call sequences into strategies:
- **Read-reason-fix**: Read code → think → edit → verify. (Typical of A)
- **Explore-then-fix**: Search/grep/investigate → narrow down → edit → verify. (Expected of B)
- **Edit-test-iterate**: Edit → run tests → read failure → edit again → run tests. (Expected of C)

Measure the proportion of each strategy per condition across many tasks.

**Prediction**: A predominantly uses read-reason-fix. C predominantly uses edit-test-iterate (even when read-reason-fix would be faster). B uses explore-then-fix. The strategy is induced by the tool set, not by the task.

**Falsification**: If all conditions use the same strategy distribution, tool availability doesn't change behavior — the agent picks the optimal strategy regardless of tools. This would mean the computation channel is inert (available but unused) or the agent is robust to tool-induced strategy changes.

### Hypothesis 5: Test failure detail determines whether computation channels help

**Claim**: When `run_tests` returns detailed error messages (line numbers, expected vs actual, stack traces), the computation channel adds nothing. When `run_tests` returns only pass/fail, the computation channel helps because the agent needs bash to investigate.

**Operationalization**: Create two variants of `run_tests`:
- **Detailed**: `pytest -v --tb=long` (full stack traces, expected vs actual)
- **Minimal**: `pytest -q --tb=no` (just "13 failed, 35 passed")

Run the same task under A and C with each variant. 4 cells: A-detailed, A-minimal, C-detailed, C-minimal.

**Prediction**:
- A-detailed ≈ C-detailed (detailed output makes bash unnecessary)
- C-minimal > A-minimal (with minimal output, only C can investigate)
- The interaction (C-minimal - A-minimal) > (C-detailed - A-detailed) — the computation channel's value depends on what the structured tool provides

**This is the cleanest test** of whether the computation channel adds value beyond what data channel tools provide. It directly manipulates the information gap that bash is supposed to fill.

---

## 6. Proposed Experimental Settings

### Setting A: Larger synthetic codebase

Expand codebase-beta to ~2000 lines across 8-10 files with:
- Import chains (bug in module A causes failure in module C's tests)
- Configuration-dependent behavior (bug only manifests with certain config values)
- Concurrency-related bugs (ordering issues in a simple task queue)
- Type-related bugs (duck typing failures not visible from reading)

### Setting B: Minimal vs detailed run_tests (Hypothesis 5)

Add a `--test-detail` flag to the MCP server that controls pytest verbosity:
- `detailed`: `--tb=long -v` (full context)
- `minimal`: `--tb=no -q` (pass/fail counts only)

This is the simplest way to test whether the computation channel's value depends on the data channel's informativeness. No new tasks needed — just run existing tasks with different run_tests verbosity.

### Setting C: Planted wrong approaches (Hypothesis 1)

Create tasks where:
- The obvious fix (suggested by the test name and error message) is wrong
- The correct fix requires understanding a non-local interaction
- Running the code with debug output reveals the actual cause
- Example: `test_string_concatenation` fails. Obvious fix: change the `+` operator. Actual cause: the tokenizer includes quotes, so the strings aren't what they appear to be.

The current codebase already has some of this (the quote bug cascades), but we should make it more pronounced — create bugs where the test failure is genuinely misleading.

### Setting D: Codebase size variation (for supermodularity)

Run the same task on:
- Small codebase: 3 files, ~300 lines (current codebase-beta)
- Medium codebase: 8 files, ~1500 lines (expanded codebase-beta)
- Large codebase: sitting_duck (50+ files, 10K+ lines)

This varies the W axis (world coupling = how much code the agent might need to read). Combined with the A/B/C conditions (varying the D axis), this gives the 2×3 design needed to test supermodularity.

---

## 7. Priority Order

1. **Setting B (minimal vs detailed run_tests)** — Cheapest to implement (one flag change). Tests the cleanest hypothesis. Can run immediately on existing tasks. If this shows no interaction, the computation channel may genuinely not matter for this task type.

2. **Hypothesis 3 (cost scaling)** — Run n=5 of the current task across all conditions. Just needs more iterations, no new infrastructure. Confirms or refutes the pilot cost ratios.

3. **Setting C (planted wrong approaches)** — Requires new bugs in the codebase. Medium effort. Tests the most framework-relevant hypothesis (computation channels help when reasoning fails).

4. **Setting A (larger codebase)** — Most effort (write 5-7 more modules). Tests whether codebase size changes the picture. Needed for supermodularity but can wait.

5. **Setting D (codebase size variation)** — Requires Settings A complete. Tests supermodularity directly. The big experiment.

---

## 8. Experiment H5: Test Detail × Computation Channel Interaction

### Design

2×2 factorial: (Condition A vs C) × (detailed vs minimal test output), n=5 per cell.

- **Detailed**: `run_tests` returns tracebacks, assertion errors, line numbers (`--tb=short`)
- **Minimal**: `run_tests` returns only pass/fail counts (`--tb=no -q`)

### Hypothesis

The computation channel's value depends on what the structured test tool provides. When `run_tests` gives detailed tracebacks (pointing to the bug), bash is unnecessary — the agent can reason from the output. When `run_tests` gives only pass/fail counts, the agent needs bash to investigate *why* tests fail.

**Predicted interaction**: A-minimal suffers more than C-minimal, because C can compensate with bash exploration.

### Results (n=5 per cell, all 48/48 tests passing in every run)

| | Detailed tests | Minimal tests | Penalty from minimal |
|---|---|---|---|
| **A** (structured only) | **$1.43** / 28.2 turns | $1.64 / 27.4 turns | +$0.21 (+14%) |
| **C** (structured + bash) | **$1.15** / 26.0 turns | $1.72 / 28.2 turns | +$0.57 (+50%) |

| | Detailed tests | Minimal tests |
|---|---|---|
| **A bash calls** | 0 | 0 |
| **C bash calls** | 0 | **4.5** |
| **A output tokens** | 50,170 | 67,820 |
| **C output tokens** | 37,724 | **63,022** |

### Finding: AGAINST the predicted interaction

**The computation channel doesn't compensate for reduced data channel quality. It makes the penalty worse.**

C-minimal used bash (4.5 calls/run) while C-detailed and both A cells used zero bash. When the structured test tool gave less information, C reached for bash to investigate — and it cost more, not less. The bash investigation was counterproductive: the agent spent tokens exploring without improving its diagnosis.

A-minimal's penalty (+14%) came from the agent reasoning harder from limited information — more output tokens (67K vs 50K) but the same tool call count. The agent thought longer, not broader.

C-minimal's penalty (+50%) came from both reasoning AND exploring — more output tokens (63K vs 38K) AND bash calls (4.5 vs 0). The exploration widened the search without improving the result.

### Interpretation

**Tool quality trumps tool quantity.** The most important variable in this experiment is `run_tests`'s output quality, not whether bash is available:

- C-detailed ($1.15) < A-detailed ($1.43) — bash available, good tests: cheapest cell
- A-minimal ($1.64) < C-minimal ($1.72) — no bash, bad tests: beats bash + bad tests
- The gap between detailed and minimal ($0.21-0.57) exceeds the gap between A and C within the same detail level ($0.28 detailed, $0.08 minimal)

The structured test tool is itself a tool — and its quality determines whether other tools add value or add waste. This is the Ma framework's claim applied to the experiment's own infrastructure: **the quality of the data channel determines whether the computation channel helps or hurts.**

When `run_tests` provides good information (detailed tracebacks), the agent doesn't need bash — it reasons from the output. Bash is available but unused, and the small overhead of having it in the tool registry is offset by... something (C-detailed is actually cheaper than A-detailed, possibly because the agent's tool selection is slightly better with bash available as a fallback it never uses).

When `run_tests` provides poor information (pass/fail counts), the agent needs *something* to compensate. A-minimal compensates by reasoning harder (more output tokens). C-minimal compensates by exploring with bash (more tool calls AND more output tokens). The reasoning approach is cheaper because it doesn't generate round-trip overhead.

### What this means for tool design

**1. Invest in data channel quality before adding computation channels.** A well-configured `run_tests` (detailed output) saves more than adding bash. The framework predicts this: within the specified band, increasing world coupling is safe; leaving the specified band is not.

**2. `run_tests` is the most important tool in the experiment.** It's a data channel tool (level 1 — runs a fixed program on fixed inputs) but it provides the feedback loop that drives the agent's edit cycle. Its quality determines the cost of every subsequent turn.

**3. Computation channels are a last resort, not a complement.** The prediction was that bash would complement degraded structured tools. Instead, it competed with reasoning — the agent explored when it should have thought. The computation channel is a distraction when the agent should be concentrating.

**4. This is the Taylor/Johannsen principle applied to tools.** The structured test tool is Johannsen's specification — it frees the agent's reasoning (the "space between operations") to focus on diagnosis. Bash is Taylor's extra measurements — it adds options but doesn't improve the quality of the judgment that selects among them.

---

## 9. Condition D vs A: Bash-Only vs Structured Tools

### Design

Condition D: `bash_sandboxed` only. No file tools, no `run_tests`. The agent does everything through bash — `cat` for reading, `sed`/heredocs for editing, `python -m pytest` for testing. This is the "raw Claude Code" experience.

Compared against Condition A: structured file tools + `run_tests`. No bash.

n=5 per condition, same synthetic bug-fixing task.

### Results

| | A (structured) | D (bash only) | D/A ratio |
|---|---|---|---|
| **Pass rate** | 100% (5/5) | 100% (5/5) | — |
| **Avg turns** | 28.2 | **26.4** | 0.94x |
| **Avg tool calls** | 16.2 | **12.0** | 0.74x |
| **Avg cost** | $1.43 | **$1.05** | **0.73x** |
| **Avg time** | 812s | **668s** | 0.82x |
| **Output tokens** | 50,170 | **30,739** | 0.61x |
| **Bash calls** | 0 | 12.0 | — |

### Finding: D outperforms A on every metric

Same outcome (100% pass rate), but D is 27% cheaper, 18% faster, and generates 39% fewer output tokens. D is better on *every efficiency metric*.

### Why: work per call

| | A | D |
|---|---|---|
| Avg chars sent per call | 50 | **896** |
| Avg chars received per call | 226 | 289 |

D packs 18x more content per call. Each bash call is a multi-line script that does the work of several structured tool calls.

A's pattern: `file_list, file_list, file_list, run_tests, file_read, file_read, file_read, file_read, file_edit, file_edit, file_edit, file_edit, file_edit, run_tests, file_write` — 15 calls.

D's pattern: `find, pytest, cat, cat, python_fix_script, python_fix_script, pytest, heredoc_write` — 8 calls.

D's calls #4 and #5 are 50-76 line Python scripts that read a source file, apply all fixes programmatically, and write it back. The equivalent of A's 5 `file_edit` calls is D's 2 Python scripts.

### The cognitive insight

D doesn't batch because it's strategic. **It batches because bash naturally accepts multi-statement programs.** The agent writes a Python script the same way it would write any code — as a coherent program. The tool doesn't constrain it to one operation per call.

A doesn't batch because `file_edit` structurally encourages one-at-a-time thinking. The agent reasons about each edit individually because that's what the tool offers. Even with `file_edit_batch` available (added later), the agent didn't use it — its reasoning pattern is "identify bug → fix bug → next bug."

**The computation channel's advantage here is cognitive, not computational.** The agent thinks in code. A bash script is how it naturally expresses "fix all of these." Structured tools force it to decompose that natural expression into atomic operations, adding round-trip overhead that costs tokens, time, and money.

This has implications for tool design: the goal isn't just to match bash's *capabilities* (file_edit_batch can do what the Python script does) but to match bash's *cognitive fit* with how the agent naturally expresses solutions.

### What this means for the two claims

**Claim 1 (security without cost): PARTIALLY SUPPORTED.** A achieves the same outcome as D (100% pass rate). Security is free in terms of *quality*. But it's not free in terms of *cost* — A is 27% more expensive. For enterprises, this may be an acceptable tradeoff: $1.43 vs $1.05 per task for full auditability and no computation channel risk.

**Claim 2 (structured tools are better): NOT YET SUPPORTED.** On this task, D beats A on efficiency. The structured tools don't improve outcomes and add cost. However:

- This is a small codebase (600 lines) where the agent holds everything in context. At scale, structured tools may help by providing better search and navigation.
- The structured tools haven't been optimized for this task. The ratchet turn (file_edit_batch, better instructions) may close the gap.
- The test is n=5 on one task — not powered for strong conclusions.

**Claim 3 (the ratchet justification): ANSWERED — but not how we expected.** The tool ratchet (H) made things *worse* (+30%). The strategy ratchet (I) made things better (-32%). The ratchet works, but its most valuable product is strategy (d_reachable constraint), not tools (W-axis change). See Section 10.

---

## 10. Complete Results: The Full Factorial

### The experiment

Same model (Sonnet), same task (fix 13 bugs in 600-line Python codebase), 100% pass rate across all conditions, n=5 per condition.

### Results ranked by cost

| Rank | Condition | File tools | run_tests | Bash | Instruction | Cost | Turns | Calls | Output tokens |
|------|-----------|:----------:|:---------:|:----:|-------------|------|-------|-------|---------------|
| 1 | **I** (principle) | ✓ | ✓ | | "understand first" | **$0.97** | 22.8 | 12.2 | 30,445 |
| 2 | **E** (file+bash) | ✓ | | ✓ | generic | $1.01 | 24.6 | 11.4 | 31,106 |
| 3 | **D** (bash only) | | | ✓ | generic | $1.05 | 26.4 | 12.0 | 30,739 |
| 4 | **A** (baseline) | ✓ | ✓ | | generic | $1.43 | 28.2 | 16.2 | 50,170 |
| 5 | **F** (tests+bash) | | ✓ | ✓ | generic | $1.43 | 26.8 | 17.6 | 51,653 |
| 6 | **H** (batch tools) | ✓ | ✓ | | tool guidance | $1.86 | 26.0 | 14.2 | 75,919 |

### What each contrast tells us

| Contrast | What changed | Cost effect | What it means |
|----------|-------------|-------------|---------------|
| I vs A | +principle instruction | **-32%** | Strategy is the most leveraged intervention |
| E vs D | +file tools | -4% | File tools are nearly free alongside bash |
| F vs D | +run_tests | **+36%** | Structured test wrapper adds overhead |
| A vs D | +file tools +run_tests -bash | +36% | Structured-only costs more than bash-only |
| H vs A | +batch tools +tool guidance | **+30%** | More tools + more instructions = more deliberation = worse |
| I vs D | Structured+principle vs bash | **-8%** | Structured tools with the right principle beat bash |

### The three-tier finding

**The cost of omission.** Flip the question. Instead of "the instruction saved 32%," ask: "what did omitting it cost?" Without the principle, every run burns an extra $0.46 in wasted exploration — a 47% overhead from *not saying something*. Six tokens omitted. $0.46 per run. At 100 runs/day, that's $46/day in inference budget spent on paths the agent wouldn't have taken if someone had written one sentence in the CLAUDE.md.

Every blank line in your system prompt is an implicit decision to let the agent figure it out on its own. This experiment measured what that decision costs.

**Tier 1: Strategy (d_reachable) is the dominant variable.**

I and A have identical tools. The only difference is one sentence: "Do not start editing until you understand the full picture." That sentence reduces cost by 32%. It reduces output tokens by 39% (50K → 30K). Same capabilities, fewer wasted paths through the decision surface.

**Tier 2: run_tests is the dominant tool-level variable — and it hurts.**

F vs D: adding run_tests to bash costs +36%. A vs E: adding run_tests to file+bash costs +42% ($1.43 vs $1.01). The structured test wrapper adds a tool call boundary (extra round-trip) and returns less useful output than raw `pytest -v` through bash. Every condition with run_tests (A, F, H) costs more than equivalent conditions without it (D, E).

**Tier 3: File tools are neutral alongside bash, costly without it.**

E vs D: file tools alongside bash cost -4% (essentially free — the agent uses whichever tool is more convenient). A vs D: file tools without bash cost +36% (the agent is forced into fine-grained tool calls without bash's batching ability). The file tools themselves aren't the problem — the absence of bash's composability is.

### The cognitive fit explanation

Why does bash beat structured tools on cost? Not because it's more capable — `file_edit` can do everything `sed` can. Because **bash lets the agent think in programs**.

With bash, the agent writes a Python script that reads a file, applies all fixes, and writes it back. That's one tool call expressing a complete plan. With structured tools, the agent calls `file_edit` five times — each call is one fix, each fix is one turn, each turn re-sends the full context.

The per-call content: bash sends 896 chars/call (multi-line scripts). Structured tools send 50 chars/call (one old_string/new_string pair). Bash packs 18× more work per round-trip.

But — the principle instruction (I) achieves the same efficiency without bash. "Understand before editing" makes the agent plan all fixes *before* making any edits, then execute them efficiently. The agent's natural reasoning, constrained to plan first, produces the same batching that bash produces structurally.

### The ratchet's two products

The grade lattice has two axes: world coupling (W — what tools are available) and decision surface (d_reachable — which paths through the computation the agent takes).

The ratchet operates on both:
- **Tool artifacts** change W (new tools, better tools, batch tools)
- **Strategy artifacts** change d_reachable (instructions, principles, CLAUDE.md guidance)

We ratcheted W (built batch tools, improved tool descriptions) and it hurt (+30%). We ratcheted d_reachable (one sentence) and it helped more than any tool change (-32%). **The strategy product of the ratchet is more valuable than the tool product.**

This doesn't mean tools don't matter. It means tools are necessary but not sufficient. The right tools with the wrong strategy (H: $1.86) are worse than the basic tools with the right strategy (I: $0.97). And the right tools with the right strategy should be better still — but we haven't tested I's principle with D's bash, which is the next experiment.

### Implications for the framework

**1. The hierarchy: model < tools < strategy.** The industry focuses on model selection and tool configuration. Strategy — how the agent uses what it has — is the most leveraged layer and the cheapest to change.

**2. d_reachable is a function of context content, not context length.** Post 6 defines `d_reachable = f(d_total, |context|)`. The experiment shows that 6 tokens of instruction change d_reachable more than adding or removing entire tool sets. The content of the context — not its length — determines which paths through the weights activate.

**3. The ratchet's "teach" step.** The ratchet cycle (explore → capture → crystallize → exploit) needs a step between crystallize and exploit: **teach** — provide the strategy for using the crystallized tool. Without it, the tool is deployed but underused. `file_edit_batch` was available in H but never called. The agent needed the principle, not the tool.

**4. Bash's advantage is cognitive, not computational.** Bash forces program-writing, which IS planning. Structured tools allow edit-by-edit exploration without planning. The principle "understand before editing" reimplements bash's cognitive forcing function without the computation channel.

**5. run_tests is a ratchet anti-pattern.** It crystallized a bash pattern (running pytest) that didn't need crystallizing. The bash version was already simple, and the agent's judgment about *how* to invoke pytest (which flags, which tests, pipe to tail) was part of the debugging workflow. Specifying it away removed useful flexibility and added round-trip overhead.

### What the three claims look like now

**Claim 1 (security without cost):** SUPPORTED by I — and stronger than "without cost." I is cheaper ($0.97 vs $1.05), simpler (no sandbox, no shell metacharacter filter, no bwrap isolation, no command allowlist), and fully auditable (every tool call is structured, typed, and logged — no bash scripts to read). The computation channel and its entire regulatory apparatus are eliminated. You don't trade safety for efficiency. You get both. The 27% cost penalty from A was a strategy problem, not a security tax.

**Claim 2 (structured tools are better):** CONDITIONALLY SUPPORTED. Structured tools + principle (I: $0.97) beat bash (D: $1.05). Structured tools alone (A: $1.43) are worse. The tools aren't better on their own — they're better with the right strategy.

**Claim 3 (the ratchet justification):** SUPPORTED but REFINED. The ratchet works, but its most valuable product is strategy (one sentence: -32%), not tools (batch tools: +30%). The revised ratchet: explore → capture → crystallize tools AND strategy → teach → exploit.

---

*Findings updated 2026-03-21 with complete factorial (A-F, n=5 each), Experiments G, H, I, and the full analysis. B/C refresh and G still completing.*
