# Toward a Formal Framework

*Part 4: What survives formalization, what doesn't, and where the open problems are.*

This document formalizes the structural claims from the series. Sections 1–10 formalize the conversation log, scopes, the conversation monad, and meta-operations. Sections 11–14 formalize the deeper structures developed in Part 3: the interface monad ordering, the monad-comonad duality, interface *ma* vs. internal *ma*, and the fractal architecture of actors. Section 15 assesses what's novel and what needs further work.

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

## 3. Ma: Scope Boundaries and Co-domain Characterizability

*Ma* has two faces. From the **visibility** side, it's the negative space between scopes — what each actor can't see. From the **output** side, it's the descriptive complexity of the actor's co-domain — how hard the output space is to characterize. Both are aspects of the same architectural property. The visibility side is formalized here; the output side in Section 11.

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

### 3.2 Co-domain characterizability (preview)

The complementary scope captures the *visibility* side of *ma*: what's hidden. But there is a second, deeper side: how hard it is to *describe the output space* of an actor.

**Definition 3.5 (Co-domain characterizability, informal).** For an actor `A` with interface type `I → O`, the *ma* of `A` is the descriptive complexity of `O` — the Kolmogorov complexity of a description of the set of possible outputs, given the interface typing.

A file-read tool's co-domain: "a string, or an error." Low *ma*. A deterministic Harness's co-domain: "enumerable given its rules and state." Low *ma*. A language model's co-domain: "requires the weights to describe." High *ma*. A human's co-domain: "requires the person to describe." Maximal *ma*.

**Remark.** This is *not* unpredictability (Shannon entropy of specific outputs). SHA-256 is unpredictable but its co-domain is trivially characterized ("uniform over 256-bit strings"). A temperature-0 LLM is deterministic for each input but its co-domain requires the weights. The distinction is between the complexity of *individual outputs* and the complexity of *the output space description*. The formal definition is developed in Section 11.

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

**Definition 12.1 (Scope comonad).** Define a comonad `W_s` over `Conv_State`, parameterized by a scope `s`:

    W_s(A) = Conv_State × A

where the `Conv_State` component is the full conversation and `A` is the focused extraction.

    extract_s : W_s(Conv_State) → FocusedView_s
    extract_s(state, _) = flatten(s(state))

    duplicate_s : W_s(A) → W_s(W_s(A))
    duplicate_s(state, a) = (state, (state, a))

    extend_s : (W_s(A) → B) → W_s(A) → W_s(B)
    extend_s(f)(state, a) = (state, f(state, a))

**Remark.** The `extract` function is the Harness's scope construction: it takes the full conversation state and projects it to a focused view (the token window for the Inferencer, the rendered output for the Principal, the arguments for the Executor). The Harness constructs a *different* extraction for each actor — multiple comonadic projections over the same underlying state.

### 12.3 The turn as comonadic extraction followed by monadic injection

**Proposition 12.2 (Turn structure).** A single turn has the structure:

    ConvState ──extract_s──→ FocusedView ──actor──→ Output ──bind──→ ConvState'

