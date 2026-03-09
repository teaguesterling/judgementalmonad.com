# Self-Critique: The Formalisms

*An honest accounting of where the formal framework is solid, where it's suggestive, and where it's doing hand-waving in a lab coat.*

**Status**: Points 1–3 resolved in [The Grade Lattice](the-grade-lattice.md). Points 4–7 resolved in [Raising and Handling](raising-and-handling.md). Point 8 resolved in-place. Point 9 remains open.

---

## 1. Ma is three things wearing one name — RESOLVED

The unified definition says ma is "the space between what an actor receives and what it produces," determined by world coupling, decision surface, and interface restriction. But the formalism gives three different formal objects for ma:

- **Section 11 of the formal framework**: `ma(A) = K(desc(M(O)))` — Kolmogorov complexity of the co-domain description. This formalizes interface restriction only.
- **The grade lattice**: `ma = (world_coupling, decision_surface)` — a pair in a 2D lattice. No interface restriction component.
- **The monad morphism preorder**: `M ≤ N iff ∃ η : M ~> N` — an expressiveness ordering on effects. Different from both of the above.

The updated Section 11 intro says it formalizes "the interface restriction *aspect* of ma." But Definition 11.2 still says `ma(A) = K(desc(M(O)))` without qualifier — that's a definition of *the thing itself*, not an aspect. And the grade lattice defines ma as a pair `(world_coupling, decision_surface)` with no interface restriction component at all.

These aren't three formalizations of one concept. They're formalizations of three different concepts that share a name.

**The question**: Is ma the space (intuitive), the grade (compositional), the K-complexity (descriptive), or the preorder position (relational)? The text equivocates. Until this is resolved, "ma determines role" could mean any of several precise claims, each with different truth conditions.

**Resolution**: Ma is the computation's *path space* — not the output space, but the space of ways inputs can become outputs. The grade lattice `(w, d) ∈ W × D` measures it. K-complexity of the co-domain projects it onto the output boundary (interface ma). The monad morphism preorder compares it (embeddability). Three tools, one concept. See [The Grade Lattice](the-grade-lattice.md).

---

## 2. The grade lattice product ⊗ is undefined — RESOLVED

The composition formula `ma(A using B) = (coupling_A ⊗ coupling_B, surface_A ⊗ surface_B)` is presented as "multiplicative." But ⊗ operates on what algebra?

The levels (sealed, pinhole, scoped, broad, open) are ordinal landmarks on a qualitative scale. What does `scoped ⊗ trained` mean? The GCC examples suggest ⊗ behaves like join (max) — the compound system's world coupling is at least as broad as both components'. But join isn't multiplication, it's a lattice operation. And the whole motivation for the grade lattice was that composition should be *multiplicative, not additive* — yet nothing defines what multiplication means on these levels.

Without a concrete algebra, the formula is a diagram, not a theorem. The GCC progression is compelling as narrative but doesn't constrain the algebra enough to make predictions. Would a different ⊗ produce different architectural recommendations?

**Resolution**: Composition is join on the product lattice: `ma(A using B) = (w_A ∨ w_B, d_A ∨ d_B)`. The "multiplicative" intuition comes from the *supermodularity of characterization difficulty* — increasing one axis has greater marginal effect when the other is already high. The cross-term (decision surface navigating world coupling) is a property of the interpretation function, not the algebra. See [The Grade Lattice](the-grade-lattice.md).

---

## 3. Decision surface has no formal definition — RESOLVED

World coupling maps (roughly) to parameterized IO: `IO_null ≤ IO_sandbox ≤ IO_filesystem ≤ IO`. That's a formal object.

Interface restriction maps to the monad morphism preorder. Also formal.

Decision surface maps to... prose. "How much the computation's processing can be influenced by its inputs." The levels (literal → specified → configured → trained → organic) are described qualitatively with examples. There is no formal measure.

This is the axis that's supposed to distinguish a temperature-0 LLM from a lookup table — the central motivation for the two-axis decomposition over the original co-domain-only definition — and it's the one axis without a mathematical definition.

