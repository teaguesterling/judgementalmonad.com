# The Anatomy of a Turn

*Working notes — a concrete model of what actually happens in a conversation turn, grounded in how Claude Code works.*

---

## The Participants

Every conversation has (at least) three agents. Not metaphorical — three actual participants with distinct scopes, capabilities, and agency.

### The Principal (User)

- **Scope**: The physical world. Their expertise, their project, their intent. Everything they know that isn't in the log.
- **Capabilities**: Provides goals. Grants/denies permissions. Backgrounds tasks. Reads and writes natural language.
- **What's invisible**: The model's system prompt. The Harness's internal state (token counts, compaction decisions). Tool implementation details.
- **Inference**: Internal, invisible. The user thinks, then types. The thinking is *ma*.
- ***Ma***: Constitutive — co-domain is essentially unbounded. The Principal can say, paste, or decide anything.

### The Harness (client/orchestrator)

- **Scope**: `Conv_State` — the structured conversation. Token counts, tool registry, permission configuration, MCP server connections, budget, backgrounded task handles.
- **Capabilities**: Mediates all communication. Manages permissions. Loads/unloads tools. Compacts history. Injects backgrounded results. Renders output. The only participant that talks to everyone. Controls which Executor co-domains compose into the conversation.
- **What's invisible**: The Principal's physical state. The Inferencer's internal weights and inference process. The actual content of tool execution (it sees inputs and outputs, not internals).
- **Inference**: Programmatic. Rules, not neural. But still decision-making: *when* to compact, *how* to render, *whether* to batch permission prompts.
- ***Ma***: Minimal — co-domain is characterizable by its rules. This is *why* it works at the hub.

### The Inferencer (Model)

- **Scope**: The token window — the flattened, filtered conversation as a token sequence. System prompt, instructions, conversation history (possibly compacted), tool descriptions, recent tool results.
- **Capabilities**: Inference. Proposes tool calls. Generates text. Can request multiple tools in parallel.
- **What's invisible**: Conv_State metadata (token counts, budget remaining). Permission configuration. MCP server topology. The Principal's physical world. Its own weights.
- **Inference**: Neural, internal, invisible to other participants. The model "thinks" then "responds." The thinking is *ma*.
- ***Ma***: Intrinsic — co-domain requires the weights to describe. The model IS the co-domain characterization.

### Executors (Tools)

- **Scope**: Their inputs (arguments) plus their sandbox (filesystem access, network access, etc.).
- **Capabilities**: Narrow and specific. `Read` reads a file. `Bash` executes a command. An MCP tool calls an external service.
- **What's invisible**: Everything outside their inputs and sandbox. The conversation context. The Inferencer's intent. Other tool calls.
- **Inference**: Typically none (pure computation). But MCP tools can be backed by LLMs, and subagents *are* tools with full inference loops. The boundary between "tool" and "agent" is a spectrum.
- ***Ma***: Borrowed — co-domain complexity comes from the world (filesystem, network), not the actor.

**Key observation**: The Harness is the only participant that communicates with all others. The Principal and Inferencer never interact directly — the Harness mediates. Executors never talk to the Principal — the Harness mediates. This star topology, with the Harness at the center, is the actual architecture.

```
      Principal
         ↕
       Harness ←→ Executor₁
         ↕     ←→ Executor₂
     Inferencer ←→ Executor₃
```

---

## The Turn Structure

A single conversation turn, fully expanded:

### Phase 1: Inference (Inferencer, internal)

The Inferencer reads its scoped view of the conversation — the token window the Harness constructed. It performs inference. This is invisible to all other participants. It produces a response: text and/or tool call proposals.

**In the framework**: This is the intrinsic *ma* of the Inferencer. The inference process is the complementary scope — it's what happens that nobody else sees. The output (text + tool proposals) is what enters the log.

### Phase 2: Proposal (Inferencer → Harness)

The Inferencer's response reaches the Harness. If it contains tool calls, each one is a **proposal**: "I want to use tool X with arguments Y."

Multiple proposals can be batched — the Inferencer can propose N tool calls in a single response. These are independent: no proposal depends on another's result.

**In the framework**: Each proposal is a request for a capability — visibility (the tool exists) is already established, but authorization (permission to use it) must be checked.

### Phase 3: Permission Gate (Harness ↔ Principal)

For each proposal, the Harness checks the permission configuration:

- **Auto-allow**: No Principal interaction. The Harness authorizes immediately.
- **Auto-deny**: No Principal interaction. The Harness rejects immediately.
- **Ask**: The Harness renders the proposal for the Principal. The Principal evaluates and decides. This is a **synchronization point** between Harness and Principal.

For batched proposals, the Harness may batch the permission prompts: "The agent wants to do A, B, and C. Allow all?"

**In the framework**: This is the protocol layer. It's not a monadic operation — it's a communication between the Harness and Principal that determines whether a state transition (scope expansion) is authorized. The Principal's decision is informed by the chain: tool availability → Inferencer's intent → Harness's rendering → Principal's judgment. This is also **co-domain management**: each permission grant widens the conversation's output space by allowing an Executor's co-domain to compose in.

