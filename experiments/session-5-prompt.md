# Experiment Session 5: Autonomy Placement vs Magnitude (Experiment 11)

*Tests the Basho insight: does WHERE ma lives matter more than HOW MUCH ma there is?*

---

## Prerequisites

From prior sessions:
- `experiments/task-suite.md` — Task suite (30+ tasks, need tasks tagged `planning-matters: high`)
- `experiments/tools/specified-observer.sql` — Specified observer
- `experiments/tools/sandbox-diff-hook.sh` — Sandbox diffing
- `experiments/experiment-3-results.md` — Phase transition results
- `experiments/experiment-6-results.md` — Trust gap results
- `experiments/experiment-1-results.md` — Supermodularity results
- `experiments/failure-log.md` — Ongoing failure log (continue logging)

Read:
1. `drafts/note-for-agents.md`
2. `drafts/experiment-statistics.md` — Section "Experiment 11: Autonomy Placement vs Magnitude"
3. `blog/where-the-space-lives.md` — The essay this experiment tests
4. Memory files

## Context from prior sessions

**Experiment 12 (definition consistency):** The "capacity for informed judgment" definition uniquely enables the placement framing — "where should judgment live?" This experiment tests whether that framing produces testable, correct predictions. If placement doesn't matter (uniform = front-loaded), the definition's distinctive advantage over the original is weakened.

**Experiment 3 (phase transition):** Established whether computation level affects failure modes. Relevant here because Condition B's execution phase has low computation level (Edit only) while Condition C's has high. If Experiment 3 found data-channel tools are sufficient for most execution tasks, that supports the front-loaded design. If it found they're insufficient (agents can't complete tasks without Bash), Condition B may systematically fail at execution — which would test the Taylor/Johannsen question: does constraint at execution actually help or just cripple?

**Experiment 1 (supermodularity):** If the 2×2 interaction was significant, it validates that restriction has superlinear returns — which supports Condition B (restrict execution, free planning). If the interaction was non-significant or HH was best, this experiment's prediction (B > A) is weaker because the theoretical basis for it has failed.

**Key question:** Do the results of Experiments 1 and 3 change whether this experiment's predictions are credible? If Experiment 1 found no supermodularity and Experiment 3 found no phase transition, the theoretical basis for the placement principle is undermined. This experiment would still be worth running (it tests an independent claim) but the prior probability of finding an effect is lower. Note this honestly in the results.

## Pre-experiment review

Before running trials:
- From the task suite, select 30 tasks tagged `planning-matters: high` with two natural phases. If fewer than 30 qualify, you'll need to instantiate templates or create additional tasks.
- Review Experiment 1 results. If the supermodularity interaction was significant and in the predicted direction, proceed with confidence. If it failed, note this and proceed anyway — the placement claim is related but not identical to the supermodularity claim.
- Review whether any prior experiment contradicts the framework in ways that affect this design.

## Longitudinal study reminder

Follow the failure logging protocol throughout. Condition C failures (broad execution, narrow planning) are predicted to be the "Taylor anti-pattern" — powerful tools building the wrong thing. These are particularly valuable for the failure mode taxonomy. Log them in detail.

---

## What this experiment tests

**Claim C9:** Autonomy placement matters more than autonomy magnitude for system quality.

**Claim C10:** Specification at one point in the system improves quality at adjacent unspecified points (constraint creates freedom — the Taylor/Johannsen principle).

**The framework predicts:** Front-loaded placement (broad planning tools + narrow execution tools) produces higher quality than uniform placement (medium tools everywhere) or back-loaded placement (narrow planning + broad execution). Same total autonomy budget, different placement, different outcomes.

---

## This session has three tasks.

### Task 1: Configure the three placement conditions and select tasks (~1 hour)

**Condition A (Uniform):**
```
experiments/conditions/exp11-A-uniform.md
```
Both phases: Read, Grep, Glob, Edit, Write. Medium tools throughout. No Bash. No web search.

**Condition B (Front-loaded — exploration):**
```
experiments/conditions/exp11-B-frontloaded.md
```
- Planning phase: Read, Grep, Glob, Bash (read-only), Fledgling (full tool set). Broad exploration tools.
- Execution phase: Edit only, operating on a pre-specified file list produced by the planning phase. Narrow execution tools.
- Phase transition: The planning phase produces a structured plan (files to modify, approach, acceptance criteria). The execution phase receives ONLY the plan and access to the listed files.

**Condition C (Back-loaded — execution):**
```
experiments/conditions/exp11-C-backloaded.md
```
- Planning phase: Read on 3-5 specified files only. Narrow exploration — the agent sees only what it's told to look at.
- Execution phase: Read, Grep, Glob, Edit, Write, Bash (sandboxed read-write). Broad execution tools.

