# Toward a Formal Framework

*Part 4: What survives formalization, what doesn't, and where the open problems are.*

This document formalizes the structural claims from the series. Sections 1–10 formalize the conversation log, scopes, the conversation monad, and meta-operations. Sections 11–14 formalize the deeper structures: the interface monad ordering, the monad-comonad duality, interface *ma* vs. internal *ma*, and the fractal architecture. Section 15 formalizes the protocol layer — session types for permission negotiation and π-calculus for parallel tool execution. Section 16 traces a concrete Claude Code interaction through the formalism. Section 17 extracts design principles. Section 18 assesses what's novel and what needs further work.

---

## 1. The Conversation Log

**Definition 1.1 (Message type).** Let `M` be a type of messages. A message `m : M` may be a Principal utterance, an Inferencer response, a tool call, a tool result, or a scoping annotation. We don't constrain the internal structure of `M` -- it's a parameter of the framework.

**Definition 1.2 (Log monoid).** The conversation log is the free monoid `(M*, ., e)` where `M*` is the set of finite sequences of messages, `.` is concatenation, and `e` is the empty sequence.

**Definition 1.3 (Log as a poset category).** Define a partial order on `M*` by the prefix relation: `l1 <= l2` iff `l1` is a prefix of `l2` (i.e., there exists `l'` such that `l2 = l1 . l'`). This poset, viewed as a category **Log**, has:
- Objects: log states (elements of `M*`)
- Morphisms: a unique morphism `l1 -> l2` whenever `l1 <= l2`

This category is filtered (every pair of objects has an upper bound -- their common extensions). It captures the append-only invariant: the log only grows.

**Remark.** The append-only property is the key structural constraint. It rules out mutation, which rules out interference between concurrent readers. This is the same property that makes persistent data structures work.

---

## 2. Scopes

**Definition 2.1 (Scope).** A scope is a monotone function `s: M* -> M*` such that for all logs `l`, `s(l)` is a subsequence of `l`.

Monotonicity means: if `l1 <= l2` then `s(l1) <= s(l2)`. As the log grows, the scoped view can only grow. An agent never loses visibility of something it could previously see.

**Remark.** In practice, a scope is typically defined by a predicate `p: M -> Bool`, where `s_p(l)` filters `l` to messages satisfying `p`. Predicate-based scopes are automatically monotone. They are also monoid homomorphisms: `s_p(l1 . l2) = s_p(l1) . s_p(l2)`, meaning the scope of a concatenation is the concatenation of scopes.

**Definition 2.2 (Scope lattice).** The set of scopes over `M*` forms a partial order under pointwise inclusion: `s1 <= s2` iff for all `l`, `s1(l)` is a subsequence of `s2(l)`. The identity function `id` is the top element (full visibility). The constant function `s_bot(l) = e` is the bottom element (no visibility).

For predicate-based scopes, this lattice corresponds to the powerset lattice of predicates on `M`, ordered by implication.

**Proposition 2.3.** Predicate-based scopes form a Boolean algebra with:
- Join: `s_{p|q}(l)` = messages satisfying `p` or `q`
- Meet: `s_{p&q}(l)` = messages satisfying both `p` and `q`
- Complement: `s_{~p}(l)` = messages satisfying `~p`

This gives us set-theoretic operations on scopes for free.

---

## 3. Scope Boundaries

The original *ma* observation — "the space between agents is functional" — has two distinct formalizations in this framework. **Scope boundaries** (this section) formalize what each actor can't *see*: input restriction. **Co-domain characterizability** (Section 11) formalizes how hard each actor's output space is to *describe*: output complexity. These are different things — one is about input, the other about output. They connect through the Harness's configuration lattice (Section 12.8): the Harness couples scope restriction with tool restriction, and it's the tool restriction that narrows the co-domain.

### 3.1 Complementary scopes

**Definition 3.1 (Complementary scope).** For a scope `s_p`, define its complement `s_bar_p = s_{~p}`. The complementary scope selects exactly the messages excluded by `s_p`.

**Proposition 3.2 (Decomposition).** For any predicate-based scope `s_p` and log `l`:

    l = s_p(l) + s_bar_p(l)

where `+` is the order-preserving merge that reconstructs `l` from its two complementary subsequences.

**Remark.** Every scope simultaneously defines what's visible (`s_p(l)`) and what's excluded (`s_bar_p(l)`). The excluded portion is not discarded — it's the complementary scope, available to other agents or to the Harness itself. The "negative space" is a first-class object in the scope lattice.

**Definition 3.3 (Scope boundary).** For a pair of agents with scopes `s1` and `s2`, the boundary between them is:

    boundary(s1, s2) = s_bar_1 & s_bar_2

Messages in the boundary are invisible to both agents. This is the information that flows through neither scope — the *ma* between agents.

