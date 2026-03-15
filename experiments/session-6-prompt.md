# Experiment Session 6: Communication Amplification (Experiment 2)

*Tests whether unstructured inter-agent communication produces quadratic growth in characterization difficulty, and whether co-domain funnels restore linear growth.*

---

## Prerequisites

From prior sessions:
- All prior experiment results (read all — this is the final experiment)
- `experiments/task-suite.md` — Task suite
- `experiments/tools/specified-observer.sql` — Specified observer
- `experiments/tools/sandbox-diff-hook.sh` — Sandbox diffing
- `experiments/failure-log.md` — Ongoing failure log (continue logging)

Read:
1. `drafts/note-for-agents.md`
2. `drafts/experiment-statistics.md` — Section "Experiment 2: Communication Amplification"
3. Blog post 9, section on multi-agent systems (Prop. 8.17, Cor. 8.18, 8.19)
4. Formal companion Props. 8.17-8.19 and Prop. 9.11
5. Memory files

**IMPORTANT:** This experiment requires multi-agent infrastructure that may not exist yet. Task 1 builds it. If the infrastructure proves too complex to build in this session, document what you built, what's missing, and fall back to the minimum viable design.

## Context from prior sessions

This is the final experiment in the program. You have results from all prior experiments. Before proceeding, synthesize what the program has found so far:

**Experiment 3 (phase transition):** Did computation level affect failure modes? If yes, the computation channel boundary is real and Prop. 9.11's claim (delegation creates emergent computation channels) has a plausible mechanism. If no, the emergence claim is less likely to produce observable effects.

**Experiment 6 (trust gap):** Did crystallization shrink the trust gap? If yes, interface structure matters for reducing behavioral variance — which supports the prediction that structured communication (Condition S) will outperform unstructured (Condition U). If no, structural constraints may not affect variance, weakening the prediction.

**Experiment 1 (supermodularity):** Did the W×D interaction exist? The communication amplification claim (Prop. 8.17) is essentially supermodularity applied to multi-agent composition — the product of context windows is the cross-term. If supermodularity held for single agents, it should hold (possibly more strongly) for multi-agent composition. If it didn't, this experiment's predictions are weaker.

**Experiment 11 (placement):** Did placement matter? If front-loaded planning beat uniform, the system is sensitive to how autonomy is distributed — which predicts that communication structure (how autonomy flows between agents) also matters.

**Synthesis question:** Across all four prior experiments, has the framework's predictions been confirmed, partially confirmed, or refuted? Your interpretation of THIS experiment's results should be informed by the overall pattern. If every prior experiment confirmed the framework, a null result here is more surprising. If prior experiments showed mixed results, a null result here fits a pattern and may indicate the framework's multi-agent claims are weaker than its single-agent claims.

## Pre-experiment review

Before building infrastructure or running trials:
- Review all prior experiment results. Does anything suggest this experiment's design should change?
- The multi-agent infrastructure is the biggest build risk. Assess honestly: can you build it in 2-3 hours? If not, start with the minimum viable design (90 runs with manual orchestration) rather than spending the whole session on infrastructure.
- If prior experiments substantially undermined the framework, consider whether 300+ runs is warranted or whether a smaller pilot (90 runs) would be more appropriate. Discuss with Principal if uncertain.

## Longitudinal study reminder

Final session. After this, review the full failure log across all sessions. Does the corpus support the three failure modes? Are there patterns the taxonomy doesn't capture? This is the last data collection point for Experiment 9 — make it count.

---

## What this experiment tests

**Claim B2:** Unstructured natural-language communication between agents produces quadratic growth in characterization difficulty (behavioral variance scales as the product of context windows, not the sum).

**Claim A5 (indirectly):** Co-domain funnels restore linear growth (Cor. 8.19).

**Claim A8 (indirectly):** Delegation between agents is a computation channel (Prop. 9.11) — even when neither agent individually has computation-channel tools.

**The framework predicts:** Two agents with data-channel-only tools communicating in natural language compose into a system with an emergent computation channel at the delegation boundary. Behavioral variance should scale quadratically with total token budget under unstructured communication, and linearly under structured communication or a co-domain funnel.

