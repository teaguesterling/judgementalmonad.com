# The Datalog Underneath

*The surface is CSS. The logic underneath is Datalog — the same restricted logic programming that OPA, Cedar, and every production authorization language of the last twenty years converges on. What we borrow, what we don't, and where the formal grounding comes from.*

---

## Why Datalog

Datalog is Prolog with three restrictions: no function symbols, stratified negation, guaranteed termination. These restrictions buy you PTIME evaluation — every query terminates in polynomial time. You give up Turing-completeness and gain decidability. For a policy language, that's the right trade.

Every umwelt selector is a conjunction of predicate applications. `file[path^="src/"][language="python"]` is `entity(E), type(E, file), attr(E, path, P), prefix(P, "src/"), attr(E, language, "python")` in Datalog notation. Every declaration block is a rule head — the properties to assign when the body matches. The descendant combinator is logical conjunction across entities: `tool#Edit file[path^="src/"]` is a join between a tool entity and a file entity with context binding.

`use[of="file#/src/auth.py"]` is unification via the `of` relation — it binds the capability to its target, making the reference explicit and auditable. The CSS syntax hides the Datalog, but the Datalog does the work.

---

## The convergence

Every production authorization system of the last twenty years arrives at the same shape: a restricted logic core (Datalog or near-Datalog), a readable surface syntax that isn't the logic directly, a compiler that lowers to an executable form, and separation between policy authoring and enforcement.

| System | Logic | Surface syntax | Key citation |
|---|---|---|---|
| Binder | Datalog + certificates | Custom DSL | DeTreville 2002 |
| SD3 | Distributed Datalog | Custom DSL | Jim 2001 |
| OPA/Rego | Datalog + JSON | Rego | Styra/CNCF 2016 |
| Cedar | Datalog, formally verified | Cedar | Cutler et al. 2024 |
| Zanzibar | Graph reachability (~Datalog) | Config tuples | Pang et al. 2019 |
| umwelt | Datalog + CSS syntax + VSM | CSS | This work |

The convergence isn't coincidence. Abadi, Burrows, Lampson, and Plotkin (1993) showed that access control is fundamentally about logical statements — "principal P says statement S." Their `says` logic is the theoretical root that every system in this table descends from, whether the authors know it or not. DeTreville's Binder (2002) made it executable: a Datalog-based language where certificates are facts and policy rules are clauses. Jim's SD3 (2001) distributed it. Cedar (Cutler et al. 2024) gave it machine-checked soundness proofs.

The deeper formal tradition runs through Lampson, Abadi, Burrows, and Wobber (1992) on authentication in distributed systems; Appel and Felten (1999) on proof-carrying authentication; Li and Mitchell (2003) on the RT framework unifying trust management with Datalog; and Becker and Nanz (2010) on Datalog with mutable state. Each contribution refines the same insight: authorization is a logic program, and Datalog is the right restricted logic for it.

umwelt joins this tradition with a different surface syntax and a different schema. The logic is the same. The bet is that CSS reads better than Rego for the specific audience — agents and their operators — while the Datalog underneath provides the same formal guarantees.

---

## What we borrow, what we don't

**Borrowed:**

- **Conjunction of predicates.** CSS selectors are Datalog bodies. Each simple selector is a predicate; compound selectors conjoin them.
- **SLD resolution.** The evaluation strategy that produces proof trees — traceable chains from conclusion back to facts. Every policy decision in umwelt has a proof tree, not because we built one, but because Datalog evaluation produces them as a byproduct.
- **Guaranteed termination.** No recursion in selectors. Every query terminates. Every cascade resolves. No halting-problem surprises.
- **PTIME evaluation.** Polynomial in the size of the entity set and the rule set. The compiled SQLite database evaluates in the same complexity class as any Datalog engine.

**Not borrowed:**

