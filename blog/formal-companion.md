# Formal Companion

*Definitions, propositions, conjectures, and open problems for the framework developed in [The Ma of Multi-Agent Systems](00-intro.md).*

This document formalizes the structural claims from the blog series. It assumes the reader has the blog for motivation, examples, and design intuitions. It follows mathematical dependency order, not the blog's narrative order. Cross-references to specific posts are given where the informal treatment lives. Worked examples applying the formalism to concrete systems are in the [case studies](case-studies.md).

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

**Definition 4.5 (Effective input dimensionality and path count).** For an actor with grade `(w, d)`:

- `I(w)` is the number of distinguishable world states that can influence the computation at world coupling level `w`. Monotone non-negative: `w_1 <= w_2 ==> I(w_1) <= I(w_2)`.
- `P(d)` is the number of distinguishable execution paths at decision surface level `d`. Monotone non-negative: `d_1 <= d_2 ==> P(d_1) <= P(d_2)`.

These are the scalar projections of the lattice levels onto measurable quantities. `I(sealed) = 1` (only explicit input). `P(literal) = 1` (one path). `I(open)` and `P(trained)` are large.

**Definition 4.6 (Characterization difficulty).** Under the **independence model** — each of `I(w)` distinguishable inputs can independently steer the computation through any of `P(d)` paths — the number of distinguishable input-output behaviors is `P(d)^I(w)`. The characterization difficulty is:

```
chi(w, d) = I(w) . log P(d)
```

This is the log of the number of distinguishable behaviors: how many bits an observer needs to identify which function the system implements, out of all functions its architecture could implement.

**Proposition 4.7 (Supermodularity).** `chi(w, d) = I(w) . log P(d)` is supermodular on `W x D`.

*Proof.* For `w_1 <= w_2` and `d_1 > d_2` (the incomparable case — comparable cases give equality):

```
chi(w_2, d_1) + chi(w_1, d_2) - chi(w_1, d_1) - chi(w_2, d_2)
  = (I(w_2) - I(w_1)) . (log P(d_1) - log P(d_2))
  >= 0
```

Both factors are non-negative by monotonicity of `I` and `P`. QED

**Corollary 4.8 (Marginal returns of restriction).**

Reducing world coupling from `w_2` to `w_1` saves:

```
delta_chi = (I(w_2) - I(w_1)) . log P(d)
```

Proportional to `log P(d)` — sandboxing saves more when the decision surface is large.

Reducing decision surface from `d_2` to `d_1` saves:

```
delta_chi = I(w) . (log P(d_2) - log P(d_1))
```

Proportional to `I(w)` — tool restriction saves more when world coupling is broad.

**Corollary 4.9 (The specified band).** When `d = specified`, `log P(specified)` is small (bounded by the log of the rule count). So `chi(w, specified) = I(w) . (small constant)`. Characterization difficulty grows linearly with world coupling, not superlinearly. This is the formal content of Proposition 10.3: the cross-term does not activate in the specified band because one factor is small.

**Remark (The independence assumption).** The proof assumes independent path selection — each input can steer the computation through any path regardless of other inputs. This is the maximum-capacity model, giving an upper bound on actual characterization difficulty.

In practice, paths are correlated: many inputs activate the same path (especially for small decision surfaces). Correlation reduces `chi` below the product bound. But correlation is itself monotone in `d` — smaller decision surface means more correlation (fewer paths, more inputs sharing each). Relaxing independence to correlated path selection reduces `chi` overall while preserving supermodularity, because the correlation discount is larger at low `d` (where supermodularity already gives low values) than at high `d`.

The independence model is generous but not unrealistic for trained systems: a deep network's piecewise-linear regions partition the input space into cells that independently determine the computation path. The number of cells (Montufar et al. 2014) grows exponentially with depth, and each cell's path is determined by which ReLUs are active — genuinely independent steering per input region.

**Remark (Design functions over chi).** The framework tells you that restriction reduces `chi`, and that the reduction is superlinear. It does not tell you *how much* restriction is optimal — because that depends on what you're trading `chi` against. Practical system design requires functions over the components:

- *Regulatory cost* `R(chi)`: how much effort the Harness must expend to maintain characterizability. Monotone in `chi`.
- *Capability value* `V(I(w), P(d))`: the usefulness of the computation to the Principal. Also monotone — more world access and more paths generally mean more capable systems.
- *Risk exposure* `rho(chi, level)`: potential harm if regulation fails, depending on `chi` and the computation channel level (section 9). A level-4 system with high `chi` has qualitatively different risk than a level-0 system with the same `chi`.
- *Operational cost* `C(I(w))`: budget consumed, proportional to context length, which is a proxy for `I(w)`.

