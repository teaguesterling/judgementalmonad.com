# Formal Companion

*Definitions, propositions, conjectures, and open problems for the framework developed in [The Ma of Multi-Agent Systems](00-intro.md).*

This document formalizes the structural claims from the blog series. It assumes the reader has the blog for motivation, examples, and design intuitions. It follows mathematical dependency order, not the blog's narrative order. Cross-references to specific posts are given where the informal treatment lives.

**Labeled environments.** *Definition*: precise formal statement. *Proposition*: proven or provable. *Conjecture*: stated precisely but open. *Convention*: modeling choice, not a truth claim. Gaps are marked honestly — they are the work queue.

---

## 1. Preliminaries

### 1.1 The conversation log

**Definition 1.1 (Message type).** Let `M` be a type of messages. A message `m : M` may be a Principal utterance, an Inferencer response, a tool call, a tool result, or a scoping annotation. We do not constrain the internal structure of `M` — it is a parameter of the framework.

**Definition 1.2 (Log monoid).** The conversation log is the free monoid `(M*, ·, ε)` where `M*` is the set of finite sequences of messages, `·` is concatenation, and `ε` is the empty sequence.

**Definition 1.3 (Log as poset category).** Define a partial order on `M*` by the prefix relation: `l₁ ≤ l₂` iff `l₁` is a prefix of `l₂`. This poset, viewed as a category **Log**, has objects `M*` and a unique morphism `l₁ → l₂` whenever `l₁ ≤ l₂`. The category is filtered and captures the append-only invariant.

### 1.2 Actors

**Definition 1.4 (Actor roles).** Every message in the log is produced by one of four roles:

| Role | What it does | Interface type |
|---|---|---|
| **Principal** | Provides intent and authorization | `MultimodalMessage` |
| **Inferencer** | Proposes actions via learned weights | `Response = TextBlock[] + ToolCall[]` |
| **Executor** | Performs world interaction | `Either E Result` |
| **Harness** | Mediates all communication | `HarnessAction` (Def. 5.3) |

The roles partition the log entries. All communication passes through the Harness (the star topology — see blog post 1).

### 1.3 Scopes

**Definition 1.5 (Scope).** A scope is a monotone function `s : M* → M*` such that for all logs `l`, `s(l)` is a subsequence of `l`. Monotonicity: if `l₁ ≤ l₂` then `s(l₁) ≤ s(l₂)`.

**Definition 1.6 (Scope lattice).** The set of scopes over `M*` forms a partial order under pointwise inclusion: `s₁ ≤ s₂` iff for all `l`, `s₁(l)` is a subsequence of `s₂(l)`. The identity function `id` is top (full visibility). The constant function `s_⊥(l) = ε` is bottom (no visibility).

**Proposition 1.7.** For predicate-based scopes `s_p(l) = filter(p, l)`, the scope lattice is a Boolean algebra with join `s_{p∨q}`, meet `s_{p∧q}`, and complement `s_{¬p}`.

**Definition 1.8 (Scope boundary).** For scopes `s₁, s₂`, the boundary is `boundary(s₁, s₂) = s_{¬p₁} ∧ s_{¬p₂}` — messages invisible to both actors. A non-trivial boundary means information flows through neither scope.

---

## 2. The Conversation Monad

The blog series (posts 3-4) introduces conversations informally as closures with effects. Here we give the monadic substrate.

### 2.1 Structured conversation state

**Definition 2.1 (Conversation state).** The conversation state is a record:

```
Conv_State = {
  system       : M*,       -- system prompt (fixed across compaction)
  instructions : M*,       -- project context (fixed)
  history      : M*,       -- conversation turns (compaction target)
  tools        : P(Tool),  -- available tool set (mutable)
  budget       : N         -- remaining token capacity
}
```

The flattening function `flat : Conv_State → M*` concatenates compartments into the token sequence actors see (filtered through their scope). Object-level actors operate on `flat(s)`. Meta-level operations operate on `Conv_State` directly.

**Remark.** We start from `Conv_State` rather than the bare log monoid `M*`. The blog series (post 6) establishes that the composite entity's type is `StateT Conv_State IO` — beginning here avoids the `Writer → State` substrate shift that complicated the earlier formalization.

### 2.2 The conversation monad

**Definition 2.2 (Scoped computation).** An agent computation that reads from a scoped view and writes to the log is:

```
Agent_s(A) = M* → A x M*
```

where the input `M*` is filtered through scope `s` before the agent sees it. Execution on log `l`: `exec(f, s, l) = f(s(l))`, yielding `(a, w)` where `w` is the new entries appended.

**Definition 2.3 (Agent closure).** An agent closure is a triple `(f, s, l)` where `f : M* → A x M*` is the behavior, `s` is the scope, and `l` is the current log state. The capture list is `s(l)`.

**Proposition 2.4 (Correspondence to PL closures).** The triple `(f, s, l)` corresponds to a PL closure `(lambda, rho)` where `lambda <-> f` and `rho <-> s(l)`. The structural difference: in a PL closure, `rho` is fixed at creation time; in an agent closure, `s(l)` grows monotonically as `l` grows. This is strictly between static scoping (fixed) and dynamic scoping (can shrink). See blog post 3.

### 2.3 Kleisli structure

**Definition 2.5 (Scope-graded monad).** Let `(S, <=, V, bot)` be the scope lattice (Def. 1.6). The scope-graded monad `Conv_s` indexed by `s in S`:

```
Conv_s(A) = M* → A x M*
```

with graded bind:

```
bind : Conv_s(A) → (A → Conv_t(B)) → Conv_{s V t}(B)
```

and graded return: `return(a) = \l. (a, epsilon)` at grade `bot`.

**Proposition 2.6.** This satisfies the graded monad laws (Katsumata 2014), with the scope lattice `(S, V, bot)` as the grading monoid.

**Definition 2.7 (Kleisli category).** The Kleisli category **Conv_K** has types as objects and morphisms `A → B x M*` (Kleisli arrows). Composition sequences computations and concatenates log output. Agent handoffs are composition in **Conv_K** (blog post 3).

### 2.4 Budget as linear resource

**Definition 2.8 (Token budget).** The budget `b in N` tracks remaining context capacity. Each message consumes budget: `cost : M → N`. The constraint `budget >= 0` is maintained invariantly. The graded monad extends to track budget:

```
Conv_{s,n}(A)    where s : S, n : N
```

with `(S x N, (V, +), (bot, 0))` as grading monoid — composing agents joins scopes and sums budget. This connects to quantitative type theory (Atkey 2018).

---

## 3. The Store Comonad and Duality

The Harness does not just inject information (monadic) — it constructs what each actor sees (comonadic). Blog post 3 introduces the Store comonad informally; post 4 develops the raising/handling duality.

### 3.1 The Store comonad

**Definition 3.1 (Store comonad, standard).** For position type `S` and value type `A`:

```
Store S A = (S → A, S)

extract (f, s)    = f(s)
duplicate (f, s)  = (\s'. (f, s'), s)
extend g (f, s)   = (\s'. g(f, s'), s)
```

**Definition 3.2 (Conversation Store comonad).**

```
ConvStore = Store Scope FocusedView
```

where the stored function is `view : Scope → FocusedView` defined by `view(s) = flatten(s(conv_state))`, and the current position is the scope of the actor being served.

The comonad operations have precise meanings:

- `extract(view, s)` — the actor's token window: the conversation projected through scope `s`
- `duplicate(view, s)` — at every scope position, the ability to see every other position. This is the Harness's perspective: it can compute any actor's view
- `extend f (view, s)` — "what would `f` compute from each possible scoping?" The handler's design space

### 3.2 The duality

**Proposition 3.3 (Turn structure).** A single turn has the structure:

```
(view, s) --extract--> FocusedView --actor--> Output --bind--> Conv(Output)
```

Comonadic extraction, opaque processing, monadic injection. The Harness controls step 1 (scope selection) and the injection gate (blog posts 4, 6).

**Proposition 3.4 (Harness mediates both structures).**

| Operation | Structure | Effect |
|---|---|---|
| Scope selection | Comonadic | Chooses position `s` |
| Scope construction | Comonadic | Computes `extract(view, s)` |
| Compaction | Meta + comonadic | Modifies the stored function `view` |
| Tool dispatch | Monadic | `bind` — result enters log |
| Permission gate | Controls which `bind`s occur | Co-domain management |

Compaction modifies the stored function itself — after compaction, `view(s)` returns a lossy summary for every scope `s`. This is a transformation of the comonadic structure, not an operation within it.

**Proposition 3.5 (Asymmetric access).** The Harness has access to `duplicate` and `extend`. Other actors only see `extract`. This asymmetry is the formal content of the Harness's privileged position in the star topology.

### 3.3 Distributive law (open problem)

**Conjecture 3.6.** There exists a distributive law between the conversation monad `Conv` (Writer over log monoid) and `ConvStore` (Store over scope lattice):

```
lambda : Store Scope (Conv(A)) → Conv(Store Scope A)
```

This would formalize how extraction and injection compose within a single turn. The specific `Writer`-`Store` instance is unstudied, though distributive laws between monads and comonads are treated by Brookes & Geva (1992) and Uustalu & Vene (2008).

**Gap.** Without this distributive law, the turn structure (Prop. 3.3) is a *description* of the pattern, not a *derivation* from compositional principles. The comonadic and monadic halves are characterized independently.

---

## 4. The Grade Lattice

The grade measures *what an actor is* — the space between what it receives and what it produces. Blog post 2 introduces it informally; post 5 connects it to the monad morphism preorder.

### 4.1 The two axes

**Definition 4.1 (Grade lattice).** The grade of an actor `A` is:

```
grade(A) = (w_A, d_A) in W x D
```

where `W` (world coupling) and `D` (decision surface) are join-semilattices:

```
W: sealed <= pinhole <= scoped <= broad <= open
D: literal <= specified <= configured <= trained <= evolved
```

ordered componentwise: `(w_1, d_1) <= (w_2, d_2)` iff `w_1 <= w_2` and `d_1 <= d_2`. The partial order is intentional — `(broad, specified)` and `(sealed, trained)` are incomparable.

**Definition 4.2 (Decision surface).** The decision surface `d` is formally the log of the number of distinguishable input-dependent execution paths through the actor's computation:

```
d = log |{paths(x) : x in Inputs, paths(x) distinguishable}|
```

This connects to Ashby's requisite variety (1956), VC dimension, and the number of linear regions in piecewise-linear networks (Montufar et al. 2014). For a lookup table: `d = log(1) = 0`. For a specified rule system: `d = log(|rules|)`. For a deep network with `L` layers of width `n`: `d` grows as `O(n^L)` (exponential in depth).

