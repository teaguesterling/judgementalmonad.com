# The Judgemental Monad

*Design theory and practice for multi-agent systems.*

---

## What this is

This site develops a framework for understanding systems where humans and AI agents work together. The central idea: the *space between* actors — what each can do, what each can see, how they connect — determines the system's behavior more than any individual component. Measure that space, and the architecture follows.

The framework draws on programming language theory, cybernetics, and capability-based security. It produces testable predictions about which architectural decisions matter and why. It also produces tools — DuckDB queries, structured macros, mode controllers, segment builders — that ship in every practitioner post.

The name comes from *ma* (間), the Japanese concept that the space between things is itself functional. And from the observation that the orchestrator at the hub of every agent system is, structurally, a judgemental monad — it threads state, manages effects, and mediates between the opaque and the specified.

---

## Three paths, one framework

### [The Ma of Multi-Agent Systems](blog/ma/index)

*The theory.* Nine posts developing a formal design theory for agent architecture. The grade lattice measures the space between actors. The specified band explains why the orchestrator must be transparent. The fold model shows that conversations aren't growing computations — they're stateless calls over managed state. Computation channels explain why Bash changes what kind of system you're running.

Supplementary essays develop the configuration ratchet, world decoupling, the failure-driven controller, and the formal companion with proofs and conjectures.

### [Ratchet Fuel](blog/fuel/index)

*The practice.* Eleven posts for people who build with AI agents, data platforms, and organizations. Every failed tool call is data about where your configuration doesn't match the task. Capture those failures. Crystallize them into tools. The system gets more trustworthy with use — not because the model improved, but because the configuration layer accumulated evidence.

Code ships in every post: DuckDB queries over conversation logs, a prototype mode controller, a complete structured tool, a segment builder, an access control layer, and a metrics dashboard.

### [Tools](blog/tools/index)

*The instruments.* The tools that crystallized from the theory and the practice. pluckit (jQuery for source code), the Lackey Papers (micro-inference and template promotion), and the full suite catalog — parsing, code intelligence, build capture, git workflow, observation, and the human-side tools that make it all work.

---

## Recent

- **[The Experiment That Proved Us Wrong](drafts/the-experiment-that-proved-us-wrong)** — We built structured tools to replace bash. They cost 28% more (p < 0.05). Then six tokens of strategy instruction closed the gap entirely — matching bash's cost with full auditability and no computation channel. A detailed strategy prescription made things 56% worse (p < 0.05). The ratchet has two products: tools and strategy. Getting strategy wrong costs more than getting tools wrong.
- **[Proposed Skills](blog/fuel/proposals/index)** — Four annotated skill proposals grounded in ratchet-detect data: [ratchet-review](blog/fuel/proposals/skill-ratchet-review), [git-workflow](blog/fuel/proposals/skill-git-workflow), [build-query](blog/fuel/proposals/skill-build-query), [codebase-explore](blog/fuel/proposals/skill-codebase-explore). Each closes a computation channel with a structured alternative.
- **[ratchet-detect](blog/fuel/ratchet-detect)** — CLI tool that analyzes your Claude Code conversation logs and finds your ratchet candidates. One command, thirty seconds, actionable report.
- **Ratchet Fuel series** — Eleven posts published. The practitioner companion to the Ma series, covering failure streams, the two-stage turn, placement, mode control, tool building, data platform case studies, organizational patterns, and metrics.
- **Coordination Is Not Control** — Companion essay filling the System 3 gap in the Ma framework. World decoupling, named modes, the snapshot-seal-funnel pattern, and the failure-driven controller.
- **External evidence** — Nate Crandall's [harness comparison](https://natesnewsletter.substack.com/p/same-model-78-vs-42-the-harness-made): the same model scored 78% in one harness and 42% in another. The infrastructure determines the outcome, not the model.

---

## Start here

**If you build things:** [The Ratchet Review](blog/fuel/00-ratchet-review) — seven rules and a series map. You'll know within two minutes whether this is useful.

**If you want the theory:** [The Ma of Multi-Agent Systems](blog/ma/00-intro) — start at the beginning. Each post builds on the previous.

**If you want one sentence:** The tools you give an agent define a harder problem than the model you choose to solve it — but *how the agent uses those tools* matters even more, and getting strategy wrong costs more than getting tools wrong.

```{toctree}
:hidden:
:maxdepth: 2

blog/ma/index
blog/fuel/index
blog/tools/index
blog/patterns/index
```
