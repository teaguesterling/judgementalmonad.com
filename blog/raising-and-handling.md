# Raising and Handling

*The two-level structure dissolves into algebraic effects. What remains is sharper.*

---

## The problem

The formal framework (Section 10.5) describes a "two-level structure":

1. **Object level** — monadic. Agents read through scopes and append to the log. The graded monad captures this. Operations preserve the append-only invariant.
2. **Meta level** — endomorphisms on `Conv_State`. Operations transform the conversation structure: compaction, tool mutation, budget reclamation. These may violate monotonicity.

The analogy is to compile-time vs runtime in programming languages — one structures the other. But the analogy breaks: both "levels" execute concurrently and interact continuously. The quartermaster straddles both. Promises blur the boundary. The Harness operates at both simultaneously.

The staging metaphor implies a separation that doesn't exist. This isn't a minor terminological complaint — it affects how we think about the Harness's role, the monad assignments to actors, and the Store comonad interpretation.

---

## The reframing: raising vs handling

The right structure isn't two levels. It's two roles in an effect system — and the mapping to algebraic effects (Plotkin & Power 2003, Plotkin & Pretnar 2009) is almost exact.

In algebraic effects:
- Computations **raise** effects: `Read(path)` means "I need a file read; give me back a string"
- **Handlers** interpret effects: they receive the operation + the continuation, and decide what to do
- Handlers can themselves be effectful — they can raise effects interpreted by an outer handler
- Handlers compose (nesting = nested scope)

In the conversation:

| Algebraic effects | Our framework |
|---|---|
| Operation declaration (`op : A → B`) | Tool signature (`Read : FilePath → String`) |
| Raising an effect | Inferencer proposes a tool call |
| Handler pattern match | Session type branches (AutoAllow, Ask→Grant/Deny, AutoDeny) |
| Handler transforms/suppresses/batches | Harness gates, reorders, denies, parallelizes |
| Handler's own effects | Harness doing IO (dispatching processes, loading images, reading config) |
| Handler modifying its state | Structure operations (compaction, tool mutation, budget reclaim) |

The session type from formal-framework §15.1 IS the handler's pattern matching. Each branch is a different handling strategy for the same raised effect (tool call proposal). `AutoAllow` handles by dispatching immediately. `Ask` handles by consulting the Principal. `AutoDeny` handles by suppressing the effect entirely.

### What the "two levels" become

**Raising**: appending to the log, proposing tool calls, producing output. Actors do this. It's monotone — the log grows, budget decreases, scopes widen within a phase. The graded monad captures it.

**Handling**: interpreting tool calls, gating permissions, compacting, reconfiguring scope and tools. The Harness does this. Not necessarily monotone — compaction breaks prefix ordering, budget reclamation reverses the budget trajectory, scope can be reconfigured between phases.

The **monotonicity boundary** isn't between levels — it's between raising and handling. And it's precisely defined: raising preserves the append-only invariant; handling can transform the substrate.

### Every "porous boundary" case dissolves