**Definition 4.3 (World coupling).** World coupling `w` maps to the parameterized IO family:

```
IO_null <= IO_sandbox <= IO_filesystem <= IO_network <= IO
```

Each restriction narrows the set of world states that can influence the computation's behavior. `sealed` corresponds to `IO_null` (pure computation); `open` corresponds to unrestricted `IO`.

### 4.2 Composition

**Proposition 4.4 (Composition is join).** When actor `A` uses tool `B`:

```
grade(A using B) = (w_A V w_B, d_A V d_B)
```

The compound's world coupling is at least as broad as either component's. Its decision surface is at least as large. Join is commutative, associative, and idempotent.

*Proof.* The compound can reach any world state either component can reach (join on `W`). The compound's execution paths include all paths from either component's decision surface (join on `D`). The product lattice join is componentwise join. QED

### 4.3 Supermodularity

**Conjecture 4.5 (Supermodularity of characterization difficulty).** The characterization difficulty `chi : W x D → R` — how hard it is for an external observer to predict the actor's behavior — is supermodular:

```
chi(w_1 V w_2, d_1 V d_2) + chi(w_1 ^ w_2, d_1 ^ d_2) >= chi(w_1, d_1) + chi(w_2, d_2)
```

Equivalently: the marginal effect of increasing one axis is greater when the other is already high. Sandboxing (reducing `w`) has greater returns when `d` is large. Tool restriction has greater returns when both axes are high.

**Gap.** This is the formal content of "restriction is load-bearing" (blog post 2). It is stated precisely enough to test — one could measure observer prediction error as axes vary — but `chi` itself has no closed-form definition. A proof would require defining `chi` in terms of the decision surface and world coupling measures. An empirical test could provide evidence.

### 4.4 Interface ma vs internal ma

**Definition 4.6 (Interface ma and internal ma).**

```
ma_internal(A) = grade(A)                         -- the actor's path space
ma_interface(A) = characterizability of M_iface    -- what others see
```

These are independent (blog post 2, post 5):

| Configuration | Internal ma | Interface ma | Example |
|---|---|---|---|
| Large model, restricted tools | High | Low | Opus as auditor (Approve/Reject) |
| Small model, many tools | Low | High | Haiku with 50 tools |
| Large model, unrestricted | High | High | Unconstrained Inferencer |
| Deterministic rules, narrow output | Low | Low | Static tool whitelist |

Internal ma determines decision quality. Interface ma determines auditability.

### 4.5 Co-domain funnels

**Definition 4.7 (Co-domain funnel).** A co-domain funnel is an actor where `ma_internal >> ma_interface` — the implementation is strictly richer than the interface. The funnel compresses high internal ma through a constrained output type.

Examples: an Opus auditor with `{Approve, Reject}`, a sub-agent whose full conversation compresses to `Either(Result, Error)`, a tool-selection agent that outputs a finite kit.

**Proposition 4.8 (Funnels as monad morphisms).** For actors with well-defined implementation monads, the funnel is a monad morphism `eta : M_impl ~> M_iface` that is surjective on the co-domain (every output is reachable) and lossy (many internal states map to the same output). See section 6.3.

---

## 5. The Configuration Lattice and Harness Control

The Harness shapes each actor's effective grade through configuration. Blog post 9 makes this the central design lever.

**Definition 5.1 (Harness configuration).** A configuration for an actor is:

```
config = (s, T) in Scope x P(Tool)
```

where `s` is the scope (what the actor sees) and `T` is the tool set (what the actor can do).

**Definition 5.2 (Configuration lattice).** Ordered componentwise:

```
(s_1, T_1) <= (s_2, T_2)  iff  s_1 <= s_2 and T_1 <= T_2
```

This is the product lattice of the scope lattice and the powerset lattice of tools.

**Proposition 5.3 (Configuration bounds grade).** For actor `A` with configuration `(s, T)`:

```
config_1 <= config_2  ==>  grade(A, config_1) <= grade(A, config_2)
```

Scope `s` restricts world coupling. Tool set `T` affects both axes — each tool contributes world coupling (what world it touches) and composes with the actor's decision surface. Restricting configuration can only reduce the effective grade.

**Definition 5.3 (HarnessAction).** The Harness step function:

```
harness_step : Conv_State → HarnessAction

data HarnessAction
  = Extract Scope (FocusedView → ProposedActions)
  | Gate ToolCall Decision
  | Inject Result Conv_State
  | Meta (Conv_State → Conv_State)
  | Yield Conv_State
```

The Harness inhabits `StateT Conv_State IO`. Its interface type `HarnessAction` is a finite tagged union — enumerable given the current state and configuration. This is the formal content of "minimal ma": the Harness's co-domain is characterizable by reading its rules. The `IO` in `StateT Conv_State IO` is the handler's own effect (process dispatch, file loading), not visible at the interface.

**Proposition 5.4 (Causal chain).** Three orderings form a causal chain:

```
Configuration lattice  →  Grade lattice  →  Monad morphism preorder
(S x P(Tool))             (W x D)            (M, <=_ma)
Harness's control          Actor's path        Interface effect type
What Harness gives         What actor IS       What others see
```

Configuration bounds grade (Prop. 5.3). Grade bounds interface ma (Prop. 4.8, direction). The scope lattice is the first component of the configuration lattice — a projection, not a separate ordering.