The cybernetics connection (Ashby's variety) could provide one: variety has a precise definition (log of the number of distinguishable states). The document says "variety is essentially decision surface size" but doesn't follow through. Kolmogorov complexity of the function itself (not its output) is another candidate — it directly measures "how much information is needed to describe the processing." But neither is adopted.

**Status**: Decision surface is an observation, not a formalization. The grid is a taxonomy, not a theory.

**Resolution**: Decision surface = log of the number of distinguishable input-dependent execution paths. Connects to Ashby's variety (the same thing measured in bits), VC dimension (capacity of the function class), and number of linear regions in piecewise-linear networks (Montufar et al., 2014). See [The Grade Lattice](the-grade-lattice.md).

---

## 4. The monad assignments to actors are stipulative — RESOLVED

The assignments blurred implementation and interface effects. The handler framing (algebraic effects) resolves this: the monad assignments are **effect signatures** — what each role raises, and what the handler receives at the interface boundary.

| Actor | Implementation effects | Interface type (what handler receives) |
|---|---|---|
| **Executor** | `IO_W` (world interaction) | `Either E Result` (text, structured data, binary, error) |
| **Inferencer** | Opaque (attention + sampling) | `Response` = text blocks + tool call proposals |
| **Principal** | `IO` (unbounded) | `MultimodalMessage` = text + images + files + structured selections |
| **Harness** | `StateT Conv_State IO` | `HarnessAction` = enumerable tagged union |

Key corrections: the Harness is `StateT Conv_State IO` (handles conversation state, lives in IO for dispatch/loading). The Inferencer's interface is `Response` not `Distribution(TokenSeq)` — sampling has already happened. The Principal provides multimodal input, not just text — images, files, and structured selections flow through the Harness.

**Resolution**: The handler doesn't need the implementation effect — it pattern-matches on the interface type. Prop 13.3 (Executor boundary = genuine monad morphism) becomes: the Executor has its own internal handler that compresses `IO_W` to `Either E Result`. Conv 13.3a (Inferencer boundary = modeling convention) becomes: the Inferencer's internal handler is opaque to the outer handler. See [Raising and Handling](raising-and-handling.md).

---

## 5. The Store comonad `extend` over-promises — RESOLVED

`extend` was interpreted as "what would inference produce under each possible scoping?" — a counterfactual the handler can't compute (it would require running inference under every scoping, which requires the weights).

**Resolution**: `extend f` where `f` is a comonadic operation captures "what would each actor *see* under each possible scoping?" — the handler's design space. The handler CAN compute this (it's just `view(s)` for each `s`). The actor's *response* to each view is opaque (internal ma, behind the interface boundary). `extract` and `duplicate` are unchanged and honest. `extend` is the handler navigating a well-characterized design space (the comonadic side) to manage an opaque process (the actor's internal effects). See [Raising and Handling](raising-and-handling.md).

---

## 6. The two-level structure is porous — RESOLVED

**Resolution**: Replace "two levels" with **raising vs handling** from algebraic effects (Plotkin & Pretnar 2009). Raising (appending to log, proposing tool calls) is monotone. Handling (interpreting effects, compacting, reconfiguring) may break monotonicity. The monotonicity boundary is between these two roles, not between two "levels."

This dissolves every porosity case: the quartermaster has delegated handler privileges (handler composition), promises are deferred handling (handler suspends interpretation), the Harness IS the handler (not straddling levels). The session types from §15.1 are literally the handler's pattern matching on raised effects.

Connection to algebraic effects literature: handlers of algebraic effects have mature composition laws and type safety results. The mapping is almost exact — tool signatures = operation declarations, session type branches = handler cases, handler's own IO = handler effectfulness. See [Raising and Handling](raising-and-handling.md).

---

## 7. Predictability requires computational tractability — RESOLVED

**Resolution**: Add a third condition: (3) computational tractability — the simulation must be cheaper than running the system. The open-weights Inferencer has conditions 1+2 but not 3 (simulation = running the model = replication, not prediction).

