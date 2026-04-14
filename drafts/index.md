# Grab Bag

*Work in progress. Notes, plans, unfinished essays, and reference material that isn't ready for the main series but is worth reading anyway.*

---

Everything here is a draft. Expect rough edges: broken cross-references, placeholder sections, arguments that haven't settled, claims that are still being tested. Some pieces will eventually be promoted into one of the main series. Others will stay here. A few may be wrong.

If you landed here from a link in the main blog, the thing you're looking for is probably in the list below. If you landed here by accident, the curated series are better starting points:

- [The Ma of Multi-Agent Systems](../blog/ma/index) — the theory
- [Ratchet Fuel](../blog/fuel/index) — the practice
- [Tools](../blog/tools/index) — the instruments

---

## Plans and system design

Documents about what we're building next or how the pieces fit together.

- [The Integration Layer Plan](integration-layer-plan) — How jetsam, blq, fledgling, pluckit, lackpy, kibitzer, and agent-riggs should connect into a coherent system. Maps the current agent architecture onto Beer's VSM, identifies three gaps (distributed System 3, scattered audit data, absent health monitoring), and sketches a five-phase implementation path around a shared DuckDB substrate.
- [The Sandbox Tower](the-sandbox-tower) — nsjail, lackpy, views, and retrieval are all the same pattern at different enforcement altitudes: declarative grade specifications rendered into whichever mechanism can check them. Once you stack them, delegation stops being nerve-wracking and starts being contractual.
- [Umwelt: The Layer We Found](umwelt-the-layer-we-found) — The companion to the sandbox tower post, capturing nine architectural decisions made while designing the umwelt package: text-emitting compilers, the compiler taxonomy (local vs remote, sync vs async), views supersede modes, git history as a view corpus, views unify the ratchet's two products, port-ready decomposition, a vocabulary-agnostic core with Ma-grounded taxa, comparison-semantics properties, and the ratchet as a first-class utility. Frames umwelt as Layer 3 of the three-layer regulation strategy the OS existence proof demonstrates.
- [An LLM Is a Subject of Your Policy](an-llm-is-a-subject-of-your-policy) — Positions umwelt in the Datalog-for-policy lineage (OPA, Cedar, Oso, Polar). Names the four subjects every agent operation already has (principal, intelligence, operation, use) and why the VSM schema is what falls out when you try to express all four in one rule. The agent-as-subject reframe as the premise; CSS syntax, `use[of=...]`, specified ILP, and proof-tree audit as the consequences.
- [Views Are Sandboxes (raw thinking)](views-are-sandboxes) — The in-conversation thinking piece that the sandbox tower writeup grew out of. Rougher, but contains the seven open questions and the original framing.
- [Toolcraft Coordinator Design](toolcraft-coordinator-design) — Earlier design sketch for the integration layer between Fledgling, blq, and jetsam.

## Experimental findings (in flight)

Results from the structured-tools-vs-bash experimental program that haven't been promoted into the main series yet.

- [The Experiment That Proved Us Wrong](the-experiment-that-proved-us-wrong) — Structured tools cost more than bash until a one-sentence strategy instruction closed the gap. The ratchet has two products: tools and strategy.
- [Retrieval Beats Stuffing](retrieval-beats-stuffing) — A 3B model went from 2/8 to 7/8 on a DSL task by reducing retrieved examples from twenty to six. The worst model in the lineup became the best.
- [The Two Products of the Ratchet](the-two-products) — The grade lattice has two axes. The ratchet operates on both. We forgot one and it cost us 32%.
- [Tools Need Strategy](tools-need-strategy) — The missing half of the ratchet, written up as a standalone argument.
- [Kibitzer Coaching Observations](kibitzer-coaching-observations) — Concrete patterns observed during ~250 experimental runs that a coaching layer should detect and address.

## Theory extensions and revisions

Proposed amendments to the main framework that haven't been integrated yet.

- [Theoretical Revisions, March 2026](theoretical-revisions-march-2026) — Substantial developments from a review conversation, flagged as proposed amendments to the formal companion and blog series.
- [Extensions to the Ma Framework](extensions-to-ma) — Five refinements to the published series, each connecting to specific posts and resolving an identified gap.
- [Where the Space Lives](where-the-space-lives) — The question isn't whether the space exists. It's whether you've put it where it can do the most good.
- [Tool Call Combinators](tool-call-combinators) — Structured composition of tool calls that stays in the specified band.

## Critiques and reference material

- [Critique: Chomsky Hierarchy as Tool Classification](chomsky-critique) — Where the formal companion's use of the Chomsky hierarchy for tool classification breaks down.
- [External Evidence: Crandall](external-evidence-crandall) — Reference document for citing Nate Crandall's harness comparison across the Ma series and Ratchet Fuel.

```{toctree}
:hidden:
:maxdepth: 1

integration-layer-plan
the-sandbox-tower
umwelt-the-layer-we-found
an-llm-is-a-subject-of-your-policy
views-are-sandboxes
the-experiment-that-proved-us-wrong
retrieval-beats-stuffing
the-two-products
tools-need-strategy
kibitzer-coaching-observations
theoretical-revisions-march-2026
extensions-to-ma
where-the-space-lives
tool-call-combinators
chomsky-critique
external-evidence-crandall
toolcraft-coordinator-design
```
