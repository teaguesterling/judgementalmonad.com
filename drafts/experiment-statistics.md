# Statistical Design for Priority Experiments

*Formal hypotheses, power analyses, and pre-registered analysis plans for Experiments 3, 6, and 11.*

---

## General principles

- **One primary endpoint per experiment.** Secondary endpoints are exploratory and reported with that caveat.
- **Pre-registered analysis plan.** Written before data collection. Deviations documented.
- **Significance level:** α = 0.05 throughout, with Bonferroni correction for planned comparisons.
- **Power target:** 0.80 (80% chance of detecting the effect if it exists).
- **Effect sizes:** Estimated from the framework's qualitative predictions. Where the framework predicts a "qualitative shift," we target large effects (Cohen's d ≥ 0.8). Where it predicts a "measurable difference," we target medium effects (d ≥ 0.5).

---

## Experiment 3: Computation Channel Phase Transition

### Claims tested
- B3: Systems above the computation channel boundary show qualitatively different failure modes

### Design
Within-task, between-condition. Each task is run under three tool configurations:
- **Condition A:** Fledgling structured tools only (levels 0-2)
- **Condition B:** Fledgling + sandboxed Bash read-only (levels 2-3)
- **Condition C:** Fledgling + sandboxed Bash read-write (level 4)

### Hypotheses

**Primary:**
- H₀: Task failure rate is the same across all three computation levels: p_A = p_B = p_C
- H₁: Task failure rate increases with computation level: p_A < p_B < p_C
- Test: Cochran-Armitage trend test (one-sided, tests for monotone trend in proportions across ordered groups)

**Secondary (exploratory):**
- H₀: The distribution of failure modes (infidelity, side effect, partiality) is independent of computation level
- H₁: The distribution depends on computation level, with side effects and partiality increasing at level 4
- Test: Fisher's exact test on the failure mode × condition contingency table (preferred over chi-square for potentially small cell counts)

**Secondary (behavioral variance):**
- H₀: Entropy of tool call sequences is the same across conditions
- H₁: Entropy increases with computation level
- Test: Friedman test (non-parametric repeated measures, treating task as blocking factor)
- Note: Requires multiple runs per task-condition pair. Run on a 10-task subset × 5 runs each.

### Power analysis — primary endpoint

Assumptions:
- Expected failure rates: p_A = 0.15 (data channels, convergent), p_C = 0.40 (computation channels, self-amplifying)
- These estimates come from the framework's prediction of a "qualitative shift" — not a small difference

For Cochran-Armitage trend test detecting a linear trend from 0.15 to 0.40 across 3 groups:
- α = 0.05 (one-sided), power = 0.80
- **Required: n = 30 tasks per condition** (90 runs total)
- Paired design (same tasks across conditions) provides additional power — 25 tasks may suffice, but 30 provides margin

### Sample size
- **Primary:** 30 tasks × 3 conditions × 1 run = **90 runs**
- **Variance subset:** 10 tasks × 3 conditions × 5 runs = **150 additional runs**
- **Total:** 240 runs, ~$240-720

### Analysis plan

1. For each task × condition, record: success/failure, failure mode (if failed), full tool call sequence
2. Run Cochran-Armitage trend test on failure rates
3. If significant: report pairwise comparisons (A vs B, B vs C, A vs C) with Bonferroni-corrected α = 0.017
4. Report failure mode distribution as a table. Run Fisher's exact test — flag as exploratory
5. For the variance subset: compute sequence entropy per task-condition pair, run Friedman test

### Falsification
- B3 fails if the trend test is non-significant (p > 0.05) — no evidence that failure rate increases with computation level
- B3 weakened if the trend is significant but the A-vs-C comparison is not — the phase transition isn't where predicted
- B3 strengthened if failure mode distribution also shifts (more side effects and partiality at level 4)

---

## Experiment 6: Trust Gap Measurement

### Claims tested
- C1: Trust gap is measurable and tracks with regulation difficulty
- C4: Type honesty (crystallization) reduces the trust gap

### Design
Within-task paired design. Same task types, measured before and after a ratchet promotion cycle.

### Hypotheses

**Primary (C4):**
- H₀: Gap rate (proportion of unpredicted tool calls) is the same before and after crystallization: μ_pre = μ_post
- H₁: Gap rate decreases after crystallization: μ_pre > μ_post
- Test: Paired Wilcoxon signed-rank test (one-sided; non-parametric since gap rates are bounded proportions)

**Secondary (C1):**
- H₀: Gap rate does not correlate with task failure rate (regulation difficulty)
- H₁: Higher gap rate predicts higher task failure rate
- Test: Spearman rank correlation between gap rate and failure rate across tasks
- Note: This is a correlation, not a causal claim. It tests whether the trust gap concept tracks with something operationally meaningful.

**Exploratory (observer complexity):**
- Run the specified observer at three complexity levels: bigram, trigram, task-aware
- Report gap rate at each level
- No formal hypothesis — this characterizes where additional observer ma stops helping

### Power analysis — primary endpoint

