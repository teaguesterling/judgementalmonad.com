# The Space Between

*Part 3: Ma as co-domain characterizability — and why restriction is the load-bearing operation.*

---

## What *ma* is

Every actor in a multi-agent conversation has an output space — the set of things it could produce. *Ma* is how hard that output space is to describe.

A file-read tool's output space: "a string, or an error." Trivially characterized. A deterministic orchestrator's output space: "enumerable given its rules and state." Characterizable with effort. A language model's output space: "all possible token sequences up to the context limit" — but that tells you almost nothing. To actually describe what it might produce, you'd need the weights. A human's output space: requires the person to describe.

***Ma* is the descriptive complexity of the co-domain under the interface typing.** Formally, it's Kolmogorov-flavored: how compressible is the description of the output space? The more *ma*, the more the description resists compression.

This is not unpredictability. A SHA-256 is unpredictable — you can't guess which hash — but its output space is trivially characterized: "uniform over 256-bit strings." Low *ma*. A temperature-0 LLM is technically deterministic, but its output space requires the weights themselves to describe. High *ma*. A random die is maximally non-deterministic, but its co-domain is `{1,2,3,4,5,6}`. Low *ma*. The distinction between specific-output-unpredictability (Shannon entropy) and output-space-characterizability (Kolmogorov complexity of the co-domain description) is the crux.

---

## The co-domain gradient

*Ma* connects to the monadic continuum — each level represents a wider, harder-to-characterize output space:

| Level | Co-domain | What expands it |
|---|---|---|
| Pure function | Single point per input | Nothing — fully determined |
| Effectful function (program) | One point per world-state | External state (fs, clock, network) |
| Temperature > 0 (inference) | Weighted distribution over outputs | Sampling / internal non-determinism |
| Conversation (no tools) | Expands per turn | Accumulated unobservable participant state |
| Conversation + tools | Expands per turn + per tool call | Tools inject effectful co-domains |
| Human in conversation | Essentially unbounded | Physical world, lived experience |

The gap between "pure function" and "effectful function" is where most tools live. `Read(path)` is deterministic given the filesystem, but the filesystem is world-state — the output depends on something outside the function. The gap between "conversation without tools" and "conversation with tools" is where harness engineering lives. Each tool in the registry is a **co-domain injector**: it widens the set of possible conversation outcomes. Permission gates are **co-domain management**: controlling which injections are allowed.

---

## The four actors, grounded in *ma*

| Actor | *Ma* (co-domain characterizability) | Why |
|---|---|---|
| **Executor** | Borrowed — output space is simple given the interface; complexity comes from the world | `Read(path) → String`. You can describe what it could produce. |
| **Harness** | Minimal — output space is characterizable by its rules | Given Conv_State and configuration, you can enumerate what it will do. |
| **Inferencer** | Intrinsic — output space requires the model to describe | You can't characterize what it might produce without having the weights. |
| **Principal** | Constitutive — output space requires the person to describe | Unbounded. Can introduce anything from outside the system. |

*Ma* determines role: the most characterizable actor mediates (Harness), the least characterizable actor authorizes (Principal), and inference sits in between (Inferencer proposes). Architecture follows from co-domain structure.

---

## Interface *ma* vs. internal *ma*

Here's a crucial distinction the framework needs. *Ma* is measured at the **interface** — the output space as seen by other actors. What happens inside is the actor's own business.

Consider an auditor in a security enclave. Internally, it might be a large model with a vast context window, reviewing thousands of log entries, performing deep chain-of-thought reasoning about what's safe to share. Enormous internal complexity. But its **interface** is:

```
audit : Message → Either(Approved(Message), Rejected(Reason))
```

The co-domain is `{Approved(msg), Rejected(reason)}` — trivially characterizable. Low *ma* at the interface. The auditor's internal reasoning is high-*ma*, but from the system's perspective, the output space is constrained by the interface typing.

