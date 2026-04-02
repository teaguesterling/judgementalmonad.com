# The Mode Controller

*Failure-driven transitions between tool configurations. Specified rules, not trained judgment.*

---

## The problem

The agent starts with a tool configuration and keeps it for the entire task. If it's wrong — too many tools, wrong tools, missing tools — the agent grinds through with what it has. The Harness doesn't notice. The human notices after the budget is spent.

## The pattern

A controller that watches the tool call stream and switches modes when failure patterns indicate the current configuration isn't working.

### What modes look like

| Mode | Available tools | Read scope | Write scope | When to use |
|---|---|---|---|---|
| **Debug** | Read, Search, Glob, RunTests | Everything | Nothing | Diagnosing failures |
| **Implement** | Read, Edit, Write, RunTests | Everything | src/ only | Fixing code |
| **Test-dev** | Read, Edit(tests/), Write(tests/) | Everything | tests/ only | Writing tests |
| **Review** | Read, Search, Glob | Everything | Nothing | Assessing code |

### Transition triggers

Mode transitions are driven by **failure patterns** — specified thresholds over specified counters. No trained judgment in the transition logic.

```python
if consecutive_edit_failures > 3:
    switch_to("debug")        # stop editing, start diagnosing

if turns_without_progress > 10:
    switch_to("debug")        # agent is spinning, force re-assessment

if tests_passing and edits_complete:
    switch_to("review")       # implementation done, verify

if test_coverage_gap_detected:
    switch_to("test-dev")     # need tests before more implementation
```

### The test boundary

In implementation mode, tests are read-only. In test-dev mode, source is read-only. At no point does the agent have simultaneous write access to both. This prevents the agent from resolving a failing test by changing the test — a natural optimization target that produces correct-looking but incorrect systems.

## The grade analysis

The mode controller is System 3 in Beer's Viable System Model — operational control. It monitors performance and reallocates resources. It's specified: the transition rules are readable, auditable, enumerable. No trained judgment in the controller itself.

The controller changes W (what tools are available) and therefore d_reachable (what paths the agent can take). But it changes them in response to *observed patterns*, not in advance. It's reactive, not predictive.

## Connection to the experiments

We didn't implement a mode controller in our experiments. But the data shows where it would help:

- **Haiku/A (40% pass)**: The agent wastes turns editing before understanding. A controller that forces debug mode for the first 10 turns would prevent this — matching what the Strategy Instruction achieves through prompting.
- **Opus/I (85% pass)**: The agent over-analyzes. A controller that switches from debug to implement after 10 turns of read-only activity would prevent the turn-cap timeout.
- **Sonnet/E (100%, cheapest)**: The agent self-selects efficiently. The controller would rarely intervene — confirming that Sonnet doesn't need external control for this task.

## Implementation

Detailed in Ratchet Fuel post 4 (`blog/fuel/04-the-failure-driven-controller.md`). The controller uses counters (consecutive failures, turns without progress, success rate) with specified thresholds for transitions.

Integration points:
- **blq**: The mode controller monitors blq's event stream for build/test failures
- **jetsam**: Mode transitions trigger jetsam workflow state changes (save, sync, finish)
- **Fledgling**: Different Fledgling tool publications per mode (Code Navigation kit in debug, full kit in implement)

## The anti-pattern: LLM-backed mode selection

Using a language model to decide when to switch modes puts System 4 (trained intelligence) where System 3 (specified control) should be. The mode controller's decisions must be readable, predictable, and auditable. If you need an LLM to decide whether to switch modes, your mode definitions are wrong — make the modes clearer so specified rules suffice.