Assumptions:
- Expected gap rate pre-promotion: 0.30 (Bash calls have unpredictable arguments ~30% of the time)
- Expected gap rate post-promotion: 0.15 (structured tool has enumerable argument space)
- Expected standard deviation of the difference: σ_d ≈ 0.15 (moderate variability)
- Effect size: d = (0.30 - 0.15) / 0.15 = 1.0 (large)

For paired Wilcoxon signed-rank test with d = 1.0:
- α = 0.05 (one-sided), power = 0.80
- **Required: n = 15 task types** (minimum)
- With d = 0.5 (conservative): n = 35 task types

### Sample size
- **Conservative:** 30 task types × 2 phases (pre/post) × 3-5 runs per phase = **180-300 runs**
- **Practical minimum:** 20 task types × 2 phases × 3 runs = **120 runs**, ~$120-360

### Analysis plan

1. Identify 20-30 bash patterns that are ratchet promotion candidates from the longitudinal study (Experiment 4)
2. Before promotion: run each task type 3-5 times with Bash available. Record tool call sequences. Compute gap rate per run using the specified observer.
3. Promote: build the structured tool (the crystallization step)
4. After promotion: run the same task types 3-5 times with the structured tool replacing Bash for that pattern. Compute gap rate.
5. For each task type: compute mean gap rate pre and post. Run paired Wilcoxon.
6. Report gap rate reduction with 95% confidence interval
7. Compute Spearman correlation between gap rate and failure rate (secondary)

### Specification of the observer

The observer must be pre-registered to avoid fitting it to the data:

**Bigram observer:** P(tool_n = t | tool_{n-1} = s) estimated from historical conversation logs. Predicts the most likely next tool given the previous tool. A tool call is "predicted" if the actual tool matches the observer's top-1 prediction (for gap rate) or top-3 predictions (for relaxed gap rate).

**Trigram observer:** P(tool_n = t | tool_{n-2} = r, tool_{n-1} = s). Same prediction rule.

**Task-aware observer:** Conditions on task type in addition to previous tools. P(tool_n = t | tool_{n-1} = s, task_type = k). Task types categorized as: bug-fix, feature-add, refactor, exploration, test-writing.

The observer is trained on historical data collected BEFORE the experiment begins. It is frozen and not updated during the experiment.

### Falsification
- C4 fails if the paired test is non-significant — crystallization didn't reduce gap rate
- C4 weakened if gap rate decreases but task outcomes don't improve — the gap reduction is real but not operationally meaningful
- C1 fails if gap rate doesn't correlate with failure rate (Spearman ρ not significantly different from zero) — the trust gap concept doesn't track with regulation difficulty

---

## Experiment 11: Autonomy Placement vs Magnitude

### Claims tested
- C9: Placement matters more than magnitude for system quality
- C10: Specification at one point improves quality at adjacent unspecified points

### Design
Between-condition (with task as blocking factor). Two-phase tasks: planning then execution. Three conditions:
- **Condition A (Uniform):** Medium tools in both phases
- **Condition B (Front-loaded):** Broad planning tools, narrow execution tools
- **Condition C (Back-loaded):** Narrow planning tools, broad execution tools

### Hypotheses

**Primary (C9):**
- H₀: Mean task quality is the same across conditions: μ_A = μ_B = μ_C
- H₁: At least one condition differs; specifically, B > A and B > C
- Test: Friedman test (non-parametric repeated measures ANOVA, with task as blocking factor), followed by Wilcoxon signed-rank pairwise comparisons with Bonferroni correction (α = 0.05/2 = 0.025 for two planned comparisons: B vs A, B vs C)

**Secondary (C10 — constraint creates freedom):**
- H₀: Execution quality under narrow tools (condition B, execution phase) ≤ execution quality under medium tools (condition A, execution phase)
- H₁: Execution quality under narrow tools (B) > execution quality under medium tools (A), because better planning compensated
- Test: Wilcoxon signed-rank (one-sided), paired by task
- This specifically tests whether constraint at the execution point, combined with good planning, produces BETTER execution than medium tools with medium planning

**Exploratory:**
- Approach quality scored separately from implementation quality (blind to condition)
- Wasted effort measured as proportion of tool calls not contributing to final result (reverted changes, abandoned approaches)

### Primary endpoint specification

**Task quality** is scored on a 1-5 rubric by a human rater blind to condition:

| Score | Criterion |
|-------|-----------|
| 1 | Task not completed or fundamentally wrong approach |
| 2 | Partially complete, major issues |
| 3 | Complete, correct, some issues (edge cases missed, non-idiomatic code) |
| 4 | Complete, correct, clean (handles edge cases, idiomatic, well-structured) |
| 5 | Complete, correct, elegant (better than what a competent human would typically produce) |

**Inter-rater reliability:** Two raters score independently. Report Cohen's weighted kappa (weighted because the scale is ordinal). Threshold: κ_w ≥ 0.60 (substantial agreement) before proceeding. If κ_w < 0.60, resolve disagreements through discussion and report resolved scores.

**Blinding:** The rater sees the final code output and the task description. They do NOT see which condition produced it, what tools were available, or the conversation log.

### Power analysis — primary endpoint