This is the sub-agent pattern generalized. A sub-agent internally has a full inference loop (high *ma*), but from the parent's perspective it's an Executor with a characterizable output space. The Executor interface **compresses** the internal co-domain. The compression is lossy (the parent can't predict which specific output), but the *kind* of output is bounded.

**The restriction isn't on the model — it's on the tools.** An auditor backed by Opus that can only `Read` logs and output `Approve/Reject` has low interface *ma* regardless of how much thinking happens in between. The tool restriction constrains the co-domain. The model's capability determines the *quality* of reasoning within that co-domain, not the *width* of the co-domain itself.

This means:
- A small model (Haiku) with many tools: low internal *ma*, high interface *ma*
- A large model (Opus) with restricted tools: high internal *ma*, low interface *ma*

The interface *ma* is what matters for the system's architecture. The internal *ma* is what matters for the quality of the actor's decisions within its constrained output space.

---

## Expansion and compression: the monad-comonad duality

The framework so far has focused on **expansion** — tool calls injecting results into the conversation, scope growing monotonically, co-domain widening. But in practice, the most valuable harness engineering operations are **compression**:

- Tool whitelisting (only `Read`/`Edit`/`Grep`, no `Bash`)
- Scope restriction for sub-agents (subset of parent's tools and context)
- Compaction (lossy summarization of conversation history)
- Kit assembly (quartermaster selecting task-specific tools)
- Sanitization (auditor stripping sensitive content at enclave boundaries)

These are all co-domain restriction operations. They narrow the output space. And they're where the actual engineering value lives — the LangChain result (same model, better harness, 52.8% → 66.5%) was almost certainly about restriction, not expansion.

### Expansion is monadic

Adding a tool result to the conversation is a monadic operation. The conversation monad wraps values with accumulated log:

```
return : A → Conv(A)                    -- pure value, no log entries
bind   : Conv(A) → (A → Conv(B)) → Conv(B)  -- sequence, concatenate logs
```

Each tool call is a Kleisli morphism `Args → Conv(Result)`. The result enters the conversation through `bind`. The co-domain expands — the conversation now contains information it didn't have before.

### Compression is comonadic

The Harness doesn't just add to the conversation — it **extracts focused views** from it. When the Harness constructs the Inferencer's token window, it takes the full Conv_State (a rich structure) and projects it into a focused representation (the tokens the Inferencer actually sees).

A comonad `W` has:

```
extract   : W(A) → A              -- get the focused value from context
duplicate : W(A) → W(W(A))        -- see the context around the focus
extend    : (W(A) → B) → W(A) → W(B)  -- apply a context-dependent function
```

The conversation as a comonad:

- **`extract(ConvState) → TokenWindow`** — the Harness extracts the Inferencer's current view. This is scope construction: selecting which messages to include, applying compaction, ordering content.
- **`duplicate(ConvState) → ConvState(ConvState)`** — the space of all possible scope constructions. Every way the Harness could focus the conversation.
- **`extend(inference)(ConvState)`** — apply the Inferencer (a function from focused view to output) across the conversation. This is what one inference step looks like: the Harness extracts a view, the Inferencer produces output from that view.

The Inferencer is a function `W(A) → B` — it takes a focused view and produces structured output. It never sees the full Conv_State. It only sees what `extract` gives it. The Harness controls `extract`.

**Compaction** changes the comonadic structure — after compaction, `extract` returns a lossy summary instead of full history. **Kit selection** changes it so that `extract` returns fewer tools. **Sanitization** changes it so that `extract` strips sensitive information. These are all modifications to the comonad's extraction function.

### The Harness lives at the monad-comonad boundary

The Harness performs both operations:

| Operation | Direction | Structure | *Ma* effect |
|---|---|---|---|
| Tool dispatch (inject results) | Expansion | **Monadic** (`bind`) | Co-domain widens |
| Scope construction (extract view) | Compression | **Comonadic** (`extract`) | Co-domain narrows |
| Permission gate | Both | Controls which expansions are allowed | Co-domain management |
| Compaction | Compression | Lossy comonadic extraction | Co-domain narrows |
| Promise injection | Expansion | Deferred monadic bind | Co-domain widens later |

The Harness is the actor that mediates between the monad (how information enters the conversation) and the comonad (how the conversation is projected to each actor). Its minimal *ma* — characterizable output space — is what makes it trustworthy in this mediating role. Other actors can reason about what the Harness will do at both the expansion and compression boundaries.

### Each actor sees a different comonadic extraction

This is key: the comonad isn't just about the Inferencer. Every actor sees a different projection of the conversation:

| Actor | What `extract` gives them | What's excluded |
|---|---|---|
| **Principal** | Rendered output — formatted text, tool summaries, status | Conv_State internals, token counts, system prompt |
| **Inferencer** | Token window — flattened, filtered, compacted conversation | Conv_State metadata, permission config, budget |
| **Executor** | Arguments + sandbox — just its inputs | Everything else — conversation, other tools, state |

The Harness constructs a different `extract` for each actor. The conversation comonad has **multiple extraction points**, each projecting a different focused view. The negative space — what each extraction excludes — is the *ma* that makes each actor's scope useful.

This is the aesthetic *ma* from the original blog post, now formalized: "the space between agents" is the gap between what the comonad contains and what each extraction reveals. The exclusions aren't limitations — they're the comonadic structure that makes each actor's view focused and useful.

---

## Co-domain funnels

All co-domain restriction operations share a pattern. A **co-domain funnel** is an actor or operation that narrows the output space for downstream actors.

### The quartermaster as funnel

The quartermaster pattern (from [Conversations Are Closures](conversations-as-closures.md)) is a co-domain funnel:

```
Full tool registry ──→ [Quartermaster] ──→ Task-specific kit
(wide co-domain)        (judgment)          (narrow co-domain)
```

A critical design insight: the quartermaster should have **lower interface *ma*** than the worker. Not because it's a worse model — but because its output space should be more characterizable. Tool selection doesn't require the rich co-domain of deep code analysis. It requires pattern matching on task descriptions and tool histories.

A Haiku model as quartermaster, delegating to an Opus worker:
- Quartermaster's interface *ma*: low. It produces a kit (finite list of tools). Characterizable.
- Worker's interface *ma*: higher. It produces analysis, code, findings. Harder to characterize.
- The low-*ma* quartermaster constrains the high-*ma* worker's co-domain.

This is the harness pattern at a different scale. The Harness (minimal *ma*) constrains the Inferencer (intrinsic *ma*). The quartermaster (low interface *ma*) constrains the worker (high interface *ma*). Same structure, nested. At every level, the more characterizable actor makes restriction decisions for the less characterizable one.

The quartermaster's internal *ma* can be as rich as needed for good judgment. But its *interface* — "here's your kit" — is constrained. The quality of the restriction comes from internal reasoning; the *auditability* of the restriction comes from the constrained interface.

### The auditor as funnel

In a multi-enclave system — call the sides Innies and Outies — the actors on each side may have comparable *ma*. The internal researcher has access to proprietary data and specialized analysis tools. The external researcher has access to public databases and computational tools. Neither is a subset of the other. Different *ma*, not less.

The restriction isn't on the actors — it's on the **channel between them**:

```
┌──────────────┐                          ┌──────────────┐
│  Innie        │                          │  Outie        │
│  (rich ma,    │◄── restricted channel ──►│  (rich ma,    │
│   own scope)  │    (low co-domain)       │   own scope)  │
└──────────────┘                          └──────────────┘
                    ↕
                 Auditor
          (high internal ma,
           low interface ma:
           Approve/Reject)
```

The auditor's interface is `Either(Approved(Message), Rejected(Reason))`. Low co-domain. But the auditor might be a large model reviewing extensive logs with deep reasoning — high internal *ma* applied to the approval decision.

### Temporal co-domain accumulation

Individual messages crossing the boundary might each be innocuous:

- "The study includes 500 participants" — fine
- "The median age is 34" — fine
- "67% are female" — fine
- "The facility is in Boston" — fine

But the **accumulated** channel output can become identifying. Each message individually has a characterizable co-domain (demographic statistics), but the *sequence* narrows the re-identification space. The channel's co-domain isn't per-message — it's the co-domain of the **message history**.

The auditor must be stateful:

```
audit : ChannelState → Message → (ChannelState', Either(Approved, Rejected))
```

Where `ChannelState` tracks what's already been shared, and the approval decision depends on what the *combination* of this message plus all previous messages reveals. The co-domain bound is on the accumulated channel, not individual messages.

This connects to information flow control (Goguen & Meseguer's non-interference, quantitative information flow). The *ma* framework adds the lens: the channel's **accumulated co-domain** must remain within characterizability bounds defined by the security policy. Each approved message potentially makes the accumulated co-domain less characterizable (more information leaked). The auditor's job is to keep the channel's accumulated *ma* below a threshold — and setting that threshold is itself a high-*ma* judgment.

### The funnel taxonomy

| Funnel | Internal *ma* | Interface *ma* | What it restricts |
|---|---|---|---|
| Static tool whitelist | None (configuration) | None | Tool co-domain (fixed subset) |
| Profile system | None (configuration) | None | Capability co-domain (role-based) |
| Compaction | Low (Harness rules) | Low | History co-domain (lossy summary) |
| Quartermaster | Medium (inference for selection) | Low (kit output) | Tool co-domain (task-specific) |
| Security auditor | High (deep review, vast context) | Low (`Approve/Reject`) | Channel co-domain (policy-bounded) |
| Sub-agent boundary | High (full inference loop) | Low (Executor interface) | Result co-domain (interface-compressed) |

The pattern: **internal *ma* determines quality of restriction; interface *ma* determines auditability of restriction.** You want funnels with enough internal *ma* to make good decisions, but low enough interface *ma* that the decisions are characterizable.

---

## The shared structure: read → infer → respond

The Principal and the Inferencer have the same process:

```
1. Read    — observe a comonadic extraction of the conversation
2. Infer   — opaque internal process (thinking, reasoning, deciding)
3. Respond — produce a lossy projection of internal state as output
```

The user doesn't type what they're thinking. They observe the rendered conversation (a comonadic extraction — not the full Conv_State, just the rendered view), think (opaquely), and produce text that compresses their actual reasoning. The Inferencer receives its token window (a different comonadic extraction), performs inference (opaquely), and produces structured output.

Both actors:
- Receive a comonadic extraction (compression of the conversation for their view)
- Perform opaque internal processing (high internal *ma*)
- Produce output that enters the conversation monadically (expansion)

The cycle is: **comonadic extraction → opaque processing → monadic injection**. Compression, then internal *ma*, then expansion. The Harness manages both boundaries — it constructs the comonadic extraction (what each actor sees) and gates the monadic injection (what enters the conversation).

The Executor has a degenerate version: it receives arguments (a very narrow comonadic extraction — just the function inputs), performs computation (low internal *ma*), and returns results (monadic injection). Same structure, minimal *ma*.

```
         Comonadic                              Monadic
         (compression)                          (expansion)
              │                                      │
              ▼                                      ▼
ConvState ──extract──→ FocusedView ──actor──→ Output ──bind──→ ConvState'
              │                        │                          │
              │                    (internal ma)                  │
              │                    (opaque)                       │
              ▼                        ▼                          ▼
         narrowed                 judgment/                  widened
         co-domain                inference                  co-domain
```

Every turn is a comonadic extraction followed by a monadic injection, with opaque processing in between. The *ma* framework tells you:
- How much the extraction narrows (compression quality)
- How much the opaque processing adds (internal *ma*, determines quality)
- How much the injection widens (expansion, measured at the interface)

---

## Restriction as the load-bearing operation

Expansion is easy — just grant more tools, add more context. Any system can expand its co-domain. The hard engineering is **restriction**: giving each actor exactly the co-domain it needs and no more.

The LangChain benchmark result (same model, better harness, 52.8% → 66.5%) is a restriction story. The improved harness didn't give the agent more tools — it gave it *the right* tools with *the right* constraints. Better comonadic extraction. Better co-domain management.

The *ma* framework predicts: **the improvement ceiling from co-domain restriction is higher than the improvement ceiling from model improvement**. Because the Harness determines the co-domain within which the Inferencer operates. A perfect Inferencer in a poorly-restricted co-domain (too many tools, too much irrelevant context, no focus) will produce poor results — it drowns in possibilities. A mediocre Inferencer in a well-restricted co-domain (right tools, focused context, clear scope) will produce good results within its bounded space.

This is testable. And if it holds, it redirects engineering investment from model capability to co-domain management — from making the horse stronger to fitting the harness better.

---

## What's novel here

The existing landscape:

- **Harness engineering** (Fowler, OpenAI): empirical practice. Knows restriction matters. No formal framework for why or how.
- **Monadic Context Engineering** (Zhang & Wang, 2025): monads for composition. Handles expansion. Doesn't model restriction.
- **Information flow control** (Goguen & Meseguer, declassification): formal tools for what information can flow where. Doesn't connect to agent architecture or *ma*.

What this series adds:

1. ***Ma* as the organizing axis**: co-domain characterizability determines role, unifying Principal/Inferencer/Executor/Harness under one property.
2. **The monad-comonad duality**: expansion is monadic (tool results entering), compression is comonadic (scope construction, compaction, restriction). The Harness lives at the boundary.
3. **Interface *ma* vs. internal *ma***: the output space at the boundary matters for architecture; the internal complexity matters for quality. These are independent.
4. **Co-domain funnels**: actors whose purpose is to use internal *ma* to restrict interface *ma* for downstream actors. The quartermaster, the auditor, and the sub-agent boundary are instances.
5. **Temporal co-domain accumulation**: restriction isn't per-message but over the accumulated channel history. Connects to information flow control.

The formal machinery (parameterized monads, π-calculus, session types) from the rest of the series gives these concepts teeth. The monadic co-domain gradient tells you *how much* expansion each operation adds. The comonadic extraction tells you *how much* compression each scope construction performs. The *ma* axis tells you *who should manage what* — the most characterizable actor at the boundary, always.

---

## Open questions

**Is compaction a comonadic morphism?** Lossy summarization changes the extraction function, but does it preserve the comonadic structure? If the summarized version of `(A then B)` doesn't equal `(summary of A) then `(summary of B)`, then compaction isn't structure-preserving. It might be a weaker structure — a Galois connection (abstract interpretation) or a general natural transformation.

**Are monad morphisms the right tool for inter-enclave sanitization?** A monad morphism `η : M ~> N` preserves sequential composition. If sanitization is structure-preserving (sanitize-then-compose = compose-then-sanitize), it's a monad morphism. If not, we need something weaker. The temporal accumulation issue suggests it's not — sanitization decisions depend on channel history, which breaks the compositionality.

**How do the monad and comonad interact formally?** Distributive laws between monads and comonads (Brookes & Geva, Uustalu & Vene) give composition rules. Is there a distributive law for the conversation monad and the scope comonad? This would tell us how expansion and compression compose — the formal structure of a turn.

**What's the right comonad?** The `Store` comonad fits: `Store Scope FocusedView` where the position selects which scope to apply and the stored function maps every scope to its projected view. `extract` gives the actor its focused view; `duplicate` gives the Harness access to every possible extraction; `extend inference` computes the counterfactual "what would inference produce under each possible scoping?" See Part 4, Section 12 for the formal development.

---

*Previous: [Part 2 — The Anatomy of a Turn](turn-anatomy.md)*
*Next: [Part 4 — Toward a Formal Framework](formal-framework.md)*