The handler framing sharpens this further: **regulation is strictly weaker than prediction**. The handler doesn't need to predict what the actor will do — it needs to handle whatever arrives. Prediction requires embeddability + accessibility + tractability. Regulation requires knowing the effect signature + having a handling strategy. The Harness succeeds because it regulates (handles effects via the session type) rather than predicts (simulates the Inferencer). This is the precise content of Conant-Ashby: the "model" the regulator needs is the effect signature + handling strategy, not a simulation. See [Raising and Handling](raising-and-handling.md).

---

## 8. Three orderings, unclear relationship — RESOLVED

The framework has four partial orders. They form a causal chain, not a confused tangle:

```
Configuration lattice          → Grade lattice          → Monad morphism preorder
(S × P(Tools))                   (W × D)                  (M, ≤_ma)
Harness's control surface        Actor's path space        Interface effect type
What the Harness gives           What the actor IS         What others see
```

**Configuration bounds grade.** The Harness's configuration `(s, T)` determines the actor's effective grade. Scope `s` restricts world coupling (less visible state = less reachable state for the Inferencer). Tool set `T` affects both axes: each tool contributes world coupling (what world it touches) and multiplies with the actor's decision surface (the decision surface navigates tool outputs). Restricting configuration can only reduce the effective grade:

```
config₁ ≤ config₂  ⟹  grade(A, config₁) ≤ grade(A, config₂)
```

The configuration lattice is the Harness's lever. It controls grade from outside.

**Grade bounds interface ma.** The actor's grade `(w, d)` — its computational path space — sets an upper bound on what its interface effects can express. You can't produce richer interface effects than your path space supports. But the co-domain funnel (§13.3) can make interface ma strictly *lower* than the grade — an actor with high grade funneled through a narrow interface type (Approve/Reject) has low interface ma despite vast path space.

```
interface_ma(A) ≤ f(grade(A))    for some monotone f
```

with equality when the interface is unconstrained, and strict inequality at co-domain funnels.

**The monad morphism preorder compares interface ma.** `M ≤_ma N` means N can embed M's interface effects — N can *model* M. This is the comparison tool for trust and predictability, operating on the interface projection.

**Where each ordering does its work:**

| Ordering | Domain | What it captures | Who uses it |
|---|---|---|---|
| **Configuration lattice** `(S × P(Tools))` | Harness decisions | What the actor is given | The Harness (navigating the lattice) |
| **Grade lattice** `(W × D)` | Actor computation | The actor's path space (internal ma) | The architect (reasoning about system properties) |
| **Monad morphism preorder** `(M, ≤_ma)` | Interface effects | What others can model (interface ma) | Other actors (reasoning about trust, embeddability) |
| **Scope lattice** `(S, ≤)` | Message visibility | What actors can see | Subsumed by configuration lattice (S is the first component) |

The scope lattice is the first component of the configuration lattice — it's not a separate ordering but a projection. So there are really three: configuration (control), grade (measurement), preorder (comparison).

**What was missing was the bounding relationships, not the connection.** The original framework had the configuration lattice and the monad preorder but no formal object for the actor's path space between them. The grade lattice fills that gap. Configuration → grade → interface ma is the causal chain. The Harness controls configuration; the grade is the result; the interface ma is the projection that other actors reason about.

The decision surface axis (absent from `formal-framework.md`) belongs in the grade lattice, which belongs between the configuration lattice and the monad preorder in the framework's structure. When integrating, the grade lattice should appear after §12.8 (configuration lattice) and before the design principles (§17), connecting the Harness's control surface to the interface ordering.

---

## 9. The composition story is incomplete for conversations

`grade(A calls B)` handles tool-call composition: A invokes B once, gets a result back. This is one-shot, unidirectional.

But conversations are *iterated, bidirectional* composition. The Inferencer and Harness alternate turns, each conditioning on the other's output. This isn't `A ⊗ B`; it's a fixpoint of `A ⊗ B ⊗ A ⊗ B ⊗ ...` with feedback. The "LLM in multi-turn conversation" entry in the grade grid notes "decision surface grows at runtime" — each turn adds context that changes how subsequent inputs are processed.

The composition formula doesn't capture this. It's a one-shot product, not an iterative one. The decision surface of a conversation isn't the product of the participants' decision surfaces — it's the *trajectory* through the grade lattice as the conversation unfolds.

