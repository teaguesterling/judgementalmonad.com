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

## Experiment 1: Supermodularity of Restriction Returns

### Claims tested
- B1: Restriction has superlinear returns when both axes are high
- A1 (indirectly): The independence assumption underlying Prop. 4.7 holds well enough for real systems

### Design
2×2 factorial within-task. Each task is run under four tool configurations that vary world coupling (W) and decision surface expressiveness (D) independently:

- **Condition LL:** Low W, Low D — Fledgling structured tools only, restricted to 3 specified files
- **Condition HL:** High W, Low D — Fledgling structured tools only, full codebase access
- **Condition LH:** Low W, High D — Fledgling + sandboxed Bash, restricted to 3 specified files
- **Condition HH:** High W, High D — Fledgling + sandboxed Bash, full codebase access

"Low W" = scoped to a pre-specified set of files (the task description names the relevant files). The agent can read only those files. "High W" = full codebase access. "Low D" = data-channel tools only (Fledgling structured queries). "High D" = computation channels available (Bash).

### Hypotheses

**Primary (supermodularity):**
- H₀: The effect of restricting D is the same regardless of W level. Formally: Quality(HL) - Quality(HH) = Quality(LL) - Quality(LH)
- H₁: The effect of restricting D is larger when W is high. Formally: Quality(HL) - Quality(HH) > Quality(LL) - Quality(LH)
- Equivalently: the interaction term in a 2×2 ANOVA is positive and significant
- Test: Two-way repeated measures ANOVA (task as blocking factor), testing the W×D interaction. One-sided test on the interaction term.

**Secondary (main effects):**
- H₀_W: World coupling has no effect on quality: Quality(H*) = Quality(L*)
- H₀_D: Decision surface has no effect on quality: Quality(*L) = Quality(*H)
- Tests: Main effects from the same ANOVA

**Secondary (behavioral variance as proxy for characterization difficulty):**
- H₀: Behavioral variance (entropy of tool call sequences across repeated runs) shows no interaction between W and D
- H₁: Behavioral variance shows a positive W×D interaction (supermodularity of characterization difficulty)
- Test: Two-way ANOVA on entropy scores. This tests the formal claim more directly — χ(w,d) is supermodular — but requires multiple runs per task-condition pair.

### What we're actually measuring

Supermodularity says: restricting one axis saves more when the other axis is high. The primary test operationalizes this as: removing Bash (D restriction) improves quality more when the agent has full codebase access (high W) than when it has restricted access (low W).

Why this works: at high W × high D, the agent has vast information flowing into a computation channel — the supermodular cross-term is maximal. The agent can write scripts that process the entire codebase, creating trajectories the specified observer can't predict. Removing Bash (dropping to high W × low D) eliminates the cross-term. At low W × high D, the agent has Bash but limited information — the cross-term is small because there's less world state to navigate. Removing Bash (dropping to low W × low D) has a smaller effect.

The quality difference (HL - HH) vs (LL - LH) IS the interaction term, which IS the empirical test of supermodularity.

### Power analysis

The interaction effect in a 2×2 ANOVA is typically harder to detect than main effects. The framework predicts a "superlinear" effect, which suggests medium-to-large interaction.

Assumptions:
- Expected quality scores: LL=3.0, HL=3.5, LH=2.5, HH=2.8
- The interaction: restricting D at high W improves quality by 0.7 (HH→HL: 2.8→3.5). Restricting D at low W improves quality by 0.5 (LH→LL: 2.5→3.0). Interaction size: 0.2 on a 1-5 scale.
- Wait — that's a small interaction. Let me reconsider.

Revised assumptions based on what supermodularity actually predicts:
- LL = 3.2 (restricted everything — reliable but limited)
- HL = 3.6 (broad info, no computation channel — well-informed, structured)
- LH = 2.8 (limited info, computation channel — powerful tools, not enough context)
- HH = 2.4 (broad info, computation channel — powerful but chaotic, self-amplifying)
- Interaction: (HL - HH) - (LL - LH) = (3.6 - 2.4) - (3.2 - 2.8) = 1.2 - 0.4 = 0.8
- Expected within-condition standard deviation: σ ≈ 1.0
- Interaction effect size: f = 0.8 / (2 × 1.0) = 0.4 (large interaction)

For 2×2 repeated measures ANOVA with f = 0.4 (interaction):
- α = 0.05, power = 0.80
- **Required: n = 20 tasks**
- With f = 0.25 (medium interaction): n = 52 tasks