**Proposition 5.5 (Harness as grade reduction).** A Harness operation `H` applied to actor `B`:

```
grade(H(B)) <= grade(B)   componentwise
```

Sandboxing reduces `w`. Tool restriction reduces effective `w` and `d`. The Harness is a grade-reducing functor.

---

## 6. The Monad Morphism Preorder

The preorder formalizes *who can reason about whom*. Blog post 5 develops this as "predictability as embeddability."

### 6.1 The ordering

**Definition 6.1 (Monad morphism).** A monad morphism `eta : M ~> N` is a natural transformation preserving monad structure:

```
eta . return_M = return_N
eta . join_M = join_N . eta . fmap(eta)
```

**Definition 6.2 (Ma preorder).** Define:

```
M <=_ma N  iff  exists eta : M ~> N
```

The existence of `eta` means every `M`-computation embeds in `N`. `N` can simulate everything `M` can do.

Standard embeddings along the gradient:

```
Identity <= Maybe <= Either E <= List <= Writer W <= State S <= IO
```

### 6.2 Actor ordering

The four actors map to positions on this preorder:

```
Either E  <=  StateT Conv_State IO  <=  Response  <=  IO
Executor      Harness                   Inferencer     Principal
```

**Proposition 6.3 (Trust and opacity).** If `M <=_ma N`, then:
- `N` can embed all `M`-computations (trust flows down)
- `M` cannot in general embed `N`-computations (opacity flows up)

The star topology falls out: the Harness sits low in the preorder, so all actors can model it.

**Convention 6.4 (Bare vs agentic Inferencer).** A bare Inferencer (no tools) inhabits `(sealed, trained)` — a 3-actor system where the Principal controls all world interaction. An agentic Inferencer (with tools) inhabits `(sealed-broad, trained)` — a 4-actor system where the Harness mediates tool access. The distinction is in the configuration, not the weights (blog post 5).

### 6.3 Interface boundary

**Proposition 6.5 (Interface boundary for characterized actors).** For actors whose implementation monad `M_impl` is well-defined (Harness, Executor, sub-agents), the interface boundary is a monad morphism:

```
eta_A : M_impl ~> M_iface
```

For the Harness: `StateT Conv_State IO ~> HarnessAction`. For Executors: `IO_W ~> Either E Result`. The morphism is surjective (every interface output reachable) and lossy (many internal states map to the same output).

**Convention 6.6 (Interface boundary for opaque actors).** For the Inferencer and Principal, we model the boundary *as if* it were a monad morphism, with `M_impl` approximating internal complexity. This is a modeling convention — it enables uniform reasoning at the cost of treating internals as a black box. The useful properties (surjective, lossy) hold regardless. What we lose is the guarantee that composition is preserved.

### 6.4 Three conditions for prediction

**Proposition 6.7 (Conditions for prediction).** Actor `N` can predict actor `M`'s behavior iff:

1. **Structural embeddability**: a monad morphism `eta : M ~> N` exists
2. **Parametric accessibility**: `N` has access to `M`'s specific parameters (configuration, scope, tool set)
3. **Computational tractability**: simulating `M` is cheaper than running `M`

