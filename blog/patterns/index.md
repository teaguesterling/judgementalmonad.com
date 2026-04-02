# Patterns for Toolcraft

*Findings from ~200 experimental runs, and the patterns that emerged.*

---

We ran ~200 experiments across three models (Haiku, Sonnet, Opus) and nine tool configurations on a synthetic bug-fixing task. The experimental foundations — what we measured and what surprised us — are in the first post. The remaining patterns are the designs that emerged from those findings, each addressing a specific problem that the data revealed.

The theory is in [The Ma of Multi-Agent Systems](../ma/index). The practice is in [Ratchet Fuel](../fuel/index). The tools are in [Tools](../tools/index).

---

## The patterns

1. **[Experimental Foundations](01-experimental-foundations)** — ~200 runs across 3 models and 9 configurations. Strategy instructions are model-dependent. Structured tools cost 5% more than bash and buy characterizability. One sandbox flag was the difference between level 4 and level 7. Don't restrict what you haven't measured.

2. **[The Calibration Probe](02-the-calibration-probe)** — Before committing to a configuration, run a 3-5 turn diagnostic to characterize the model's behavior. The probe costs $0.03-0.15 (~1% of task cost). A misconfigured task costs 15-56% more.

3. **[Tool-Call Combinators](03-tool-call-combinators)** — Compose structured tool calls at the Harness level without crossing the computation channel boundary. `gather`, `try_and_check`, `scope`, `pipe`, `for_each`. Reduces 15 calls to 3, saving ~200K tokens of re-sent context.

4. **[The Mode Controller](04-the-mode-controller)** — Failure-driven transitions between tool configurations. The controller watches the tool call stream and switches modes when patterns indicate the current configuration isn't working. Specified rules, not trained judgment.

5. **[The Coach](05-the-coach)** — Continuous observation with suggestions. Fires periodically, analyzes recent tool usage via Fledgling/blq, and injects context the agent is missing. The ratchet's observation phase, automated.

---

```{toctree}
:hidden:
:maxdepth: 1

01-experimental-foundations
02-the-calibration-probe
03-tool-call-combinators
04-the-mode-controller
05-the-coach
```