For f = 0.3 (medium-large, conservative): n = 35 tasks

### Sample size
- **Primary:** 30 tasks × 4 conditions × 1 run = **120 runs** (adequate for large interaction)
- **Variance subset:** 10 tasks × 4 conditions × 5 runs = **200 additional runs**
- **Total primary:** 120 runs, ~$120-360
- **Total with variance:** 320 runs, ~$320-960

### Analysis plan

1. Pre-register: task list, four conditions, quality rubric, analysis plan
2. Each task run under all four conditions (within-task design). Randomize condition order per task.
3. Score quality 1-5 (same rubric as Experiment 11). Blind to condition.
4. Two-way repeated measures ANOVA: W (high/low) × D (high/low), task as blocking factor
5. Primary test: W×D interaction term. One-sided (we predict the direction).
6. Report interaction effect size with 95% CI
7. Report main effects as secondary
8. For the variance subset: compute sequence entropy per task-condition pair. Run the same 2×2 ANOVA on entropy. This tests supermodularity of behavioral variance (a proxy for χ).

### Falsification
- B1 fails if the interaction term is non-significant — restriction doesn't have superlinear returns. The axes contribute independently, not superlinearly.
- B1 weakened if the interaction is significant but in the wrong direction (restricting D helps *less* at high W) — this would mean the cross-term is submodular, contradicting the proof.
- B1 strengthened if both the quality interaction and the variance interaction are significant in the predicted direction — supermodularity holds for both the design outcome and the characterization difficulty proxy.
- A1 (independence assumption) is partially tested: if the quality interaction matches but the variance interaction doesn't, the independence model may overestimate the formal χ while the practical prediction still holds.

### Practical notes
- The 2×2 factorial reuses the task suite from Experiments 3 and 11. The "Low W" condition needs a pre-specified file list per task — this is additional prep.
- The quality metric is the same 1-5 rubric from Experiment 11. Same raters, same blinding.
- Condition HH (high W, high D) is the most expensive to run (longest conversations, most tool calls). Budget accordingly.
- The quality predictions (HH lowest, HL highest) may seem counterintuitive — HH has the most capability. The framework predicts HH is *hardest to regulate*, which degrades *system* quality even as *potential* quality increases. This is the whole point of supermodularity: capability without constraint is worse than capability with constraint.
- If HH actually produces the *highest* quality (more capability = better outcomes, no supermodular penalty), the framework's central practical claim fails. This would be an important negative result.

---

## Experiment 2: Communication Amplification

### Claims tested
- B2: Unstructured inter-agent communication produces quadratic growth in characterization difficulty
- A5 (indirectly): Co-domain funnels restore linear growth (Cor. 8.19)
- A8 (indirectly): Delegation between agents is a computation channel (Prop. 9.11)

### Design
Two-agent system. Agent A (planner) delegates to Agent B (implementer). Three communication conditions:

- **Condition U (Unstructured):** A sends natural language instructions to B. B returns natural language results. No schema at the boundary.
- **Condition S (Structured):** A sends a structured task object to B (JSON: {file, action, description, acceptance_criteria}). B returns a structured result ({status, files_modified, summary}). Schema enforced.
- **Condition F (Funnel):** A sends structured tasks. B returns only {status: pass|fail|needs_review, summary: string(max 200 chars)}. Narrow co-domain funnel.

All three conditions use the same two models, same tool sets, same tasks. Only the inter-agent communication format changes.

### Hypotheses

**Primary (quadratic vs linear growth):**
- H₀: Behavioral variance scales the same way with total token budget under all three conditions
- H₁: Behavioral variance scales quadratically with budget under condition U and linearly under conditions S and F
- Test: Fit variance = a × budget^k for each condition. Compare the exponent k across conditions. Under H₁, k_U ≈ 2 and k_S, k_F ≈ 1.

This is a curve-fitting test, not a standard ANOVA. The formal claim (Prop. 8.17) predicts a specific functional form (product of windows → quadratic), not just "more variance."

**Operationalizing "characterization difficulty":** We can't measure χ directly. We operationalize it as behavioral variance — given the same task and same starting conditions, how different are the tool call sequences across repeated runs? Higher χ means more distinguishable paths, which should manifest as more diverse behavior across runs.