- **Recursion.** Recursive queries (transitive closure, graph reachability) are deferred. umwelt v1 has no recursive selectors. The world file handles transitive relationships explicitly via `include:` chains and `discover:` matchers. Recursion would add expressiveness and complexity; the tradeoff isn't worth it yet.
- **Stratified negation.** CSS `:not()` is limited to simple selectors (`:not(.dangerous)` is fine; `:not(tool#Bash file)` is not). This matches Datalog's stratification constraint naturally — negation over conjunctions requires careful stratification to avoid non-monotonic paradoxes. CSS's restriction sidesteps the problem.
- **The surface syntax.** This is the whole point. Rego's syntax was designed for Rego. Cedar's for Cedar. Each is clean but unfamiliar. CSS is familiar to every developer and every LLM. The Datalog underneath is the same; the surface is what changes.

---

## Defeasible logic and cascade

García and Simari (2004) formalized defeasible logic programming: a framework where rules can be defeated by more specific rules. A general rule applies unless a more specific rule contradicts it. The more specific rule wins — not by priority declaration, but by the structural relationship between the rules.

CSS cascade is defeasible logic, implemented at web scale since 1996. When `file { editable: false; }` and `file[path^="src/"] { editable: true; }` both match the same file, the more specific rule wins. The general rule isn't wrong — it's defeated. It still applies to files outside `src/`.

The contrast with other policy languages is instructive:

**OPA/Rego** requires rules to agree or produces a conflict error. If two rules set the same value differently, Rego raises an evaluation error unless you write explicit aggregation logic. No cascade, no specificity, no layered override. The policy author must coordinate all rules manually.

**Cedar** has explicit policy-level priority (forbid overrides permit) but no intra-policy cascade. Rules within a single Cedar policy don't override each other by specificity — they're evaluated independently, and the most restrictive wins by convention.

**umwelt** composes by cascade. Base policy + project overlay + task refinement + mode qualification, composed by specificity. No explicit priority. No manual coordination. The cascade handles it. This enables the layering pattern that makes policy authoring scalable: each layer addresses its own concerns without knowing what the other layers said.

Nute showed that propositional defeasible logic has linear complexity. The cascade isn't a performance concern — it's evaluated once at materialization time, producing the effective policy as a materialized view.

---

## Proof trees as audit

Datalog evaluation produces proof trees as a byproduct of SLD resolution. Every derived fact traces back through the rules that derived it to the base facts that grounded it. This isn't an add-on feature. It's the nature of logic programming: every conclusion has a derivation.

For policy, this means every authorization decision has a proof:

```
permission(file#/src/auth.py, editable, true)
  ← rule R₁: mode#implement file[path^="src/"] { editable: true; }
    ← fact: mode#implement is active (world file, entity 42)
    ← fact: file#/src/auth.py has path ^= "src/" (world file, entity 17)
    ← specificity: R₁ (2 axes, [0,1,0], [0,0,1]) defeats R₀ (1 axis, [0,0,0])
```

The proof tree answers "why did the agent have permission to edit auth.py?" with a concrete chain from the decision back to the world file and the policy rule. Lampson (1999) argued for exactly this in "Computer Security in the Real World" — audit requires traceable decisions. Datalog gives you traceability for free.

In umwelt, the proof tree lives in the compiled SQLite database. The `cascade_candidates` table records which rules matched which entities. The `effective_properties` view records which rule won. The compilation pipeline preserves provenance from world file through cascade to effective policy. Compilers become queries: the nsjail compiler queries for mount facts, the bwrap compiler queries for the same facts differently encoded, the audit compiler queries for proof trees. Same database, different SQL.

---

## The agent-safety bridge

The agent-safety community is arriving at Datalog independently — and incompletely. A survey of ten academic papers from 2024–2026 reveals a striking gap: the forty-year authorization-logic tradition and the emerging agent-safety tradition have barely made contact.

**PCAS** (Palumbo et al. 2026) is the closest existing work. A Datalog-derived declarative language with a reference monitor. Models agentic systems as dependency graphs capturing causal relationships among events. Policies over transitive information flow and cross-agent provenance. But it arrives at Datalog through program analysis, not through the authorization-logic tradition. No citation of Abadi, Binder, or Cedar.

