# Self-Critique: The Formalisms

*An honest accounting of where the formal framework is solid, where it's suggestive, and where it's doing hand-waving in a lab coat.*

**Status**: Points 1–3 resolved in [The Grade Lattice](the-grade-lattice.md). Points 4–7 resolved in [Raising and Handling](raising-and-handling.md). Points 8–9 remain open.

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

## 8. Three orderings, unclear relationship

The framework introduces three partial orders:

1. **Scope lattice** (Section 2): orders what actors can see. Comonadic side.
2. **Monad morphism preorder** (Section 11): orders effect expressiveness. Monadic side.
3. **Grade lattice** (predictability-as-embeddability): orders world coupling × decision surface. New.

The configuration lattice (Section 12.8) couples the first two as a product `(Scope × P(Tools))`. But the grade lattice is a third structure that doesn't obviously embed in the configuration lattice.

Where does the decision surface appear in `formal-framework.md`? Nowhere. It lives entirely in the working notes. If decision surface is one of the three determinants of ma, and the formal framework doesn't formalize it, the framework formalizes two-thirds of its central concept.

**Possible resolution**: The grade lattice belongs in the working notes (as it currently is) until the decision surface axis is formalized. The formal framework should be explicit that it formalizes the *boundary* aspects of ma (what enters and exits the space) and leaves the *interior* aspect (what fills the space) informal. Section 3's new three-part introduction to ma should flag this asymmetry.

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

Points 1–7 resolved. Remaining:

1. **Three orderings, unclear relationship** (point 8). The scope lattice, monad morphism preorder, and grade lattice are three partial orders. The configuration lattice couples the first two. The grade lattice is a third structure that needs explicit connection. The decision surface axis is absent from `formal-framework.md` entirely.

2. **Composition story incomplete for conversations** (point 9). Tool-call composition (one-shot join) is clean. Conversation-as-iterated-composition (multi-turn with feedback, decision surface growing at runtime) is an open problem. The grade of a conversation is a trajectory through the lattice, not a single point.

3. **Integrate the algebraic effects connection into the formal framework.** The raising/handling reframing (point 6) is currently in working notes. Sections 10.5 (two-level structure), 12.2 (Store extend), and the monad assignment table in §11 should be updated to reflect the handler framing.

4. **Integrate the grade lattice into the formal framework.** The grade lattice (resolving points 1-3) is currently a separate document. The formal framework's Section 3 (scope boundaries) and Section 11 (interface monad ordering) should reference the grade as the definition of ma, with K-complexity and the preorder as projections.

---

## The meta-observation

The strongest parts of the framework are the *structural* claims: the Store comonad for scope construction, the monad-comonad duality, the session types for protocols, the configuration lattice. These formalize *architectural relationships* — who sees what, how information flows, where the boundaries are.

The weakest parts are the *measurement* claims: what ma IS (as a number, a grade, a position), how it composes quantitatively, what the decision surface IS formally. These attempt to formalize *actor properties* — intrinsic characteristics rather than relationships.

This pattern is not accidental. Category theory is a theory of *structure-preserving maps between structures* — it's naturally good at relationships and naturally bad at intrinsic properties. The framework is strongest when it uses categorical tools for categorical questions (how do scopes compose? what's the Harness's structural role? how do permission branches interact?) and weakest when it uses them for non-categorical questions (how complex is this actor's decision surface? how much ma does this computation have?).

The honest framing: the formal framework is a **structural theory of agent architecture** — it formalizes relationships, boundaries, and flows. Ma is the **motivating concept** that guided the structural theory. The structural theory doesn't fully formalize ma, and it doesn't need to. The design principles (Section 17) follow from the structural theory alone. Ma is the intuition; the math is the architecture.