**Proposition 3.4 (Boundary is non-trivial iff scopes don't jointly cover the log).** `boundary(s1, s2) = s_bot` iff `s1 | s2 = id` (the scopes jointly cover the full log). A non-trivial boundary means there exist messages that no agent sees. In the quartermaster pattern, this is by design: the primary agent's internal reasoning may be visible to neither the quartermaster nor the worker.

### 3.2 Scope boundaries vs. co-domain characterizability

Scope boundaries formalize what's *hidden* — input restriction. But the series' central concept, *ma*, is about what's hard to *describe* — output complexity. These aren't the same thing:

- An actor with **zero visibility** (bottom scope) can still have high *ma* if it has internal state — a random number generator sees nothing but produces unpredictable output.
- An actor with **full visibility** (top scope) can still have low *ma* if its interface is constrained — an auditor that sees everything but can only output `Approve/Reject`.

The connection is indirect: the Harness typically couples scope restriction with tool restriction (Section 12.8), and it's the tool restriction that bounds the co-domain. Scope restriction focuses the actor's *attention*; tool restriction bounds its *output space*. Both matter for architecture, but they're independent levers.

The formal definition of *ma* as co-domain characterizability is in Section 11.

---

## 4. The Conversation Monad

**Definition 4.1 (Conversation monad).** The conversation monad is the Writer monad over the log monoid `(M*, ., e)`:

    Conv(A) = A x M*

with:
- `return(a) = (a, e)` -- pure value, no log output
- `(a, w) >>= f = let (b, w') = f(a) in (b, w . w')` -- sequence computations, concatenate logs

**Proposition 4.2.** `Conv` satisfies the monad laws:
1. Left identity: `return a >>= f = f a`
2. Right identity: `m >>= return = m`
3. Associativity: `(m >>= f) >>= g = m >>= (\a. f a >>= g)`

*Proof.* These follow directly from the monoid laws for `(M*, ., e)`. This is the standard proof for Writer monads. QED

**Remark.** The Writer monad captures one direction: agents *append* to the log. It does not capture the other direction: agents *read from* the log. For that, we need additional structure.

---

## 5. Scoped Computation

**Definition 5.1 (Scoped Reader-Writer).** An agent computation that both reads from a scoped view and writes to the log is:

    Agent_s(A) = M* -> A x M*

where the input log is filtered through scope `s` before the agent sees it. That is, an agent with scope `s` and behavior `f` executes on log `l` as:

    exec(f, s, l) = f(s(l))    -- returns (a, w) where w is the new entries

The resulting log after execution is `l . w` (the original log with new entries appended).

**Remark.** This is a State-like monad constrained to append-only updates, composed with a Reader-like component filtered through a scope. The agent can't modify or delete existing log entries -- it can only read (through its scope) and append.

**Definition 5.2 (Agent closure).** An agent closure is a triple `(f, s, l)` where:
- `f: M* -> A x M*` is the agent's behavior
- `s: M* -> M*` is its scope
- `l: M*` is the current log state

The closure's *capture list* is `s(l)` -- the actual log entries visible to the agent at the time of execution.

**Proposition 5.3 (Correspondence to PL closures).** The triple `(f, s, l)` corresponds to a programming language closure `(lam, rho)` where:
- `lam` (the code) corresponds to `f` (the agent's behavior)
- `rho` (the environment) corresponds to `s(l)` (the scoped log)

The key structural difference: in a PL closure, `rho` is fixed at creation time. In an agent closure, `s(l)` can grow as `l` grows, because `s` is a function applied to the current log, not a snapshot. This corresponds to the pi-calculus notion of **scope extrusion** -- the ability for new names (messages) to enter an agent's scope after creation.

**Remark.** This is where the blog post's informal claim "the correspondence isn't exact" receives a precise characterization. PL closures have *static* capture; agent closures have *monotonically growing* capture. The monotonicity constraint (agents never lose visibility) preserves the most important property of lexical scoping -- predictability -- while allowing the scope to expand. This is strictly weaker than full dynamic scoping (where visibility can both grow and shrink) and strictly stronger than static scoping (where visibility is fixed).

---

## 6. Agents as Kleisli Morphisms

**Definition 6.1 (Kleisli category of Conv).** The Kleisli category **Conv_K** has:
- Objects: types
- Morphisms `A -> B`: functions `A -> B x M*` (a computation that takes an `A`, produces a `B` and appends to the log)
- Composition: `(g o_K f)(a) = let (b, w1) = f(a) in let (c, w2) = g(b) in (c, w1 . w2)`
- Identity: `id_K(a) = (a, e)`

**Proposition 6.2.** Agent handoffs are composition in **Conv_K**.

Given:
- Agent 1: `f: Task -> Analysis x M*`
- Agent 2: `g: Analysis -> Report x M*`

The composite `g o_K f: Task -> Report x M*` represents the pipeline: Agent 1 processes the task, appends to the log, Agent 2 reads the analysis and appends further.

**Remark.** This is clean but incomplete. It captures the *data flow* (Agent 1's output type matches Agent 2's input type) but not the *scope change* between agents. In the quartermaster pattern, Agent 2 doesn't see everything Agent 1 appended -- it sees a scoped view. We need to incorporate scoping into the Kleisli structure.

---

## 7. Graded Monads for Scoped Composition

**Definition 7.1 (Scope-graded monad).** Let **(S, <=, |, bot)** be the scope lattice from Definition 2.2. Define a graded monad `Conv_s` indexed by scopes `s in S`:

    Conv_s(A) = M* -> A x M*

where the input `M*` is understood to be filtered through `s`.

The graded bind:

    bind : Conv_s(A) -> (A -> Conv_t(B)) -> Conv_{s|t}(B)

sequences two scoped computations. The composite has the join of the two scopes -- it can see everything either agent could see.

The graded return:

    return : A -> Conv_bot(A)
    return(a) = \l. (a, e)

A pure value requires no scope (bottom element).

**Proposition 7.2.** This satisfies the graded monad laws (Katsumata, 2014):
1. `bind (return a) f = f a` (left identity, with `bot | t = t`)
2. `bind m return = m` (right identity, with `s | bot = s`)
3. `bind (bind m f) g = bind m (\a. bind (f a) g)` (associativity, with `(s | t) | u = s | (t | u)`)

*Proof sketch.* The monad laws follow from the monoid laws for `(M*, ., e)`. The grading laws follow from the lattice laws for `(S, |, bot)`. QED

**Remark.** The graded monad is the central construction. It captures what the blog post describes informally: different agents operate in the same monadic structure but with different visibility, and the composition of agents has a scope that reflects both contributors. The grade tracks *what the computation is allowed to see*.

---

## 8. The Quartermaster as Scope Selection

**Definition 8.1 (Quartermaster).** The quartermaster is a morphism in the Kleisli category that takes a task description and produces a scope:

    qm: Task -> (s : S) x M*

It reads the task (and its own scoped view of history), selects a scope for the worker, and appends its selection rationale to the log.

**Definition 8.2 (Kit).** A kit is a pair `(s, c)` where `s` is a scope and `c : M*` is pre-computed context (the initial log entries the worker should see, possibly derived from the quartermaster's queries over past sessions).

The full quartermaster function:

    qm: Task -> Kit x M*

**Proposition 8.3 (Factoring through the quartermaster).** A direct pipeline `Task -> Report` can be factored as:

    Task --[qm]--> Kit --[worker]--> Report

where:
- `qm : Task -> Kit x M*` selects scope and pre-computes context
- `worker : Kit -> Report x M*` operates within the provided scope

In the Kleisli category: `pipeline = worker o_K qm`.

**Remark.** The quartermaster factorization is a standard pattern in category theory: factoring a morphism through an intermediate object. What's specific to this setting is that the intermediate object (the Kit) contains a *scope* -- a specification of future visibility. The quartermaster doesn't just produce data for the worker; it determines what the worker can *see*. This is scope construction as a first-class computational operation.

---

## 9. Continuations and Scope Renegotiation

**Definition 9.1 (Continuation).** A continuation for an agent of type `Agent_s(A)` is a function:

    k: A -> Conv_t(B)

The agent produces a value `a : A` and passes it to `k`, which continues in a (possibly different) scope `t`.

**Definition 9.2 (Tool request as continuation).** When a worker with scope `s` needs a tool outside its scope, it produces a special value:

    data Result a = Done a | NeedTool ToolName Reason (Tool -> Conv_s(a))

The `NeedTool` constructor carries a continuation `Tool -> Conv_s(a)`: given the requested tool, the worker can resume in its current scope.

The quartermaster handles this by:
1. Receiving the `NeedTool` request
2. Deciding whether to provide the tool (possibly expanding the worker's scope to `s' >= s`)
3. Calling the continuation with the tool

**Proposition 9.3.** Tool request handling is a natural transformation between scoped computation functors. Specifically, providing a tool corresponds to a morphism:

    expand: Conv_s(A) -> Conv_{s'}(A)    where s <= s'

This is a monotone map in the scope lattice, lifted to the graded monad. The worker's computation is re-executed (or resumed) in a wider scope.

**Remark.** In the pi-calculus, this is scope extrusion: a new name (tool) becomes visible to an agent that didn't originally have it in scope. The formal correspondence is:
- Worker scope `s` <-> pi-calculus restriction `(vx)P`
- Scope expansion to `s'` <-> scope extrusion where `x` becomes free
- The quartermaster's decision <-> the environment providing the extruded name

---

## 10. Meta-Conversation Operations

The framework so far describes operations *within* a conversation: agents read through scopes and append to the log. But some operations transform the conversation itself -- the log, the scopes, or both. These are not monadic operations within the conversation. They are functorial operations *on* it.

### 10.1 Structured Conversations

The formalization so far treats the log as `M*` -- a flat sequence of messages. But actual conversation state has richer structure. A meta-level operator (or a Harness command like `/context`) sees the conversation not as a token stream but as a typed, compartmentalized object:

**Definition 10.1 (Structured conversation).** A conversation state is a record:

    Conv_State = {
      system:       M*,      -- system prompt (fixed across compaction)
      instructions: M*,      -- CLAUDE.md, project context (fixed)
      history:      M*,      -- conversation turns (compaction target)
      tools:        T,       -- available tool set (mutable)
      budget:       Nat      -- remaining token capacity
    }

where `T` is a set of tool specifications. The *flattening* function `flat: Conv_State -> M*` concatenates the compartments into the token sequence that an object-level agent actually sees (filtered through its scope). Object-level agents operate on `flat(s)`. Meta-level operations operate on the structured `Conv_State` directly.

**Remark.** The structured view is simpler to reason about than the flat view because it exposes *type boundaries* that the flat view erases. Compaction can target `history` while preserving `system` and `instructions`. Tool mutations modify `tools` without touching the log. Budget management tracks a global constraint across all compartments. The meta-level has *more information* than the object level, not less.

### 10.2 Meta-operations as endomorphisms

**Definition 10.2 (Meta-operation).** A meta-operation is an endomorphism on `Conv_State`:

    meta: Conv_State -> Conv_State

Meta-operations are classified by which compartments they affect and whether they preserve content:

**Read-only (observations):**
- `/context` -- inspects the structure, reports compartment sizes and budget usage. A *lens* into `Conv_State` that produces a measurement without transforming it. Formally: a function `observe: Conv_State -> Report` (not an endomorphism, but a morphism to an observation type).

**History transformations:**
- `/compact` -- `compact(s) = { s with history = C(s.history), budget = s.budget + saved }`. Lossy compression of the history compartment. Reclaims budget. Preserves system, instructions, and tools.
- `/clear` -- `clear(s) = { s with history = e, budget = s.budget + |s.history| }`. Resets history to empty. Maximal budget reclamation. Not the monoid unit `e` on the full state -- it's a *projection* onto the fixed compartments.

**Scope/tool mutations:**
- `add_tool(t)` -- `{ s with tools = s.tools + {t} }`. Widens the available tool set.
- `remove_tool(t)` -- `{ s with tools = s.tools - {t} }`. Narrows it.

**External persistence:**
- `/memory` -- operates on persistent state *outside* `Conv_State` entirely. A morphism to a separate store that survives across conversations. This is not an endomorphism on `Conv_State` -- it's a side-effecting operation in a different monad (a persistence monad that outlives the conversation).

### 10.3 Budget as a linear resource

**Definition 10.3 (Token budget).** The token budget `b` is a natural number representing remaining context window capacity. Each object-level operation consumes budget:

    cost: M -> Nat                    -- token cost of a message
    append(m, s) = { s with
      history = s.history . [m],
      budget  = s.budget - cost(m)
    }

The budget constraint is: `s.budget >= 0` at all times. When budget is exhausted, no further object-level operations are possible without a meta-level intervention (compaction or clear).

**Remark.** This introduces a *resource sensitivity* that the pure Writer monad doesn't capture. The Writer monad allows unbounded appending. The actual conversation monad is a Writer monad with a *finite resource* -- closer to a linear or affine type discipline. Each message consumes a non-renewable resource (context window tokens). Compaction is the only operation that *reclaims* budget, and it does so lossily.

The graded monad from Section 7 could be extended to track budget alongside scope:

    Conv_{s,n}(A) = M* -> A x M*

where `s` is the scope grade and `n : Nat` is the budget consumed. The grading monoid becomes `(S x Nat, (|, +), (bot, 0))` -- composing two agents joins their scopes and sums their budget usage. A computation is valid only if the total budget consumed doesn't exceed the available budget in `Conv_State`.

This is essentially a graded monad over a *resource semiring*, which connects to the quantitative type theory literature (Atkey, 2018; McBride, 2016). The budget is a quantity that object-level operations spend and meta-level operations (partially) replenish.

### 10.4 Properties of meta-operations

**Proposition 10.4.** Compaction is:
- **Lossy**: Not injective. Multiple histories may compact to the same summary.
- **Not monotone**: For logs `l1 <= l2`, it is not necessarily the case that `C(l1) <= C(l2)`.
- **Not a monoid homomorphism**: `C(l1 . l2) != C(l1) . C(l2)` in general.
- **Structure-preserving**: It respects the compartment boundaries of `Conv_State`. It transforms `history` but does not affect `system`, `instructions`, or `tools`.
- **Budget-reclaiming**: `compact(s).budget > s.budget` (strictly, assuming history is non-empty and compression is non-trivial).

**Proposition 10.5.** Meta-operations are not morphisms in the Kleisli category **Conv_K**. They operate at a different categorical level -- transforming the substrate that monadic operations work within, not performing operations within that substrate.

### 10.5 Two-level structure

**Definition 10.6 (Two-level structure).** The full framework has two levels:

1. **Object level** -- monadic. Agents read (through scopes) and append to the flat log `flat(s)`. The graded monad `Conv_s` from Section 7 handles this. Operations at this level preserve the append-only invariant, scope monotonicity, and consume budget monotonically.

2. **Meta level** -- endomorphisms on `Conv_State`. Operations transform the structured conversation: history (compaction, clear), tools (add/remove), budget (reclaim via compaction). Operations at this level may violate monotonicity, reclaim budget, and change scope.

The relationship between levels: a meta-level operation transforms the *parameters* of the object-level monad. After compaction, the graded monad `Conv_s` still applies -- but over a different log `C(l)` instead of `l`, with a different budget. After a scope mutation, the grade changes from `s` to `R(s)`. The monadic structure is preserved; the ground it operates on shifts.

**Remark.** This resolves the tension in Section 5. The claim that agent closures have "monotonically growing capture" is correct *at the object level* -- within a single uninterrupted computation phase. Meta-level operations are the *phase boundaries* where monotonicity is suspended and re-established on new ground.

This also clarifies why compaction feels different from regular conversation turns. A message is a morphism in **Log** (extending the prefix order). Compaction is not -- it breaks the ordering and re-establishes it from a new base. The framework accommodates both, but they live at different categorical levels.

**Remark.** The quartermaster pattern straddles these two levels. Within a single task, the quartermaster operates at the object level: reading the log, selecting a scope, passing a kit. But the quartermaster's *scope mutation* -- changing what tools a worker can see -- is a meta-level operation on `Conv_State`. The quartermaster is the agent authorized to perform certain meta-level transformations on behalf of the Harness. This is precisely the "programmable semicolon" intuition: the quartermaster controls what happens *between* computation phases, not within them.

### 10.6 Four actors, three scopes

The two-level structure becomes concrete when we observe that a real conversation has (at minimum) four actors with three distinct projections of the same underlying state. (Executors share the Harness's level but with narrow, argument-scoped views.)

| Actor | Read scope | Write scope | Level | *Ma* |
|---|---|---|---|---|
| **Principal** | Terminal rendering (formatted markdown, tool summaries) | Natural language text | Object (via Harness) | Constitutive |
| **Harness** | `Conv_State` (compartments, token counts, budget, tool registry) | Meta-operations (compaction, tool loading, context management) | Meta | Minimal |
| **Inferencer** | Token vector (flattened, tokenized conversation filtered through scope) | Structured responses + tool calls | Object | Intrinsic |
| **Executor** | Arguments + sandbox (just its inputs) | Computed results | Object (invoked by Harness) | Borrowed |

**Remark.** None of the actors sees the same thing. The Harness sees structural metadata (compartment boundaries, budget) that neither the Principal nor the Inferencer sees directly. The Inferencer sees the full tokenized context including system prompts the Principal never sees. The Principal sees the physical world and their own internal state that no other actor can access. The Executor sees only its arguments and its sandbox (filesystem, network, etc.).

Critically, the write scopes are asymmetric. The Principal inputs unstructured text. The Inferencer inputs structured responses and tool calls. The Harness inputs meta-operations. The Executor inputs computed results. These are four different *write channels* into the same growing state.

**Proposition 10.7 (The Harness is the quartermaster).** In a system like Claude Code, the Harness occupies exactly the quartermaster role:
- It reads the task and the conversation history (its read scope includes `Conv_State`)
- It constructs the Inferencer's scope (decides what tokens to include, what to compact, what tools to load)
- It manages the budget (triggers compaction when budget is low)
- It performs meta-level operations that the Inferencer cannot perform on its own

The quartermaster pattern is not hypothetical. It is the architecture of every Harness that manages context windows, tool availability, and conversation history on behalf of an Inferencer. The Harness's minimal *ma* — its characterizable output space — is *why* it works at the hub (see Section 11).

### 10.7 Memory as a State monad

**Definition 10.8 (Memory monad).** Persistent memory (e.g., `MEMORY.md`, project-specific memory files) is a mutable store that supports read, write, overwrite, and delete. This is a State monad:

    Mem(A) = MemStore -> A x MemStore

where `MemStore` is the current state of all memory files.

**Remark.** Memory is not part of the conversation monad. It is a separate effect with different properties:
- **Mutable**: Unlike the append-only conversation log, memory supports arbitrary edits. It is not a Writer monad.
- **Persistent**: Memory outlives the conversation. It survives `/clear`, `/compact`, and session boundaries. The State monad has a *longer lifetime* than the Writer monad it interacts with.
- **Cross-conversation**: Memory written in one conversation is read in the next. It is the mechanism by which past conversations inform future ones — the formal substrate for the "learning loop" described in the blog post.

The interaction between the conversation monad and the memory monad is a monad transformer stack. The full effect signature for a conversation with memory is approximately:

    Full(A) = MemStore -> M* -> A x M* x MemStore

This is `StateT MemStore (Writer M*) A` -- the memory state threaded through a conversation that appends to a log. The unusual property is that the inner monad (Writer/conversation) has a shorter lifetime than the outer monad (State/memory). Normally in a transformer stack, the outer effect has the shorter scope. Here it's inverted: memory persists, conversations are ephemeral.

**Remark.** The memory monad is where the "homoiconic" intuition from the blog post partially resurfaces in a cleaner form. Memory is not the conversation log inspecting itself (which would be homoiconicity). It is a *separate store* that accumulates patterns from past conversations and makes them available to future ones. The quartermaster's "query past sessions" operation is a read from the memory monad. The "note the gap for next time" operation is a write to it. The learning loop is a cross-monad interaction: conversation effects get distilled into memory state, which informs future conversation scoping.

---

## 11. The Interface Monad Ordering

This section formalizes *ma* as co-domain characterizability. The intuition from Part 3: *ma* is how hard it is to describe an actor's output space. Here we make this precise as a partial order on monads.

### 11.1 The co-domain gradient

**Definition 11.1 (Co-domain gradient).** Following Moggi (1991), define a partial order on monads by the descriptive complexity of their co-domain — how much information is needed to characterize the set of possible outputs:

    Identity ≤ Maybe ≤ Either ≤ List ≤ Writer ≤ State ≤ Distribution ≤ IO

where:
- `Identity(A) = A` — single output per input. Co-domain = input type. Zero *ma*.
- `Maybe(A) = A + 1` — present or absent. Co-domain adds one point. Minimal *ma*.
- `Either(A) = A + E` — value or typed error. Co-domain adds error space. Low *ma*.
- `List(A) = [A]` — finitely many values. Co-domain is finite powerset. Bounded *ma*.
- `Writer(A) = A × W` — value with accumulated output. Co-domain grows with `W`. Medium *ma*.
- `State(A) = S → A × S` — depends on and modifies state. Co-domain parameterized by `S`. Higher *ma*.
- `Distribution(A)` — weighted over possible values. Co-domain is a measure space. High *ma*.
- `IO(A)` — depends on the entire external world. Co-domain is essentially unbounded. Maximal *ma*.

**Remark.** This is the same ordering as the blog post's co-domain gradient, but now we see the formal object: each monad determines an interface co-domain, and the ordering is by descriptive complexity of that co-domain. The four actors map cleanly:

| Actor | Interface monad | Co-domain characterizability |
|---|---|---|
| **Executor** | `Either E` (result or error) | Low — output type + error type |
| **Harness** | `State Conv_State` (deterministic given state) | Low — enumerable given rules |
| **Inferencer** | `Distribution` (weighted over token sequences) | High — requires the weights |
| **Principal** | `IO` (depends on the world) | Maximal — requires the person |

### 11.2 Ma as Kolmogorov complexity of the co-domain

**Definition 11.2 (Ma, formal).** For an actor `A` with interface type `I → M(O)` where `M` is a monad, define:

    ma(A) = K(desc(M(O)))

where `K` is Kolmogorov complexity and `desc(M(O))` is a description of the set `{m(o) | o ∈ O}` — the image of the monadic co-domain.

**Remark.** This is Kolmogorov-flavored, not literal Kolmogorov complexity (which is uncomputable). The definition captures the intuition: how much information is needed to describe what the actor *could* produce. For a file-read tool: "a string or an error" — a few bits. For a language model: "any token sequence the weights would assign nonzero probability" — essentially the model size. The ordering on actors by *ma* is an ordering on their interface monads by co-domain complexity.

### 11.3 Monad morphisms as the ordering relation

**Definition 11.3 (Monad morphism).** A monad morphism `η : M ~> N` is a natural transformation that preserves the monad structure:

    η . return_M = return_N
    η . join_M = join_N . η . fmap(η)

**Proposition 11.4 (Monad morphisms order *ma*).** If there exists a monad morphism `η : M ~> N`, then `ma(M) ≤ ma(N)`. The morphism embeds the smaller co-domain into the larger one.

The embeddings along the gradient:
- `Identity ~> Maybe` : `a ↦ Just(a)` — every pure value is a non-absent value
- `Maybe ~> Either` : `Just(a) ↦ Right(a), Nothing ↦ Left(default)` — absence as a specific error
- `Either ~> State` : a pure error/value computation is a degenerate stateful computation
- `State ~> IO` : stateful computation over a known state type embeds into world-dependent computation

**Caveat.** This ordering is partial, not total. `Writer` and `State` model orthogonal axes (accumulation vs. threading). `Cont` is incomparable to most. The ordering is meaningful specifically for monads that characterize *output spaces* — the axis relevant to *ma*.

### 11.4 Parameterized IO for Executors

Executors illustrate a subtlety: the same tool can have different *ma* depending on its sandbox.

**Definition 11.5 (Parameterized IO).** Define a family of monads `IO_W` indexed by a *world* `W`:

    IO_filesystem(A) — may read/write the entire filesystem
    IO_sandbox(A)    — may access only allowed_directories
    IO_network(A)    — may make HTTP requests
    IO_null(A)       — pure computation (no world access)

Each restriction on the world narrows the co-domain:

    IO_null ≤ IO_sandbox ≤ IO_filesystem ≤ IO

The Harness controls which world an Executor inhabits. `Bash(full)` lives in `IO_filesystem`. `Bash(scoped)` lives in `IO_sandbox`. The permission lattice from Section 9 is a **lattice of worlds** — each permission grant expands the Executor's world, widening its co-domain.

**Remark.** This connects directly to the Harness's role as co-domain manager. When the Harness configures `allowed_directories` or sets `enable_external_access = false`, it is choosing which `IO_W` the Executor inhabits. The Executor's interface *ma* is determined not by the tool's implementation but by the Harness's world restriction. The same `Bash` tool can be high-*ma* (full filesystem) or low-*ma* (sandboxed), depending on the Harness's configuration.

---

## 12. The Monad-Comonad Duality

Part 3 describes expansion as monadic and compression as comonadic. Here we formalize this.

### 12.1 Expansion: monadic injection

Tool results enter the conversation through the monadic `bind`:

    bind : Conv(A) → (A → Conv(B)) → Conv(B)

Each tool call is a Kleisli morphism `Args → Conv(Result)`. The result enters the conversation, widening the co-domain — the conversation now contains information it didn't have before. This is the standard story from Section 4.

### 12.2 Compression: comonadic extraction

The right comonad is `Store` — a value in context with a *position* that determines the focus.

**Definition 12.1 (Store comonad, standard).** The Store comonad over a position type `S` and value type `A` is:

    Store S A = (S → A, S)

A pair of: a function from every position to a value, and the current position. With operations:

    extract (f, s)   = f s                          -- value at the current position
    duplicate (f, s) = (λs'. (f, s'), s)            -- at each position, the whole store
    extend g (f, s)  = (λs'. g (f, s'), s)          -- apply g from every position's perspective

**Definition 12.2 (Conversation as Store comonad).** Define the conversation comonad as:

    ConvStore = Store Scope FocusedView

where:
- `Scope` is the position type — which scope/extraction strategy to apply (from the scope lattice of Definition 2.2)
- `FocusedView` is the value type — the projected conversation an actor actually sees
- The stored function is `view : Scope → FocusedView`, defined by `view(s) = flatten(s(conv_state))`
- The current position is the scope of the actor being served

The comonad operations now have precise meanings:

    extract (view, s_inferencer) = view(s_inferencer)
        -- the Inferencer's token window: the conversation projected through its scope

    duplicate (view, s_inferencer) = (λs'. (view, s'), s_inferencer)
        -- at every scope position, the ability to see every other scope position
        -- this is the Harness's perspective: it can compute any actor's view

    extend infer (view, s_inferencer) = (λs'. infer(view, s'), s_inferencer)
        -- "what would inference produce under each possible scoping?"
        -- a counterfactual: the Inferencer's output as a function of scope choice

**Remark.** The `Store` comonad captures the Harness's structural role precisely:

- **`extract`** is what the Inferencer (or any actor) experiences — it receives the focused view at its scope position. The actor never sees the full store; it sees `extract`.
- **`duplicate`** is the Harness's god-view — access to every possible extraction, not just the current one. The Harness can compute what *any* actor would see under *any* scope. This is the formal content of "the Harness constructs each actor's view."
- **`extend f`** applies a function `f : ConvStore → B` across all scope positions. If `f` is inference, this gives the counterfactual: "what would the Inferencer produce if we gave it a different scope?" This is what the Harness is implicitly optimizing when it chooses which tools to load or how aggressively to compact.

The Harness has access to `duplicate` and `extend`. Other actors only ever see `extract`. This asymmetry — the Harness operates on the comonad, other actors operate on extracted values — is the formal content of the Harness's privileged position.

### 12.3 The turn as comonadic extraction followed by monadic injection

**Proposition 12.2 (Turn structure).** A single turn has the structure:

    (view, s) ──extract──→ FocusedView ──actor──→ Output ──bind──→ Conv(Output)

where:
- `extract` is comonadic (the Store comonad projects the conversation to a focused view)
- `actor : FocusedView → Output` is opaque internal processing (the actor's internal *ma*)
- `bind` is monadic (the output enters the conversation log, widening the co-domain)

The Harness orchestrates this by:
1. Choosing the scope position `s` (which extraction to apply)
2. Letting `extract` produce the focused view
3. Passing the view to the actor
4. Receiving the output and injecting it via monadic `bind`
5. Updating `conv_state` (which changes the stored function `view` for the next turn)

This is the `read → infer → respond` cycle from Part 3, now formalized. Every turn is a comonad-to-monad bridge: compress, process, expand. The Harness controls step 1 (scope selection) and step 4 (injection gating).

### 12.4 The Harness at the boundary

**Proposition 12.3 (The Harness mediates both structures).** The Harness operates on both the comonadic and monadic sides:

| Operation | Structure | Store operation | Effect on co-domain |
|---|---|---|---|
| Scope selection | Comonadic | Choosing position `s` | Determines what actor sees |
| Scope construction | Comonadic | Computing `extract(view, s)` | Narrows (projects conversation) |
| Compaction | Meta + comonadic | Modifying the stored function `view` | Narrows (lossy — changes what `extract` returns at every position) |
| Tool dispatch | Monadic | `bind` (result enters log) | Widens (new information in conversation) |
| Permission gate | Controls which `bind`s are allowed | — | Co-domain management |
| Promise injection | Deferred monadic | Deferred `bind` | Widens later |

**Remark.** Compaction is the most interesting case. It doesn't change the scope position — it changes the *stored function*. After compaction, `view(s)` returns a lossy summary instead of full history, for *every* scope `s`. This is a modification of the comonadic structure itself, not an operation within it. In the two-level structure (Section 10.5), compaction is a meta-level operation that transforms the comonad's stored function.

The Harness mediates between the comonad (how the conversation is projected to each actor) and the monad (how information enters the conversation). Its minimal *ma* — characterizable output space — is what makes it trustworthy in this role. Other actors can reason about what the Harness will do precisely because the Harness operates on the `Store` structure (choosing positions, gating injections) rather than performing inference.

### 12.5 Each actor sees a different extraction

The conversation has multiple actors, each at a different scope position. The Store comonad handles this naturally: the stored function `view : Scope → FocusedView` can be evaluated at any position.

| Actor | Scope position `s` | What `extract(view, s)` gives them |
|---|---|---|
| **Principal** | `s_render` | Rendered output — formatted text, tool summaries, status |
| **Inferencer** | `s_token` | Token window — flattened, filtered, compacted conversation |
| **Executor** | `s_args` | Arguments + sandbox — just its inputs |

The Harness doesn't have a scope position in the Store — it has access to the `duplicate`d store. It sees `(λs'. (view, s'), s)` — the full function at every position. This is the formal content of "the Harness is the only participant that communicates with all others."

### 12.6 Distributive laws (open problem)

**Conjecture 12.4.** There exists a distributive law between the conversation monad `Conv` (Writer over log monoid) and the conversation comonad `ConvStore` (Store over scope lattice):

    λ : Store Scope (Conv(A)) → Conv(Store Scope A)

This would tell us how extraction and injection compose — the formal structure of a full turn. Concretely: given a scoped view of a log-producing computation, can we factor it into a log-producing computation that yields a scoped view? Distributive laws between monads and comonads are studied by Brookes & Geva and Uustalu & Vene, but the specific instance for `Writer` and `Store` is worth investigating — both are well-understood individually.

### 12.7 The Harness, formally

The Harness has been described narratively (Section 10.6) and structurally (Sections 12.2–12.5). Here we give it a type.

**Definition 12.5 (Harness step).** A single Harness step is a function:

    harness_step : Conv_State → HarnessAction

where `HarnessAction` is the sum type of everything the Harness can do:

    data HarnessAction
      = Extract Scope (FocusedView → ProposedActions)
          -- construct a view for an actor, receive their proposals
      | Gate ToolCall Decision
          -- approve or deny a proposed tool call
      | Inject Result Conv_State
          -- inject a tool result into the conversation (monadic bind)
      | Meta (Conv_State → Conv_State)
          -- perform a meta-operation (compaction, tool mutation, budget)
      | Yield Conv_State
          -- turn complete, return updated state

**Remark.** The Harness is a `State Conv_State` computation — it reads and writes `Conv_State`. But its *interface* type is `HarnessAction`, which is fully enumerable given the current `Conv_State` and configuration. This is the formal content of "minimal *ma*": the Harness's co-domain is a tagged union of characterizable operations. You can describe what the Harness might do without having the Harness — you just need its rules and the current state.

**Definition 12.6 (Harness as comonad-monad mediator).** The Harness's role in the turn cycle (Prop. 12.2) is precisely:

    harness : Conv_State → (Store Scope FocusedView, Conv_State → Conv(Conv_State))

It produces:
1. A `Store Scope FocusedView` — the comonadic side (the conversation projected for each actor)
2. A gating function `Conv_State → Conv(Conv_State)` — the monadic side (how approved results enter the conversation)

The first component constructs the comonad from raw state. The second component gates monadic injection back into state. The Harness is the function that **bridges** `Conv_State` to `Store` (comonadic) and `Conv` (monadic).

**Proposition 12.7 (The Harness's *ma*).** The Harness inhabits `State Conv_State` with interface type `HarnessAction`. Its interface *ma* is:

    ma_interface(Harness) = K(desc(HarnessAction))

Since `HarnessAction` is a finite tagged union over characterizable operations (each determined by rules and state), `K(desc(HarnessAction))` is bounded by the size of the Harness's configuration — its rules, permission tables, and compaction thresholds. This is small relative to the model weights (Inferencer) or the physical world (Principal).

**Remark.** The Harness is the only actor whose type signature spans both the comonadic and monadic structures. Other actors operate on one side: the Inferencer receives `extract` output and proposes `bind` inputs; Executors receive arguments and produce results. The Harness *constructs* the comonad and *gates* the monad. Its type signature is the formal reason it must sit at the hub.

### 12.8 The Harness coupling: scope restriction and co-domain restriction

The document has two orderings that should be related:

1. The **scope lattice** (Section 2) — orders *what an actor can see* (input restriction, comonadic side)
2. The **monad ordering** (Section 11) — orders *how hard the output space is to describe* (co-domain characterizability, monadic side)

Do they correspond? Not directly. An actor with zero visibility could still have high *ma* (a random number generator sees nothing but produces unpredictable output). Restricting input doesn't automatically restrict output.

But the Harness **couples** them. When the Harness constructs a restricted view for an actor, it typically also restricts the actor's available tools — and it's the *tool restriction* that narrows the co-domain. The correspondence isn't between scope and co-domain directly. It's between the Harness's paired comonadic and monadic decisions.

**Definition 12.8 (Harness configuration).** A Harness configuration for an actor is a pair:

    config = (s, T) ∈ Scope × P(Tools)

where `s` is the scope (which messages the actor sees) and `T` is the tool set (which actions the actor can propose). The Harness assigns a configuration to each actor.

**Definition 12.9 (Configuration lattice).** Define a partial order on configurations:

    (s₁, T₁) ≤ (s₂, T₂)  iff  s₁ ≤ s₂  and  T₁ ⊆ T₂

This is the product lattice of the scope lattice and the powerset lattice of tools. Moving down restricts both visibility and capability.

**Proposition 12.10 (Configuration determines interface *ma*).** For an actor `A` with Harness configuration `(s, T)`:

    ma_interface(A, (s, T)) ≤ ma_interface(A, (s', T'))  when  (s, T) ≤ (s', T')

Restricting an actor's configuration (narrower scope *and* fewer tools) cannot increase its interface *ma*. The actor's output space is bounded by what its tools can produce, regardless of its internal capability.

*Argument.* The actor's interface co-domain is determined by the outputs of its available tools: `co-domain(A, T) = ⋃{co-domain(t) | t ∈ T} ∪ {text}`. Removing a tool removes its co-domain from the union. Narrowing the scope doesn't directly affect the co-domain, but it reduces the information available for the actor to *differentiate* its outputs — a narrower view means fewer distinct inputs, which means fewer distinct output trajectories. The tool restriction is the primary driver; the scope restriction is secondary.

**Remark.** This is why the Harness's paired decisions matter. Scope restriction alone (comonadic side) doesn't guarantee co-domain restriction. Tool restriction alone (monadic side) does guarantee it — fewer tools means a strictly smaller co-domain union. The Harness's power is in coupling both: it gives the worker a focused view (so inference is focused) *and* a restricted tool set (so the co-domain is bounded). This is the formal content of "restriction is the load-bearing operation."

**Corollary 12.11 (The configuration lattice connects both halves of the framework).** The scope lattice (Sections 2–3, comonadic) and the monad ordering (Section 11, monadic) meet in the configuration lattice. The Harness navigates this lattice when it sets up each actor: choosing a position in the scope lattice (what the actor sees) and a position in the tool powerset (what the actor can do). The *ma* ordering of actors (Executor < Harness < Inferencer < Principal) is not a consequence of either lattice alone — it's a consequence of the Harness's typical configuration choices: Executors get narrow scope + single tool (minimal), the Inferencer gets broad scope + gated tools (moderate), the Principal gets full physical world + unbounded agency (maximal).

---

## 13. Interface Ma and Internal Ma

The key insight from Part 3: *ma* is measured at the **interface**, not inside the actor. This section formalizes the distinction.

### 13.1 The interface boundary as a monad morphism

**Definition 13.1 (Implementation monad).** Every actor `A` has an *implementation monad* `M_impl` that describes its internal computational structure — its full monad transformer stack. For a language model, this includes attention, sampling, chain-of-thought. For the Harness, it includes state management, rule evaluation, configuration lookup.

**Definition 13.2 (Interface monad).** Every actor `A` has an *interface monad* `M_iface` that describes its output space as seen by other actors. This is determined by the actor's interface type — its tool signature, its output format, its co-domain.

**Proposition 13.3 (Interface as monad morphism).** The interface boundary is a monad morphism:

    η_A : M_impl ~> M_iface

This morphism is the formal structure of the interface. It maps the actor's rich internal computation to the constrained output space visible externally. The morphism is:
- **Surjective** on the co-domain (every interface output can be produced)
- **Lossy** (many internal states map to the same interface output)
- **Structure-preserving** (sequential composition inside maps to sequential composition outside)

### 13.2 Internal ma and interface ma

**Definition 13.4.**

    ma_internal(A) = K(desc(M_impl(O)))    -- complexity of the implementation co-domain
    ma_interface(A) = K(desc(M_iface(O)))   -- complexity of the interface co-domain

These are *independent*:

| Configuration | Internal *ma* | Interface *ma* | Example |
|---|---|---|---|
| Small model, many tools | Low | High | Haiku with full tool registry |
| Large model, restricted tools | High | Low | Opus as auditor (Approve/Reject) |
| Deterministic rules, narrow output | Low | Low | Static tool whitelist |
| Large model, unrestricted | High | High | Unconstrained Inferencer |

**Remark.** Internal *ma* determines the **quality** of the actor's decisions within its constrained co-domain. Interface *ma* determines the **auditability** of the actor's output — how well other actors can reason about what it might produce. A good funnel has high internal *ma* (good judgment) and low interface *ma* (characterizable output).

### 13.3 Co-domain funnels as monad morphisms

**Definition 13.5 (Co-domain funnel).** A co-domain funnel is an actor where the interface monad morphism `η : M_impl ~> M_iface` has `ma(M_impl) >> ma(M_iface)` — the implementation is strictly richer than the interface.

Examples:
- **Sub-agent boundary**: Implementation is a full conversation loop (`Conv_s`). Interface is `Either(Result, Error)`. The Executor wrapper compresses the sub-agent's co-domain.
- **Quartermaster**: Implementation may use inference for tool selection. Interface is `Kit` (a finite list of tools). The kit type compresses the selection reasoning.
- **Security auditor**: Implementation may use deep analysis over large context. Interface is `Either(Approved(Message), Rejected(Reason))`. The binary-ish output compresses the review.

The monad morphism `η` is what **makes** it a funnel: it maps the rich internal monad to a constrained interface monad. The morphism is lossy — the parent can't recover the internal reasoning from the interface output — and that's the point.

---

## 14. Fractal Architecture

Every actor, examined internally, has a conversation-like architecture.

### 14.1 Self-similarity

**Observation 14.1.** The Inferencer is an actor with minimal visible structure: it receives a token window and produces a response. But internally, it has:
- **A scope** — the attention mechanism selects which tokens to attend to
- **State management** — KV cache, internal representations
- **Sequential processing** — layers compose, attention is multi-headed
- **An output interface** — the final token probabilities

The internal architecture of the Inferencer mirrors the conversation architecture: scoped reading, stateful processing, structured output. The Principal has a richer version: physical perception (scope), cognition (processing), communication (interface).

### 14.2 The interface as a monad morphism between levels

**Proposition 14.2 (Self-similar architecture).** At every level of nesting, the architecture has the same shape:

    extract → process → inject

The interface between levels is a monad morphism from the implementation level to the interface level. Each actor's implementation is itself a conversation-like system. The interface peels off the outer layers of the implementation's monad transformer stack, exposing only the interface monad.

```
Level 0 (conversation): Principal ←→ Harness ←→ Inferencer ←→ Executors
                                                      |
Level 1 (sub-agent):                          Principal ←→ Harness ←→ Inferencer ←→ Executors
                                                                           |
Level 2 (tool):                                                     Args → Result
```

At each level boundary, a monad morphism compresses the lower level's co-domain into the upper level's interface type. The sub-agent's full conversation is compressed to an Executor result. The tool's world interaction is compressed to a return value.

### 14.3 The Executor's worlds

**Proposition 14.3 (Executor world lattice).** Consider the Executor's interface monad `IO_W`. The world parameter `W` determines the Executor's co-domain:

    IO_null ≤ IO_sandbox ≤ IO_filesystem ≤ IO_full

But the Executor's `IO_W` is in a *different world* than the Principal's `IO`. The Principal's world is physical reality. The Executor's world is the sandbox, the filesystem, the network. They don't compose directly — each sees a different slice of "the world."

The Harness mediates between these worlds. It takes results from the Executor's `IO_W` and injects them into the conversation (which the Principal observes). The injection crosses a world boundary: `IO_sandbox → Conv → IO_physical`. The monad morphism at each boundary determines what information survives the crossing.

**Remark.** This resolves a tension in the original framework. The Executor has "borrowed" *ma* — its co-domain complexity comes from the world, not the actor. But *which* world? The Harness determines this by configuring the sandbox. The same Executor implementation can inhabit different worlds (different `IO_W`), and its *ma* changes accordingly. The Harness doesn't just construct the Inferencer's scope — it constructs the Executor's *world*.

---

## 15. The Protocol Layer: Session Types and π-Calculus

The monadic framework (Sections 4–7) handles sequential data flow. The comonadic framework (Section 12) handles scope construction. But a conversation is also a **concurrent protocol with negotiated authorization** — multiple actors communicating, tools executing in parallel, permissions granted or denied mid-conversation. This section formalizes the protocol layer.

### 15.1 The permission protocol as a session type

A session type specifies the *structure* of a communication protocol — who sends what to whom, in what order, with what branching. The tool-use protocol (from Part 2) has a clean session type:

**Definition 15.1 (Tool-use session type).**

```
type ToolUse =
    Inferencer → Harness   : Propose(tool, args)
  ; Harness    → Harness   : CheckPermission(tool, args, mode)
  ; case mode of
      AutoAllow →
          Harness  → Executor  : Execute(args)
        ; Executor → Harness   : Result(output)
        ; Harness  → Inferencer: ToolResult(output)
      Ask →
          Harness  → Principal : PermissionRequest(tool, args)
        ; Principal → Harness  : Grant | Deny
        ; case of
            Grant →
                Harness  → Executor  : Execute(args)
              ; Executor → Harness   : Result(output)
              ; Harness  → Inferencer: ToolResult(output)
            Deny →
                Harness  → Inferencer: PermissionDenied(tool, reason)
      AutoDeny →
          Harness  → Inferencer: PermissionDenied(tool, reason)
```

**Remark.** Several things are visible in the session type that aren't visible in the monadic formalism:

- **The Harness mediates every message.** No actor communicates directly with any other. The Inferencer never talks to the Executor; the Principal never talks to the Inferencer. The star topology is encoded in the session type as "every arrow has the Harness on one end."
- **Authorization is a branch, not a value.** The `Grant | Deny` branch determines which *continuation* the protocol follows — a completely different sequence of messages. This is richer than a boolean: the denied path doesn't invoke the Executor at all.
- **The Principal only participates in the `Ask` branch.** In `AutoAllow` and `AutoDeny`, the Principal is never consulted. The session type makes this structural: the Principal's channel isn't even opened in those branches.

**Example: the worked example (Section 16), step 4.** The `Read` tool is auto-allowed. The session type takes the `AutoAllow` branch: `Propose → CheckPermission → Execute → Result → ToolResult`. No Principal synchronization. If the tool were `Bash`, the session type would take the `Ask` branch, adding a `PermissionRequest → Grant|Deny` exchange with the Principal before proceeding.

### 15.2 Co-domain management in the session type

Each branch of the session type has a different co-domain effect:

| Branch | What enters the conversation | Co-domain effect |
|---|---|---|
| `AutoAllow → Result` | Tool output | Widens — Executor's `IO_W` co-domain injected |
| `Ask → Grant → Result` | Tool output (after Principal approval) | Widens — same injection, but gated |
| `Ask → Deny` | `PermissionDenied` message | Narrows — Executor's co-domain is *not* injected |
| `AutoDeny` | `PermissionDenied` message | Narrows — same |

The `Deny` branches are **co-domain restriction operations**. They prevent an Executor's `IO_W` from composing into the conversation. The permission protocol is the Harness's mechanism for controlling *which* monadic injections actually happen — it's the gate between the Inferencer's proposals and the conversation's co-domain.

**Proposition 15.2.** The permission configuration is a function from tool calls to session type branches:

```
perm : ToolCall → {AutoAllow, Ask, AutoDeny}
```

This function determines, for each proposed co-domain injection, whether it proceeds immediately, requires Principal authorization, or is blocked. It is the Harness's **static** co-domain management policy. The Principal's `Grant | Deny` decisions are the **dynamic** co-domain management — contextual, per-invocation judgments that the static policy can't capture.

### 15.3 Parallel tool execution in π-calculus

When the Inferencer proposes multiple tool calls in one response, they execute concurrently. The π-calculus gives the right formalism: concurrent processes communicating over channels with name restriction.

**Definition 15.3 (Parallel tool execution).** For N proposed tool calls, each independently permitted:

```
(ν r₁)(ν r₂)...(ν rₙ)(
    tool₁⟨args₁, r₁⟩ | tool₂⟨args₂, r₂⟩ | ... | toolₙ⟨argsₙ, rₙ⟩
  | r₁(res₁).r₂(res₂)...rₙ(resₙ).harness⟨res₁, ..., resₙ⟩
)
```

Where:
- `(ν rᵢ)` creates a **private channel** `rᵢ` — only tool `i` and the collector can use it (name restriction)
- `toolᵢ⟨argsᵢ, rᵢ⟩` sends args and a return channel to the tool (concurrent execution)
- `rᵢ(resᵢ)` receives the result on the private channel (barrier synchronization)
- `harness⟨res₁, ..., resₙ⟩` collects all results and proceeds

**Remark.** The key structural properties:

- **Independence.** The tools execute in parallel (`|`). They share no channels with each other — `r₁` is invisible to `tool₂`. No tool can see another tool's arguments or results. This is the formal content of "Executors have disjoint scopes."
- **Name restriction as scope.** Each `(ν rᵢ)` creates a scope boundary. The private channel `rᵢ` is the tool's "result slot" — nobody else can read it or write to it. This is the π-calculus version of the scope lattice: each tool's communication is restricted to its own private channel.
- **The barrier is sequential composition of receives.** The collector `r₁(res₁).r₂(res₂)...` waits for results in order. The tools may finish in any order, but the collector processes them sequentially. The Harness controls the ordering of injection into the conversation.

**Example: two parallel tool calls.** The Inferencer proposes `Read("src/main.py")` and `Glob("*.test.py")` in one response. Both are auto-allowed.

```
(ν r₁)(ν r₂)(
    Read⟨"src/main.py", r₁⟩ | Glob⟨"*.test.py", r₂⟩
  | r₁(file_contents).r₂(test_files).harness⟨file_contents, test_files⟩
)
```

Both tools run concurrently in their respective `IO_sandbox` worlds. Neither sees the other's results. The Harness collects both results and injects them into the conversation in a single monadic `bind` — the log grows by two tool result messages, the budget decreases by both costs, and the co-domain expands by both tools' output spaces.

### 15.4 Scope extrusion: tool requests as channel mobility

Section 9 noted the correspondence between tool requests and π-calculus scope extrusion. With the session type in hand, we can be more precise.

When the Inferencer proposes a tool call, it is requesting that a *new channel* be opened — a channel to an Executor that didn't previously exist in the Inferencer's scope. The permission gate decides whether this channel is extruded:

```
-- Before permission: the Executor channel is restricted (not in Inferencer's scope)
(ν exec_channel)(Harness⟨exec_channel⟩)

-- After Grant: the channel is extruded into the conversation scope
Harness⟨exec_channel⟩ | Inferencer(result_on(exec_channel))
```

Each `Grant` decision is a scope extrusion event — a new name (the Executor's result channel) becomes available to the Inferencer (indirectly, through the Harness). Each `Deny` prevents the extrusion. The permission protocol is the **gatekeeper for scope extrusion** — the Harness decides which new channels enter the conversation.

This connects to the configuration lattice (Section 12.8): a `Grant` moves the configuration from `(s, T)` to `(s, T ∪ {tool})` — the tool set expands. A `Deny` keeps the configuration unchanged. The scope lattice grows monotonically within a phase (Section 10.5), and each permission grant is a monotone step upward.

### 15.5 What session types add to the framework

| Aspect | Monadic framework alone | With session types |
|---|---|---|
| Permission gate | "The Harness checks permissions" (narrative) | A branching protocol with distinct continuations per decision |
| Co-domain management | "Permission gates control co-domain" (informal) | Each branch has a formal co-domain effect (widen or narrow) |
| Principal participation | "The Principal decides" (narrative) | The Principal's channel is only opened in `Ask` branches |
| Parallel tools | Not modeled | π-calculus: concurrent processes with private channels |
| Scope extrusion | Mentioned (Section 9) | Permission grants are channel extrusion events |

### 15.6 Promises and backgrounded tasks (deferred)

The session type above assumes synchronous execution: the Harness waits for tool results before continuing. But Claude Code supports **backgrounded tasks** — the Harness dispatches an agent, continues the conversation, and injects the result later.

In π-calculus terms, the promise variant replaces the barrier with independent injection:

```
  | r₁(res₁).inject⟨res₁⟩ | r₂(res₂).inject⟨res₂⟩ | ... | continue⟨⟩
```

Each result is injected when it arrives. The continuation doesn't wait. The Harness controls *when* and *how* each injection enters the conversation — it might batch them, summarize them, or defer them.

A full formalization would need:
- A **future type** in the conversation monad: `Future(A)` representing a value that will arrive later
- A **resolution protocol**: the session type for how the Harness injects resolved futures
- **Temporal ordering**: the log becomes a merge of concurrent streams, and the Harness controls the interleaving

This interacts with the Store comonad in interesting ways: after a promise resolves, the stored function `view` changes (the conversation now contains new information), which changes what `extract` returns for every scope. A resolved promise is a **comonad modification** triggered by an **asynchronous monadic event**. The interaction between these structures is an open problem — likely requiring the distributive law from Conjecture 12.4 or something stronger.

We defer this to future work. The synchronous protocol captures the common case; the asynchronous extension is where the real complexity lives.

---

## 16. Worked Example: A Tool Call in Claude Code

The formalism above is abstract. Here we trace a single, concrete interaction through it: a user asks Claude Code to read a file.

### The interaction

```
User:    "What's in src/main.py?"
Claude:  [proposes Read("src/main.py")]
Harness: [checks permissions → auto-allow]
         [dispatches Read tool]
Read:    [returns file contents]
Harness: [injects result into conversation]
Claude:  "Here's what's in src/main.py: ..."
```

### Phase by phase

**1. The Harness constructs the Store comonad (Section 12.2).**

Before the Inferencer sees anything, the Harness builds:

```
conv_state = {
  system:       [system prompt, CLAUDE.md instructions],
  instructions: [tool descriptions, permission config],
  history:      [...previous turns..., user: "What's in src/main.py?"],
  tools:        {Read, Edit, Write, Bash, Grep, Glob, ...},
  budget:       87000
}

view : Scope → FocusedView
view(s) = flatten(s(conv_state))
```

The Harness evaluates `extract(view, s_inferencer)` — the token window the model will see. This is the comonadic extraction. The model doesn't see `budget`, doesn't see `permission config` internals, doesn't see the raw `Conv_State` structure. It sees a flat token sequence. The *ma* between the Harness's view and the Inferencer's view (the information gap) is by design.

**2. The Inferencer performs inference (opaque).**

The model receives `extract(view, s_inferencer)` — a `FocusedView`. Internally, it performs attention, sampling, chain-of-thought. This is the actor's internal *ma* (Section 13) — high, intrinsic, requires the weights to describe. From outside, we see only the output.

**3. The Inferencer proposes a Kleisli morphism (Section 6).**

The model's output is a tool call proposal:

```
propose : FocusedView → ToolCall
propose(view) = Read("src/main.py")
```

In the Kleisli category: this is a morphism `FocusedView → ToolCall × M*` — the model produces a tool call and appends its reasoning to the log. The tool call is a *request* — it hasn't been executed or authorized yet.

**4. The Harness gates the injection (Sections 12.7 and 15.1).**

The Harness receives the proposal and performs:

```
harness_step(conv_state) = Gate(Read("src/main.py"), decision)
```

It checks the permission configuration: `Read` is auto-allowed for all paths within `allowed_directories`. The decision is `Grant`. No Principal synchronization needed. In the session type (Section 15.1), this is the `AutoAllow` branch: `Propose → CheckPermission → Execute → Result → ToolResult`. The Principal's channel is never opened.

This is **co-domain management** (Section 12.8). The `Read` tool's co-domain (`Either(String, Error)`) is about to be injected into the conversation. The permission gate controls *which* co-domain injections are allowed. If the model had proposed `Bash("rm -rf /")`, the session type would take the `Ask` branch — the Harness would render the proposal for the Principal, who might deny, preventing that Executor's wider co-domain from entering the conversation.

**5. The Executor runs in its world (Section 11.4).**

The `Read` tool executes:

```
Read : FilePath → IO_sandbox(Either(String, Error))
Read("src/main.py") = Right("import sys\ndef main(): ...")
```

The Executor inhabits `IO_sandbox` — not `IO_filesystem`, because `allowed_directories` restricts it. It can read files in the project root but not `/etc/passwd`. The Harness chose this world (Prop. 14.3). The Executor's interface *ma* is low: `Either(String, Error)` is trivially characterizable.

**6. The Harness performs monadic injection (Section 12.1).**

The result enters the conversation through `bind`:

```
bind(conv_state, λ_. (file_contents, [tool_result_message]))
```

The log grows: `conv_state.history` now includes the tool result. The budget decreases by the token cost of the result. The co-domain has expanded — the conversation now contains information about `src/main.py` that it didn't have before.

**7. The Harness reconstructs the Store and extracts again.**

The stored function `view` has changed — `conv_state` now includes the tool result, so `view(s_inferencer)` returns a longer token window. The Harness evaluates `extract(view', s_inferencer)` for the Inferencer's next turn. The cycle restarts.

**8. The Inferencer responds.**

The model sees the updated `FocusedView` (now including file contents) and produces a natural language summary. This is another Kleisli morphism: `FocusedView → Response × M*`. The response enters the conversation via `bind`. The Harness then extracts for the Principal: `extract(view'', s_render)` — the rendered markdown the user sees in their terminal.

### What the formalism reveals

This is a routine interaction. But the formalism exposes structure that the interaction hides:

- The **Store comonad** makes precise that the model never sees `Conv_State` — it sees `extract`. The Harness could have compacted history, loaded different tools, or changed the system prompt, and the model would have no way to tell. The comonadic extraction is the Harness's primary lever.

- The **configuration lattice** (Section 12.8) shows why this works: the Inferencer's configuration is `(s_inferencer, {Read, Edit, Write, ...})`. The `Read` tool's co-domain (`Either(String, Error)`) is part of the conversation's co-domain because `Read ∈ T`. If the Harness had configured `T = {Grep, Glob}` (no `Read`), the model couldn't have proposed this tool call — the co-domain would be narrower.

- The **permission gate** is co-domain management in action. Auto-allow for `Read` means the Harness pre-authorizes this co-domain injection. Ask-mode for `Bash` means the Principal must authorize that wider co-domain. The gate is where *ma* meets authorization.

- The **Executor's world** (`IO_sandbox` vs `IO_filesystem`) is invisible to the Inferencer. The model proposes `Read("src/main.py")` without knowing whether the sandbox allows it. The Harness constructed the Executor's world; the Inferencer works within what the Harness provides.

- The **turn cycle** is `extract → infer → propose → gate → execute → inject → extract → ...`. Comonadic compression, opaque processing, monadic expansion, repeated. The Harness controls every boundary.

---

## 17. Design Principles Derived

The formalism isn't just descriptive — it generates actionable design rules.

### Principle 1: Ma determines role

The interface monad ordering (Section 11) gives a partial order on actors by co-domain characterizability. The architecture follows:

- **Most characterizable actor mediates.** The Harness's `HarnessAction` (Section 12.7) is a finite tagged union — enumerable given configuration. Put it at the hub.
- **Least characterizable actor authorizes.** The Principal's co-domain is `IO` — unbounded. Only it can make judgments from outside the system.
- **Medium-characterizability actor proposes.** The Inferencer's co-domain is `Distribution` — rich but bounded by the weights. It proposes; it doesn't decide.

*Design test*: if you're putting a language model at the hub of your orchestration (deciding which agents run, managing state), you're putting a high-*ma* actor where a low-*ma* actor should be. The system becomes harder to reason about — because the hub's behavior is harder to characterize.

### Principle 2: Interface *ma* and internal *ma* are independent levers

From Section 13: internal *ma* determines quality, interface *ma* determines auditability. These are independent design choices.

- **Restrict tools, not models.** An Opus model with `{Read, Approve, Reject}` has high internal *ma* (good reasoning) and low interface *ma* (characterizable output). A Haiku model with 50 tools has low internal *ma* and high interface *ma*. The first is a better auditor. The second is a riskier worker.
- **Funnels need high-internal, low-interface.** Quartermasters, auditors, and sub-agent boundaries should use capable models with constrained tool sets (Section 13.3). The quality of the restriction comes from internal *ma*; the auditability comes from interface *ma*.

*Design test*: can you describe the set of possible outputs from each actor in a sentence? If not, its interface *ma* is too high for its role.

### Principle 3: Restriction ceiling > model ceiling

From Section 12.8 and the worked example: the Harness's configuration choices (scope + tools) bound the conversation's co-domain. The model works *within* those bounds.

- **Improving the comonadic extraction has more leverage than improving the model.** The LangChain result (same model, better harness, 52.8% → 66.5%) is a restriction story. Better scope construction, better tool selection, better co-domain management.
- **Tool restriction is the primary driver; scope restriction is secondary.** Removing a tool removes its entire co-domain from the conversation. Narrowing scope focuses attention but doesn't bound output type.

*Design test*: before upgrading the model, ask whether the current model is bottlenecked by its capability (internal *ma*) or by what it's being given to work with (the Harness's extraction). Usually it's the extraction.

### Principle 4: The Harness constructs worlds, not just scopes

From Sections 11.4 and 14.3: the Harness determines not only what the Inferencer sees but what world the Executor inhabits.

- **`allowed_directories` is co-domain management.** Setting `IO_sandbox` vs `IO_filesystem` determines the Executor's output space. This isn't just security — it's architecture.
- **Permission modes are co-domain gates.** Auto-allow widens the co-domain preemptively. Ask-mode makes the Principal a co-domain gate. Deny removes a co-domain entirely.

*Design test*: for each Executor, can you name the world (`IO_W`) it inhabits? If it's `IO_full` and it doesn't need to be, you're paying a *ma* tax — the system's co-domain is wider than necessary.

### Principle 5: Every turn is extract → process → inject

From Section 12.3 and the worked example: the turn cycle is comonadic compression, opaque processing, monadic expansion.

- **Optimize extract first.** What the actor sees determines the quality ceiling. A perfect model with a bad extraction (too much irrelevant context, missing key information) will produce poor results.
- **Gate inject carefully.** Every tool result widens the conversation's co-domain permanently (the log is append-only). Permission gates aren't just security — they're co-domain management. Each grant is irreversible within the object level.
- **The Harness controls both boundaries.** If your architecture gives an actor control over its own extraction or injection, you've moved a Harness responsibility to a higher-*ma* actor. The system becomes harder to reason about.

---

## 18. What This Formalization Shows

### Claims from the series, assessed:

**"Agents are closures."** *Partially formalized.* Agent closures (Def. 5.2) correspond to PL closures with one structural difference: monotonically growing capture vs. static capture (Prop. 5.3). This monotonicity holds at the object level (Section 10) but can be violated by meta-level operations like compaction. "Structural correspondence with a characterized divergence" — not identity, but precise enough to be a design guide.

**"The conversation is the shared heap."** *Formalized.* The log monoid (Def. 1.2) serves as a shared, append-only store. Scopes (Def. 2.1) determine visibility. Clean.

**"Handoffs are continuations."** *Formalized.* Agent handoffs are Kleisli composition (Prop. 6.2). Tool requests with resume callbacks are continuations in the technical sense (Def. 9.2). The cleanest part of the formalization.

**"Ma determines role."** *Formalized.* The interface monad ordering (Section 11) gives a partial order on actors by co-domain characterizability. The four-actor taxonomy (Executor/Harness/Inferencer/Principal) corresponds to positions on this ordering (Def. 11.1). The claim that *ma* determines role — the most characterizable actor mediates, the least characterizable authorizes — is now grounded in the monad ordering rather than informal intuition.

**"Restriction is load-bearing."** *Formalized via duality.* The monad-comonad duality (Section 12) identifies expansion as monadic (`bind`) and compression as comonadic (`extract`). The Harness lives at the boundary (Prop. 12.3). Co-domain funnels (Def. 13.5) formalize the pattern where internal *ma* is high but interface *ma* is low — the monad morphism from implementation to interface is the funnel.

**"The architecture is self-similar."** *Formalized.* The fractal architecture (Section 14) identifies the `extract → process → inject` cycle at every level of nesting. The interface between levels is a monad morphism (Prop. 14.2). The Executor's world lattice (Prop. 14.3) shows that the Harness constructs not just the Inferencer's scope but the Executor's world.

**"Determinism is a context window of size one."** *Formalized.* The co-domain gradient (Def. 11.1) gives a partial order on monads. The blog post's claim is that this ordering is a continuum. The formalization shows it's a partial order (not total — some effects are incomparable) with monad morphisms between adjacent levels (Prop. 11.4). The "dial" metaphor is valid along the co-domain complexity axis.

**"The quartermaster constructs capture lists."** *Formalized.* The quartermaster is a Kleisli morphism that produces a scope (Def. 8.1). The factorization through Kit (Prop. 8.3) is standard. The new contribution: the quartermaster is a co-domain funnel (Section 13.3) — it uses internal *ma* to restrict interface *ma* for the worker.

**"Permissions are co-domain management."** *Formalized.* The tool-use session type (Def. 15.1) makes this structural: each branch (`AutoAllow`, `Ask → Grant`, `Ask → Deny`, `AutoDeny`) has a different co-domain effect (Prop. 15.2). Permission grants are scope extrusion events in the π-calculus (Section 15.4). The permission configuration is a function from tool calls to session type branches — the Harness's static co-domain management policy.

### What might be novel:

1. ***Ma* as co-domain characterizability on the monad ordering** (Section 11). The single axis that explains all four actor roles, grounded in a partial order on monads via monad morphisms. This connects informal design intuitions ("put the deterministic thing at the hub") to sixty years of PL theory.

2. **The monad-comonad duality for agent architecture** (Section 12). Expansion is monadic, compression is comonadic, the Harness lives at the boundary. This is a new application of a known duality to a new domain.

3. **Interface *ma* vs. internal *ma*** (Section 13). The distinction between co-domain characterizability at the interface and at the implementation level, formalized as a monad morphism between implementation and interface monads. The independence of quality (internal) and auditability (interface) is architecturally significant.

4. **Co-domain funnels as monad morphisms** (Section 13.3). The quartermaster, auditor, and sub-agent boundary as instances of a single pattern: rich implementation monad mapped to constrained interface monad.

5. **Fractal/self-similar architecture** (Section 14). Every actor has internal conversation architecture. The interface is a monad morphism from implementation level to interface level. The `extract → process → inject` cycle repeats at every scale.

6. **Parameterized IO for Executor worlds** (Section 11.4). The Harness doesn't just construct the Inferencer's scope — it constructs the Executor's *world*. The permission lattice is a lattice of worlds.

7. **The configuration lattice** (Section 12.8). The scope lattice (comonadic, input restriction) and the tool powerset (monadic, co-domain restriction) meet in a product lattice navigated by the Harness. Tool restriction is the primary driver of co-domain narrowing; scope restriction is secondary. This connects the two halves of the formalism.

8. **The graded monad construction for scoped agents** (Section 7). Graded monads are known (Katsumata, 2014; Orchard et al., 2019) but applying them with a *scope lattice* as the grading monoid for multi-agent conversation appears to be new.

9. **Permission protocol as a session type with co-domain effects** (Section 15). Each branch of the tool-use protocol has a formal co-domain effect (widen or narrow). Permission grants are scope extrusion events. The session type makes structural what the monadic framework leaves narrative.

10. **Parallel tool execution in π-calculus** (Section 15.3). Private result channels, concurrent execution with name restriction, and the barrier/promise distinction. The connection between π-calculus name restriction and the scope lattice.

11. **The two-level structure** (Section 10). Object-level (monadic, monotone) and meta-level (endomorphisms on `Conv_State`, possibly lossy) operations. The Harness straddles both levels.

12. **Budget as a linear resource** (Section 10.3). Context window as a finite resource, connecting to quantitative type theory and resource-sensitive logic.

### What needs further work:

1. **The distributive law between conversation monad and scope comonad** (Conjecture 12.4). This would formalize how expansion and compression compose within a single turn. Known territory (Brookes & Geva, Uustalu & Vene) but the specific instance is open.

2. **Monad morphisms for inter-enclave sanitization.** A monad morphism preserves sequential composition. If sanitization is structure-preserving, it's a monad morphism. The temporal accumulation issue (Part 3) suggests it may not be — sanitization decisions depend on channel history, which breaks compositionality. This needs a weaker structure, possibly Galois connections.

3. **The meta-level's algebraic structure.** Section 10 identifies meta-operations as endomorphisms on `Conv_State` but doesn't formalize their composition laws. The endomorphism monoid has structure worth characterizing.

4. **The graded monad needs mid-computation scope change.** Definition 7.1 assigns a fixed scope. In practice, scopes expand (tool requests). The two-level structure handles this at the meta level, but a unified treatment would be cleaner.

5. **Compaction as a comonadic morphism.** Does lossy summarization preserve comonadic structure? If `compact(A then B) ≠ compact(A) then compact(B)`, compaction isn't structure-preserving. It might be a Galois connection (abstract interpretation) rather than a morphism.

6. **The `Writer`-`Store` distributive law.** Section 12 identifies `Store Scope FocusedView` as the conversation comonad and `Writer M*` as the conversation monad. Does a distributive law exist between them? This would give the formal structure of a full turn (extraction composed with injection).

7. **The relationship between `/memory` and the conversation monad.** The inverted transformer stack (persistent State outlives ephemeral Writer) needs formal treatment. The interaction pattern looks like a monad morphism between conversation and persistence monads.

8. **Promises and backgrounded tasks** (Section 15.6). The synchronous protocol is formalized; the asynchronous extension (futures, deferred injection, the Harness controlling interleaving of concurrent streams) is deferred. This likely requires the distributive law from Conjecture 12.4 or something stronger.

9. **Mechanical verification.** None of this has been verified in Coq or Agda.

---

## References

- Atkey, R. (2009). Parameterised notions of computation. *Journal of Functional Programming*, 19(3-4).
- Atkey, R. (2018). Syntax and semantics of quantitative type theory. *LICS*.
- Brookes, S., & Geva, S. (1992). Computational comonads and intensional semantics. *Applications of Categories in Computer Science*, London Mathematical Society Lecture Notes 177.
- Fowler, M. (2025). Harness engineering. *martinfowler.com*.
- Honda, K. (1993). Types for dyadic interaction. *CONCUR*.
- Honda, K., Yoshida, N., & Carbone, M. (2008). Multiparty asynchronous session types. *POPL*.
- Hewitt, C., Bishop, P., & Steiger, R. (1973). A universal modular ACTOR formalism for artificial intelligence. *IJCAI*.
- Katsumata, S. (2014). Parametric effect monads and semantics of effect systems. *POPL*.
- McBride, C. (2016). I got plenty o' nuttin'. *A List of Successes That Can Change the World*, LNCS 9600.
- Milner, R. (1999). *Communicating and Mobile Systems: The Pi-Calculus*. Cambridge University Press.
- Moggi, E. (1991). Notions of computation and monads. *Information and Computation*, 93(1).
- Orchard, D., Wadler, P., & Eades, H. (2019). Unifying graded and parameterised monads. *arXiv:1907.10276*.
- Parnas, D. L. (1972). On the criteria to be used in decomposing systems into modules. *Communications of the ACM*, 15(12).
- Uustalu, T., & Vene, V. (2008). Comonadic notions of computation. *ENTCS*, 203(5).
- Zhang, H., & Wang, M. (2025). Monadic context engineering for LLM agents. *arXiv:2512.22431*.
