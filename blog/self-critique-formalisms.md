# Self-Critique: The Formalisms

*An honest accounting of where the formal framework is solid, where it's suggestive, and where it's doing hand-waving in a lab coat.*

**Status**: Points 1–3 resolved in [The Grade Lattice](the-grade-lattice.md). Points 4–9 remain open.

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

## 4. The monad assignments to actors are stipulative

| Actor | Assigned monad | Problem |
|---|---|---|
| Harness | `State Conv_State` | The Harness also does IO (reads config, dispatches processes). Is it `StateT Conv_State IO`? |
| Inferencer | `Distribution` | Acknowledged as a "modeling convention" (Conv 13.3a). But `Distribution` assumes you know the sample space — the point of high ma is that you *don't*. |
| Principal | `IO` | IO is the "everything" monad. It characterizes the Principal by not characterizing them. |
| Executor | `Either E` | File-read executors do `IO_sandbox`, not `Either`. The *interface* type is `Either`; the *implementation* is `IO_W`. |

The assignments work as *interface* monads (what other actors observe) but not as *implementation* monads. This is acknowledged in Section 13, but the co-domain gradient (Def 11.1) presents the ordering `Identity ≤ ... ≤ IO` as a single chain, blurring which level of description it applies to.

**The deeper issue**: The monad morphism preorder is well-defined on actual monads. But the "monads" assigned to the Inferencer and Principal are modeling conventions, not descriptions. The preorder is doing real work (it formalizes trust, embeddability, predictability) — but only on the actors whose monad assignments are genuine (Harness, Executors). For the high-ma actors, it's "as if" reasoning. This is explicitly acknowledged (Conv 13.3a is admirably honest), but it means the central claim — "ma determines role" via the monad preorder — is formally grounded for half the actors and informally motivated for the other half.

---

## 5. The Store comonad `extend` over-promises

Section 12.2 claims:

> `extend infer (view, s_inferencer)` = "what would inference produce under each possible scoping?"

This treats inference as a function `ConvStore → B`. But inference is stochastic — it's `ConvStore → Distribution(B)`. The `extend` would give `Store Scope (Distribution(B))`, not a clean counterfactual. And the Harness can't actually compute this — it would need to *run* inference under each possible scoping, which requires the model weights.

The Store comonad captures the *structural role* of the Harness beautifully: the asymmetry between `extract` (what actors see) and `duplicate` (the Harness's god-view) is real and important. But the `extend` interpretation as a counterfactual optimization tool over-promises. The Harness doesn't evaluate "what would inference produce under each scoping?" It uses heuristics and rules to choose a scoping, then runs inference once.

**What survives**: `extract` and `duplicate` are honest. The Harness constructs views (`extract`) and has access to all possible views (`duplicate`). The `extend` interpretation should be weakened from "computable counterfactual" to "formal characterization of the design space the Harness navigates heuristically."

---

## 6. The two-level structure is porous

Object level (monadic, append-only) vs meta level (endomorphisms on `Conv_State`). The distinction is motivated by the analog to compile-time vs runtime in PLs — one structures the other.

But the boundary is crossed constantly:
- The quartermaster "straddles both levels"
- Promises blur the boundary (Section 15.6)
- The Harness operates at both simultaneously
- Scope expansion (tool grants) is a meta-level operation triggered by object-level proposals

In a real PL, the compile-time/runtime distinction is sharp because of *staging* — compile-time decisions are made before runtime begins. Here there's no staging. Both levels execute concurrently and interact continuously. The "two levels" may be a category error — applying a staged metalanguage intuition to an unstaged system.

**What survives**: The distinction between *append-only operations* (adding messages to the log) and *structure-modifying operations* (compaction, tool mutation, scope change) is real and useful. These have different algebraic properties — the former preserves the prefix ordering, the latter doesn't. But calling them "levels" implies a staging discipline that doesn't exist.

**Possible resolution**: Replace "two levels" with "two operation classes": log operations (monadic, monotone, within-phase) and structure operations (endomorphisms, possibly non-monotone, phase-boundary). The Harness interleaves both. No staging claim needed.

---

## 7. Predictability requires computational tractability

The two conditions for predictability: (1) structural embeddability (monad morphism exists) and (2) parametric accessibility (parameters known).

Missing: (3) computational tractability — can you *run* the simulation in reasonable time?

A temperature-0 LLM with published weights is both structurally embeddable and parametrically accessible. Is it predictable? Only if you can afford to run inference. The morphism exists; the parameters are accessible; but computing the simulation requires GPU-hours.

This matters for the Conant-Ashby connection: "every good regulator must be a model of the system." But a model must be *cheaper to run* than the system it models. The Harness models the Inferencer's interface because the interface model is *cheap* — `HarnessAction` is an enumerable tagged union. Emulation is ruled out not just by parametric inaccessibility but by computational cost. The Harness can check "is this a valid tool call?" in microseconds; it cannot check "is this the response the Inferencer would give?" without running the Inferencer.

This third condition is missing from the formal framework. Its absence means "predictability = embeddability + accessibility" is a necessary condition, not a sufficient one.

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

In order of priority:

1. **Reconcile the three formal objects called "ma."** Either define ma as a single formal object with the grade, K-complexity, and preorder as derived quantities, or explicitly name them as separate concepts (ma-grade, ma-complexity, ma-expressiveness) that project from a shared informal concept. The current equivocation undermines every claim of the form "ma determines X."

2. **Formalize decision surface or scope the framework honestly.** Either adopt Ashby's variety (or K-complexity of the function) as the formal measure, or explicitly say: "the formal framework captures boundary aspects of ma; the interior (decision surface) is the open problem." Don't present a two-axis lattice as a formal contribution when one axis is informal.

3. **Define ⊗ concretely.** If it's join on a lattice, say so. If it's something else, define it. The GCC narrative constrains the algebra but doesn't determine it.

4. **Add computational tractability** as a third condition for predictability. This completes the Conant-Ashby connection: a good regulator must be a model that is *cheaper than* the system.

5. **Weaken `extend` claims.** Keep `extract`/`duplicate` as the honest comonadic content. Reframe `extend` as the formal design space, not a computable counterfactual.

6. **Soften the two-level language.** "Two operation classes" rather than "two levels." The staging metaphor implies a separation that doesn't exist.

---

## The meta-observation

The strongest parts of the framework are the *structural* claims: the Store comonad for scope construction, the monad-comonad duality, the session types for protocols, the configuration lattice. These formalize *architectural relationships* — who sees what, how information flows, where the boundaries are.

The weakest parts are the *measurement* claims: what ma IS (as a number, a grade, a position), how it composes quantitatively, what the decision surface IS formally. These attempt to formalize *actor properties* — intrinsic characteristics rather than relationships.

This pattern is not accidental. Category theory is a theory of *structure-preserving maps between structures* — it's naturally good at relationships and naturally bad at intrinsic properties. The framework is strongest when it uses categorical tools for categorical questions (how do scopes compose? what's the Harness's structural role? how do permission branches interact?) and weakest when it uses them for non-categorical questions (how complex is this actor's decision surface? how much ma does this computation have?).

The honest framing: the formal framework is a **structural theory of agent architecture** — it formalizes relationships, boundaries, and flows. Ma is the **motivating concept** that guided the structural theory. The structural theory doesn't fully formalize ma, and it doesn't need to. The design principles (Section 17) follow from the structural theory alone. Ma is the intuition; the math is the architecture.
