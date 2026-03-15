# Experiment Session 4: Supermodularity (Experiment 1)

*Tests the framework's core formal result: does restriction have superlinear returns when both axes are high?*

---

## Prerequisites

From prior sessions:
- `experiments/task-suite.md` — Task suite (30+ tasks)
- `experiments/tools/specified-observer.sql` — Specified observer
- `experiments/tools/sandbox-diff-hook.sh` — Sandbox diffing
- `experiments/experiment-3-results.md` — Phase transition results
- `experiments/experiment-6-results.md` — Trust gap results
- `experiments/failure-log.md` — Ongoing failure log (continue logging)

Read:
1. `drafts/note-for-agents.md`
2. `drafts/experiment-statistics.md` — Section "Experiment 1: Supermodularity of Restriction Returns"
3. Blog post 2 (The Space Between) — supermodularity section
4. Formal companion Prop. 4.7 and Cors. 4.8-4.9
5. Memory files

## Context from prior sessions

**Experiment 3 (phase transition):** Established whether failure rates differ across computation levels. If Experiment 3 found NO phase transition (failure rates constant across levels), that weakens but doesn't eliminate the supermodularity claim — supermodularity is about the *interaction* between axes, not about main effects. Review Experiment 3 results and note whether the D-axis main effect (computation channels vs data channels) was significant. This experiment tests the *interaction* with the W axis.

**Experiment 6 (trust gap):** Established whether crystallization reduces the trust gap. If it did, the trust gap is a valid operationalization of "regulation difficulty." Use gap rate as a secondary measure alongside quality scores. If Experiment 6 found no trust gap reduction, gap rate may not be a useful measure for this experiment — rely on quality scores as primary.

