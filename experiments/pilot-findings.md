# Pilot Findings: Session 1-2

*Observations from infrastructure development and pilot runs, March 2026.*

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

*These findings are from pilot runs (n=1 per condition). All numerical comparisons are descriptive, not inferential. The next phase should produce data at n≥5 per cell for statistical testing.*