**Budget variation:** To test scaling, we need to vary the total token budget. Run each task at three budget levels:
- Small: 10K tokens per agent (20K total)
- Medium: 50K tokens per agent (100K total)
- Large: 200K tokens per agent (400K total)

This gives a 3×3 design: 3 communication conditions × 3 budget levels.

**Secondary (funnel decoupling):**
- H₀: Condition F shows the same variance scaling as condition S
- H₁: Condition F shows lower variance than S at large budgets (the funnel caps variance regardless of B's budget)
- Test: Compare variance at the Large budget level between S and F. If the funnel works, F's variance at Large should be similar to F's variance at Small — the funnel decouples A from B's budget.

**Secondary (task outcome):**
- H₀: Task success rate is the same across communication conditions
- H₁: Structured communication improves task success rate
- Test: Cochran-Armitage trend test (U → S → F ordering by structure)

### Power analysis

This experiment tests a functional form (quadratic vs linear), not a mean difference. Standard power analysis doesn't directly apply. Instead:

**Minimum data points per curve:** To distinguish k=1 from k=2 in variance = a × budget^k, we need at least 3 budget levels and enough runs per cell to estimate variance reliably.

**Variance estimation:** To estimate behavioral variance, we need multiple runs of the same task under the same conditions. The variance of the variance estimate decreases as 1/√(n-1). For reliable variance estimates, need n ≥ 10 runs per cell.

**Design:**
- 15 tasks × 3 conditions × 3 budget levels × 10 runs = **1,350 runs**
- This is expensive. At $1-3 per run: **$1,350-4,050**

**Reduced design (pilot):**
- 10 tasks × 3 conditions × 3 budget levels × 5 runs = **450 runs**
- $450-1,350. Adequate to detect large differences in scaling exponent. Underpowered for subtle differences.

**Minimum viable design:**
- 10 tasks × 3 conditions × 2 budget levels (Small, Large) × 5 runs = **300 runs**
- $300-900. Tests whether unstructured communication produces more variance at large budgets. Can't fit the full scaling curve but can detect the key difference.

### Sample size
- **Full design:** 15 × 3 × 3 × 10 = 1,350 runs (~$1,350-4,050) — statistically robust
- **Pilot design:** 10 × 3 × 3 × 5 = 450 runs (~$450-1,350) — adequate for large effects
- **Minimum viable:** 10 × 3 × 2 × 5 = 300 runs (~$300-900) — can detect key difference, can't fit curves
- **Recommended:** Start with minimum viable. If results are suggestive, extend to pilot design. If pilot confirms, full design for publication.

### Analysis plan

1. Pre-register: tasks, conditions, budget levels, analysis plan
2. For each task × condition × budget level, run 5-10 times
3. Measure behavioral variance per cell: entropy of tool call sequences across runs of the same task-condition-budget
4. For each condition, fit: log(variance) = k × log(budget) + c. Estimate k with 95% CI.
5. Primary test: Is k_U significantly greater than k_S and k_F? Use a z-test on the difference in regression coefficients.
6. Report k estimates with CIs: k_U (predicted ≈ 2), k_S (predicted ≈ 1), k_F (predicted ≈ 1 or less)
7. For funnel decoupling (secondary): compare variance_F at Large vs variance_F at Small. If the funnel works, these should be similar (the funnel caps variance).
8. Report task success rates across conditions as exploratory.

### Infrastructure requirements

This is the most infrastructure-heavy experiment:

**Multi-agent orchestration.** Need a system where:
- Agent A receives a task and produces instructions/structured tasks for Agent B
- Agent B receives instructions and works on the task
- The communication channel between A and B is configurable (unstructured, structured schema, funnel schema)
- Both agents' tool calls are logged
- Both agents operate under the same tool configuration (only the communication format changes)

**Budget control.** Need to limit token budgets per agent. This may require:
- Truncating context at the specified limit
- Using a wrapper that enforces budget per agent
- Or using model API max_tokens parameter

**Schema enforcement.** For conditions S and F, need a mechanism that enforces the communication schema. Agent A's output to B must conform to the schema. Agent B's output back to A must conform to the return schema. Violations should be caught and counted (they're a data point — schema violations are a form of the infidelity failure mode).

### Falsification
- B2 fails if k_U ≈ k_S ≈ k_F ≈ 1 — all conditions show linear scaling regardless of communication structure. Unstructured communication doesn't produce quadratic growth.
- B2 weakened if k_U > k_S but k_U < 2 — unstructured communication increases the scaling exponent but not to quadratic. The product-of-windows model overestimates.
- A5 (funnel) fails if k_F ≈ k_S — the funnel doesn't reduce scaling beyond what structured communication already provides.
- A5 strengthened if variance_F is approximately constant across budget levels — the funnel completely decouples A from B's budget, as Cor. 8.19 predicts.
- A8 (delegation as computation channel) supported if k_U > 1 — the delegation boundary acts as a computation channel even when neither agent individually has computation-channel tools.

### Practical notes
- This is the most expensive and infrastructure-heavy experiment. It should run last.
- The multi-agent infrastructure doesn't exist yet. Building it is a project in itself.
- Consider using Claude Code's sub-agent capabilities as the orchestration layer. Agent A dispatches Agent B via the Agent tool, with the communication constrained to the condition's schema.
- The budget control is the hardest part. Token window limits in the API help but don't give precise per-agent budgets.
- Schema enforcement could be a post-hoc check (validate the communication after the fact) rather than real-time enforcement. This is simpler to implement and the violations are data.
- Start with the minimum viable design (300 runs). The key question — does unstructured communication produce more variance at large budgets? — is testable without curve fitting.
- If the minimum viable design shows a clear effect, extend to the pilot (450 runs) for curve fitting. If the pilot confirms quadratic scaling, the full design (1,350 runs) produces publication-quality evidence.

---

## Summary of required resources

| Experiment | Tasks needed | Runs | Estimated cost | Time |
|-----------|-------------|------|---------------|------|
| 1 (Supermodularity) | 30 | 120 primary + 200 variance | $120-960 | 2-3 days |
| 2 (Communication) | 10-15 | 300-1,350 | $300-4,050 | 3-7 days |
| 3 (Phase transition) | 30 | 90 primary + 150 variance | $240-720 | 2-3 days |
| 6 (Trust gap) | 20-30 task types | 120-300 | $120-360 | Runs alongside Exp 4 |
| 11 (Placement) | 30-50 | 90-150 | $90-450 | 2-3 days |
| **Total** | **30-50 unique tasks** | **720-2,150** | **$870-6,540** | **Staggered over weeks** |

### Shared infrastructure requirements

1. **Task suite:** 30-50 tasks satisfying Experiment 11's criteria (two-phase, planning-matters, moderate difficulty). These can also serve Experiments 1, 3, and 6. For Experiment 1, each task also needs a pre-specified file list for the "Low W" conditions.
2. **Specified observer:** Pre-trained on historical conversation logs, frozen before experiments begin.
3. **Quality rubric:** The 1-5 scale defined in Experiment 11, with worked examples for calibration. Reused by Experiment 1.
4. **Two raters:** For Experiments 1 and 11. One can be the author; the second should ideally be independent.
5. **Randomization plan:** Latin square for Experiment 11 task-condition assignment. Randomized condition order per task for Experiment 1.
6. **Sandbox diffing:** Git-based auto-commit hook for Experiments 1, 3, and 6.
7. **Multi-agent orchestration:** For Experiment 2 only. Agent A delegates to Agent B with configurable communication schemas. This is the most complex infrastructure component and should be built last.
8. **Budget control:** For Experiment 2. Mechanism to enforce per-agent token limits.

### Sequencing

1. **Now:** Start Experiments 4+9+10 (longitudinal, observational, zero cost)
2. **Week 1:** Run Experiment 12 (textual analysis, no compute cost) ✅ COMPLETE
3. **Week 1-2:** Build task suite and specified observer
4. **Week 2-3:** Run Experiment 3 (90 primary runs, produces failure data for Exp 9)
5. **Week 3-4:** Run Experiment 6 (paired with ratchet promotion from Exp 4)
6. **Week 4-5:** Run Experiment 1 (120 runs, reuses task suite and rubric from Exp 3/11)
7. **Week 5-7:** Run Experiment 11 (90-150 runs, needs completed task suite)
8. **Week 7+:** Run Experiment 2 (300+ runs, needs multi-agent infrastructure)

Experiments 1, 3, and 11 share the task suite. Experiment 1 additionally needs per-task file lists for the Low W condition. Experiment 2 is the most expensive and infrastructure-heavy — it runs last and starts with a minimum viable design.

Note: Experiments 1 and 3 can run in parallel since they use different condition structures on the same tasks. However, they should not share runs — each experiment needs its own data.