**Key question from prior results:** Did Experiments 3 and 6 produce any surprising results that should change how you run this experiment? If Experiment 3 found that data-channel-only conditions (level 0-2) actually had HIGHER failure rates than computation-channel conditions (because agents couldn't do the task without Bash), that changes the interpretation of the Low D conditions here. Review and assess before running.

## Pre-experiment review

Before running trials:
- Review Experiment 3 results. Does the D-axis main effect exist? This is a prerequisite for the interaction making sense.
- Review the task suite. Each task needs a 3-5 file list for the Low W conditions. If these don't exist yet, creating them is Task 1 prep work.
- If any prior experiment produced results that contradict the framework's predictions, note this and flag whether it affects the design of this experiment. The design is pre-registered and shouldn't change, but the decision to RUN it might.

## Longitudinal study reminder

Follow the failure logging protocol throughout. Failures in the HH condition (broad info + computation channels) are predicted to be the most complex and the most informative for the failure mode taxonomy. Log them carefully.

---

## What this experiment tests

**Claim B1:** Restriction has superlinear returns when both axes of the grade are high (Prop. 4.7).

**The framework predicts:** Removing computation channels (restricting D) improves system quality MORE when world coupling is broad (high W) than when world coupling is narrow (low W). The interaction between the axes is superlinear — the cross-term dominates.

**The most consequential falsification in the program:** If the HH condition (broad information + computation channels) produces the HIGHEST quality outcomes, then more capability is simply better, the supermodular penalty is a theoretical artifact, and the framework's central practical claim fails.

---

## This session has three tasks.

### Task 1: Prepare the four conditions (~1 hour)

Create four tool configuration files:

**Condition LL (Low W, Low D):**
```
experiments/conditions/exp1-LL-lowW-lowD.md
```
- Tools: Fledgling structured tools, Read, Glob, Grep, Edit, Write
- File access: Restricted to a pre-specified list of 3-5 files per task (the task description names the relevant files)
- No Bash
- Computation level: 0-2
- World coupling: scoped (pinhole — only the named files)

**Condition HL (High W, Low D):**
```
experiments/conditions/exp1-HL-highW-lowD.md
```
- Tools: Fledgling structured tools, Read, Glob, Grep, Edit, Write
- File access: Full codebase
- No Bash
- Computation level: 0-2
- World coupling: broad (full repo)

**Condition LH (Low W, High D):**
```
experiments/conditions/exp1-LH-lowW-highD.md
```
- Tools: Fledgling + Bash (sandboxed, read-write)
- File access: Restricted to pre-specified files only (Bash also restricted to those paths)
- Computation level: 4
- World coupling: scoped (pinhole)

**Condition HH (High W, High D):**
```
experiments/conditions/exp1-HH-highW-highD.md
```
- Tools: Fledgling + Bash (sandboxed, read-write, full codebase access)
- File access: Full codebase
- Computation level: 4
- World coupling: broad

**Per-task file lists:** For each of the 30 tasks, create a file list specifying the 3-5 files relevant to the task. These files are what the agent sees in the Low W conditions. The lists should be:
- Sufficient to complete the task (the relevant files ARE the files needed)
- Not so broad that Low W ≈ High W (don't include the whole directory)

Write file lists to `experiments/conditions/exp1-file-lists/task-NN.txt`

### Task 2: Run the experiment (30 tasks × 4 conditions = 120 runs)

**Time estimate:** 120 runs at ~20-30 minutes each is ~40-60 agent-hours. With parallel dispatch of 3-5 agents, 8-20 wall-clock hours across multiple sub-sessions. This is a large experiment — plan for 2-3 days of intermittent running.

For each task, under each of the four conditions:

1. Set up: Initialize sandbox diffing. Load the condition's configuration. If Low W, restrict file access to the task's file list.
2. Run: Give the task to an agent. The agent does not know which condition it's in.
3. Record:
   - Full tool call sequence with timestamps
   - Task outcome: success / partial / failure
   - If failure: classify using failure logging protocol
   - Quality score: 1-5 rubric (same as Experiments 3 and 11)
   - Sandbox diff history
   - Specified observer predictions vs actual (gap rate)
   - Time to completion
   - Total tokens consumed

**Execution strategy:** Randomize condition order per task. For task 1: run in order HH, LL, LH, HL (random). For task 2: different random order. This prevents systematic order effects.

**CRITICAL:** The agent must not know which condition it's in. It gets a task and a tool set. For Low W conditions, the agent's file access is restricted — it doesn't know other files exist. Do not mention the experiment, the conditions, or the factorial design.

Write raw results to `experiments/experiment-1-raw/task-NN-condition-XX.md`

### Task 3: Analyze results (~1.5 hours)

**Compile to:** `experiments/experiment-1-results.md`

**Primary analysis (supermodularity — the interaction test):**

1. Organize quality scores into the 2×2 table:

| | Low D (no Bash) | High D (Bash) |
|---|---|---|
| **Low W** (restricted files) | LL scores | LH scores |
| **High W** (full codebase) | HL scores | HH scores |

2. Two-way repeated measures ANOVA (task as blocking factor):
   - Factor 1: W (low/high)
   - Factor 2: D (low/high)
   - Test the W×D interaction term (one-sided: predicted positive interaction)
3. Report: F-statistic, p-value, partial η² for the interaction
4. Report main effects of W and D
5. Planned comparisons with Bonferroni correction:
   - Effect of restricting D at High W: Quality(HL) - Quality(HH)
   - Effect of restricting D at Low W: Quality(LL) - Quality(LH)
   - The difference between these two IS the interaction

**Key predictions to test:**
- HL (broad info, no Bash) should be highest quality — well-informed, structured
- HH (broad info, Bash) should be lower than HL — the supermodular penalty
- The quality drop from HL→HH should be LARGER than the drop from LL→LH — supermodularity

**Secondary analysis (behavioral variance):**
If the variance subset was run (10 tasks × 4 conditions × 5 runs):
1. Compute sequence entropy per task-condition cell
2. Same 2×2 ANOVA on entropy
3. Does the entropy interaction match the quality interaction?

**Secondary (gap rate):**
1. Report mean gap rate per condition
2. Does gap rate correlate with quality? (Spearman correlation across conditions)

**Interpret:**
- Is the interaction significant? In the predicted direction?
- Is HH really the worst condition? Or does more capability = better outcomes?
- Does the interaction size match the theoretical prediction (superlinear, not just additive)?
- If the interaction is non-significant: is the experiment underpowered, or is the effect genuinely absent?

**Power assessment:**
- Report observed effect sizes
- Given observed variability, how many tasks would be needed to detect the observed interaction at 80% power?
- If the experiment was underpowered, state this honestly

---

## Deliverables

1. `experiments/conditions/exp1-*.md` — Four condition configurations
2. `experiments/conditions/exp1-file-lists/` — Per-task file lists for Low W conditions
3. `experiments/experiment-1-raw/` — Raw results (120 files)
4. `experiments/experiment-1-results.md` — Analysis with ANOVA, interaction test, interpretation

Commit everything. Update `experiments/README.md`.

---

## Notes

- This experiment has the most consequential falsification in the program. If HH produces the highest quality, the framework's central claim about restriction fails. Report this honestly.
- The per-task file lists for Low W conditions are the most labor-intensive prep. They must be carefully chosen: sufficient to complete the task, not so broad that Low W ≈ High W.
- The 2×2 design reuses the quality rubric from Experiments 3 and 11. Same raters, same blinding.
- This can share tasks with Experiments 3 and 11 but must use its own runs — don't reuse data across experiments.
- Follow the failure logging protocol throughout. Failures in HH conditions are particularly valuable for the failure mode taxonomy (Experiment 9).