All three are required. The Harness can predict the Executor (all three hold: `Either E` embeds in `StateT Conv_State IO`, the Harness knows the tool's args, and simulation is trivial). The Harness cannot predict the Inferencer (condition 1 holds via Convention 6.6, but condition 3 fails — simulation requires the weights).

**Remark (Regulation does not require prediction).** The Harness does not need to predict the Inferencer. It needs to *handle* whatever the Inferencer proposes (blog post 4). The handler pattern-matches on the effect signature, not on the implementation. This is the algebraic effects insight formalized in section 7.

---

## 7. Algebraic Effects and Handler Structure

The Harness handles effects raised by other actors. Blog post 4 develops this as "raising and handling."

### 7.1 Raising and handling

**Definition 7.1 (Raising).** Actors raise effects: appending to the log, proposing tool calls, producing output. Raising is monotone — the log grows, budget decreases, scopes widen within a phase. The graded monad `Conv_s` (Def. 2.5) captures it.

**Definition 7.2 (Handling).** The Harness handles raised effects: interpreting tool calls, gating permissions, compacting, reconfiguring scope and tools. Handling may violate monotonicity — compaction breaks prefix ordering, budget reclamation reverses the budget trajectory, scope can be reconfigured between phases.

The monotonicity boundary is between raising and handling, not between two "levels." A handling operation transforms the *parameters* of the raising monad. After compaction, `Conv_s` still applies — but over a different log and budget.

### 7.2 Effect signatures

**Definition 7.3 (Effect signature).** Each actor role has a characteristic effect signature — what the handler receives at the boundary:

| Actor | Effect signature | What handler receives |
|---|---|---|
| **Executor** | World interaction | `Either E Result` |
| **Inferencer** | Text + tool proposals | `Response = TextBlock[] + ToolCall[]` |
| **Principal** | Intent + authorization | `MultimodalMessage` |
| **Harness** | State management + IO | `HarnessAction` (raises in outer `IO`) |

The handler receives the interface type, not the implementation effects. The Inferencer's internal attention/sampling is opaque; the handler gets one structured `Response`.

### 7.3 Handler pattern matching

**Definition 7.4 (Permission gates as handler cases).** The Harness handles tool call effects by pattern matching on the permission configuration:

```
handle : ToolCall → PermissionMode → HandlerAction

handle(call, AutoAllow) = dispatch(call)
handle(call, Ask)       = escalate(call, Principal)
handle(call, AutoDeny)  = deny(call, reason)
```

This is algebraic effect handling (Plotkin & Pretnar 2009): the effect (tool call proposal) is raised by the Inferencer, and the handler (Harness) interprets it according to specified rules. The handler's decision surface is `specified` — you can read its rules and predict its behavior.

**Remark (Context reconstruction).** The Inferencer is not suspended while the handler executes (unlike algebraic effects in PL, where the continuation is captured). The Harness simulates continuation by reconstructing context — each "continuation" is a fresh inference call with an augmented input (blog post 4). The observable behavior matches a continuous computation with effects, but the mechanism is reconstruction, not resumption.

**Gap.** The mapping to algebraic effects is structural, not exact. Standard algebraic effects have continuation capture; the conversation architecture has context reconstruction. Whether a formal correspondence exists (perhaps via a CPS transform that relates reconstruction to continuation) is open. The connection to Plotkin & Pretnar (2009) imports intuition but not proofs.

---

## 8. The Fold Model and Conversation Dynamics

Conversations are not growing computations — they are sequences of stateless computations over managed state. Blog post 6 develops this; posts 7-8 develop the consequences.

### 8.1 Conversations as folds

**Definition 8.1 (Conversation fold).** A conversation is:

```
Conv_State_0 -[extract]-> view_0 -[infer]-> response_0 -[inject]-> Conv_State_1
Conv_State_1 -[H]-> Conv_State_1' -[extract]-> view_1 -[infer]-> response_1 -[inject]-> Conv_State_2
...
```

Each arrow through the Inferencer is a pure function of its input. The state lives in `Conv_State`, managed by the Harness. The `[H]` step is where the Harness reshapes the substrate — adding tools, compacting history, reconfiguring scope — before the next extraction.

**Proposition 8.2.** The Inferencer's grade is a constant: `(sealed, trained)`. Its weights are fixed, its architecture is fixed, it reads only its token window. The *compound* grade varies per turn because the Harness varies the configuration. The Inferencer's role is stable across the conversation because its ma is stable.

**Proposition 8.3 (Composite entity type).** The composite entity — what the Principal sees as a persistent conversational agent — has type `StateT Conv_State IO`. This is the Harness's own type. The Inferencer is the step function invoked and discarded each turn; the Harness is the persistent identity.

### 8.2 Reachable vs total decision surface

**Definition 8.4 (d_total and d_reachable).**

```
d_total     = const                      -- the weights (fixed)
d_reachable = f(d_total, |context|)      -- monotone in context length
```

`d_total` is the full path space of the weights — the grade component, constant across the conversation. `d_reachable` is the portion of that path space the current input can activate. It grows with context length because the attention mechanism creates an interaction graph whose size depends on input length (`O(n^2)` pairwise interactions per layer per head).

The Harness controls context length (scope construction, compaction), which controls `d_reachable`. Compaction reduces both world coupling (discards accumulated data) and `d_reachable` (shorter context, fewer interactions). Context management is the single most leveraged Harness operation because it simultaneously controls both axes.

### 8.3 The coupled recurrence

**Definition 8.5 (Grade trajectory).** At turn `n`, the composite has effective grade `g(n) = (w(n), d_reachable(n))`. The trajectory over a conversation:

```
gamma(C) = (g(0), g(1), ..., g(n))
```

**Proposition 8.6 (Coupled recurrence).** The grade evolves:

```
g(n+1) = F(g(n), config(n))

w(n+1)           = W(w(n), d_reachable(n), config(n))
d_reachable(n+1) = D(w(n), d_reachable(n), config(n))
```

Both components at `n+1` depend on both components at `n`. World coupling depends on what tools were called (chosen by the decision surface) and what results came back (determined by world coupling). Reachable decision surface depends on context accumulation (determined by both).

**Proposition 8.7 (Harness as controller).** The Harness's role is controller for this dynamical system. It observes `g(n)` (to the extent it can — `w` is characterizable, `d_reachable` is not fully), applies `config(n)`, and keeps the trajectory within regulatory bounds.

| Harness action | Effect on w | Effect on d_reachable |
|---|---|---|
| Grant tool | Increases | Indirect (tool results grow context) |
| Revoke tool | Decreases | -- |
| Compaction | Decreases | Decreases |
| Scope restriction | -- | Decreases |
| Tool result injection | Increases | Increases |

**Proposition 8.8 (Conversation grade).** The overall grade is the supremum of per-turn grades:

```
g_conv = V_t g_turn(t)
```

This is what the Harness must regulate for.

**Conjecture 8.9 (Convergence conditions).** Under what conditions does the trajectory converge? With data-channel-only tools (section 9), the trajectory drifts upward gently and compaction resets it — convergent. With computation channels (section 9), the trajectory can self-amplify. Characterizing the boundary between convergent and divergent trajectories as a function of the tool set and sandbox configuration is open.

**Gap.** The recurrence `F` is stated but not given a type or constraints. The dynamical systems theory of grade trajectories — convergence, rate of inflation, stability — is the most important open problem in the framework.

---

## 9. Computation Channels and Trajectory Dynamics

Not all tools are data channels. Some are computation amplifiers. Blog post 7 develops the taxonomy; post 8 develops the regulatory consequences.

### 9.1 Data channels vs computation channels

**Definition 9.1 (Data channel).** A tool where the input is an address and the tool resolves it. `Read("/etc/hostname")`, `SQL SELECT`, `Glob("*.py")`. The agent selects from the world. The space of possible queries is characterizable given the interface.

**Definition 9.2 (Computation channel).** A tool where the input is a program and the tool executes it. `Bash("python -c '...'")`, `eval(code)`. The agent specifies a computation. The space of possible computations is bounded by the specification language's expressiveness — potentially Turing-complete.

### 9.2 The computation level as derivative

**Definition 9.3 (Computation level).** The computation level characterizes how fast the grade can change between steps — it is the derivative of the trajectory, not a third axis:

| Level | What it enables | dw | d(d_reachable) | Character |
|---|---|---|---|---|
| 0-2 | Observe (query, pure compute, read) | > 0 | ~ 0 | Data accumulation |
| 3 | Mutate (write within sandbox) | > 0 | ~ 0 | Path-dependent |
| 4 | Amplify (generate executable specs) | > 0 | > 0 via w | Self-amplifying |
| 5 | Extend (modify execution environment) | > 0 | >> 0 via w | Ceiling-raising |
| 6-8 | Reshape (persistent processes, capability creation, controller modification) | d(system) | d(system) | Lattice-reshaping |

### 9.3 Phase transitions

**Definition 9.4 (Phase transitions).** Three level boundaries are qualitative shifts:

1. **Mutation (2 to 3)**: The world becomes writable. The trajectory becomes path-dependent — what the agent did changes what future observations return.

2. **Amplification (3 to 4)**: The agent generates tokens interpreted as executable specifications. The composite's effective reach extends beyond the weights. The trajectory can self-amplify. This is the most architecturally consequential boundary.

3. **Escape from fold (5 to 6)**: Persistent processes have their own lifetime, state, and behavior — invisible to the Harness. The star topology breaks. The fold model (section 8) becomes an approximation.

### 9.4 The sandbox as dynamics controller

**Proposition 9.5 (Sandbox controls dynamics).** The sandbox determines which phase transitions are reachable. A tool set including `Bash` with full sandbox access operates at levels 0-8. The same `Bash` with read-only, network-isolated sandbox caps at level 2. Same tool, radically different dynamics.

This is supermodularity (Conj. 4.5) applied to sandbox configuration: restricting the sandbox of a computation-channel tool does not just reduce world coupling — it eliminates phase transitions. A qualitative shift in what kind of regulatory problem the Harness faces.

### 9.5 Regulation at level 4+

**Conjecture 9.6 (Halting-problem shape of regulation).** At computation level 4, the Harness can inspect each command and apply specified rules (approve `cat`, deny `rm -rf`, escalate `pip install`). For simple commands this works. But the general question — "what will this program do?" — has the shape of the halting problem. Each individual invocation is regulatable; the space of things to check is not enumerable. Across multiple calls, the problem compounds: the cost of regulation grows with the product of specification complexity and accumulated world state.

**Gap.** This conjecture links the computation channel taxonomy to computability theory. A formal characterization — perhaps via the expressiveness of the specification language — would give precise phase transition boundaries. Currently descriptive, not algebraic.

---

## 10. The Specified Band

The Harness can stay characterizable at any scale of world coupling, provided its decision surface stays transparent. Blog post 8 develops this with the OS as existence proof.

### 10.1 The band

**Definition 10.1 (The specified band).** The region of the grade lattice where `d = specified`:

```
{(w, specified) : w in W}
```

Every actor in this band — regardless of world coupling — has a transparent decision surface. Its behavior can be understood by reading its rules.

**Proposition 10.2 (Characterizability vs auditability).** Characterizability is qualitative: is the decision surface specified at all, or opaque? Auditability is quantitative: how much specified logic must you read? An OS kernel at `(open, specified)` is as characterizable *in kind* as a simple Harness at `(scoped, specified)`. The kernel is harder to audit (more rules) but not harder to characterize (still transparent).

**Proposition 10.3 (World coupling growth in the specified band).** For actors in the specified band, characterization difficulty scales with the *size* of the specification — more rules, more state to track — not exponentially with world coupling. The supermodular cross-term (Conj. 4.5) does not activate because the decision surface is transparent.

### 10.2 Layered regulation

**Definition 10.4 (Three regulatory layers).** The OS pattern, adapted for conversation architecture:

1. **Constraint** (Layer 1): Bounds what is *possible*. Sandbox, `allowed_directories`, network isolation. Does not observe or decide — limits. Effective ma near 0.

2. **Observation** (Layer 2): Reports what *happened*. Tool inputs/outputs, `Conv_State` tracking. Produces data for the policy layer. Specified — reports facts, not judgments.

3. **Policy** (Layer 3): Applies specified rules to observed state. Permission configuration, compaction thresholds, budget management. Decides with transparent rules over vast observed state.

**Proposition 10.5.** Each layer stays in the specified band independently. The composition of three specified layers is still specified.

### 10.3 The Ashby resolution

**Proposition 10.6 (Variety reduction, not matching).** The naive reading of Ashby's Law of Requisite Variety: as the agent gets more capable, the Harness must match its variety. This leads to the Ashby trap — the regulator becomes as complex as the regulated system.

The framework's resolution:

1. **Co-domain funnels** (Def. 4.7) are variety attenuators — they reduce the agent's effective variety
2. **Observation growth** stays in the specified band — more world coupling, same decision surface
3. **Capability publishing** shifts the variety burden to the regulated system — tools declare effect signatures, the Harness evaluates declarations with specified rules
4. **The sandbox** bounds variety regardless of what the Harness observes — a constraint, not a controller

At no point does the Harness need to leave the specified band. At no point does its decision surface need to grow.

### 10.4 Constraint projection

**Definition 10.7 (Transparent vs opaque specification).** A transparent specification has rules visible to the governed actor — the actor can model its own constraints. An opaque specification has rules that are specified but invisible to the governed actor.

**Proposition 10.8.** Both are characterizable by the administrator. But opaque constraints reduce the portion of the Inferencer's decision surface spent on proposals that could succeed, while keeping the total decision surface the same. The agent explores paths the policy will reject. Unnecessary opacity is a direct tax on system performance (blog post 8, SELinux coda).

**Design principle.** Minimize the gap between the full policy and its projection into the actor's scope.

---

## 11. Session Types for the Permission Protocol

The monadic framework handles data flow. The comonadic framework handles scope construction. Session types handle the *protocol* — who communicates what to whom, in what order, with what branching. Blog posts 1 and 4 describe the protocol informally.

### 11.1 The tool-use session type

**Definition 11.1 (Tool-use protocol).**

```
type ToolUse =
    Inferencer -> Harness   : Propose(tool, args)
  ; Harness    -> Harness   : CheckPermission(tool, args, mode)
  ; case mode of
      AutoAllow ->
          Harness  -> Executor  : Execute(args)
        ; Executor -> Harness   : Result(output)
        ; Harness  -> Inferencer: ToolResult(output)
      Ask ->
          Harness  -> Principal : PermissionRequest(tool, args)
        ; Principal -> Harness  : Grant | Deny
        ; case of
            Grant ->
                Harness  -> Executor  : Execute(args)
              ; Executor -> Harness   : Result(output)
              ; Harness  -> Inferencer: ToolResult(output)
            Deny ->
                Harness  -> Inferencer: PermissionDenied(tool, reason)
      AutoDeny ->
          Harness  -> Inferencer: PermissionDenied(tool, reason)
```

### 11.2 Structural properties

**Proposition 11.2.** The session type encodes:

- **Star topology**: Every arrow has the Harness on one end. No actor communicates directly with another.
- **Authorization as branching**: `Grant | Deny` determines which *continuation* the protocol follows — different message sequences, not just different values.
- **Selective participation**: The Principal's channel opens only in the `Ask` branch. In `AutoAllow` and `AutoDeny`, the Principal is never consulted — structural, not just behavioral.

**Proposition 11.3 (Co-domain management in the protocol).** Each branch has a co-domain effect:

| Branch | Co-domain effect |
|---|---|
| `AutoAllow -> Result` | Widens (Executor's IO_W injected) |
| `Ask -> Grant -> Result` | Widens (same, gated) |
| `Ask -> Deny` | Narrows (Executor's co-domain not injected) |
| `AutoDeny` | Narrows (same) |

The `Deny` branches are co-domain restriction operations — they prevent an Executor's `IO_W` from composing into the conversation. Permission configuration is the Harness's static co-domain management policy:

```
perm : ToolCall -> {AutoAllow, Ask, AutoDeny}
```

### 11.3 Parallel execution and non-determinism (open problem)

When the Inferencer proposes multiple tool calls, they execute concurrently. The pi-calculus gives the right formalism: concurrent processes with private channels and name restriction.

**Definition 11.4 (Parallel tool execution, sketch).**

```
(v r_1)(v r_2)...(v r_n)(
    tool_1<args_1, r_1> | tool_2<args_2, r_2> | ... | tool_n<args_n, r_n>
  | r_1(res_1).r_2(res_2)...r_n(res_n).harness<res_1, ..., res_n>
)
```

Private channels `(v r_i)` ensure tool independence. The barrier collects results sequentially; the Harness controls injection ordering.

**Conjecture 11.5 (Non-determinism without structural change).** Parallel execution adds a layer of non-determinism to the computation paths — the grade trajectory becomes a distribution over trajectories rather than a single path, depending on execution order and timing of concurrent tools. However, the framework's structure (grade lattice, preorder, fold model, coupled recurrence) does not change. The non-determinism is in the *realization* of each fold step, not in the fold structure itself.

**Gap.** Full pi-calculus formalization is deferred. The key question: does non-deterministic tool execution change the convergence properties of the grade trajectory (Conj. 8.9), or only the variance around a trajectory that converges/diverges for structural reasons? If the latter, the synchronous formalism is a sufficient abstraction for regulation, and the pi-calculus treatment is an extension rather than a correction.

### 11.4 Promises (sketch)

**Definition 11.6 (Conversation future).**

```
data Future A = Pending TaskHandle | Resolved A | Failed Error
```

Backgrounded tasks create `Pending` futures; the Harness decides when/whether/how to inject resolved results. This introduces scheduling agency — the promise is not a synchronization primitive but a Harness decision about when to trigger existing turn-boundary mechanisms.

**Conjecture 11.7 (Promise coherence).** The Harness maintains coherence by restricting promise injection to turn boundaries. If this holds, promises are a scheduling layer over the synchronous formalism — the formal structure of each turn is unchanged. If it does not hold, the interaction requires the distributive law (Conj. 3.6) or something stronger.

---

## 12. Open Problems and Extensions

Prioritized by novelty and testability.

### 12.1 Coupled recurrence convergence (high priority)

The grade trajectory `g(n+1) = F(g(n), config(n))` is stated (Prop. 8.6) but `F` is not characterized. Under what conditions does the trajectory converge, diverge, or cycle? How do computation channel levels (section 9) affect the stability boundary? What is the optimal compaction strategy for a given tool set? This is the most important open problem — it connects the static framework to operational predictions.

### 12.2 Computation channel formalization (high priority)

The nine-level taxonomy (Def. 9.3) is descriptive. A formal characterization — perhaps via the Chomsky hierarchy of the specification language each tool accepts, or via the expressiveness of the tool's input language — would give precise phase transition boundaries and connect to computability theory.

### 12.3 Supermodularity proof or counterexample (high priority)

Conjecture 4.5 is testable. Define `chi` precisely (perhaps as observer prediction error given partial information about grade components) and prove or disprove supermodularity. An empirical study measuring prediction difficulty as axes vary could provide evidence.

### 12.4 Parallel execution in pi-calculus (medium priority)

Full treatment of concurrent tool execution with private channels. Does non-determinism change the convergence properties of the trajectory, or only variance? Formalize the connection between pi-calculus name restriction and the scope lattice.

### 12.5 The Writer-Store distributive law (medium priority)

Conjecture 3.6. Would give compositional structure to the turn (extraction composed with injection) rather than describing the pattern.

### 12.6 The algebraic effects correspondence (medium priority)

The mapping from conversation handling to algebraic effect handling (section 7) is structural. Formalize whether context reconstruction corresponds to continuation capture via a CPS transform. Import composition laws from Plotkin & Pretnar (2009), Kammar et al. (2013).

### 12.7 Compaction as abstract interpretation (medium priority)

Is lossy compaction a Galois connection between detailed and summarized conversation states? If `compact(A . B) != compact(A) . compact(B)`, compaction is not a monoid homomorphism. Abstract interpretation (Cousot & Cousot 1977) provides the right framework for lossy, non-compositional approximation.

### 12.8 Promises and interleaving semantics (lower priority)

The log may need partial ordering rather than total ordering when promises inject asynchronously. Budget accounting for outstanding futures. The free monad connection (is the promise set a free monad with `inject` as interpreter?).

### 12.9 Memory as cross-conversation state (lower priority)

The `Mem(A) = MemStore -> A x MemStore` monad outlives the conversation monad — an inverted transformer stack where the persistent outer monad has longer lifetime than the ephemeral inner monad. The interaction pattern may be a monad morphism between conversation and persistence monads.

### 12.10 Mechanical verification (aspirational)

None of this has been verified in Agda, Lean, or Coq. The monad/comonad definitions, Kleisli structure, and session types are the most amenable to mechanization. The grade lattice and coupled recurrence would require more novel encoding.

---

## References

- Ashby, W. R. (1956). *An Introduction to Cybernetics*. Chapman & Hall.
- Atkey, R. (2009). Parameterised notions of computation. *JFP*, 19(3-4).
- Atkey, R. (2018). Syntax and semantics of quantitative type theory. *LICS*.
- Bauer, A. (2018). What is algebraic about algebraic effects and handlers? *arXiv:1807.05923*.
- Brookes, S., & Geva, S. (1992). Computational comonads and intensional semantics. *Applications of Categories in Computer Science*, LMS Lecture Notes 177.
- Conant, R. C., & Ashby, W. R. (1970). Every good regulator of a system must be a model of that system. *IJSS*, 1(2).
- Cousot, P., & Cousot, R. (1977). Abstract interpretation: A unified lattice model for static analysis of programs. *POPL*.
- Fowler, M. (2025). Harness engineering. *martinfowler.com*.
- Honda, K. (1993). Types for dyadic interaction. *CONCUR*.
- Honda, K., Yoshida, N., & Carbone, M. (2008). Multiparty asynchronous session types. *POPL*.
- Kammar, O., Lindley, S., & Oury, N. (2013). Handlers in action. *ICFP*.
- Katsumata, S. (2014). Parametric effect monads and semantics of effect systems. *POPL*.
- McBride, C. (2016). I got plenty o' nuttin'. *A List of Successes*, LNCS 9600.
- Miller, M. S. (2006). *Robust Composition*. PhD thesis, Johns Hopkins University.
- Milner, R. (1999). *Communicating and Mobile Systems: The Pi-Calculus*. Cambridge University Press.
- Moggi, E. (1991). Notions of computation and monads. *Information and Computation*, 93(1).
- Montufar, G. F., Pascanu, R., Cho, K., & Bengio, Y. (2014). On the number of linear regions of deep neural networks. *NeurIPS*.
- Orchard, D., Wadler, P., & Eades, H. (2019). Unifying graded and parameterised monads. *arXiv:1907.10276*.
- Plotkin, G., & Power, J. (2003). Algebraic operations and generic effects. *Applied Categorical Structures*, 11(1).
- Plotkin, G., & Pretnar, M. (2009). Handlers of algebraic effects. *ESOP*.
- Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proc. IEEE*, 63(9).
- Uustalu, T., & Vene, V. (2008). Comonadic notions of computation. *ENTCS*, 203(5).
- Zhang, H., & Wang, M. (2025). Monadic context engineering for LLM agents. *arXiv:2512.22431*.