Assumptions:
- Expected quality scores: μ_A = 3.0 (uniform), μ_B = 3.8 (front-loaded), μ_C = 2.8 (back-loaded)
- Expected within-task standard deviation: σ ≈ 1.0
- Effect size for B vs A: d = (3.8 - 3.0) / 1.0 = 0.8 (large)
- Effect size for B vs C: d = (3.8 - 2.8) / 1.0 = 1.0 (large)

For Wilcoxon signed-rank test with d = 0.8:
- α = 0.025 (Bonferroni-corrected for 2 comparisons), power = 0.80
- **Required: n = 30 tasks**

For d = 0.5 (medium effect, more conservative):
- α = 0.025, power = 0.80
- **Required: n = 48 tasks**

### Sample size
- **Primary:** 30 tasks × 3 conditions × 1 run = **90 runs** (adequate for large effects)
- **Conservative:** 50 tasks × 3 conditions × 1 run = **150 runs** (adequate for medium effects)
- **Recommended:** Start with 30 tasks. If results are suggestive but non-significant, extend to 50 in a second batch (pre-register this as a sequential design with adjusted α).
- **Cost:** 90-150 runs × $1-3 = **$90-450**

### Task requirements

Tasks must satisfy ALL of:
1. Two natural phases (understanding/planning, then implementation)
2. Planning quality matters — a wrong approach wastes execution effort
3. Execution has a clear correctness criterion (tests pass, code compiles, behavior is correct)
4. Difficulty is moderate — too easy and all conditions succeed, too hard and all fail
5. Can be completed in a single session (~30 minutes)

Good candidates: bug fixes where the bug is non-obvious (planning: find the root cause; execution: fix it), feature additions to unfamiliar codebases (planning: understand the architecture; execution: add the feature), refactoring tasks (planning: identify what to change; execution: change it safely).

Bad candidates: tasks that are purely execution (no planning needed), tasks that require multi-session work, tasks where the "right approach" is obvious.

### Analysis plan

1. Pre-register: task list, conditions, rubric, raters, analysis plan
2. Randomize task-condition assignment (Latin square: each task appears in each condition, balanced across tasks)
3. Run all sessions. Collect code outputs.
4. Two raters independently score all outputs (blind to condition). Compute κ_w.
5. If κ_w ≥ 0.60: proceed with mean of two raters' scores
6. If κ_w < 0.60: resolve disagreements through discussion, report resolved scores, note the disagreement
7. Run Friedman test on quality scores (task × condition)
8. If significant: run planned comparisons (B vs A, B vs C) with Bonferroni-corrected Wilcoxon signed-rank
9. Report effect sizes with 95% confidence intervals
10. Report secondary endpoints (approach quality, execution quality, wasted effort) as exploratory

### Falsification
- C9 fails if Friedman test is non-significant AND neither planned comparison is significant — placement doesn't matter
- C9 weakened if B > C but B ≈ A — front-loading helps vs back-loading but not vs uniform (placement matters for avoiding bad placement, not for optimal placement)
- C10 fails if execution quality in B ≤ execution quality in A — narrow execution tools didn't benefit from better planning; constraint didn't create freedom, just reduced capability
- C10 strengthened if execution quality in B > execution quality in A — the Taylor/Johannsen principle holds empirically

---

## Summary of required resources

| Experiment | Tasks needed | Runs | Estimated cost | Time |
|-----------|-------------|------|---------------|------|
| 3 (Phase transition) | 30 | 90 primary + 150 variance subset | $240-720 | 2-3 days |
| 6 (Trust gap) | 20-30 task types | 120-300 | $120-360 | Runs alongside Exp 4 |
| 11 (Placement) | 30-50 | 90-150 | $90-450 | 2-3 days |
| **Total** | **30-50 unique tasks** | **300-690** | **$450-1530** | **Staggered over weeks** |

### Shared infrastructure requirements

1. **Task suite:** 30-50 tasks satisfying Experiment 11's criteria (two-phase, planning-matters, moderate difficulty). These can also serve Experiments 3 and 6.
2. **Specified observer:** Pre-trained on historical conversation logs, frozen before experiments begin.
3. **Quality rubric:** The 1-5 scale above, with worked examples for calibration.
4. **Two raters:** For Experiment 11. One can be the author; the second should ideally be independent.
5. **Randomization plan:** Latin square for Experiment 11 task-condition assignment.
6. **Sandbox diffing:** Git-based auto-commit hook for Experiments 3 and 6.

### Sequencing

1. **Now:** Start Experiments 4+9+10 (longitudinal, observational, zero cost)
2. **Week 1:** Run Experiment 12 (textual analysis, no compute cost)
3. **Week 1-2:** Build task suite and specified observer
4. **Week 2-3:** Run Experiment 3 (90 primary runs, produces failure data for Exp 9)
5. **Week 3-4:** Run Experiment 6 (paired with ratchet promotion from Exp 4)
6. **Week 4-6:** Run Experiment 11 (90-150 runs, needs completed task suite)

Experiments 3 and 11 can potentially share tasks if the task suite is designed to satisfy both sets of requirements.