**The quartermaster straddles both levels** → The quartermaster is an actor with delegated handler privileges. It raises effects in one capacity (reading the log, producing a kit) and handles effects in another (configuring the worker's tool set). Delegating handler capabilities is standard in algebraic effects — it's handler composition.

**Promises blur the boundary** → Promises are deferred handling. The effect is raised now (tool call proposed), acknowledged (handler starts dispatch), but handling completes asynchronously (result injection happens later). The handler suspends part of its interpretation. This is standard — algebraic effect handlers can suspend and resume.

**The Harness operates at both simultaneously** → The Harness IS the handler. It doesn't straddle two levels. Handlers interleave handling with their own effectful computation (the handler lives in `StateT Conv_State IO`). Handling a tool call and then compacting the log is the handler interpreting one effect and then modifying its own state — both within the handler's single execution context.

**Scope expansion is triggered by object-level proposals** → An effect is raised (tool call with scope expansion request), and the handler interprets it (granting the expansion). The raised effect triggers handler action. This is the basic mechanic of algebraic effects — effects are raised precisely so the handler can act on them.

---

## Monad assignments refined: effect signatures

The original framework assigned monads to actors, but the assignments blurred implementation and interface. With the handler framing, the assignments become effect signatures — what effects each role raises, and what the handler sees at the interface.

### What the handler actually receives

| Actor | Implementation effects | Interface type (what handler receives) | Notes |
|---|---|---|---|
| **Executor** | `IO_W` (world interaction within sandbox) | `Either E Result` | Result = text, structured data, binary (images), error. The handler doesn't see the IO — it sees the result after error handling. |
| **Inferencer** | Opaque (attention + sampling + chain-of-thought) | `Response` = text blocks + tool call proposals | One sample from the internal process. Sampling has already happened. The handler receives the structured output, not the distribution. |
| **Principal** | `IO` (unbounded world interaction) | `MultimodalMessage` = text + images + files + structured selections | Richer than `Text`. Images flow: Principal references → Harness loads (handler IO) → included in Inferencer's focused view. |
| **Harness** | `StateT Conv_State IO` (manages state, lives in IO) | `HarnessAction` = enumerable tagged union | The handler IS the interface. `Extract`, `Gate`, `Inject`, `Meta`, `Yield`. |

### What this resolves

**"The Harness also does IO."** Yes — the handler is itself effectful. In algebraic effects, a handler can live in an outer effect context. `handle_with { tool_call(args, k) → dispatch(args) >>= k } : StateT Conv_State IO`. The Harness handles conversation effects (`State Conv_State`) while raising its own effects in `IO` (process dispatch, file loading, image processing). The original assignment of `State Conv_State` described the handled effect. `IO` is the handler's own effect. Both are real; the original just named one.

**"Distribution assumes you know the sample space."** Correct, and we don't. But the handler doesn't need the distribution — it receives one sample (`Response`). Convention 13.3a (modeling the Inferencer's effects *as if* drawn from a distribution) is sufficient for the handler's purpose: receive the structured output, check protocol conformance, handle the proposed effects. The handler pattern-matches on the response structure, not the generation process.

**"IO for the Principal characterizes by not characterizing."** Yes — and that's correct. `IO` as an effect signature means "can raise any effect." The handler can't usefully pattern-match on Principal effects. It receives `MultimodalMessage` and processes it. The Principal is the *unhandled context* — effects from outside the handler's scope. Every effect system has an outermost boundary where effects come from "the world." The Principal is that boundary.

**"Either E for Executors, but they do IO_W."** The Executor *raises* `IO_W` effects internally. The handler *receives* `Either E Result` at the interface — the result after the Executor's own effect handling (its internal error handling, sandbox enforcement, etc.). The interface boundary IS the handler boundary. This is exactly what Proposition 13.3 (genuine monad morphism for Executors) formalizes: the Executor has its own internal handler that maps `IO_W` to `Either E Result` before the outer handler (Harness) sees it.

### The implementation/interface table

| Actor | Implementation effect | Interface effect | Boundary type |
|---|---|---|---|
| **Executor** | `IO_W` | `Either E Result` | Genuine monad morphism (Prop 13.3). The Executor's internal handler compresses IO to Either. |
| **Inferencer** | Opaque | `Response` (structured output) | Modeling convention (Conv 13.3a). We don't have the implementation effect; we model the interface. |
| **Principal** | `IO` | `MultimodalMessage` | Unhandled context. Effects from outside the system. |
| **Harness** | `StateT Conv_State IO` | `HarnessAction` | Self-characterizing. The handler's interface IS its action type. |

---

## Store comonad `extend`: what it actually captures

The formal framework (Section 12.2) claims:

> `extend infer (view, s_inferencer)` = "what would inference produce under each possible scoping?"

This over-promises. The handler can't run inference. With the handler framing, `extend` becomes precise:

**`extract(view, s)`** = what the handler produces as input to the actor at scope position `s`. The handler CAN compute this — it's just `view(s)`, projecting `Conv_State` through a scope.

**`duplicate(view, s)`** = at every scope position, the ability to compute every other position's extraction. The handler's full knowledge — it knows what every actor would see under every scoping. The handler CAN compute this — it has access to `Conv_State`.

**`extend f (view, s)`** where `f` operates on the Store — apply `f` at every scope position. If `f` is "compute the extraction" (a comonadic operation), this gives the handler's design space: what each possible scoping would produce as input to the actor. The handler CAN compute this.

The over-promise: interpreting `f` as "compute the extraction AND run inference AND return the result." The handler can compute what each actor would *see* under each scoping (comonadic — the handler's domain). The handler CANNOT compute what each actor would *do* with what it sees (that's the actor's internal ma — opaque to the handler, requiring the actor's implementation effect which is behind the interface boundary).

**Clean statement**: `extend` captures the handler's ability to evaluate "what would each actor *see* under each possible scoping?" — the design space the handler navigates. The actor's *response* to each view is opaque. The handler navigates this design space heuristically — choosing a scope that it expects (but cannot prove) will produce good inference results.

This is still powerful. The handler's ability to compute every possible extraction — to know what it *could* show each actor — is the formal content of the Harness's structural advantage. It navigates a well-characterized design space (the comonadic side) to manage an opaque process (the actor's internal effects). The Store comonad captures the well-characterized part honestly.

---

## Computational tractability: the missing condition

The predictability-as-embeddability thesis gives two conditions:

1. **Structural embeddability**: `η : M ~> N` exists — N's effect type can represent M's effects
2. **Parametric accessibility**: M's specific parameters are known

Missing: a third condition that the handler framing makes obvious.

3. **Computational tractability**: the simulation `η ∘ f` is cheaper to run than the original computation `f`

All three are needed:

| Actor | Embeddable? | Accessible? | Tractable? | Predictable? |
|---|---|---|---|---|
| Harness (`HarnessAction`) | Yes — embeds in everything | Yes — `Conv_State` in the log | Yes — enumerable, cheap to check | **Yes** |
| Executor (`Either E Result`) | Yes — embeds in IO | Yes — sandbox config visible | Yes — bounded computation | **Yes** |
| Inferencer (open weights) | Yes — `Response` embeds in IO | Yes — weights published | **No** — simulation = running the model | **No** (in practice) |
| Inferencer (closed weights) | Yes | No — weights proprietary | N/A | **No** |
| Principal (`MultimodalMessage`) | Top of preorder | No — mind inaccessible | No — unbounded | **No** |

The open-weights Inferencer is the critical case. It has conditions 1 and 2 but fails condition 3. You *could* simulate it — you have the morphism and the parameters — but the simulation costs as much as running the model. This isn't prediction; it's replication.

### Why the handler doesn't need prediction

The Conant-Ashby Good Regulator Theorem: "every good regulator must be a model of the system." But what kind of model?

The handler framing gives the answer: the handler doesn't need to *predict* what the actor will do. It needs to *handle* whatever the actor does. These are fundamentally different:

- **Prediction** requires: structural embeddability + parametric accessibility + computational tractability. You simulate the actor and check the result before it happens. Expensive. Often impossible.
- **Handling** requires: knowing the effect signature (what effects can be raised) + a handling strategy (what to do with each effect). You receive the raised effect and respond. Cheap. Always possible given the interface type.

The Harness succeeds by handling, not predicting. It knows the Inferencer's interface type (`Response` = text blocks + tool call proposals). It knows its handling strategy (the session type: check permissions, dispatch or deny, inject results). It doesn't need to predict which tool call will be proposed — it needs to handle whatever arrives.

This is the precise content of the Conant-Ashby connection: the Harness's "model" of the Inferencer is the effect signature + the handling strategy. The session type IS this model. It's cheaper than the system it regulates because it describes the protocol structure (a finite state machine) rather than the computation (a neural network).

### The three conditions, updated

For *prediction* (can you know what the actor will do before it does it?):
1. Structural embeddability
2. Parametric accessibility
3. Computational tractability

For *regulation* (can you ensure the system behaves within bounds?):
1. Knowledge of the effect signature (what effects can be raised)
2. A handling strategy for each effect (the session type)
3. The handler's own effects are tractable (checking permissions, dispatching tools)

Regulation is strictly weaker than prediction. The Harness regulates the Inferencer without predicting it. This is why low-ma actors work at the hub: they can *handle* high-ma actors' effects because handling operates on the interface type, not the implementation.

---

## Connection to the existing framework

### What changes

| Framework element | Old framing | New framing |
|---|---|---|
| Two-level structure (§10.5) | Object level (monadic) vs meta level (endomorphisms) | Raising effects (monotone) vs handling effects (may break monotonicity) |
| Harness role | "Operates at the meta level" | IS the handler — interprets raised effects, manages its own state |
| Quartermaster | "Straddles both levels" | Actor with delegated handler privileges |
| Promises | "Blur the boundary" | Deferred handling — handler suspends interpretation |
| Monad assignments | Implementation monads assigned to actors | Effect signatures: what each role raises, what the handler receives |
| Store `extend` | "What would inference produce under each scoping?" | "What would each actor *see* under each scoping?" — handler's design space |
| Predictability conditions | Embeddability + accessibility | + Computational tractability (but regulation is weaker than prediction) |

### What doesn't change

- The **Store comonad** for scope construction: `extract`/`duplicate` are unchanged. The handler constructs views and has access to all possible views.
- The **monad-comonad duality**: expansion = monadic (effect results enter the log), compression = comonadic (handler projects the conversation). The handler mediates both.
- The **session types**: these ARE the handler's pattern matching. Each branch is a handling strategy. Unchanged — if anything, strengthened by the algebraic effects connection.
- The **configuration lattice**: `(Scope × P(Tools))` navigated by the handler when configuring each actor. Unchanged.
- The **co-domain funnel** pattern: actors with internal handlers that compress rich implementation effects to constrained interface effects. This IS handler composition — the Executor's internal handler maps `IO_W` to `Either E Result` before the Harness's handler sees it.
- The **grade lattice**: characterizes the computation's path space. Orthogonal to the raising/handling distinction — the grade describes *what* the actor is; raising/handling describes *how* it participates in the effect system.

### What's gained

1. **Connection to established theory.** Algebraic effects have a mature literature with composition laws, type safety results, and implementations. The handler framing potentially imports decades of work.

2. **No staging fiction.** The framework no longer pretends there's a clean temporal separation between levels. Handlers and computations interleave — which is what actually happens.

3. **Handler delegation is natural.** The quartermaster receiving handler privileges from the Harness is just handler composition/delegation — a standard operation in algebraic effects, not an awkward straddling of levels.

4. **The interface boundary is the handler boundary.** Proposition 13.3 (monad morphism for Executors) and Convention 13.3a (modeling convention for opaque actors) become: "the Executor has its own internal handler" and "the Inferencer's internal handler is opaque." Same content, clearer framing.

5. **Regulation ≠ prediction.** The handler framing makes precise why the Harness doesn't need to predict the Inferencer: handling operates on the effect signature, not the implementation. This sharpens the Conant-Ashby connection and adds computational tractability as the missing condition for prediction specifically.

---

## References (to add)

- Plotkin, G., & Power, J. (2003). Algebraic operations and generic effects. *Applied Categorical Structures*, 11(1).
- Plotkin, G., & Pretnar, M. (2009). Handlers of algebraic effects. *ESOP*.
- Kammar, O., Lindley, S., & Oury, N. (2013). Handlers in action. *ICFP*.
- Bauer, A. (2018). What is algebraic about algebraic effects and handlers? *arXiv:1807.05923*.
