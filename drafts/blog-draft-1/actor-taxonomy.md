# Actor Taxonomy

*Formal definitions of the participant types in the conversation framework.*

---

## Preamble: Why "Actor"

We use "actor" in the sense of Hewitt (1973): an entity with private state that communicates via message passing. This is more precise than "agent" (which implies inference) and more general than "process" (which implies a specific computational model). Every participant in a conversation — human, model, tool, orchestrator — is an actor with a scope, capabilities, and communication channels.

---

## The Central Axis: *Ma*

*Ma* (間) — the space between what an actor receives and what it produces. Every actor has inputs and outputs. Between them is a space: the space where processing happens, where decisions are made. *Ma* is this space — shaped by restriction, filled by the actor's decision surface, measured by characterizability.

A SHA-256 hash is unpredictable (you can't guess which hash), but the space between input and output is trivially characterized: "a uniform mapping." Low *ma*. A temperature-0 LLM is technically deterministic, but the space between its input and output is the entire weight manifold — billions of pathways that could have gone differently. High *ma*. A human's space is a lifetime of accumulated structure, all active at runtime. Maximal *ma*.

Three things determine an actor's *ma*:

- **World coupling** — what can enter the space at runtime (the input boundary)
- **Decision surface** — what fills the space (the internal structure that inputs can influence)
- **Interface restriction** — what can exit the space (the output boundary, shaped by tools and co-domain constraints)

Not unpredictability (SHA is unpredictable, low *ma*). Not hidden state (lookup table has vast state, low *ma*). Not variability (random die has six outcomes, low *ma*). *Ma* is the *space between* — how much room exists between receiving and producing, and how hard that room is to characterize.

### Properties that correlate with *ma*

These are not definitions of *ma* — they are consequences that tend to co-occur with high co-domain complexity:

| Property | How it relates to co-domain complexity |
|---|---|
| **Hidden state** | Rich internals are needed to *generate* a rich output space — but a lookup table has vast hidden state and low *ma* |
| **Output variability** | More possible outputs means a wider co-domain — but a die has high variability and low *ma* (trivially characterized) |
| **Judgment quality** | Uncharacterizable output spaces enable decisions no specification anticipated — that's what judgment *is* |
| **Predictability** | Harder to characterize → harder to predict — but the converse doesn't hold (SHA is unpredictable, low *ma*) |
| **Identity** | When describing the co-domain requires describing the actor, behavior becomes constitutive |

These cluster in practice: neural inference has both rich hidden state and a vast output space; human cognition has both. But the clustering is empirical, not definitional. *Ma* is one thing — co-domain characterizability — and the other properties are its correlates.

### *Ma* determines role

The role an actor naturally plays in a conversation is a consequence of its *ma*:

```
borrowed ma ——→ minimal ma ——→ intrinsic ma ——→ constitutive ma
   |                |               |                  |
   ↓                ↓               ↓                  ↓
 execute         connect          propose            authorize
(characterizable (characterizable (rich but         (judgment from
 given interface) by rules)        bounded)          uncharacterizable
                                                     output space)
```

- You put the **low-*ma*** actor at the hub because other actors need to *reason about* what the hub will do. That requires a characterizable output space.
- You put the **high-*ma*** actor at the authorization boundary because authorization requires decisions from an uncharacterizable output space — that's what makes them judgment calls rather than rule applications.
- You constrain the **medium-*ma*** actor to proposing because its output space is rich enough to generate novel solutions but too complex for other actors to fully verify.
- You sandbox the **borrowed-*ma*** actor because its co-domain complexity comes from the world, not from the actor — and the world's complexity should be contained.

The conversation topology — who talks to whom, who mediates, who authorizes — follows from the *ma* structure. Architecture is a consequence of co-domain complexity.

### The co-domain gradient

*Ma* connects to the monadic continuum — each level represents a wider, harder-to-characterize output space:

| Level | Co-domain | What expands it |
|---|---|---|
| Pure function | Single point per input | Nothing — fully determined |
| Effectful function (program) | One point per world-state | External state (fs, clock, network) |
| Temperature > 0 (inference) | Weighted distribution over outputs | Sampling / internal non-determinism |
| Conversation (no tools) | Expands per turn | Accumulated unobservable participant state |
| Conversation + tools | Expands per turn + per tool call | Tools inject effectful co-domains |
| Human in conversation | Essentially unbounded | Physical world, lived experience |

Tools are **co-domain injectors**: each tool in the registry widens the conversation's output space. Permission gates are **co-domain management**: denying a tool keeps the conversation more characterizable. The Harness controls how wide the conversation's *ma* gets.

### Kinds of *ma*

Every actor has *ma*, but the *kind* differs — specifically, where the co-domain complexity comes from:

- **Borrowed *ma***: The Executor's output space is simple given its interface (`Read(path) → string`). The complexity comes from the world behind it — different filesystem states produce different outputs. Given the same inputs and the same world state, the output is determined. The co-domain complexity is the world's, not the actor's.
- **Minimal *ma***: The Harness's output space is characterizable by its rules and Conv_State. In principle, you could enumerate the possible actions for any given state. The co-domain is large but *describable* — you can say what the Harness will do without having the Harness.
- **Intrinsic *ma***: The Inferencer's output space requires the weights, activations, and sampling process to describe. You can't characterize what the model might output without having the model. The co-domain description IS the model.
- **Constitutive *ma***: The Principal's output space requires the person to describe — their experience, physical state, everything they've ever known. You can't compress the co-domain description without reducing the Principal. The description of the output space is the person.

### When actors play unnatural roles

Actors can be constrained or delegated into roles that don't match their *ma*, but the mismatch leaks:

- A **CI pipeline as Principal** (minimal *ma* in the authorization role): Can only apply fixed rules, never exercise judgment. Its co-domain is too characterizable — it can't make the decisions that require an uncharacterizable output space.
- An **LLM as Harness** (intrinsic *ma* in the minimal-*ma* role): The connection between participants becomes unpredictable. Other actors can't reason about what the hub will do because its co-domain is too complex to characterize. Works when trust mechanisms (chain-of-thought, approval protocols) compensate for the *ma* mismatch.
- A **sub-agent** (Inferencer constrained to Executor interface): The parent treats it as a function call, but the output varies in ways a true function wouldn't. The Executor interface compresses the sub-agent's co-domain into something the parent can characterize — but the compression is lossy.

### Secondary properties

*Ma* is the central axis. Actors also vary in properties that describe the *circumstances* of participation rather than the actor's nature:

| Property | Description | Range |
|---|---|---|
| **Lifetime** | How long the actor persists | Single invocation → Session → Cross-session → Indefinite |
| **Representation** | What space the actor operates in | Token space, Message space, Physical space |
| **Scope width** | How much of the conversation the actor can observe | Arguments only → Token window → Conv_State → Physical world |

These correlate with *ma* in practice (higher *ma* actors tend to have broader scope and longer lifetime) but the correlation isn't definitional.

---

## Actor Types

### Principal

The entity on whose behalf the conversation happens.

**Defining properties:**
- **External scope**: Observes things the system can never fully access — physical world, business context, intent beyond what's been stated, prior experience.
- **Authorization authority**: The ultimate arbiter of permissions. Can grant or deny capability transitions for other actors.
- **Asymmetric representation**: Operates in physical space (or the calling system's space). Reads rendered output. Writes natural language (or structured API calls).
- **Constitutive *ma***: The output space is essentially unbounded — you can't characterize what the Principal might say, paste, decide, or refuse without describing the Principal themselves.

**What a Principal is NOT required to be:**
- Human. A Principal can be an API caller, a CI/CD pipeline, another AI system, a scheduled job, or a human at a keyboard.
- Present. A Principal can configure permissions in advance and leave the conversation to run autonomously (auto-allow mode).
- Singular. Multi-user scenarios have multiple Principals with potentially different authorities.

**The key invariant:** The Principal's co-domain encompasses every other actor's co-domain and more. The Principal can paste tool output (injecting Executor co-domain through the constitutive-*ma* channel), override the Harness's decisions, or introduce information from entirely outside the system. The same content arriving through different actors has different *ma* — mediated tool output is characterizable; Principal-pasted content is not.

**Lifetime:** Outlives the conversation. The Principal exists before and after the session. Their persistent state (memory, preferences, project knowledge) spans conversations.

**Reads:** Rendered output — formatted text, tool call summaries, status indicators. A lossy projection of the conversation, filtered and formatted by the Harness.

**Writes:** Natural language text, permission decisions (grant/deny/configure), meta-commands (/compact, /clear, backgrounding decisions). Writes enter the conversation through the Harness, never directly into the log.

---

### Inferencer

An actor that performs non-deterministic inference. Reads a scoped representation of the conversation, produces structured output.

**Defining properties:**
- **Opaque inference**: The internal process — attention, sampling, chain-of-thought — is invisible to all other actors. You observe inputs and outputs, not the reasoning.
- **Intrinsic *ma***: The output space requires the model to describe. You can't characterize what the Inferencer might produce without having the weights — the co-domain description IS the model.
- **Structured output**: Produces a response containing text content, tool-use proposals, and (optionally) thinking traces. This is not "writing to the log" — it's producing output that the Harness receives, routes, and appends.

**Representation:**
- **Reads in token space**: The Inferencer receives a tokenized sequence — the conversation flattened and encoded by the inference infrastructure (API + tokenizer). The Inferencer never sees structured messages, Conv_State, or the Harness's internal bookkeeping. It sees tokens.
- **Writes in message space**: The Inferencer's output is de-tokenized by the inference infrastructure into structured messages (text blocks, tool_use blocks, thinking blocks). The Harness receives these structured messages.
- **The boundary between token space and message space is the API/tokenizer**, which is part of the inference infrastructure, not the Harness. The Harness operates entirely in message space.

**Scope:** Whatever the Harness constructs. The Inferencer has no independent access to the conversation, the tool registry, or any external state. Its entire observable world is the token sequence the Harness provided. The Harness is the Inferencer's reality.

**Lifetime:** A single inference call (one turn). The Inferencer has no persistent state across turns — all continuity comes from the conversation log, which the Harness manages. (Fine-tuning and RLHF are out of scope here — they affect the Inferencer's weights, not its per-turn state.)

**What the Inferencer produces (not "writes"):**
- Text content → Harness renders for Principal, appends to log
- Tool-use proposals → Harness routes through permission gate
- Thinking traces → Harness handles per configuration (may append, may discard)

The Inferencer never directly mutates any shared state. All its output is mediated by the Harness.

---

### Executor

An actor that performs a specific computation. Takes inputs, produces outputs, no inference.

**Defining properties:**
- **Borrowed *ma***: The Executor's co-domain is simple given its interface. A `Bash` tool running `date` returns different results every second — but the variation comes from the clock, not from the tool. A `Read` tool depends on filesystem state — but the tool itself is a pure function over that state. The co-domain complexity is the world's, passing through the Executor.
- **Narrow scope**: Sees only its explicit inputs (arguments) and its sandbox (e.g., allowed filesystem paths, network access). Has no access to the conversation, other tool calls, or the Harness's state.
- **No negotiation**: Does not propose, request, or refuse. Receives a request, executes or fails, returns a result. Has no concept of permissions from its own perspective — the permission gate happens *before* the Executor is invoked.

**Representation:** Operates in its native space — filesystem, shell, network, database. Its inputs are structured arguments (usually strings/JSON). Its output is structured results. The Harness translates between message space and the Executor's native space.

**Scope:** Defined by its arguments + sandbox configuration. The sandbox (allowed_directories, network access, resource limits) is set by the Harness at invocation time. The Executor cannot expand its own scope.

**Lifetime:** Single invocation. Stateless across calls (though it may interact with stateful external systems like filesystems or databases).

**As co-domain injector:** Each tool call injects the Executor's world-dependent co-domain into the conversation. A conversation with `Bash` available has a radically wider co-domain than one limited to text. The Harness manages which Executors are available — and therefore which co-domains can be injected. Permission gates are co-domain management.

**Examples:**
- `Read(file_path)` — reads a file, returns content
- `Bash(command)` — executes a shell command, returns stdout/stderr
- `Edit(file, old, new)` — modifies a file, returns success/failure
- MCP tool calls — dispatched to external servers, arguments in, result out
- `WebSearch(query)` — queries an external service

**The near-determinism caveat:** An Executor that calls an external service (web search, database query) may receive different results at different times. The Executor itself is deterministic — it faithfully dispatches and returns — but the external system introduces non-determinism. This is analogous to how `IO` wraps a deterministic dispatch mechanism around a non-deterministic world.

---

### The Harness

The actor that constitutes the conversation. Connects all participants. Manages state. Constructs scopes. Controls which co-domains compose.

The term comes from its literal meaning: a harness doesn't do the work — the horse does. It doesn't decide where to go — the driver does. But without the harness, the horse's power isn't connected to anything. The Harness is what turns capability into directed action. It's also the term the industry has converged on — [harness engineering](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html) is the emerging discipline of building these systems well.

**Defining properties:**
- **Hub topology**: The only actor that communicates with all others. All Principal ↔ Inferencer communication routes through it. All Inferencer ↔ Executor communication routes through it. All permission negotiation routes through it. No other pair of actors communicates directly.
- **Full Conv_State visibility**: Sees the structured conversation state — message history, token counts, tool registry, permission configuration, MCP server connections, budget, backgrounded task handles. This is strictly more information than any other actor sees.
- **Scope construction**: Builds the Inferencer's token window. Decides what's included, what's compacted, what's excluded. The Inferencer's reality is the Harness's construction.
- **Minimal *ma***: The Harness's output space is characterizable by its rules. You can describe what the Harness will do given its state — enumerate its possible actions, predict its responses to events. This characterizability is *why* it works at the hub: other actors can reason about what the Harness will do. A high-*ma* Harness (an LLM orchestrator) makes the entire system harder to reason about because the hub's behavior becomes uncharacterizable.
- **Co-domain management**: Controls which Executor co-domains compose into the conversation. Each tool in the registry widens the conversation's output space. Each permission gate constrains it. The Harness manages the conversation's *ma* budget.
- **Meta-level operations**: Can perform operations that no other actor can: compaction (lossy history transformation), tool loading/unloading, permission mode changes, scope reconstruction, promise injection.

**Representation:** Operates in message space. Receives structured messages from the Inferencer (via API). Sends structured messages to the Inferencer (via API). Renders output for the Principal. Dispatches calls to Executors. Manages Conv_State as a structured record.

**Scope:**
- Reads: Conv_State (full structured state), Principal's text input, Inferencer's structured output, Executor results.
- Does NOT see: Principal's physical/external state, Inferencer's internal inference process, Executor internals (only inputs/outputs).

**Lifetime:** The conversation session. Created when the session starts, destroyed when it ends. (Some state — memory files, configuration — persists through other mechanisms.)

**What it does, concretely:**
- Receives Principal input → appends to log → reconstructs Inferencer scope → invokes inference
- Receives Inferencer output → appends assistant message to log → renders text for Principal → routes tool proposals through permission gate
- Permission gate: checks configuration → if "ask", synchronizes with Principal → grants or denies
- Tool dispatch: invokes approved Executors (possibly in parallel) → collects results → appends to log OR holds as promises
- Promise management: holds backgrounded task handles → decides when to inject resolved results
- Budget management: tracks token usage → triggers compaction when needed
- Scope construction: selects which messages to include in the Inferencer's next window, applies compaction, orders content

**Why "Harness" and not other names:**
- *System*: Accurate (it's the `system` role) but ambiguous with "the system" meaning the whole architecture.
- *Orchestrator*: Implies coordination of equals. The Harness is privileged — it has capabilities no other actor has.
- *Mediator*: Undersells it. A mediator passes messages. The Harness constructs realities.
- *Kernel*: Strong analogy but too loaded with OS connotations.

The harness metaphor captures the key insight: a harness is fully characterizable (straps and buckles, low *ma*) yet structurally the most consequential piece. A poorly fitted harness wastes the horse's power. A well-fitted one multiplies it. The Harness is powerful *because* its co-domain is characterizable, not despite it.

---

## Compositions

### Sub-agents

A sub-agent is not a fifth actor type. It is a **composition** that presents an Executor interface to its parent:

```
Sub-agent (external) ≈ Executor
Sub-agent (internal) = Harness + Inferencer + {Executors}
```

From the parent conversation:
- The sub-agent is invoked like an Executor: arguments in, result out
- The sub-agent's internal turns are invisible — *ma* from the parent's perspective
- The sub-agent may use tools, perform inference, even spawn sub-sub-agents internally
- Only the final result (and possibly a summary) propagates back to the parent

**Co-domain compression:** The sub-agent internally has high *ma* (full inference loop, tool access), but the Executor interface compresses its co-domain into something the parent can characterize. This is lossy — the parent can't fully predict the sub-agent's output — but the interface constrains the *kind* of output the parent must handle.

**Scope inheritance:** The sub-agent's Harness typically inherits:
- A subset of the parent's tool registry (scoped by the parent)
- The parent's permission configuration (or a restricted version)
- A subset of the parent's conversation context (the capture list)

What it does NOT inherit:
- The parent's full conversation history
- The parent's budget (it may get an allocated sub-budget)
- The parent Harness's internal state

**Recursion:** Sub-agents can spawn sub-sub-agents. Each level is a composition that collapses to an Executor interface at its boundary. The nesting depth is theoretically unbounded but practically limited by budget and latency.

### The Tool-Inferencer Spectrum

The boundary between Executor and Inferencer is not sharp:

| Actor | Scope | Inference | Co-domain |
|---|---|---|---|
| `Read(file)` | File path + sandbox | None | Simple: string or error |
| `Bash(cmd)` | Command + shell env | None | Wide but characterizable by command |
| `WebSearch(q)` | Query string | None internally | World-dependent, hard to characterize |
| MCP tool (LLM-backed) | Arguments | Neural (hidden) | Uncharacterizable without the backing model |
| Sub-agent | Capture list + tools | Full inference loop | High — compressed by Executor interface |

The spectrum runs from pure computation to full agency. The key structural distinction: **how characterizable is the actor's output space given its interface?** The more the co-domain resists description, the more *ma* the actor has, regardless of whether the source is borrowed, intrinsic, or constitutive.

---

## The Communication Topology

```
              Principal (driver)
                  ↕ (text, permissions, meta-commands)
              Harness
             ↙    ↕       ↘
    Executor₁  Inferencer  Executor₂
                            (sub-agent, internally:
                              Harness'
                                ↕
                              Inferencer'
                                ↕
                              Executor'₁)
```

All arrows pass through the Harness. The Inferencer and Executors never communicate directly. The Principal and Inferencer never communicate directly. The Harness is the sole point of mediation.

In a sub-agent, a nested Harness' replicates this topology internally. The parent Harness sees the sub-agent as an Executor. The sub-agent's Harness' is invisible to the parent.

---

## The Shared Structure: Read → Infer → Respond

The Principal and the Inferencer are more alike than different.

Both have the same process:

```
1. Read    — observe a scoped view of the conversation
2. Infer   — opaque internal process (thinking, reasoning, deciding)
3. Respond — produce a lossy projection of internal state as output
```

The user doesn't type what they're thinking. They observe the rendered conversation, think (opaquely — *ma*), and produce text that compresses their actual reasoning into what they choose to express. The gap between the user's full internal state and what they type is exactly the same structural gap as between the Inferencer's hidden layers and its output tokens.

| | Principal | Inferencer |
|---|---|---|
| Reads | Rendered output (physical space) | Token window (token space) |
| Infers | Biological, opaque, unbounded context | Neural, opaque, bounded context |
| Responds | Natural language text, permission decisions | Text + tool proposals |
| *Ma* | Co-domain requires the person to describe | Co-domain requires the model to describe |

The difference isn't structural — it's **co-domain width**:
- The Principal has *wider co-domain* (physical world, lived experience) and *more authority* (can authorize)
- The Inferencer has *narrower co-domain* (bounded by architecture/training) and *no authority* (can only propose)

But the **process** — read a scoped input, perform opaque inference, produce a lossy output — is identical. This is the monadic continuum from the blog post, made concrete in the actor model. Both are monadic computations with underspecified context. They differ in how *much* is underspecified, not in the structure of the computation.

This means the Executor and Harness are the structurally distinct cases — they have **no opaque inference**. The Executor is a function. The Harness is a deterministic rule system. Their outputs are (in principle) fully determined by their inputs. The Principal and Inferencer are the actors whose outputs are drawn from distributions conditioned on unobservable state.

**The spectrum, grounded in actors:**

```
Executor          Harness             Inferencer         Principal
(pure function)   (deterministic      (neural inference,  (biological inference,
                   rules, full         bounded opaque      unbounded opaque
                   Conv_State scope)   internal state)     internal state)

low ma ←————————————— increasing ma ——————————————→ maximal ma
characterizable ←——————————————————————————→ requires the actor itself to describe
```

The same structure at every point. The dial turns on how characterizable the output space is.

---

## Summary Table

| Property | Principal | Inferencer | Executor | Harness |
|---|---|---|---|---|
| *Ma* | Constitutive | Intrinsic | Borrowed | Minimal |
| Co-domain | Unbounded | Vast, bounded by architecture | Simple given interface | Characterizable by rules |
| Inference | External (human/system) | Neural/probabilistic | None | Deterministic (rules) |
| Scope | Physical world + rendered output | Token window (constructed) | Arguments + sandbox | Conv_State (full) |
| Authority | Grants/denies permissions | None — proposes only | None — executes only | Enforces on behalf of Principal |
| Lifetime | Cross-session | Single turn | Single invocation | Session |
| Representation | Physical/API space | Token space | Native (fs, shell, net) | Message space |
| Writes to log | Via Harness | Via Harness | Via Harness | Directly |
| Communication | ↔ Harness only | ↔ Harness only | ↔ Harness only | ↔ All |
| API role | `user` | `assistant` | `tool` | `system` |

**The asymmetry in the writes-to-log row is the defining structural fact.** Only the Harness writes to the log directly. All other actors' contributions are mediated. The Harness is not just a participant — it is the substrate on which the other actors operate.

---

## References

- Hewitt, C., Bishop, P., & Steiger, R. (1973). A universal modular ACTOR formalism for artificial intelligence. *IJCAI*.
- Agha, G. (1986). *Actors: A Model of Concurrent Computation in Distributed Systems*. MIT Press.
- Fowler, M. (2025). Harness Engineering. *martinfowler.com*.
- Zhang, Y. & Wang, M. (2025). Monadic Context Engineering. *arXiv:2512.22431*.