---

## This session has four tasks.

### Task 1: Build multi-agent orchestration infrastructure (~2-3 hours)

This is the most infrastructure-heavy experiment. You need a system where:

**Two agents (A and B) operate on the same task:**
- Agent A (planner/delegator) receives the task and produces instructions for Agent B
- Agent B (implementer) receives instructions and works on the task
- Communication flows: A→B (instructions) and B→A (results)

**Three communication conditions:**

**Condition U (Unstructured):**
- A sends natural language instructions to B (free text, no schema)
- B returns natural language results to A (free text)
- No structural constraints on what crosses the boundary

**Condition S (Structured):**
- A sends structured task objects to B:
  ```json
  {
    "file": "path/to/file",
    "action": "modify|create|delete",
    "description": "what to do",
    "acceptance_criteria": ["list of criteria"]
  }
  ```
- B returns structured results:
  ```json
  {
    "status": "success|partial|failure",
    "files_modified": ["list"],
    "summary": "what was done",
    "issues": ["any problems encountered"]
  }
  ```
- Schema enforced: messages that don't conform are rejected (count rejections as data)

**Condition F (Funnel):**
- A sends structured tasks (same as S)
- B returns a narrow co-domain funnel:
  ```json
  {
    "status": "pass|fail|needs_review",
    "summary": "max 200 characters"
  }
  ```
- Extremely narrow output from B — the tightest possible interface

**Budget control:**
- Each agent has a configurable token budget (context window limit)
- Three budget levels: Small (10K), Medium (50K), Large (200K) tokens per agent

**Implementation approach:**

The simplest implementation uses Claude Code's Agent tool for sub-agent dispatch:
- Agent A runs as the primary conversation
- Agent A dispatches Agent B using the Agent tool with a prompt that includes the communication (unstructured, structured, or funnel)
- Agent B's response comes back to Agent A through the Agent tool's return
- Budget is controlled by limiting context length in the sub-agent prompt

For schema enforcement (conditions S and F): validate the JSON structure of A's output before passing to B, and B's output before passing back to A. Log schema violations.

**Build:**
- `experiments/tools/multi-agent-harness.py` (or `.sh`) — orchestrator that:
  1. Takes a task, a communication condition, and a budget level
  2. Runs Agent A with the task
  3. Captures A's output, validates against the condition's schema
  4. Passes to Agent B with the appropriate prompt
  5. Captures B's output, validates, passes back to A
  6. Continues for up to K rounds (configurable, default 3)
  7. Logs everything: tool calls, communication content, schema violations, timing
- `experiments/tools/communication-schemas/` — JSON schemas for conditions S and F

**Test the infrastructure** on 2-3 tasks before running the full experiment. Verify that:
- Both agents complete their work
- Schema enforcement catches violations
- Budget limiting works
- All tool calls are logged for both agents

### Task 2: Run the minimum viable experiment

**Time estimate:** 300 runs (minimum viable). Each involves two agents working for ~10-20 minutes. With sequential orchestration, this is ~50-100 agent-hours. With parallel dispatch of 3-5 pairs, 10-33 wall-clock hours. This will span multiple days. The infrastructure build (Task 1) may take a full session on its own — plan for this experiment to take 2-3 sessions total, not one.

**Minimum viable design:** 10 tasks × 3 conditions × 2 budget levels (Small, Large) × 5 runs = **300 runs**

This tests the key question: does unstructured communication produce more behavioral variance at large budgets?

**For each cell (task × condition × budget):**
1. Run 5 times with identical setup
2. Record: full tool call sequences for both agents, communication content, task outcome, timing
3. Compute behavioral variance: entropy of the set of 5 tool call sequences

**Execution strategy:** Run by condition to minimize infrastructure switching:
- All Small-U runs, then all Small-S runs, then all Small-F runs
- Then all Large-U, Large-S, Large-F
- Within each block, randomize task order

Write raw results to `experiments/experiment-2-raw/task-NN-cond-X-budget-Y-run-Z.md`

### Task 3: Extend to pilot if results are suggestive (optional, ~2-3 hours)

If the minimum viable results show a clear variance difference between conditions at Large budget:

**Pilot design:** Add the Medium budget level. 10 tasks × 3 conditions × 3 budget levels × 5 runs = **450 runs**

This allows curve fitting: log(variance) = k × log(budget) + c

If the minimum viable results show NO difference, do NOT extend. Report the null result.

### Task 4: Analyze results (~1.5 hours)

**Compile to:** `experiments/experiment-2-results.md`

**Primary analysis (quadratic vs linear scaling):**

For minimum viable (2 budget levels):
1. For each condition, compute mean variance at Small and Large budgets
2. Compute the variance ratio: variance_Large / variance_Small
   - Under linear scaling (k=1): ratio ≈ Large/Small = 200K/10K = 20
   - Under quadratic scaling (k=2): ratio ≈ (200K/10K)² = 400
3. Test: Is the ratio under Condition U significantly greater than under Conditions S and F?
4. Use a permutation test (bootstrap the variance ratios across tasks, compare condition distributions)

For pilot (3 budget levels):
1. For each condition, fit: log(variance) = k × log(budget) + c
2. Report k with 95% CI for each condition
3. Test: Is k_U significantly greater than k_S? Greater than k_F?
4. Use a z-test on the difference in regression slopes

**Secondary (funnel decoupling):**
1. Compare variance_F at Large vs variance_F at Small
2. If the funnel works: these should be similar (the funnel caps variance regardless of B's budget)
3. Wilcoxon signed-rank: variance_F_Large ≈ variance_F_Small (two-sided)

**Secondary (task outcomes):**
1. Task success rate per condition
2. Cochran-Armitage trend (U → S → F)
3. Schema violation rate for conditions S and F

**Secondary (emergent computation channel):**
1. Even under condition U with data-channel-only tools, is behavioral variance consistent with a computation channel? (Variance grows faster than linear with budget)
2. This tests Prop. 9.11: delegation IS a computation channel

**Interpret:**
- Does unstructured communication produce quadratic scaling? Or is the growth rate lower?
- Does structured communication restore linear scaling?
- Does the funnel decouple A from B's budget entirely?
- If U ≈ S ≈ F: communication structure doesn't matter, the framework's prediction fails
- If U > S ≈ F: structure matters but the funnel doesn't add beyond structure
- If U > S > F: both structure and funnel narrowing contribute, as predicted

---

## Deliverables

1. `experiments/tools/multi-agent-harness.py` — Multi-agent orchestration infrastructure
2. `experiments/tools/communication-schemas/` — JSON schemas for S and F conditions
3. `experiments/experiment-2-raw/` — Raw results
4. `experiments/experiment-2-results.md` — Analysis with scaling tests and interpretation

Commit everything. Update `experiments/README.md`.

---

## Fallback plans

**If multi-agent infrastructure can't be built in this session:**
Document what you built and what's missing. Save partial infrastructure. The experiment can be completed in a follow-up session. This is the most infrastructure-heavy experiment in the program — partial progress is expected.

**If 300 runs is too many:**
The absolute minimum to test the key question: 5 tasks × 3 conditions × 2 budgets × 3 runs = 90 runs. This is underpowered but can detect very large effects. Report what you have.

**If budget control doesn't work precisely:**
Log actual token usage per agent per run. Use actual tokens (not configured budget) as the x-axis in the scaling analysis. The design is robust to imprecise budget control as long as actual usage is measured.

---

## Notes

- This is the most expensive experiment in the program. Start with the minimum viable design. Only extend if results warrant it.
- The multi-agent infrastructure is reusable for future multi-agent research beyond this experiment.
- Schema violations in conditions S and F are data, not errors. They indicate where the agent's natural output doesn't fit the structured format — which is itself a measure of the "infidelity" failure mode at the communication boundary.
- The key insight being tested (Prop. 9.11): natural language delegation IS a computation channel, even when both agents have only data-channel tools. If this is confirmed empirically, it's the framework's strongest non-obvious prediction with direct design implications.
- Follow the failure logging protocol. Multi-agent failures are particularly interesting for the failure mode taxonomy.
- This experiment should run LAST in the program, after all single-agent experiments. Its results are important but not load-bearing for the other experiments.