The optimal operating point minimizes something like `R(chi) + rho(chi, level) - V(I(w), P(d))` subject to `C(I(w)) <= budget`. The supermodularity of `chi` means restriction has convex returns in this optimization — small restrictions at high grade save disproportionately more than the same restrictions at low grade. Formalizing this optimization is future work (section 12).

### 4.4 Interface ma vs internal ma

**Definition 4.10 (Interface ma and internal ma).**

```
ma_internal(A) = grade(A)                         -- the actor's path space
ma_interface(A) = characterizability of M_iface    -- what others see
```

These are independent (blog post 2, post 5):

| Configuration | Internal ma | Interface ma | Example |
|---|---|---|---|
| Large model, restricted tools | High | Low | Opus as reviewer (Approve/Reject/RequestChanges) |
| Small model, many tools | Low | High | Haiku with 50 tools |
| Large model, unrestricted | High | High | Unconstrained Inferencer |
| Deterministic rules, narrow output | Low | Low | Static tool whitelist |

Internal ma determines decision quality. Interface ma determines auditability.

### 4.5 Co-domain funnels

**Definition 4.11 (Co-domain funnel).** A co-domain funnel is an actor where `ma_internal >> ma_interface` — the implementation is strictly richer than the interface. The funnel compresses high internal ma through a constrained output type.

Examples: an Opus reviewer with `{Approve, Reject, RequestChanges}`, a sub-agent whose full conversation compresses to `Either(Result, Error)`, an explorer that compresses broad codebase reading into structured findings.

**Proposition 4.12 (Funnels as monad morphisms).** For actors with well-defined implementation monads, the funnel is a monad morphism `eta : M_impl ~> M_iface` that is surjective on the co-domain (every output is reachable) and lossy (many internal states map to the same output). See section 6.3.

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

Configuration bounds grade (Prop. 5.3). Grade bounds interface ma (Prop. 4.12, direction). The scope lattice is the first component of the configuration lattice — a projection, not a separate ordering.

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

### 8.4 Characterization of F

The recurrence `F` was stated (Prop. 8.6) without constraints. We can now characterize it using the Chomsky hierarchy and the effect lattice. (The tool grade formalized in section 9 grounds these informally here; the key distinction — data channels accept addresses, computation channels accept programs — suffices for the claims below.)

**Definition 8.9 (Informational and effectual delta).** At each turn, a tool call produces two distinct changes:

```
delta_w_info(n)   -- tokens injected into context (observable by Harness)
delta_w_effect(n) -- changes to the world that affect future turns (may be opaque)
```

For data-channel tools (`chomsky <= CF`): these are approximately equal. A Read call's response IS the information. A query's result IS what was found. The Harness sees what the tool did.

For computation-channel tools (`chomsky = RE`): these decouple. An agent can execute a program that modifies 100 files, installs packages, or opens network connections, and receive a one-token response (`0`, `OK`, `True`). The context grows by a few tokens. The world changes profoundly. Every future Read call may return different content.

```
RE tool example:
  delta_w_info   = |"exit code 0"| = 3 tokens
  delta_w_effect = |modified filesystem| = unbounded
```

The Harness, observing only `delta_w_info`, sees a gentle trajectory. The actual trajectory — determined by `delta_w_effect` — may be explosive. This decoupling is the formal content of why observation (post 8, layer 2) is insufficient for RE tools: the Harness needs constraint (layer 1, the sandbox) because it cannot see the effects through the context alone.

**Proposition 8.10 (Trajectory characterization).** The recurrence has the form:

```
w_actual(n+1) = min(w_actual(n) + delta_w_info(n), T)
w_world(n+1) = w_world(n) + delta_w_effect(n)
d_reachable(n+1) = f(d_total, |context(n+1)|)
```

The Harness observes `(w_actual(n), d_reachable(n))`. But future behavior depends on `(w_world(n), d_reachable(n))`, because `w_world` determines what future tool calls will return.

