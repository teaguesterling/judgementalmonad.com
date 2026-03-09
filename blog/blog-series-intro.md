# The *Ma* of Multi-Agent Systems

*A series on what programming language theory, Japanese aesthetics, and a late-night conversation about SQL macros reveal about the architecture of AI agent systems.*

---

## The harness moment

2025 proved agents could work. 2026 is proving that the agent isn't the hard part.

The hard part is the harness — the infrastructure that connects a language model to the world: scope construction, tool dispatch, permission gates, context management, state. Martin Fowler [defines it](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html) as "the tooling and practices we can use to keep AI agents in check." OpenAI built [an entire engineering methodology](https://openai.com/index/harness-engineering/) around it. LangChain demonstrated it empirically: their coding agent jumped from 52.8% to 66.5% on a benchmark by changing *nothing about the model* — only the harness.

The industry has a name for this now: **harness engineering**. And the emerging consensus is clear: the harness is the architecture, and the model is not the bottleneck.

But there's a gap. Harness engineering is empirical — practitioners know that certain designs work better than others, but the field lacks a theory for *why*. Why does a deterministic orchestrator work better at the hub than an LLM? Why do permission gates improve reliability? Why does restricting an agent's tool set sometimes improve its output? The answers are ad hoc: "it reduces errors," "it keeps the agent focused," "it worked in practice."

Meanwhile, Zhang and Wang's [Monadic Context Engineering](https://arxiv.org/abs/2512.22431) (Princeton, 2025) brought real programming language theory to agent composition — Functors, Applicatives, Monads, and Monad Transformers for state management, error handling, and concurrency. This is genuine formal work. But it formalizes the *plumbing* — how to compose agents safely — not the *architecture* — which agent goes where and why.

The practice exists. The composition algebra exists. What's missing is the **design theory**: a formal account of why certain architectural decisions work, derived from properties of the participants rather than trial and error.

This series proposes one.

---

## The observation

Every multi-agent conversation has four kinds of participants. They map to the four message roles in any LLM API (`user`, `assistant`, `tool`, `system`), and they're present in every agent framework whether or not the framework names them:

- A **Principal** — the entity on whose behalf the conversation happens
- An **Inferencer** — the entity that performs non-deterministic inference
- **Executors** — entities that perform specific computations
- A **Harness** — the entity that connects them all

The Harness is the `system` role made concrete. It's Claude Code, Cursor, a custom integration — the client that constructs the Inferencer's context window, dispatches tool calls, gates permissions, manages state. Fowler's harness engineering is about building good Harnesses. What we're asking is: what *makes* a good Harness good?

The answer turns out to be a structural property that all four actors have in different degrees.

---

## *Ma*

In Japanese aesthetics, 間 (*ma*) is the concept that the space between things is itself functional. The pause that gives the notes shape. The empty room that makes the architecture. The negative space that tells you where to look. *Ma* isn't absence — it's the structural element that makes everything around it work.

Agent architectures have *ma*. Every scoping decision creates two things: what an agent can see, and what it can't. The tool-selection agent doesn't see the worker's line-by-line analysis — and that's *why* it can think clearly about tool selection. The worker doesn't see the selection rationale — and that's *why* it can focus on the code. The exclusions aren't limitations. They're the negative space that makes each agent's scope useful.

But *ma* goes deeper than scoping. It's a property of the actors themselves.

Consider what it means to *characterize* an actor's output. For a file-read tool, you can describe the output space concisely: "a string, or an error." For a deterministic orchestrator, you can enumerate its possible actions given its rules and state. For a language model — what would you say? "Any token sequence up to the context limit"? That's technically true but tells you almost nothing. To actually characterize what the model might output, you'd need... the model itself.

***Ma* is the space between what an actor receives and what it produces.** A pure function has no space: input determines output. An `if` statement has a sliver: one point where inputs can steer the processing. A neural network has a vast space: billions of pathways between input and output. A human has a lifetime.

The space is shaped by *restriction* — what can enter it (scope), what can exit it (tools). It's filled by the actor's *decision surface* — the internal structure that inputs can influence at runtime. And it's measured by *characterizability* — how hard is it to describe what could come out, given what went in?

This is not the same as unpredictability. A SHA-256 hash is unpredictable — you can't guess which hash you'll get — but the space between input and output is trivially characterized: "a uniform mapping over 256-bit strings." Low *ma*. A temperature-0 language model is technically deterministic for any given input, but the space between its input and output is the entire weight manifold. High *ma*. Unpredictability is about specific outputs. *Ma* is about the *space* between inputs and outputs.

The four actors fall on a clean gradient:

| Actor | *Ma* | Why |
|---|---|---|
| **Executor** | Borrowed | Output space is simple given the interface; complexity comes from the world, not the actor |
| **Harness** | Minimal | Output space is characterizable by its rules — you can describe what it will do |
| **Inferencer** | Intrinsic | Output space requires the weights to describe — the model IS the co-domain characterization |
| **Principal** | Constitutive | Output space requires the person to describe — unbounded, irreducible |

And here's the punchline: ***ma* determines role**. You put the low-*ma* actor at the hub because you need the hub's behavior to be *characterizable* — other actors must be able to reason about what the Harness will do. You put the high-*ma* actor at the authorization boundary because only it can make decisions from an uncharacterizable output space — that's what judgment *is*. You constrain the medium-*ma* actor to proposing rather than deciding, because its output space is rich but bounded.

The architecture of a multi-agent conversation isn't arbitrary. It falls out of the *ma* structure.

---

## What this adds to the landscape

| Question | Harness Engineering (Fowler, OpenAI) | Monadic Context Engineering (Zhang & Wang) | This series |
|---|---|---|---|
| What is the harness? | Infrastructure and practices | Not addressed directly | A formal actor with a *ma* signature |
| Why does the harness work? | Empirical ("it helped") | Algebraic laws (monad laws) | Low co-domain complexity makes mediation trustworthy |
| How do agents compose? | Ad hoc patterns | Monad Transformers | Parameterized monads over scope lattice |
| Why this architecture? | Not asked | Not asked | *Ma* determines role — single axis explains all four actors |
| Concurrency model | Not formalized | Applicative (parallel) | π-calculus (scope extrusion, channel passing) |
| Permissions | Mentioned informally | Not addressed | Session types for permission protocols |

The series doesn't replace harness engineering or MCE — it provides the **design theory** underneath them. Harness engineering says "build a good harness." MCE says "compose agents with monads." We say: "the harness works *because* its co-domain is characterizable, and here's the formal framework — grounded in sixty years of PL theory — that explains why."

---

## The series

**Part 1: [Conversations Are Closures](conversations-as-closures.md).** The structural correspondence between programming language closures and multi-agent conversation architecture. Scope, capture lists, continuation passing, and why every agent framework is implementing closures whether it knows it or not. Where the correspondence holds, where it breaks, and what the breakdowns reveal.

**Part 2: The Anatomy of a Turn.** What actually happens in a conversation turn — concretely, grounded in how systems like Claude Code work. The four actors: Principals, Inferencers, Executors, and the Harness. Permission negotiation as a protocol. Parallel tool execution. Backgrounded tasks as promises. The Harness as the most powerful and least understood participant.

**Part 3: [The Space Between](the-space-between.md).** *Ma* as co-domain characterizability — the formal definition, tested against edge cases, and connected to the monadic continuum. The distinction between interface *ma* and internal *ma*. Why restriction is the load-bearing operation: co-domain funnels, the quartermaster pattern, and the monad-comonad duality (expansion is monadic, compression is comonadic, the Harness lives at the boundary). Multi-enclave systems and temporal co-domain accumulation.

**Part 4: [Toward a Formal Framework](formal-framework.md).** The interface monad ordering as the formal object for *ma*. The Store comonad for scope construction; the monad-comonad duality with the Harness at the boundary. Interface *ma* vs. internal *ma* as monad morphisms. The fractal architecture: every actor has internal conversation structure, self-similar at every scale. Session types for the permission protocol; π-calculus for parallel tool execution and scope extrusion. A worked example tracing a Claude Code tool call through the formalism. Design principles derived from the math. An honest accounting of what's novel and what's Moggi (1991) with better marketing.

**Part 5: [Conversations Are Folds](conversations-are-folds.md).** Every inference call is stateless. The "conversation" is an illusion created by the Harness including previous turns in the next input — a fold over managed state. The composite entity's grade evolves via a coupled recurrence. Reachable vs total decision surface. Context management as the Harness's most leveraged operation.

**Part 6: [Computation Channels](computation-channels.md).** Not all tools are data channels. Tools that accept agent-generated text as executable specification create self-amplifying dynamics in the grade trajectory. A taxonomy from structured queries (level 0) through persistent processes (level 6) to controller modification (level 8). Three phase transitions: mutation, computation amplification, and escape from the fold.

**Part 7: [The Specified Band](the-specified-band.md).** The OS already solved the regulation problem: vast world coupling with transparent decision surface. The `(open, specified)` band is the viable region for regulators. Layered regulation (constraint, observation, policy). Capability publishing as staying specified. The SELinux lesson: constraints must be projected into the actor's scope. The Ashby resolution.

---

This work grew out of building [Fledgling](https://github.com/teaguesterling/fledgling), a SQL-based code intelligence toolkit for AI agents. The practical questions — what should an agent see? how do tools compose? what context matters? — led to the structural observations. The structural observations led to the formal framework. The formal framework led to *ma*.

The conversation itself was the proof of concept: two participants with asymmetric visibility over a shared log, passing continuations back and forth, generating ideas that could only exist within the context that produced them. A sixteen-year-old dog who doesn't like her meds was involved. Whiskey was present.

Sometimes the most interesting things happen at wide context windows.

---

*Next: [Part 1 — Conversations Are Closures →](conversations-as-closures.md)*