**Status**: The tool-call composition story is clean. The conversation-as-iterated-composition story is an open problem.

---

## What's strongest

These survive scrutiny and do real formal work:

1. **The Store comonad for the Harness's structural role.** The `extract`/`duplicate` asymmetry precisely captures why the Harness sees everything and actors see projections. This is the cleanest formalization in the framework.

2. **The monad-comonad duality.** Expansion = monadic (`bind` injects information), compression = comonadic (`extract` projects views). The Harness at the boundary. This is genuine structural insight, not decoration.

3. **The session types for the permission protocol.** The tool-use session type (Def 15.1) makes structural what was narrative. Each branch has a formal co-domain effect. The Principal's channel is only opened in `Ask` branches. This is precise and useful.

4. **The configuration lattice** (Section 12.8). `(Scope × P(Tools))` as a product lattice navigated by the Harness. Tool restriction as the primary driver of co-domain narrowing. This connects the two halves of the formalism through a concrete algebraic object.

5. **Co-domain funnels** (Def 13.5). High internal ma mapped to low interface ma via a monad morphism. The quartermaster, auditor, and sub-agent boundary as instances of one pattern. Clean, useful, and likely novel in this application.

6. **The Conant-Ashby connection.** "Every good regulator must be a model of the system." The Harness models the Inferencer's interface (not its implementation). This justifies the entire formalization effort — we're building the regulator's model. The two-morphism distinction (`η_interface` exists, `η_impl` does not) is precise and load-bearing.

7. **The interface/internal ma distinction** (Section 13). Independent levers: restrict tools not models. An Opus model with `{Approve, Reject}` has high internal ma and low interface ma. This is architecturally actionable.

## What needs the most work

Points 1–8 resolved. Remaining:

1. **Composition story incomplete for conversations** (point 9). Tool-call composition (one-shot join) is clean. Conversation-as-iterated-composition (multi-turn with feedback, decision surface growing at runtime) is an open problem. The grade of a conversation is a trajectory through the lattice, not a single point.

2. **Integrate the algebraic effects connection into the formal framework.** The raising/handling reframing (point 6) is currently in working notes. Sections 10.5 (two-level structure), 12.2 (Store extend), and the monad assignment table in §11 should be updated to reflect the handler framing.

3. **Integrate the grade lattice into the formal framework.** The grade lattice (resolving points 1-3) and the three-orderings relationship (point 8) should appear in the formal framework after §12.8 (configuration lattice), connecting the Harness's control surface to the interface ordering. The framework's Section 11 should reference the grade as the definition of ma, with K-complexity and the preorder as projections.

---

## The meta-observation

The original version of this critique concluded that the framework was strongest as a structural theory (Store comonad, session types, configuration lattice) and weakest as a measurement theory (what ma IS, how it composes). That was true at the time. The grade lattice and handler reframing have partially closed the gap:

- Ma now has a definition (the computation's path space) and a measure (the grade `(w, d) ∈ W × D`).
- Composition is defined (join on the product lattice) with the "multiplicative" intuition grounded in supermodularity.
- Decision surface has a formal definition (log of distinguishable input-dependent execution paths, connecting to Ashby's variety and VC dimension).
- The two-level structure is replaced by raising/handling from algebraic effects — no staging fiction, clean handler delegation.
- The monad assignments are refined to effect signatures with correct interface types.
- Predictability gains a third condition (computational tractability) and the regulation/prediction distinction.

What remains weakest: the **composition story for conversations** (multi-turn, iterated, with decision surface growing at runtime) and the **relationship between the three orderings** (scope lattice, monad morphism preorder, grade lattice). These are genuine open problems, not hand-waving.

The honest framing, updated: the formal framework is a **structural theory of agent architecture** grounded in a **measurement theory of computational latitude**. The structural theory (Store comonad, session types, configuration lattice, handler framing) formalizes relationships and flows. The measurement theory (grade lattice, supermodularity, decision surface) formalizes actor properties. They connect through the Harness: the handler navigates the grade lattice (measurement) while managing the Store comonad (structure). The framework needs both halves, and both halves are now at least partially formalized.
