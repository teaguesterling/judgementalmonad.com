# Plan: SWE-bench Integration

*Adding real-world bug-fixing tasks from SWE-bench Verified to the experimental program.*

---

## Why

Our synthetic codebase (codebase-beta) is too small and too clean. Sonnet solves it in one pass regardless of tool configuration. SWE-bench gives us:

- **Real bugs** in real codebases with known solutions and automated grading
- **Difficulty calibration** — human-estimated fix times from 15 minutes to 4+ hours
- **Natural condition differentiation** — larger codebases where bash exploration genuinely helps navigate
- **External validity** — results comparable to published benchmarks
- **Direct connection** to Crandall's "78% vs 42%" claim (likely measured on similar tasks)

## What we're testing

Same hypothesis as the synthetic tasks, but at realistic scale: **does the computation channel change debugging behavior and outcomes when the codebase is large enough that reasoning-from-reading alone is insufficient?**

Our pilot showed that for a 600-line codebase, all conditions succeed identically. SWE-bench tasks operate on codebases of 5K-300K lines — where the search space exceeds what the agent can hold in context, and strategic exploration matters.

## Dataset: SWE-bench Verified

500 tasks across 12 Python repos, each human-validated by software engineers. Key fields per task:

| Field | What it is |
|-------|-----------|
| `instance_id` | e.g. `django__django-11099` |
| `repo` | GitHub owner/repo |
| `base_commit` | The commit before the fix |
| `problem_statement` | The GitHub issue text (becomes the agent's prompt) |
| `test_patch` | Tests added by the PR (applied before the agent works — these are the failing tests) |
| `patch` | The gold solution (never shown to agent — used for grading) |
| `FAIL_TO_PASS` | Test IDs that must flip from fail to pass |
| `PASS_TO_PASS` | Test IDs that must stay passing |
| `difficulty` | Human estimate: `<15 min`, `15 min - 1 hour`, `1 - 4 hours`, `>4 hours` |

## Task selection (20-30 tasks)

### Filter pipeline

```
500 Verified tasks
  → Filter difficulty: "15 min - 1 hour" and "1 - 4 hours" (~300)
  → Filter patch size: 5-200 diff lines (~200)
  → Filter FAIL_TO_PASS count: 1-10 tests (~180)
  → Filter problem statement: 80-1000 words (~150)
  → Filter Python compatibility: 3.10+ (~100)
  → Ensure repo diversity: 3-5 tasks per repo
  → Manual review for diagnostic quality
  → Final: 25 tasks
```

### Selection criteria for our experiment

Tasks should:
- **Require understanding program behavior** (not just fixing a typo)
- **Have diagnostic test failures** (point toward the bug without prescribing the fix)
- **Live in navigable codebases** (agent needs to find the right files, not just edit a known file)
- **Not require exotic environment setup** (installable with pip in a standard Python env)

### Repos to prioritize

| Repo | Size | Tasks available | Good for our experiment? |
|------|------|----------------|------------------------|
| requests | ~5K lines | Few | Yes — small, readable, bash helps navigate |
| flask | ~10K lines | Few | Yes — moderate size |
| pytest | ~50K lines | Many | Yes — good test infrastructure |
| xarray | ~50K lines | Some | Yes — data-oriented, moderate size |
| scikit-learn | ~150K lines | Many | Yes — large enough for exploration to matter |
| sympy | ~200K lines | Many | Moderate — very large, math-heavy |
| django | ~300K lines | Many | Moderate — very large, complex test setup |

## Integration architecture

### Preparation (one-time per task)

```
HuggingFace dataset → select_tasks.py → prepare_task.py
                       (filter)          (clone, checkout base_commit,
                                          apply test_patch, write TASK.md)
```

Each prepared task becomes a git repo with:
```
worktrees/{instance_id}/
  ├── (repo source at base_commit + test_patch applied)
  ├── TASK.md                    (problem_statement, formatted as task prompt)
  └── .swebench-metadata.json   (instance_id, fail_to_pass, pass_to_pass, gold_patch)
```

### Execution (per condition per task)

Same as current runner, with extensions:

```bash
./run-experiment.sh \
  --condition A \
  --task-id django__django-11099 \
  --task-file worktrees/django__django-11099/TASK.md \
  --repo worktrees/django__django-11099 \
  --test-cmd "python -m pytest" \
  --max-turns 100 \
  --max-budget 10.00
```

### Grading (after each run)

```python
# Extract agent's diff
git diff {test_patch_commit}..HEAD

# Run FAIL_TO_PASS tests — did they flip?
# Run PASS_TO_PASS sample — any regressions?

# Result: resolved (bool), tests_flipped (int), regressions (int)
```

## Changes needed to experiment infrastructure

### 1. `server.py` modifications

| Change | Why |
|--------|-----|
| Add `--test-cmd` argument | SWE-bench repos use different test runners (django test runner vs pytest) |
| Add `--test-dir` argument | Test directories vary by repo |
| Increase `run_tests` timeout to 300s | Real repos have heavier test suites |
| Add FAIL_TO_PASS-only mode | Running specific failing tests is faster than full suite |

### 2. New scripts

| Script | Purpose |
|--------|---------|
| `tools/swebench/select_tasks.py` | Filter and select tasks from Verified dataset |
| `tools/swebench/prepare_task.py` | Clone repo, create worktree, apply test patch |
| `tools/swebench/grade_task.py` | Run FAIL_TO_PASS and PASS_TO_PASS tests, report results |
| `tools/swebench/batch_run.sh` | Run selected tasks across conditions |

### 3. Dependencies

```
pip install datasets swebench
```

## Environment strategy

**Start simple (option D from research):** Pre-select tasks where the repo works with the system Python (3.12). Accept that some tasks will have environment issues. Exclude those from analysis rather than building per-task conda environments.

If too limiting, fall back to one venv per repo (not per task — tasks from the same repo share the same environment).

## Experimental design

### Primary comparison

25 SWE-bench tasks × 3 conditions (A, B, C) × 1 run = 75 runs

Measure:
- **Resolve rate**: Did the FAIL_TO_PASS tests flip? (Binary)
- **Regression rate**: Did any PASS_TO_PASS tests break?
- **Tool call patterns**: How many calls, which tools, what sequence?
- **Cost**: Tokens consumed per run
- **Time**: Wall-clock duration

### Predictions

The framework predicts:
- Condition C (bash_sandboxed) will have the **highest resolve rate** on harder tasks because the agent can run code to investigate
- Condition A (file tools only + run_tests) will have **competitive resolve rate** on easier tasks where the bug is findable by reading
- Condition B (bash_readonly) may **underperform A** on easy tasks (counterproductive exploration) but **outperform A** on hard tasks (exploration finds the right files)
- Cost will be **C > B > A** regardless of resolve rate

### The key test

If Condition A achieves the same resolve rate as C across all difficulty levels, the computation channel doesn't help even at scale — and the framework's prediction about computation channel dynamics is wrong for debugging tasks.

If C outperforms A specifically on harder tasks (1-4 hours) but not easier ones (15 min - 1 hour), that's the phase transition: below a complexity threshold, structured tools suffice; above it, computation channels enable strategies that structured tools can't.

## Interaction with Hypothesis 5

We can also run the `--test-detail` variation on SWE-bench tasks:
- `detailed`: run_tests shows full pytest output (tracebacks, assertions, line numbers)
- `minimal`: run_tests shows only "X failed, Y passed"

This tests whether the computation channel's value depends on what the structured test tool provides — and whether that dependency changes with codebase size.

## Cost estimate

- 75 runs × ~$2-5 per run = **$150-375** for the primary comparison
- With Hypothesis 5 variation (×2): **$300-750**
- With n=3 iterations: **$450-1125**

## Priority and sequencing

1. **Wait for H5 results** on synthetic tasks — if test detail doesn't matter even on small codebases, it won't matter on large ones
2. **Install dependencies** and run the selection script
3. **Prepare 5 pilot tasks** (one per repo, medium difficulty)
4. **Pilot run**: 5 tasks × 3 conditions = 15 runs to validate the pipeline
5. **Full run**: 25 tasks × 3 conditions = 75 runs
6. **Analysis**: Compare resolve rates, tool patterns, and costs across conditions and difficulty levels

## Risks

- **Environment setup may dominate**: If tasks fail because of missing dependencies rather than agent inability, the data is useless. Mitigation: pilot with known-good tasks first.
- **Django tasks may be too large**: 300K lines, complex test setup. Mitigation: select tasks from smaller repos first, add django only if pipeline works.
- **run_tests may be too slow**: Full django test suites take minutes. Mitigation: FAIL_TO_PASS-only mode for the agent's verification loop.
- **Tasks may be too hard for Sonnet**: SWE-bench Verified solve rates for frontier models are 30-50%. Many tasks may fail across all conditions, giving no condition differentiation. Mitigation: select from the easier end (15 min - 1 hour) and from repos where Sonnet is known to perform well.

---

*This plan should be executed AFTER the Hypothesis 5 batch completes and results are analyzed. The H5 results will inform whether the test-detail variation is worth running on SWE-bench tasks.*