**CaMeL** (Debenedetti et al. 2025) is the sole paper that genuinely engages capability theory. It proves a "capability safety theorem" — the reachability graph is the only authority mechanism — bridging Dennis and Van Horn, Miller's POLA, and object-capability discipline. But it doesn't bridge to Datalog or to the authorization-language tradition.

**Progent** (Syros et al. 2025) designs a custom DSL for privilege control, achieving impressive results (attack success rate 41.2% to 2.2%) without reference to existing policy-language research. The DSL reinvents concepts that Rego and Cedar already formalized.

**SEAgent** (Qi et al. 2026) proposes mandatory access control for agents without citing Bell-LaPadula or Biba — the foundational MAC formalism. It borrows the label, not the apparatus.

Of ten surveyed papers, zero cite Abadi's calculus. Zero cite Binder. One uses a Datalog-derived language. Microsoft's Agent Governance Toolkit (2026) is the sole production bridge, supporting Cedar, OPA/Rego, and YAML rules in the same framework.

The gap isn't a criticism — it's a diagnosis. Agent safety and authorization logic are working on the same problem from different directions. The Datalog underneath is the bridge. Where PCAS diverges from umwelt: they use Datalog over dependency graphs with provenance tracking; umwelt uses Datalog views over a CSS cascade with seven authorization axes. Same formal substrate, different surface and schema.

---

## The specified ILP connection

Inductive Logic Programming (Muggleton 1991) learns logic programs from examples. Given positive and negative examples, induce a Datalog program that covers the positives and excludes the negatives. FOIL. Progol. Aleph. Modern Metagol and Popper. Thirty years of formal work on rule induction.

The [configuration ratchet](../ma/the-configuration-ratchet) has been doing specified ILP the whole time. Observe what the agent does (positive examples). Observe what the agent tried and failed (negative examples). Propose a tighter policy consistent with the observations. The "specified" qualifier means: no learned component in the mining pipeline. Just structural pattern matching over observation traces — set intersection, range containment, SQL aggregation.

Classical pre-neural ILP (Progol, Aleph) is in principle sufficient for this. The ratchet has been reinventing a lineage it didn't know it was in. Naming it puts the ratchet on a forty-year formal footing — and makes its output pasteable into a view, because both the ILP program and the policy speak the same Datalog.

The ratchet turn: observe → propose → review → commit. Each turn tightens the policy. Each turn is reversible. Each turn stays in the specified band. The tightening is monotonic — the ratchet only narrows, never widens, unless the human explicitly approves widening. This is the same monotonicity property that makes Datalog evaluation well-founded: new facts can only derive new conclusions, never retract old ones.

---

## Key citations

- Abadi, Burrows, Lampson & Plotkin (1993), "A Calculus for Access Control"
- DeTreville (2002), "Binder: A Logic-Based Security Language"
- Jim (2001), "SD3: Trust Management with Certified Evaluation"
- Cutler et al. (2024), "Cedar: A New Language for Authorization" (OOPSLA)
- Pang et al. (2019), "Zanzibar: Google's Authorization System" (USENIX ATC)
- García & Simari (2004), "Defeasible Logic Programming"
- Muggleton (1991), "Inductive Logic Programming"
- Li & Mitchell (2003), "Datalog with Constraints"
- Lampson (1999), "Computer Security in the Real World"
- Appel & Felten (1999), "Proof-Carrying Authentication"
- Becker & Nanz (2010), "A Logic for State-Modifying Authorization Policies"
- Palumbo et al. (2026), "PCAS" (arXiv:2602.16708)
- Debenedetti et al. (2025), "CaMeL" (arXiv:2503.18813)
- Syros et al. (2025), "Progent" (arXiv:2504.11703)
- Qi et al. (2026), "SEAgent" (arXiv:2601.11893)
- Microsoft Agent Governance Toolkit (2026)

---

*Next: [Entities, Selectors, Cascade](05-entities-selectors-cascade) — The entity model in detail. CSS selectors over non-DOM worlds. How cross-taxon compound selectors work, and why the cascade is a composition mechanism.*
