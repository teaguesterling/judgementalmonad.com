# Experiment Session 3: Trust Gap Measurement (Experiment 6)

*Tests whether the trust gap is measurable and whether crystallization (the ratchet) shrinks it.*

---

## Prerequisites

From prior sessions:
- `experiments/experiment-12-results.md` — Definition consistency (read for context)
- `experiments/task-suite.md` — Task suite (30+ tasks)
- `experiments/tools/specified-observer.sql` — The specified observer (from Session 2)
- `experiments/tools/sandbox-diff-hook.sh` — Sandbox diffing (from Session 2)
- `experiments/experiment-3-results.md` — Phase transition results (read for context)
- `experiments/failure-log.md` — Ongoing failure log (continue logging)
- `~/.claude/projects/.../memory/protocol_failure_logging.md` — Follow this protocol

Read:
1. `drafts/note-for-agents.md`
2. `drafts/experiment-statistics.md` — Section "Experiment 6: Trust Gap Measurement"
3. `drafts/experiment-designs.md` — Experiment 6 description
4. Memory files

Read blog posts 7 (Computation Channels) and the configuration ratchet essay. This experiment tests the ratchet's mechanism.

---

## What this experiment tests

**Claim C1:** The trust gap (reachable minus expected) is a measurable quantity that tracks with regulation difficulty.

**Claim C4:** Type honesty — crystallizing a bash pattern into a structured tool — reduces the trust gap measurably.

**The framework predicts:** When a bash pattern is replaced by a structured tool, the gap rate (proportion of unpredicted tool calls) should decrease because the structured tool's argument space is enumerable while bash's is not.

---

## This session has four tasks.

### Task 1: Identify ratchet promotion candidates (~1 hour)

This experiment is paired with the longitudinal study (Experiment 4). It requires bash patterns that are candidates for crystallization.

**From the Experiment 3 data:** Review the tool call sequences from the 90 Experiment 3 runs. Identify bash patterns that:
- Appeared 5+ times across different tasks
- Succeeded consistently (>80% success rate)
- Have identifiable world dependencies and side effects
- Are candidates for promotion to structured tools

**From the failure log:** Check `experiments/failure-log.md` for any ratchet observations logged during normal work.

**From the user's existing tools:** Review Fledgling's tool list — which bash patterns has the user *already* promoted? These provide a natural before/after comparison (historical data from before Fledgling existed vs current data with Fledgling).

**Produce:** `experiments/experiment-6-candidates.md` listing 20-30 bash patterns with:
- The command pattern and its variants
- Frequency and success rate (from Experiment 3 data)
- World dependencies (reads what?)
- Side effects (modifies what?)
- Totality (always returns, or can hang?)
- Promotion plan: what structured tool would replace it?

### Task 2: Measure pre-promotion gap rate (~2-3 hours)

For each of 20-30 task types that exercise the identified bash patterns:

1. Run the task with bash available (the computation channel configuration from Experiment 3 Condition C)
2. At each tool call, record the specified observer's prediction and the actual call
3. Compute gap rate: proportion of tool calls the observer didn't predict
4. Run each task type 3-5 times to get a reliable gap rate estimate

**Use three observer complexities:**
- Bigram: P(tool_n | tool_{n-1})
- Trigram: P(tool_n | tool_{n-2}, tool_{n-1})
- Task-aware: P(tool_n | tool_{n-1}, task_type)

Report gap rate at each complexity level. The observer must be the SAME frozen observer from Session 2 — do not retrain it.

**Write raw data to:** `experiments/experiment-6-raw/pre-promotion/`

### Task 3: Crystallize and measure post-promotion gap rate (~2-3 hours)

For each bash pattern identified in Task 1:

**Stage 1 (Discovery) measurements:**
- Record the command string and its variants from the pre-promotion runs
- Characterize the gap between `IO String` (what the type says) and observed behavior
- Document world dependencies, side effects, totality

**Stage 2 (Crystallization):**
- Build the structured tool that replaces the bash pattern
- Record what type commitments the new tool makes (effect signature, totality, structured output)
- Verify: can the implementation violate its declared effects? (Type honesty check)
- If the tool makes commitments the implementation can't back, flag it as aspirational — this is a C3 falsification data point

**Post-promotion measurement:**
- Run the same task types with the structured tool replacing the bash pattern
- 3-5 runs per task type
- Same specified observer, same prediction protocol
- Compute gap rate

**Write raw data to:** `experiments/experiment-6-raw/post-promotion/`

### Task 4: Analyze results (~1 hour)

**Compile to:** `experiments/experiment-6-results.md`

**Primary analysis (C4):**
1. For each task type: compute mean gap rate pre-promotion and post-promotion
2. Paired Wilcoxon signed-rank test (one-sided: pre > post)
3. Report gap rate reduction with 95% confidence interval
4. Report effect size (matched-pairs rank-biserial correlation)

**Secondary analysis (C1):**
1. Compute Spearman rank correlation between gap rate and task failure rate (from Experiment 3)
2. Report ρ with 95% CI and p-value
3. If significant: the trust gap tracks with regulation difficulty

**Observer complexity analysis (exploratory):**
1. Report gap rate at each observer complexity (bigram, trigram, task-aware)
2. Does gap rate decrease with observer complexity? (Expected: yes, but with diminishing returns)
3. At what complexity does the observer stop improving? This characterizes where additional observer ma stops helping.

**Type honesty audit (C3):**
1. For each crystallized tool: does the implementation back its type commitments?
2. Report the proportion of honest vs aspirational types
3. C3 fails if tools make commitments implementations can't back

**Interpret:**
- Does crystallization shrink the trust gap? By how much?
- Is the trust gap a useful predictor of regulation difficulty?
- Were the two stages (discovery, crystallization) both necessary?
- Any tools where crystallization didn't help? Why?

---

## Deliverables

1. `experiments/experiment-6-candidates.md` — Ratchet promotion candidates
2. `experiments/experiment-6-raw/pre-promotion/` — Pre-promotion gap rate data
3. `experiments/experiment-6-raw/post-promotion/` — Post-promotion gap rate data
4. `experiments/experiment-6-results.md` — Analysis with statistical tests
5. Crystallized tools (if built) committed to appropriate repos

Commit everything. Update `experiments/README.md`.

---

## Notes

- This experiment naturally produces ratchet artifacts — the crystallized tools are real infrastructure improvements, not just experimental data.
- The specified observer must be frozen from Session 2. Do not retrain between pre and post measurements.
- If fewer than 20 bash patterns are identified as promotion candidates, the experiment is underpowered. Report what you have and assess whether partial results support any conclusions.
- Follow the failure logging protocol throughout.