**The rejected-then-approved pattern**: The Inferencer proposes tool X, the Principal denies. The Inferencer adjusts its approach, perhaps reproposing with different arguments or a different tool. Later, the Principal approves. What changed? Not the permission configuration (necessarily) — the Principal made a different judgment on a different invocation. The authorization landscape is not just stateful but *contextual*: the same tool with different arguments can get different decisions.

### Phase 4: Execution (Harness → Executors, parallel)

Approved Executors run. The Harness dispatches them — potentially in parallel. Each Executor runs in its own scope (its inputs + sandbox). Execution is concurrent and independent.

**In the framework**: Each Executor invocation is a mini-agent computation: `Executor(args) → Result × Log`. The Executors don't see each other. They don't see the conversation. They see their arguments and their sandbox. The Harness collects the results. Each result injects the Executor's world-dependent co-domain into the conversation.

**Subagents are Executors with inference**: A subagent call spawns a nested conversation — the subagent has its own Harness and turn loop (inference → propose → gate → execute → collect). The parent Inferencer doesn't see the subagent's internal turns. Only the final result (and maybe a summary) propagates back. The subagent's internal conversation is *ma* from the parent's perspective — the Executor interface compresses the sub-agent's co-domain.

### Phase 5: Collection — Barrier or Promise

Here's where the user's observation changes the model.

**Barrier collection (default)**: The Harness waits for all Executor invocations to complete. Results are collected. The Harness appends them to the log. The Inferencer's next step sees all results. This is synchronous: propose → wait → receive → next turn.

**Promise collection (backgrounded)**: The Principal or Inferencer indicates that a task should be backgrounded. The Harness doesn't wait. Instead:

1. The Harness creates a **promise handle** — a reference to the in-progress work.
2. The conversation continues. The Inferencer begins its next step without the backgrounded result.
3. At some later point, the backgrounded task completes.
4. The **Harness decides when and how** to inject the result into the conversation.

This is crucial: the Harness has agency over *when* the promise resolves into the log. It might:
- Inject immediately at the next turn boundary
- Wait until the Inferencer is idle
- Wait until the result is relevant to the current discussion
- Batch multiple resolved promises together
- Summarize or compact the result before injection

The Harness is not a dumb promise scheduler. It's an actor making decisions about when to introduce new information — and therefore when to expand the conversation's co-domain. This is the Harness's most consequential role: it controls not just *what* enters the Inferencer's scope but *when*.

**What this means structurally**: The log is no longer strictly alternating turns. The Harness can inject content at turn boundaries, making the log a merge of multiple concurrent streams:

```
Log = Inferencer turns ⊕ Executor results ⊕ Harness injections ⊕ Principal messages
```

These streams are ordered *within* each source but interleaved *across* sources. The Harness controls the interleaving. The Inferencer sees whatever ordering the Harness presents in the token window.

### Phase 6: Append

Results (immediate or resolved promises) are appended to the log. The conversation state advances. The Harness may also perform meta-operations at this point: compaction if budget is low, tool set changes, permission updates.

### Phase 7: Scope Reconstruction

Before the next inference step, the Harness reconstructs the Inferencer's scope:
- Apply compaction if needed (lossy — budget reclamation)
- Filter through the Inferencer's visibility rules
- Flatten Conv_State into the token window
- Include or exclude backgrounded task status

This is the Harness acting as scope constructor — it builds the capture list for the Inferencer's next closure.

→ Back to Phase 1.

---

## Parallel Tool Calls, Formally

When the Inferencer proposes N tool calls in one response:

```
Propose: {tool₁(args₁), tool₂(args₂), ..., toolₙ(argsₙ)}
```

The Harness processes these as:

```
Gate:    perm₁ = check(tool₁), perm₂ = check(tool₂), ..., permₙ = check(toolₙ)
         (may involve Principal synchronization for "ask" permissions)

Execute: for each permᵢ = granted:
           resultᵢ = toolᵢ(argsᵢ)    -- concurrent
         for each permᵢ = denied:
           resultᵢ = PermissionError  -- immediate

Collect: barrier — wait for all resultᵢ
         OR promise — continue, inject later
```

Each tool execution is independent — they don't share scope, they can't see each other's results. They're parallel computations over disjoint scopes that merge results into the shared log.

In π-calculus terms:

```
(ν r₁)(ν r₂)...(ν rₙ)(
    tool₁(args₁, r₁) | tool₂(args₂, r₂) | ... | toolₙ(argsₙ, rₙ)
  | r₁(res₁).r₂(res₂)...rₙ(resₙ).continue(res₁, res₂, ..., resₙ)
)
```

Each tool gets a private result channel `rᵢ`. The continuation waits for all results (barrier) before proceeding. The channels are restricted — only the tool and the collector can use them.

For the promise variant, replace the barrier with:

```
  | r₁(res₁).inject(res₁) | r₂(res₂).inject(res₂) | ... | continue()
```

Each result is injected independently when it arrives. The continuation doesn't wait.

---

## Authorization as a Separate Structure

Pulling together the earlier observations: there are three independent axes.