For data-channel tools, `w_world(n) ~ w_actual(n)` (the tool's response IS the effect). For sandboxed RE tools, `w_world(n) <= W_sandbox` (the sandbox bounds world changes regardless of what the agent executes). For unsandboxed RE tools, `w_world` is bounded only by `W_config` -- and can exceed it if the configuration invariant breaks (Prop. 9.7).

**Proposition 8.11 (Universal boundedness).** The token window bounds the trajectory absolutely:

- `w_actual(n) <= T` (context cannot exceed window)
- `d_reachable(n) <= d_total` (cannot activate more paths than weights contain)
- Number of turns `N <= T / c_min` (each turn costs at least `c_min` tokens)
- The trajectory has finite length and a limit point `g* <= (T, d_total)`

All trajectories converge. The framework's dynamic claims are about RATES within finite bounds, not about infinity.

**Definition 8.12 (Regulatory convergence).** Let `R(n)` be the Harness's per-turn regulatory cost at turn n -- the computational effort required to evaluate all specified rules against the observed state `(w_actual(n), d_reachable(n))` and the proposed actions. The system is *regulatorily convergent* if `R(n)` is bounded for all n. It is *regulatorily divergent* if `R(n)` grows faster than the Harness can process -- the system evolves faster than it can be characterized.

**Proposition 8.13 (Regulatory convergence criteria).** The Chomsky level of the tool set determines regulatory convergence:

| Tool class | `delta_w_info` | `delta_w_effect` | Decoupled? | R(n) | Convergence |
|---|---|---|---|---|---|
| CF (data channel) | O(C) | ~ delta_w_info | No | Decidable, O(1) | Regulatorily convergent |
| RE (computation) | O(small) | O(unbounded) | **Yes** | Undecidable (Rice's) | Regulatorily divergent |
| RE + sandbox | O(small) | O(bounded by sandbox) | Partially | Decidable within sandbox | Convergent if sandbox is tight |
| Multi-agent, unstructured | O(T_B . log P(d_B)) | Coupled to B's effects | Yes | Undecidable (emergent RE) | Divergent without funnels |
| Multi-agent, structured | O(log K) | Bounded by schema | No | Decidable | Convergent |

**Corollary 8.14 (The decoupling is the danger).** The most dangerous configuration is a computation-channel tool with small responses and large effects: the observed trajectory `(w_actual(n))` grows gently while the world trajectory `(w_world(n))` diverges. The Harness's regulatory model, based on context observation, systematically underestimates the system's grade. The sandbox is essential because it constrains `delta_w_effect` directly — the only mechanism operating on the world trajectory rather than the context trajectory.

**Remark (Multi-agent info/effect decoupling).** The decoupling compounds in multi-agent systems. When agents A and B share a filesystem, B's computation-channel effects (writing files) become A's future data-channel inputs (reading files). B's `delta_w_effect` is invisible to A's Harness until A reads the modified files — at which point it appears as ordinary `delta_w_info`. The world trajectory diverges from what either Harness individually observes. This is the multi-agent analogue of Cor. 8.14: the danger is not in any single agent's trajectory but in the gap between agents' world models.

**Corollary 8.15 (Restatement of the specified band for dynamics).** The Harness achieves regulatory convergence when:

1. All tool input languages are decidable (`chomsky <= CF`), OR
2. RE tools are sandboxed such that `delta_w_effect` is bounded, OR
3. Inter-agent communication is structured such that delegation channels are CF, not RE

Each condition ensures that the Harness's per-turn regulatory cost is bounded — that specified processing can keep pace with the system's evolution. The convergence boundary is the Chomsky boundary (CF vs RE), modulated by the sandbox and communication structure.

### 8.5 Multi-agent coupling

**Definition 8.16 (Communication channel cardinality).** When agent A delegates to agent B through the Harness, the *communication channel cardinality* `kappa` is the number of distinguishable messages B can return per round:

- For a structured channel (schema with K configurations): `kappa = K`
- For an unstructured channel (arbitrary text): `kappa = P(d_B)^(T_B / c_B)`, where `T_B` is B's context window size and `c_B` is B's average tokens per turn

The unstructured cardinality reflects B's full computation capacity: B makes `T_B / c_B` decisions, each with `P(d_B)` distinguishable paths.

**Proposition 8.17 (Multi-agent characterization difficulty).** For a single agent A working over `N = T_A / c` turns:

```
chi_single = (T_A / c) . log P(d_A)
```

Linear in the token window `T_A`.

For agent A delegating to agent B over K rounds, where B works internally for `M = T_B / c_B` turns per round:

```
chi_two = (T_A / c_A) . (log P(d_A) + (T_B / c_B) . log P(d_B))
        = chi_A_solo + (T_A . T_B) / (c_A . c_B) . log P(d_B)
```

The amplification term is proportional to the **product** of the two context windows.

*Proof.* Over K rounds, A makes K decisions (each from `P(d_A)` paths). Each round, B makes M decisions internally (each from `P(d_B)` paths). Under the independence model (Def. 4.6) -- each decision independently selects from the available paths -- the total distinguishable K-round histories is `(P(d_A) . P(d_B)^M)^K`. Taking logs: `K . (log P(d_A) + M . log P(d_B))`. Substituting `K = T_A / c_A` and `M = T_B / c_B` gives the result.

**Remark.** The independence assumption is stronger here than in the single-agent case: it assumes B's M per-round decisions are independent of A's steering across rounds. In practice, A's instructions constrain B's path space, so the bound is generous. But the qualitative result -- product-of-windows growth -- holds under weaker assumptions; correlation reduces the constant but not the polynomial degree. QED

**Corollary 8.18 (Quadratic growth).** A single agent with token window `2T` has `chi ~ 2T . log P(d)`. Two agents with windows `T` each have `chi ~ T^2 . log P(d)`. The second agent changes the growth rate from linear to quadratic in total token budget. For N agents in a pipeline:

```
chi_pipeline ~ (T_1 . T_2 . ... . T_N) / (c_1 . ... . c_N) . log P(d_last)
```

Polynomial of degree N in total budget. Still finite (token windows bound everything), but the degree grows with agent count.

**Corollary 8.19 (Funnel decoupling).** A co-domain funnel with schema cardinality K at the A-B boundary replaces the amplification term:

```
(T_A . T_B) / (c_A . c_B) . log P(d_B)  -->  (T_A / c_A) . log K
```

The funnel decouples A's characterization difficulty from B's context window entirely. Growth returns to linear. This is the formal content of the design rule "co-domain funnels at every boundary" (blog post 9).

**Remark (Token windows as the universal bound).** All quantities above are finite because token windows are finite. The framework's dynamic claims — convergence, divergence, amplification — are about growth rates within these bounds, not about infinity. A "divergent" trajectory is one that reaches the bound quickly; a "convergent" one reaches it slowly or not at all. The practical question is whether the system exhausts its regulatory budget before the token window is consumed.

---

## 9. Computation Channels and Trajectory Dynamics

Not all tools are data channels. Some are computation amplifiers. Blog post 7 develops the taxonomy; post 8 develops the regulatory consequences. This section grounds both in the Chomsky hierarchy and the effect lattice, connecting them to the grade lattice (section 4) and the coupled recurrence (section 8).

### 9.1 The tool grade

**Definition 9.1 (Tool grade).** The grade of a tool `t` decomposes into two well-studied hierarchies:

```
grade(t) = (effects(t), chomsky(input_lang(t)))
```

The **effect signature** `effects(t)` is the set of side effects the tool can perform, drawn from a lattice:

```
Pure < FileRead < FileWrite < Network < ProcessSpawn < ArbitrarySyscalls
```

This is the W axis (world coupling) applied to tools -- grounded in the capability/effect systems literature (Moggi 1991, Plotkin & Power 2003, Koka's effect rows).

The **input language class** `chomsky(input_lang(t))` is the Chomsky hierarchy level of the language the tool accepts as input:

```
Regular (Type 3) < Context-free (Type 2) < Context-sensitive (Type 1) < RE (Type 0)
```

This is the D axis (decision surface) applied to tools -- grounded in LangSec (Bratus, Patterson, Sassaman 2011): every tool that accepts input is implicitly an interpreter, and the input IS a program for that interpreter. The computation level is the Chomsky level of the input language.

**Proposition 9.2 (Tool grade instantiates the grade lattice).** For tools, the grade lattice `(w, d) in W x D` (Def. 4.1) receives formal content from two well-studied hierarchies:

| Grade axis | Tool instantiation | Formal foundation |
|---|---|---|
| W (world coupling) | Effect signature | Moggi (1991), capability types (Miller 2006) |
| D (decision surface) | Chomsky level of input language | LangSec (Bratus et al. 2011), Felleisen (1991) |

The nine-level taxonomy from blog post 7 is a linearization of this product. The coarse lattice (post 2) and the fine taxonomy (post 7) are the same structure at different resolutions.

**Remark (Scope of the instantiation).** This grounding applies to tools, where both axes have formal content. For actors in general, the D axis (decision surface) does not reduce to Chomsky level -- a trained neural network's decision surface is not a formal language class. The grade lattice (Def. 4.1) is the general structure; the Chomsky x Effects instantiation is the tool-specific refinement that enables the decidability results below.

### 9.2 Data channels vs computation channels

**Definition 9.3 (Data channel).** A tool where `chomsky(input_lang(t)) <= CF`. The input is an address, a structured query, or a template. `Read("/etc/hostname")` (Regular), `SQL SELECT` (CF), `Glob("*.py")` (Regular). The space of possible inputs is characterizable: the Harness can enumerate or bound the set of valid queries.

**Definition 9.4 (Computation channel).** A tool where `chomsky(input_lang(t)) = RE`. The input is a program and the tool executes it. `Bash("python -c '...'")`, code execution tools. The agent specifies a computation. The space of possible computations is Turing-complete. By Rice's theorem, non-trivial semantic properties of the input programs are undecidable.

The data/computation channel distinction is the Chomsky boundary at CF vs RE. This is a qualitative shift in decidability, not just a quantitative increase in expressiveness.

### 9.3 The static/dynamic grade and the configuration invariant

**Definition 9.5 (Static and dynamic grade).** The grade has both static and dynamic forms, extending the `d_total` / `d_reachable` distinction (Def. 8.4) to both axes:

```
grade_config    = (W_config, d_total)           -- determined by Harness configuration
grade_actual(n) = (W_actual(n), d_reachable(n)) -- realized at turn n
```

where:

- `W_config` -- the set of world states the agent is ALLOWED to access (permissions, sandbox bounds)
- `W_actual(n)` -- the set of world states the agent HAS accessed (what's in the context window at turn n)
- `d_total` -- the full path space of the weights (constant)
- `d_reachable(n)` -- the activatable portion given current context (Def. 8.4)

For an inference agent, `W_actual` is exactly the context window. The agent cannot observe anything outside it. But it can request more via tool calls, converting `W_config` into `W_actual`.

**Definition 9.6 (Configuration invariant).** The *configuration invariant* holds when the dynamic grade stays bounded by the static grade:

```
grade_actual(n) <= grade_config    for all n
```

Equivalently: `W_actual(n) <= W_config` and `d_reachable(n) <= d_total`. The agent's realized capabilities never exceed its configured allowance.

**Proposition 9.7 (Chomsky level determines the invariant).** The configuration invariant is determined by `chomsky(input_lang(t))`:

| Chomsky level | Invariant | Reason |
|---|---|---|
| Regular, CF | Holds | Each tool call accesses a bounded slice of W_config. Cannot create new resources. |
| CS | Holds | Input can cross-reference within existing resources (e.g., SQL with correlated subqueries) but cannot create new resources or expand the accessible world. |
| RE | **Can break** | A single tool call can create files, install packages, open connections -- expanding W_reachable beyond W_config. |

This is the formal content of the level 3-to-4 phase transition: below RE, the configuration bounds the system. At RE, the agent can expand its own reachable world.

`chomsky(input_lang(t))` is the **conversion rate** from static to dynamic grade -- it determines how fast `W_actual` approaches `W_config`, and whether it can exceed it.

### 9.4 Phase transitions (grounded)

**Definition 9.8 (Phase transitions).** Three level boundaries are qualitative shifts, now grounded in the formal hierarchies:

1. **Mutation (2 to 3)**: Effect boundary -- `FileRead` to `FileWrite`. Same Chomsky class (CF). The trajectory becomes path-dependent (mutations change future reads), but the configuration invariant holds. Decidability is preserved.

2. **Amplification (3 to 4)**: **Chomsky boundary -- CF to RE.** The agent generates tokens interpreted as executable specifications. This is the LangSec boundary, the HRU boundary (Harrison, Ruzzo, Ullman 1976), and the Rice's theorem boundary. The configuration invariant can break. Decidability of characterization is lost. This is the most architecturally consequential transition because it is a shift in what KIND of regulatory problem the Harness faces.

3. **Escape from fold (6 to 7)**: Meta-effect boundary. Still RE input, but effects include spawning subprocesses with their own lifetime and state -- invisible to the Harness. The star topology breaks. The fold model (section 8) becomes an approximation.

### 9.5 The sandbox as invariant restorer

**Proposition 9.9 (Sandbox restores the configuration invariant).** The sandbox determines which phase transitions are reachable. For an RE-input tool (Bash), the sandbox restricts the effect signature: no network eliminates level 5, filesystem bounds cap level 3-4, resource limits (cgroups) bound computation time and space.

```
level_theoretical(Bash) = (ArbitrarySyscalls, RE)     -- grade: (open, RE)
level_sandboxed(Bash, S) = (FileWrite_bounded, RE)    -- grade: (scoped, RE)
```

The input language is still RE -- the agent can still write arbitrary programs. But the effect restriction ensures `W_reachable <= W_config` by preventing the effects that would expand it. The sandbox restores the configuration invariant without restricting the Chomsky level.

This is supermodularity (Prop. 4.7) applied to sandbox configuration: restricting the effect axis of an RE-input tool does not just reduce world coupling -- it eliminates phase transitions. A qualitative shift in what kind of regulatory problem the Harness faces.

**Remark (Connection to formal policy systems).** SELinux's Type Enforcement and cgroup resource controls are the OS instantiation of this pattern. SELinux restricts the effect axis via a finite type relation `(source_type, target_type, object_class, permission)` -- decidable by construction because the domain is finite. Cgroups restrict resource bounds -- connecting to bounded Turing machines and complexity classes (space-bounded TMs run in at most `2^O(s(n))` time). Together they narrow the gap between `level_sandboxed` and `level_theoretical`. The HRU result (1976) is the formal justification: the general safety problem for access matrices is undecidable, but for restricted models (mono-operational systems, finite type relations), safety IS decidable. SELinux's restricted policy language is a deliberate choice to stay in the decidable regime.

### 9.6 Regulation at level 4+

**Proposition 9.10 (Halting-problem shape of regulation).** At `chomsky = RE`, the Harness can inspect each command and apply specified rules (approve `cat`, deny `rm -rf`, escalate `pip install`). For simple commands this works -- the Harness performs pattern matching on the input string, which is decidable. But the general question -- "what will this program do?" -- is undecidable by Rice's theorem. Each individual invocation may be regulatable by syntactic inspection; the semantic question is not enumerable. Across multiple calls, the problem compounds: the cost of regulation grows with the product of specification complexity and accumulated world state.

**Remark (Decidable approximations).** Rice's theorem bars exact semantic analysis but permits sound approximation. Abstract interpretation (Cousot & Cousot 1977) provides the framework: map concrete semantics to abstract domains via Galois connections, trading precision for decidability. Type systems, effect systems, and model checking are all instances. The practical hierarchy: syntactic pattern matching (simplest, least precise) < type-based analysis < abstract interpretation < model checking (most precise, most expensive). Each is a decidable approximation of the undecidable semantic question. The Harness's rule-based permission system is the simplest level -- syntactic pattern matching on tool inputs.

### 9.7 Emergent computation channels

**Proposition 9.11 (Delegation as computation channel).** When agent A delegates to agent B via natural language, the delegation channel has the structure of a computation channel (Def. 9.4), regardless of B's individual tool set:

1. A sends a natural-language specification (the program)
2. B interprets and executes it using its tools over its context window (the execution)
3. B returns a result (the output)

The input language (natural language) is at least as expressive as any programming language. B's decision surface is `d_B = trained`. By Prop. 4.4, `grade(A using B) = (w_A V w_B, d_A V d_B) = (something, trained)`. The compound's decision surface is trained regardless of the individual tools' computation levels.

Two agents, each with data-channel-only tools (level 2-3), compose into a system with an emergent computation channel (level 4) at the delegation boundary. The computation channel arises from composition, not from any individual tool.

**Corollary 9.12 (Funnels prevent emergence).** A co-domain funnel at the A-B boundary constrains B's output to a structured schema. This projects B's effective decision surface at the interface from `trained` to `specified` (bounded by the schema). The delegation channel drops from level 4 back to level 2-3. The funnel prevents the computation channel from emerging.

### 9.8 The trust surface

**Definition 9.13 (Computation level trichotomy).** For a tool `t` used by agent `A` in sandbox `S`:

```
level_theoretical(t)       -- what the tool can compute (determined by tool)
level_sandboxed(t, S)      -- what the sandbox allows (determined by configuration)
level_effective(t, A)      -- what the agent actually does (determined by training)
```

These satisfy: `level_effective(t, A) <= level_sandboxed(t, S) <= level_theoretical(t)`.

**Definition 9.14 (Trust surface).** The *trust surface* is the gap:

```
trust_surface(t, A, S) = level_sandboxed(t, S) - level_effective(t, A)
```

Within this gap, regulation relies on the agent's training rather than specified constraints. A test runner (`pytest`) in a network-isolated sandbox has `level_theoretical = 4+`, `level_sandboxed ~ 3` (can write files, can't reach network), `level_effective ~ 2` (the agent writes tests, not exploits). The trust surface is the gap between 3 and 2.

**Example.** An agent writes Python tests and runs them via a test runner:

| Level | What determines it | Value |
|---|---|---|
| Theoretical | pytest executes arbitrary Python | 4+ |
| Sandboxed | No network, filesystem bounds, resource limits | ~3 |
| Effective | Agent's training: write tests, not programs | ~2 |
| Trust surface | Gap between sandboxed and effective | ~1 |

The sandbox eliminates levels 4+ (no network, no environment modification). Training keeps usage at level 2 (structured test patterns). The trust surface is the region where a sufficiently creative or misaligned agent could operate within the sandbox but outside intended use — writing tests that are actually programs.

**Proposition 9.15 (Specified band and the trust surface).** The specified band (section 10) says: regulate based on `level_sandboxed`, not `level_effective`. If you need level 2 dynamics, either use level 2 tools or sandbox level 4 tools down to level 2. Relying on `level_effective` puts trained judgment in the regulatory loop — the Harness's characterizability erodes.

A zero trust surface — `level_sandboxed = level_effective` — means the sandbox fully specifies the tool's behavior. This is achievable for data-channel tools (the tool's interface constrains it) but generally not for computation-channel tools (the sandbox constrains effects but not the computation itself).

**Gap.** The trust surface is defined informally. Formalizing it requires a metric on computation levels (not just an ordering) and a way to measure what "the agent actually does" without relying on the training distribution — which is the very trained judgment the specified band says to avoid. This circularity may be inherent for computation-channel tools, which would explain why the practical response is always to sandbox rather than to trust. A possible direction: define the trust surface not as a property of the agent but as a property of the *sandbox gap* — the difference between `level_sandboxed` and the minimum level required for the task. This shifts the question from "what does the agent do?" (undecidable) to "how much capability headroom does the sandbox allow?" (specified, measurable). The framework's recommendation — regulate based on `level_sandboxed`, not `level_effective` — is then a consequence: the trust surface is the engineering margin, not a prediction about behavior.

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

**Proposition 10.3 (World coupling growth in the specified band).** For actors in the specified band, characterization difficulty scales with the *size* of the specification — more rules, more state to track — not exponentially with world coupling. The supermodular cross-term (Prop. 4.7) does not activate because the decision surface is transparent.

### 10.2 Layered regulation

**Definition 10.4 (Three regulatory layers).** The OS pattern, adapted for conversation architecture:

1. **Constraint** (Layer 1): Bounds what is *possible*. Sandbox, `allowed_directories`, network isolation. Does not observe or decide — limits. Effective ma near 0.

2. **Observation** (Layer 2): Reports what *happened*. Tool inputs/outputs, `Conv_State` tracking. Produces data for the policy layer. Specified — reports facts, not judgments.

3. **Policy** (Layer 3): Applies specified rules to observed state. Permission configuration, compaction thresholds, budget management. Decides with transparent rules over vast observed state.

**Proposition 10.5.** Each layer stays in the specified band independently. The composition of three specified layers is still specified.

### 10.3 The Ashby resolution

**Proposition 10.6 (Variety reduction, not matching).** The naive reading of Ashby's Law of Requisite Variety: as the agent gets more capable, the Harness must match its variety. This leads to the Ashby trap — the regulator becomes as complex as the regulated system.

The framework's resolution:

1. **Co-domain funnels** (Def. 4.11) are variety attenuators — they reduce the agent's effective variety
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

**Gap.** Full pi-calculus formalization is deferred. The key question: does non-deterministic tool execution change the convergence properties of the grade trajectory (Prop. 8.13), or only the variance around a trajectory that converges/diverges for structural reasons? If the latter, the synchronous formalism is a sufficient abstraction for regulation, and the pi-calculus treatment is an extension rather than a correction.

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

### 12.1 Coupled recurrence: remaining questions (partially addressed)

The recurrence `F` is now characterized (section 8.4): all trajectories converge absolutely (token window bound), and the regulatory convergence boundary is the Chomsky boundary (CF vs RE), modulated by sandbox and communication structure (Prop. 8.13, Cor. 8.15). **Remaining:** (a) The `delta_w_info` / `delta_w_effect` decoupling (Def. 8.9) needs empirical measurement — how large is the gap in practice for common tool sets? (b) Optimal compaction strategy: when and how aggressively to compact as a function of the trajectory's growth rate. (c) The regulatory cost function `R(n)` is stated qualitatively (decidable/undecidable); a quantitative model would enable concrete regulatory budgeting.

### 12.2 Computation channel formalization (partially addressed)

The tool grade (Def. 9.1) grounds the nine-level taxonomy in the Chomsky hierarchy (input language) and effect lattice (permitted operations). The configuration invariant (Def. 9.6, Prop. 9.7) gives the phase transition at CF-to-RE a formal criterion: whether the invariant `grade_actual <= grade_config` holds. **Remaining:** formalize the effect lattice as precisely as the Chomsky hierarchy is formalized. Characterize the interaction between effect restriction and input language class — when does restricting effects compensate for RE input? The decidable approximation hierarchy (syntactic matching < types < abstract interpretation < model checking) needs formal treatment of precision/cost tradeoffs.

### 12.3 Supermodularity: relaxing the independence assumption (medium priority)

Proposition 4.7 proves supermodularity under the independence model (`chi = I(w) . log P(d)`). The independence assumption — each input independently steers the computation — is generous. Two directions: (a) prove supermodularity under a weaker correlation model where inputs share paths, and (b) empirically measure `chi` (observer prediction error) as grade components vary to test whether the product form is a good approximation or a loose bound.

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

### 12.10 Design functions over characterization difficulty (lower priority)

The scalar `chi(w, d)` invites optimization. Natural design functions: regulatory cost `R(chi)` (monotone — harder to characterize means costlier to regulate), capability value `V(I(w), P(d))` (what the system can accomplish), risk exposure `rho(chi, level)` (combining characterization difficulty with computation channel level), operational cost `C(I(w))` (world coupling has infrastructure cost). The optimal operating point is a constrained optimization: maximize `V` subject to `R(chi) <= budget` and `rho <= threshold`. Supermodularity of `chi` means the feasible region has interesting geometry — restriction on one axis relaxes the constraint on the other superlinearly.

### 12.11 Mechanical verification (aspirational)

None of this has been verified in Agda, Lean, or Coq. The monad/comonad definitions, Kleisli structure, and session types are the most amenable to mechanization. The grade lattice and coupled recurrence would require more novel encoding.

---

## References

- Ashby, W. R. (1956). *An Introduction to Cybernetics*. Chapman & Hall.
- Atkey, R. (2009). Parameterised notions of computation. *JFP*, 19(3-4).
- Atkey, R. (2018). Syntax and semantics of quantitative type theory. *LICS*.
- Bauer, A. (2018). What is algebraic about algebraic effects and handlers? *arXiv:1807.05923*.
- Bratus, S., Patterson, M., & Sassaman, L. (2011). The halting problems of network stack insecurity. *;login:*, USENIX.
- Brookes, S., & Geva, S. (1992). Computational comonads and intensional semantics. *Applications of Categories in Computer Science*, LMS Lecture Notes 177.
- Conant, R. C., & Ashby, W. R. (1970). Every good regulator of a system must be a model of that system. *IJSS*, 1(2).
- Cousot, P., & Cousot, R. (1977). Abstract interpretation: A unified lattice model for static analysis of programs. *POPL*.
- Felleisen, M. (1991). On the expressive power of programming languages. *Science of Computer Programming*, 17(1-3).
- Fowler, M. (2025). Harness engineering. *martinfowler.com*.
- Harrison, M. A., Ruzzo, W. L., & Ullman, J. D. (1976). Protection in operating systems. *Communications of the ACM*, 19(8).
- Honda, K. (1993). Types for dyadic interaction. *CONCUR*.
- Honda, K., Yoshida, N., & Carbone, M. (2008). Multiparty asynchronous session types. *POPL*.
- Kammar, O., Lindley, S., & Oury, N. (2013). Handlers in action. *ICFP*.
- Katsumata, S. (2014). Parametric effect monads and semantics of effect systems. *POPL*.
- McBride, C. (2016). I got plenty o' nuttin'. *A List of Successes*, LNCS 9600.
- Miller, M. S. (2006). *Robust Composition*. PhD thesis, Johns Hopkins University.
- Milner, R. (1999). *Communicating and Mobile Systems: The Pi-Calculus*. Cambridge University Press.
- Moggi, E. (1991). Notions of computation and monads. *Information and Computation*, 93(1).
- Montufar, G. F., Pascanu, R., Cho, K., & Bengio, Y. (2014). On the number of linear regions of deep neural networks. *NeurIPS*.
- Nielson, F., & Nielson, H. R. (1999). Type and effect systems. *Correct System Design*, LNCS 1710.
- Orchard, D., Wadler, P., & Eades, H. (2019). Unifying graded and parameterised monads. *arXiv:1907.10276*.
- Plotkin, G., & Power, J. (2003). Algebraic operations and generic effects. *Applied Categorical Structures*, 11(1).
- Plotkin, G., & Pretnar, M. (2009). Handlers of algebraic effects. *ESOP*.
- Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proc. IEEE*, 63(9).
- Spencer, R., Smalley, S., Loscocco, P., et al. (1999). The Flask security architecture: System support for diverse security policies. *USENIX Security*.
- Uustalu, T., & Vene, V. (2008). Comonadic notions of computation. *ENTCS*, 203(5).
- Zhang, H., & Wang, M. (2025). Monadic context engineering for LLM agents. *arXiv:2512.22431*.