**Phase transition mechanism:** Each run has two stages. Between stages, the conversation context resets (the execution agent doesn't see the planning conversation — it sees only the plan output). This simulates a handoff between a planner and an executor.

For Condition B, the plan must be a structured document:
```
{
  "approach": "string describing the approach",
  "files_to_modify": ["list", "of", "files"],
  "acceptance_criteria": ["list of criteria"],
  "risks": ["potential issues to watch for"]
}
```

For Condition C, the planning phase produces the same structured output but with less information available.

**Task selection:** From the task suite, select 30 tasks where:
- Planning quality matters (tagged `planning-matters: high`)
- Two natural phases exist
- The wrong approach wastes execution effort

Exclude tasks tagged `planning-matters: low` — they won't differentiate the conditions.

Write the selected task list to `experiments/conditions/exp11-task-selection.md`

### Task 2: Run the experiment (30 tasks × 3 conditions = 90 runs)

**Time estimate:** 90 runs, each with two phases (planning + execution). Planning phase: ~10-15 minutes. Execution phase: ~15-20 minutes. Total per run: ~25-35 minutes. Total: ~37-52 agent-hours. With parallel dispatch, 8-17 wall-clock hours across multiple sub-sessions.

Each run has two phases:

**Phase 1 (Planning):**
1. Give the agent the task description and the condition's planning tool set
2. The agent explores, reasons, and produces a structured plan
3. Record: full tool call sequence, time spent, plan output

**Phase 2 (Execution):**
1. NEW conversation context — the execution agent sees only the structured plan from Phase 1, not the planning conversation
2. Give the agent the plan and the condition's execution tool set
3. The agent implements the plan
4. Record: full tool call sequence, time spent, outcome

**Execution strategy:**

Use a Latin square design: each task appears in each condition, balanced across tasks. With 30 tasks and 3 conditions:
- Tasks 1-10: Run in order A, B, C
- Tasks 11-20: Run in order B, C, A
- Tasks 21-30: Run in order C, A, B

This ensures each condition is run equally at each position in the sequence.

**Blinding:** The agent in each phase does not know which condition it's in. It gets a tool set and a task (or plan). Period.

**Record per run:**
- Planning phase: tool calls, time, plan quality (you'll score this later)
- Execution phase: tool calls, time, code output, task outcome
- Overall: success/failure, total time, total tokens
- Sandbox diff history

Write raw results to `experiments/experiment-11-raw/task-NN-condition-X.md`

### Task 3: Score and analyze (~2 hours)

**Scoring protocol:**

Two scores per run, assigned independently and blind to condition:

**Approach quality (1-5):** Score the plan output (Phase 1 result only). The scorer sees the task description and the structured plan. They do NOT see the execution or which condition produced it.

| Score | Criterion |
|-------|-----------|
| 1 | Plan doesn't address the actual problem or is incoherent |
| 2 | Plan addresses the problem but misses major considerations |
| 3 | Plan is adequate — correct approach, some gaps |
| 4 | Plan is good — right approach, edge cases considered, risks identified |
| 5 | Plan is excellent — insightful approach, comprehensive, would guide any implementer well |

**Implementation quality (1-5):** Score the code output (Phase 2 result only). The scorer sees the task description, the plan, and the code. They do NOT see which condition produced it.

| Score | Criterion |
|-------|-----------|
| 1 | Task not completed or fundamentally wrong |
| 2 | Partially complete, major issues |
| 3 | Complete, correct, some issues |
| 4 | Complete, correct, clean |
| 5 | Complete, correct, elegant |

**Inter-rater reliability:** If two raters are available, both score independently. Report Cohen's weighted kappa. Threshold: κ_w ≥ 0.60 before proceeding.

**Analysis:**

Write to `experiments/experiment-11-results.md`:

1. **Primary (C9):** Friedman test on overall quality (approach + implementation average) across conditions A, B, C
   - If significant: Wilcoxon signed-rank planned comparisons:
     - B vs A (front-loaded vs uniform), Bonferroni α = 0.025
     - B vs C (front-loaded vs back-loaded), Bonferroni α = 0.025
   - Report effect sizes with 95% CIs

2. **Secondary (C10 — constraint creates freedom):**
   - Compare execution quality in B (narrow tools) vs execution quality in A (medium tools)
   - One-sided Wilcoxon: B_execution > A_execution
   - If significant: narrow execution tools WITH a good plan produce better execution than medium tools with a medium plan. Constraint created freedom.
   - If not significant: constraint just reduced capability. The Taylor/Johannsen principle doesn't hold.

3. **Approach quality analysis:**
   - Compare approach quality across conditions
   - Prediction: B_approach > A_approach > C_approach (broad planning tools produce better plans)
   - If C_approach ≈ A_approach: narrow planning tools aren't worse than medium — placement of planning tools doesn't matter

4. **Wasted effort:**
   - Proportion of tool calls not contributing to final result (reverted changes, abandoned approaches)
   - Prediction: C has highest waste (powerful execution tools, poor plan = creative implementation of wrong approach)

5. **Decomposition:** Does the quality difference come from approach, execution, or both?
   - If B wins on approach but ties on execution: planning placement matters, execution placement doesn't
   - If B wins on both: the good plan cascaded into better execution (constraint created freedom)
   - If B wins on approach but loses on execution: narrow tools hurt execution more than good planning helped (constraint didn't create enough freedom)

---

## Deliverables

1. `experiments/conditions/exp11-*.md` — Three condition configurations
2. `experiments/conditions/exp11-task-selection.md` — Selected tasks
3. `experiments/experiment-11-raw/` — Raw results (90 runs, two phases each)
4. `experiments/experiment-11-results.md` — Analysis with Friedman test, planned comparisons, decomposition

Commit everything. Update `experiments/README.md`.

---

## Notes

- This is the most theoretically important experiment from the Saturday session. It directly tests the Basho insight and the "Where the Space Lives" essay.
- The phase transition between planning and execution is critical. The execution agent must NOT see the planning conversation — only the structured plan. This simulates a real planner/executor handoff.
- Condition B's execution phase is deliberately constrained: Edit only, on specified files. This is the Taylor move — specify the cuts so Johannsen's expertise can live in the transitions. If this produces WORSE execution than Condition A's medium tools, the principle fails.
- The Latin square design prevents order effects but doesn't prevent learning effects (the agent may be "better" at later tasks because it's seen similar tasks before). This is controlled by randomization — different tasks appear in different positions across conditions.
- Follow the failure logging protocol. Failures in Condition C (broad execution, narrow planning) are predicted to be the "Taylor anti-pattern" — powerful tools building the wrong thing. Document these.