**Visibility** — what exists in the agent's scope.
- Determined by: tool registry, MCP connections, Conv_State filtering
- Changed by: tool loading/unloading, MCP server reload, compaction
- Structure: scope lattice (monotone within a phase, can change at meta-level boundaries)

**Authorization** — what the agent is *permitted* to do.
- Determined by: permission configuration (auto/ask/deny per tool), allowed_directories, sandbox rules
- Changed by: Principal decisions, permission mode changes, configuration updates
- Structure: a **protocol** between Harness and Principal, not a static lattice. Context-dependent (same tool, different args → different decision).

**Capability** — what the agent can *actually do right now*.
- Capability = Visibility ∧ Authorization
- This is what the "scope" in the graded monad should actually track

The current framework models Visibility (scope lattice) but not Authorization (permission protocol). The permission protocol is where session types would contribute:

```
type ToolUseProtocol =
    Inferencer → Harness   : Propose(tool, args)
  ; Harness    → Principal : PermissionCheck(tool, args)    -- only if mode = "ask"
  ; Principal  → Harness   : Grant | Deny
  ; if Grant:
      Harness  → Executor  : Execute(args)
    ; Executor → Harness   : Result(output)
    ; Harness  → Inferencer: ToolResult(output)
  ; if Deny:
      Harness  → Inferencer: PermissionDenied(tool, reason)
```

This protocol composes: N parallel tool calls are N parallel instances of this protocol, with the barrier/promise collection as the synchronization strategy.

---

## Where the Existing Framework Applies

| Turn Phase | Framework Section | Status |
|---|---|---|
| Inference (Inferencer internal) | *ma* as co-domain complexity | Clean — intrinsic *ma* |
| Proposal (tool calls) | Kleisli morphisms (Section 6) | Clean — effectful functions |
| Permission gate | **Not modeled** | Needs session types or protocol model |
| Tool execution | Parameterized monad (scope-transitions.md) | Partially — Executors are degenerate agents |
| Barrier collection | Kleisli composition | Clean — sequential |
| Promise collection | **Not modeled** | Needs futures/promises in the monad |
| Harness meta-operations | Section 10 (two-level structure) | Partially — endomorphisms on Conv_State |
| Scope reconstruction | Scope lattice + graded monad (Section 7) | Clean |

### Gaps

1. **The permission protocol** — cross-level negotiation between Harness and Principal. Session types. This is also co-domain management: each grant widens the conversation's output space.
2. **Promise/future injection** — backgrounded tasks that resolve later. The log becomes a merge of concurrent streams. The Harness controls the interleaving.
3. **The Harness as formal actor** — it has scope, makes decisions, and its decisions affect the other actors' scopes. The framework now treats it as a participant with minimal *ma* (see [Actor Taxonomy](actor-taxonomy.md)), but the formal monad structure needs to account for the Harness's agency over scope construction and co-domain management.
4. **Authorization as a dynamic, contextual property** — not a static lattice. The same tool can be authorized or denied depending on arguments, conversation state, and Principal judgment.
5. **The tool-agent spectrum** — Executors, subagents, and the Inferencer are all actors with different co-domain complexity. The *ma* framework provides the unifying axis (see [Actor Taxonomy](actor-taxonomy.md)), but the formal monad treatment needs to be updated.

---

## What We're Converging On

The conversation monad (Writer over append-only log) is the easy part. It handles the data flow.

The interesting structure is in three other places:

1. **The protocol layer** — how participants negotiate authorization and coordinate. Session types.
2. **The concurrency model** — parallel tool execution, backgrounded tasks, promise resolution. π-calculus.
3. **The Harness's agency** — scope construction, compaction timing, promise injection, permission mediation, co-domain management. The Harness is the most powerful participant and the least modeled.

The monadic framework (graded/parameterized) handles the sequential, data-flow aspects well. But the conversation is fundamentally a **multi-party concurrent protocol with negotiated authorization**, and that's a different beast. The next step is to model the protocol layer — starting with the permission negotiation — and see how it composes with the existing monadic structure.

---

## Open Questions

- Is the Harness a monad transformer? It wraps every interaction between other participants. Every Inferencer ↔ Executor interaction goes through it. Every Principal ↔ Inferencer interaction goes through it. It *transforms* the underlying monads by adding mediation — and in doing so, it controls the co-domain composition.

- Are backgrounded tasks a free monad construction? A promise is "a computation that hasn't been evaluated yet" — which is exactly what the free monad provides: a description of a computation, separated from its execution.

- The Inferencer's step is a black box in this model. But it's also where the actual *thinking* happens. The framework models everything around inference but not inference itself. Is that the right boundary? The *ma* framework says yes: the Inferencer's intrinsic *ma* (uncharacterizable co-domain) is precisely the property we're choosing not to model. Modeling inference would mean characterizing the co-domain — which would reduce the *ma*.

- Subagent conversations are nested turn loops. How deep can this nest? Each level has its own Harness, its own co-domain management, its own *ma* budget. The Executor interface compresses the inner co-domain for the parent. Is the compression lossy in a formally characterizable way?
