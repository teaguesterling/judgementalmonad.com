# Patterns for Toolcraft

*Design patterns for equipping agents with the right tools, the right focus, and the right constraints for the job.*

---

A carpenter doesn't carry every tool to every job. They assess the work, select the right kit, and the specialization enables focus. The craft isn't just knowing how to use a chisel — it's knowing when the chisel is the right tool and when it isn't.

Agent toolcraft is the same discipline. Which tools should the agent see? What strategy instruction focuses its attention? How should the execution environment be bounded? When should the configuration change? Each pattern in this series addresses one of these questions, grounded in experimental data from ~200 runs across three models.

The theory is in [The Ma of Multi-Agent Systems](../ma/index). The practice is in [Ratchet Fuel](../fuel/index). These patterns are the recurring designs that emerge when you apply the theory to real systems — the craft of making and selecting tools that enable agents to do their best work.

---

## The patterns

### Configuration patterns

1. **[The Quartermaster](01-the-quartermaster)** — Select the right tools, strategy, and constraints for the task and model *before* execution begins. A fast, cheap pre-pass that configures everything the executor needs.

2. **[The Strategy Instruction](02-the-strategy-instruction)** — A short principle (~50 tokens) that reshapes which paths the agent takes through its decision surface, without changing which tools are available. The most cost-effective intervention measured: -16% for Sonnet, 40%→100% reliability for Haiku. Harmful for Opus.

3. **[The Calibration Probe](03-the-calibration-probe)** — Before committing to a configuration, run a 3-5 turn diagnostic to characterize the model's behavior. Does it plan before acting? Does it choose the right tools? The probe tells the Quartermaster what it's working with.

### Execution patterns

4. **[Write/Execute Separation](04-write-execute-separation)** — The agent writes through auditable, structured tools. Execution of what it wrote goes through a sandbox it doesn't control. The separation prevents the agent from closing the computation channel loop and keeps the system at level 3 instead of level 4+.

5. **[Sandbox Specifications](05-sandbox-specifications)** — Declarative execution environment bounds that make every command's grade explicit, enforceable, and queryable. The sandbox provides an effects ceiling; the tool interface determines the computation level. Neither alone is sufficient.

6. **[Tool-Call Combinators](06-tool-call-combinators)** — Compose structured tool calls without crossing the computation channel boundary. `gather`, `try_and_check`, `scope`, `pipe`, `for_each`. The Harness executes them — deterministically, traceably, auditably.

### Operational patterns

7. **[The Mode Controller](07-the-mode-controller)** — Failure-driven transitions between tool configurations. The controller watches the tool call stream and switches modes when patterns indicate the current configuration isn't working. Specified rules, not trained judgment.

8. **[The Coach](08-the-coach)** — Continuous observation with suggestions. A hook that fires periodically, analyzes recent tool usage via Fledgling/blq, and injects context the agent is missing. Not enforcement — guidance. The ratchet's observation phase, automated.

---

## How the patterns compose

```
Quartermaster (before task)
    → selects tools, strategy, mode
    → informed by Calibration Probe

Mode Controller (during task)
    → watches failure stream
    → switches between modes (debug, implement, verify)
    → each mode uses Write/Execute Separation
    → each mode's execution bounded by Sandbox Spec

Coach (during task)
    → observes tool usage patterns
    → suggests via hooks (not enforcement)
    → feeds observations to Mode Controller

Tool-Call Combinators (within each mode)
    → compose tool calls efficiently
    → stay in the specified band
    → reduce round-trip overhead

Strategy Instruction (throughout)
    → shapes d_reachable within whatever mode is active
    → model-dependent: essential for Haiku, optional for Opus
```

---

## Grounding

Every pattern includes:
- **The problem it solves** — what goes wrong without it
- **The experimental evidence** — which experiment demonstrated it, with data
- **The grade analysis** — what computation level it operates at
- **The implementation** — code, configuration, or specification
- **The anti-pattern** — what happens when you get it wrong

The experiments behind these patterns: ~200 runs across 9 tool configurations, 3 models (Haiku, Sonnet, Opus), measuring pass rate, cost, tool usage, and behavioral patterns on a synthetic bug-fixing task.

---

```{toctree}
:hidden:
:maxdepth: 1

01-the-quartermaster
02-the-strategy-instruction
03-the-calibration-probe
04-write-execute-separation
05-sandbox-specifications
06-tool-call-combinators
07-the-mode-controller
08-the-coach
```
