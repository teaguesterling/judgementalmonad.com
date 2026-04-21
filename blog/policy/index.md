# The Policy Layer

*Agent security is a policy problem. The authorization community solved it twenty years ago. The agent community is reinventing inferior versions from scratch.*

Want the theory? See [The Ma of Multi-Agent Systems](../ma/00-intro).
Want the practice? See [Ratchet Fuel](../fuel/index).
Want the tools? See [umwelt](../tools/index) — the policy language this series describes.

```{toctree}
:maxdepth: 1
:caption: The Series

00-the-missing-layer
01-world-as-capability
02-css-as-policy-syntax
03-the-pair
04-the-datalog-underneath
05-entities-selectors-cascade
06-the-seven-axes
07-materialization-and-audit
```

## What this series is

Every agent framework has a security story. Hooks. Guardrails. Permission prompts. System-prompt instructions. Sandboxed tool calls. Each addresses a real symptom. None of them are a policy.

A policy is a declarative, auditable, composable specification of what's allowed — written once, enforced everywhere, readable by every participant. The identity and access management community has been building these for forty years: from Lampson's access matrices to XACML to OPA to Cedar. The formalism is Datalog. The architecture is always the same: author a policy, compile it to enforcement points, audit the decisions.

The agent community hasn't adopted this architecture. Not because it doesn't apply — it applies more urgently here, because one of the subjects is stochastic and the decisions are harder to audit. The gap exists because agent security grew up in a different tradition (ML safety, prompt engineering, guardrails) that treats the problem as: *detect and block bad outputs.* The authorization tradition treats the problem as: *declare what's allowed and make everything else impossible.* These are fundamentally different postures.

This series argues for the second posture. It describes a specific policy language — [umwelt](https://github.com/teague/umwelt) — that instantiates it. But the argument is larger than the tool. The argument is that agent authorization needs a policy layer, that the layer has a specific shape (dictated by forty years of formal work), and that the novel constraints of the agent case (stochastic subjects, multi-altitude enforcement, environment-as-capability) produce specific design requirements that existing policy languages don't meet.

## What this series is not

This is not the Ma series. Ma describes the *theory* of multi-agent coordination — the grade lattice, the specified band, the four actors, the regulatory strategy. This series describes the *policy layer* that the theory requires. The Ma series asks "what should the regulatory architecture look like?" This series asks "what should the policy language look like, and why?"

This is not a tools series. The tools series describes individual instruments (pluckit, blq, jetsam). This series describes the *policy substrate* those tools consume — the shared vocabulary that lets them interoperate.

This is not a Datalog tutorial. The formalism underneath is Datalog, but the surface syntax is CSS, and the series spends more time on *why CSS* and *why these axes* than on the logic programming. For the formal companion, see [Logic Semantics](https://github.com/teague/umwelt/blob/main/docs/vision/notes/logic-semantics.md) in the umwelt docs.

## The series at a glance

**[Post 0: The Missing Layer](00-the-missing-layer)** — The landscape argument. What agent security looks like today (hooks, guardrails, permission prompts). Why it's a policy problem being treated as a tooling problem. The authorization community's solution and why it doesn't transfer directly. What a fitted policy language needs.

**[Post 1: The World as Capability](01-world-as-capability)** — The world file. Why declaring *what exists* is different from declaring *what's allowed*. Capability grants vs permission rules. The "doesn't exist vs not allowed" distinction. The Docker analogy. Materialization as audit. Connection to Ma's world-coupling axis, but as its own design concern.

**[Post 2: CSS as Policy Syntax](02-css-as-policy-syntax)** — The syntax choice. Training-data saturation. Why every prior policy language invented a DSL and why that's the wrong move for agent authorization. CSS Houdini as precedent for type declarations. The dialect-design argument: borrow a grammar the model already knows.

**[Post 3: The Pair](03-the-pair)** — Why YAML + CSS together. YAML's traditional weaknesses (no types, permissive of unknown keys, highly expressive) are world-declaration strengths. CSS's traditional weakness (ignores what it doesn't understand) is restrict-by-default for policy. Both treat the unknown safely — and together, "unknown" is never a gap.

**[Post 4: The Datalog Underneath](04-the-datalog-underneath)** — The formal grounding. Views as Datalog programs. What we borrow from the tradition (conjunction, SLD resolution, proof trees) and what we don't (recursion, stratification). Comparison to OPA, Cedar, Oso. Defeasible logic and cascade semantics.

**[Post 5: Entities, Selectors, Cascade](05-entities-selectors-cascade)** — CSS selectors over non-DOM worlds. The entity model as queryable structured data. Type selectors, ID selectors, class selectors, attribute selectors — each with policy semantics. Cross-taxon compound selectors. The cascade as defeasible conflict resolution.

**[Post 6: The Seven Axes](06-the-seven-axes)** — Why principal/action/resource isn't enough. The S0/S2 deconvolution: resources vs execution environment. The VSM-derived seven-axis schema. SELinux domains as prior art. How the axes compose via CSS combinators. Comparison to Cedar's three-axis model.

**[Post 7: Materialization and Audit](07-materialization-and-audit)** — The world snapshot as security artifact. Provenance tracking. Detail levels. SQL as the query surface. The compilation pipeline: world + policy → database. Fixed constraints as physics. The ratchet as specified ILP over materialized observations.

## Reading order

The series is designed to be read in order. Each post builds on the previous one:

- **Post 0** establishes why a policy language is needed at all
- **Post 1** establishes what the policy operates *over* (the world)
- **Post 2** establishes *how* the policy is expressed (CSS syntax)
- **Post 3** explains why the *pairing* works — YAML + CSS as complementary safety
- **Post 4** establishes *what* the policy means formally (Datalog)
- **Posts 5–6** develop the entity model and schema
- **Post 7** closes the loop with audit and the ratchet

If you've read the Ma series, start at Post 0 — the policy layer is a separate argument that the theory motivates but doesn't contain. If you haven't, Post 0 is still the right starting point — it's written to stand alone.