where:
- `extract_s` is comonadic (compression — narrowing the co-domain)
- `actor` is opaque internal processing (the actor's internal *ma*)
- `bind` is monadic (expansion — widening the co-domain)

This is the `read → infer → respond` cycle from Part 3, now formalized. Every turn is a comonad-to-monad bridge: compress, process, expand.

### 12.4 The Harness at the boundary

**Proposition 12.3 (The Harness mediates both structures).** The Harness performs:

| Operation | Structure | Effect on co-domain |
|---|---|---|
| Scope construction | Comonadic `extract` | Narrows (selects what actor sees) |
| Compaction | Comonadic `extract` (lossy) | Narrows (lossy summarization) |
| Tool dispatch | Monadic `bind` | Widens (result enters conversation) |
| Permission gate | Controls which `bind`s are allowed | Co-domain management |
| Promise injection | Deferred `bind` | Widens later |

The Harness is the actor that mediates between the comonad (how the conversation is projected to each actor) and the monad (how information enters the conversation). Its minimal *ma* — characterizable output space — is what makes it trustworthy in this role.

### 12.5 Distributive laws (open problem)

**Conjecture 12.4.** There exists a distributive law between the conversation monad and the scope comonad:

    λ : W(Conv(A)) → Conv(W(A))

This would tell us how extraction and injection compose — the formal structure of a full turn. Distributive laws between monads and comonads are studied by Brookes & Geva and Uustalu & Vene, but the specific instance for conversation state and scope extraction is an open problem.

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

## 15. What This Formalization Shows

### Claims from the series, assessed:

**"Agents are closures."** *Partially formalized.* Agent closures (Def. 5.2) correspond to PL closures with one structural difference: monotonically growing capture vs. static capture (Prop. 5.3). This monotonicity holds at the object level (Section 10) but can be violated by meta-level operations like compaction. "Structural correspondence with a characterized divergence" — not identity, but precise enough to be a design guide.

**"The conversation is the shared heap."** *Formalized.* The log monoid (Def. 1.2) serves as a shared, append-only store. Scopes (Def. 2.1) determine visibility. Clean.

**"Handoffs are continuations."** *Formalized.* Agent handoffs are Kleisli composition (Prop. 6.2). Tool requests with resume callbacks are continuations in the technical sense (Def. 9.2). The cleanest part of the formalization.

**"Ma determines role."** *Formalized.* The interface monad ordering (Section 11) gives a partial order on actors by co-domain characterizability. The four-actor taxonomy (Executor/Harness/Inferencer/Principal) corresponds to positions on this ordering (Def. 11.1). The claim that *ma* determines role — the most characterizable actor mediates, the least characterizable authorizes — is now grounded in the monad ordering rather than informal intuition.

**"Restriction is load-bearing."** *Formalized via duality.* The monad-comonad duality (Section 12) identifies expansion as monadic (`bind`) and compression as comonadic (`extract`). The Harness lives at the boundary (Prop. 12.3). Co-domain funnels (Def. 13.5) formalize the pattern where internal *ma* is high but interface *ma* is low — the monad morphism from implementation to interface is the funnel.

**"The architecture is self-similar."** *Formalized.* The fractal architecture (Section 14) identifies the `extract → process → inject` cycle at every level of nesting. The interface between levels is a monad morphism (Prop. 14.2). The Executor's world lattice (Prop. 14.3) shows that the Harness constructs not just the Inferencer's scope but the Executor's world.

**"Determinism is a context window of size one."** *Formalized.* The co-domain gradient (Def. 11.1) gives a partial order on monads. The blog post's claim is that this ordering is a continuum. The formalization shows it's a partial order (not total — some effects are incomparable) with monad morphisms between adjacent levels (Prop. 11.4). The "dial" metaphor is valid along the co-domain complexity axis.

**"The quartermaster constructs capture lists."** *Formalized.* The quartermaster is a Kleisli morphism that produces a scope (Def. 8.1). The factorization through Kit (Prop. 8.3) is standard. The new contribution: the quartermaster is a co-domain funnel (Section 13.3) — it uses internal *ma* to restrict interface *ma* for the worker.

### What might be novel:

1. ***Ma* as co-domain characterizability on the monad ordering** (Section 11). The single axis that explains all four actor roles, grounded in a partial order on monads via monad morphisms. This connects informal design intuitions ("put the deterministic thing at the hub") to sixty years of PL theory.

2. **The monad-comonad duality for agent architecture** (Section 12). Expansion is monadic, compression is comonadic, the Harness lives at the boundary. This is a new application of a known duality to a new domain.

3. **Interface *ma* vs. internal *ma*** (Section 13). The distinction between co-domain characterizability at the interface and at the implementation level, formalized as a monad morphism between implementation and interface monads. The independence of quality (internal) and auditability (interface) is architecturally significant.

4. **Co-domain funnels as monad morphisms** (Section 13.3). The quartermaster, auditor, and sub-agent boundary as instances of a single pattern: rich implementation monad mapped to constrained interface monad.

5. **Fractal/self-similar architecture** (Section 14). Every actor has internal conversation architecture. The interface is a monad morphism from implementation level to interface level. The `extract → process → inject` cycle repeats at every scale.

6. **Parameterized IO for Executor worlds** (Section 11.4). The Harness doesn't just construct the Inferencer's scope — it constructs the Executor's *world*. The permission lattice is a lattice of worlds.

7. **The graded monad construction for scoped agents** (Section 7). Graded monads are known (Katsumata, 2014; Orchard et al., 2019) but applying them with a *scope lattice* as the grading monoid for multi-agent conversation appears to be new.

8. **Scope renegotiation as scope extrusion** (Section 9). The connection between tool requests and π-calculus scope extrusion.

9. **The two-level structure** (Section 10). Object-level (monadic, monotone) and meta-level (endomorphisms on `Conv_State`, possibly lossy) operations. The Harness straddles both levels.

10. **Budget as a linear resource** (Section 10.3). Context window as a finite resource, connecting to quantitative type theory and resource-sensitive logic.

### What needs further work:

1. **The distributive law between conversation monad and scope comonad** (Conjecture 12.4). This would formalize how expansion and compression compose within a single turn. Known territory (Brookes & Geva, Uustalu & Vene) but the specific instance is open.

2. **Monad morphisms for inter-enclave sanitization.** A monad morphism preserves sequential composition. If sanitization is structure-preserving, it's a monad morphism. The temporal accumulation issue (Part 3) suggests it may not be — sanitization decisions depend on channel history, which breaks compositionality. This needs a weaker structure, possibly Galois connections.

3. **The meta-level's algebraic structure.** Section 10 identifies meta-operations as endomorphisms on `Conv_State` but doesn't formalize their composition laws. The endomorphism monoid has structure worth characterizing.

4. **The graded monad needs mid-computation scope change.** Definition 7.1 assigns a fixed scope. In practice, scopes expand (tool requests). The two-level structure handles this at the meta level, but a unified treatment would be cleaner.

5. **Compaction as a comonadic morphism.** Does lossy summarization preserve comonadic structure? If `compact(A then B) ≠ compact(A) then compact(B)`, compaction isn't structure-preserving. It might be a Galois connection (abstract interpretation) rather than a morphism.

6. **The right comonad.** The `Store` comonad (focused position), the `Env` comonad (read-only environment), and `Cofree` (annotated trees) are all candidates. The conversation might be `Cofree` over the message type.

7. **The relationship between `/memory` and the conversation monad.** The inverted transformer stack (persistent State outlives ephemeral Writer) needs formal treatment. The interaction pattern looks like a monad morphism between conversation and persistence monads.

8. **Mechanical verification.** None of this has been verified in Coq or Agda.

---

## References

- Atkey, R. (2009). Parameterised notions of computation. *Journal of Functional Programming*, 19(3-4).
- Atkey, R. (2018). Syntax and semantics of quantitative type theory. *LICS*.
- Brookes, S., & Geva, S. (1992). Computational comonads and intensional semantics. *Applications of Categories in Computer Science*, London Mathematical Society Lecture Notes 177.
- Fowler, M. (2025). Harness engineering. *martinfowler.com*.
- Hewitt, C., Bishop, P., & Steiger, R. (1973). A universal modular ACTOR formalism for artificial intelligence. *IJCAI*.
- Katsumata, S. (2014). Parametric effect monads and semantics of effect systems. *POPL*.
- McBride, C. (2016). I got plenty o' nuttin'. *A List of Successes That Can Change the World*, LNCS 9600.
- Milner, R. (1999). *Communicating and Mobile Systems: The Pi-Calculus*. Cambridge University Press.
- Moggi, E. (1991). Notions of computation and monads. *Information and Computation*, 93(1).
- Orchard, D., Wadler, P., & Eades, H. (2019). Unifying graded and parameterised monads. *arXiv:1907.10276*.
- Parnas, D. L. (1972). On the criteria to be used in decomposing systems into modules. *Communications of the ACM*, 15(12).
- Uustalu, T., & Vene, V. (2008). Comonadic notions of computation. *ENTCS*, 203(5).
- Zhang, H., & Wang, M. (2025). Monadic context engineering for LLM agents. *arXiv:2512.22431*.
