# Raising and Handling

*Agent closures are effectful. The question of who handles the effects — and how — turns out to have a precise answer.*

---

## The effects we noticed

Post 3 ended with an observation: agent closures aren't pure. They read external state, modify shared logs, request resources, widen scope. These are *effects* — computations that do something beyond returning a value.

The closure framing identified the effects but didn't say much about their structure. Who decides whether a tool call goes through? Who manages the log? Who controls which effects an agent is allowed to raise? We've been calling that entity the Harness, and we've described what it does (post 1) and measured the space it operates in (post 2). But we haven't said what it *is* in formal terms.

There's a framing from programming language theory that fits almost exactly.

---

## The two roles

In algebraic effects (Plotkin & Power 2003, Plotkin & Pretnar 2009), computation has two roles:

**Raising**: a computation declares that it needs something. `Read(path)` means "I need a file read — give me back a string." The computation doesn't perform the read. It raises the effect and waits.

**Handling**: a handler receives the raised effect and decides what to do. It might fulfill the request, deny it, defer it, transform it, or batch it with other requests. The handler gets the effect and a continuation — the computation suspended at the point where it raised the effect, ready to resume when the handler provides a result.

The two roles map directly onto the conversation:

| Algebraic effects | Multi-agent conversation |
|---|---|
| Raising an effect | An actor proposes an action (tool call, resource request) |
| The handler | The Harness |
| Handler pattern-matching | Permission gates: auto-allow, ask the Principal, auto-deny |
| Handler transforming/suppressing | The Harness reordering, batching, denying proposals |
| Handler's own effects | The Harness doing IO: dispatching processes, loading files, reading config |
| Handler modifying its state | Structure operations: compaction, tool registry changes, budget updates |
| Nested handlers | Sub-agent boundaries (the outer Harness handles the sub-conversation's summary) |

The Inferencer proposes `Read("src/main.py")` — it raises an effect. The Harness receives the proposal and the continuation (the Inferencer suspended, waiting for the file contents). The Harness checks permissions, dispatches the Executor, collects the result, injects it, and resumes the Inferencer with the file contents in its next input.

This is the turn cycle from post 1 (extract → process → inject), now with a formal name: the Harness is an algebraic effect handler.

---

## Why this isn't just relabeling

The handler framing resolves several problems that arise when you try to describe the Harness as just "the orchestrator" or "the meta level."

### There is no meta level

A natural first attempt at formalizing the Harness is to describe two levels: an *object level* where agents read and write, and a *meta level* where the Harness manages state. Agents operate at the object level; the Harness operates at the meta level. Clean separation.

But the separation doesn't exist. The Harness doesn't operate in a separate phase — it interleaves with the agents continuously. It handles a tool call (meta), then updates the log (meta), then re-extracts the Inferencer's view (meta), then waits for the Inferencer to respond (object). A tool-selection agent reads the log (object) but also configures the worker's tool set (meta). Promises start as proposals (object) and complete as injections (meta).

The handler framing dissolves this: there aren't two levels, there are two *roles*. Actors raise effects. The Harness handles them. Both happen in the same execution context, interleaved. The handler is itself effectful — it lives in IO (dispatching processes, reading files) while handling conversation effects (managing state, gating permissions). This is standard in algebraic effects: handlers can raise effects that outer handlers interpret.

### Delegation is natural

A tool-selection agent that configures the worker's tools isn't "straddling levels." It's an actor with delegated handler privileges — the Harness has handed it a limited ability to handle certain effects (tool configuration) on behalf of the worker. In algebraic effects, this is handler composition: one handler delegates part of its interpretation to another. The delegation is scoped and revocable.

### Scope extrusion is an effect

Post 3 identified scope extrusion (pi-calculus) as the key place where closures break down — agents can widen their scope at runtime. In the handler framing, scope extrusion is just another effect: the agent raises "I need access to X," and the handler decides whether to grant it. Every permission grant is a handled scope-extrusion effect. The handler decides; the agent receives.

---

## What the Harness receives

Each actor has internal effects — what happens inside its processing step. But the Harness doesn't see those. It sees what arrives at the interface: the raised effect after the actor's own internal handling.

| Actor | Internal effects | What the Harness receives |
|---|---|---|
| **Executor** | IO within its sandbox (file reads, process execution) | A result or an error. The Executor's own error handling has already run. |
| **Inferencer** | Attention, sampling, chain-of-thought — opaque | A structured response: text blocks + tool call proposals. One sample from an opaque process. |
| **Principal** | Unbounded IO — the physical world, expertise, judgment | A message: text, images, files, selections. Rich but finite per turn. |

This is the interface/internal ma distinction from post 2, now visible as a handler boundary. The Executor has its own internal handler that compresses `IO` to `Result | Error` before the Harness sees it. The Inferencer's internal handler is opaque — we don't have access to its implementation effects, only its interface output. The Principal's internal effects are unbounded — the Harness receives whatever the Principal chooses to send.

The Harness itself has an effect signature too: `Extract | Gate | Inject | Compact | Yield` — the operations from post 1's turn cycle, now typed as a finite enumerable set. The Harness is self-characterizing: its interface IS its implementation, which is why it belongs at the hub.

---

## The handler's design space

Post 3 noted that the conversation log is closer to the Store comonad than to a simple closure — it's a data structure with a focus, where the Harness chooses where to look. The handler framing makes this precise.

The handler can compute what every actor would *see* under every possible scoping. Given the full conversation state and a scope function, it can produce the extraction — the flattened, tokenized view the Inferencer would receive, or the argument package the Executor would get. It can evaluate every possible scope and choose among them.

What the handler *cannot* compute is what each actor would *do* with what it sees. The Inferencer's response to a given input requires running inference — the actor's internal ma is opaque to the handler. The handler navigates a well-characterized design space (all possible extractions) to manage an opaque process (the actor's response).

This is the formal content of the Harness's architectural advantage. It doesn't need to understand the Inferencer's weights. It needs to understand the space of possible inputs it could construct — and choose well among them. Scope construction is the handler's primary lever, and it's fully within the handler's computational reach.

---

## Regulation, not prediction

Here's the punchline, and it resolves a tension that's been building since post 2.

Post 2 introduced the Conant-Ashby Good Regulator Theorem: "Every good regulator of a system must be a model of that system." The Harness regulates the Inferencer. So what model does the Harness need?

The obvious answer is wrong. The Harness does NOT need a model of the Inferencer's internal computation — that would require the weights, and simulating the weights costs as much as running the model. That's not regulation; it's replication.

What the Harness needs is a model of the Inferencer's *interface*: what effects it can raise (text + tool proposals), what protocol it follows (propose → gate → execute → collect), and what handling strategy each effect gets (the permission configuration). The handler pattern-matches on the effect signature, not on the implementation.

This is the difference between prediction and regulation:

**Prediction** asks: what will the actor do? This requires understanding its internal computation — the implementation effects, the weights, the decision surface. For a trained model, this is intractable. For a human, it's impossible.

**Regulation** asks: whatever the actor does, can I handle it? This requires understanding the interface — what effects can be raised, and what to do with each one. For any actor with a typed interface, this is tractable. The session type (auto-allow Read, ask for Bash, auto-deny network) IS the regulation strategy, and it operates entirely at the interface level.

The Harness succeeds not because it predicts what the Inferencer will propose, but because it can handle any proposal the Inferencer makes. The handling strategy is finite, enumerable, auditable — low ma at the interface, regardless of the Inferencer's internal ma.

This is why restriction has superlinear returns (post 2's supermodularity): reducing the set of effects an actor can raise makes the handler's job easier in proportion to how complex the actor is internally. Restricting a specified script's tools is nice. Restricting a trained model's tools eliminates the combinatorial interaction between vast decision surface and broad world coupling — the handler's finite strategies now cover the space.

---

## What we have so far

Four posts in, the framework has:

- **The actors** (post 1): Principal, Inferencer, Executor, Harness — four structurally distinct participants in every multi-agent conversation
- **The grade** (post 2): ma measured as (world coupling, decision surface), with composition as join and supermodular characterization difficulty
- **The structure** (post 3): conversations as closures, with scope extrusion, effectful computation, and the monadic spectrum from deterministic to radically open
- **The dynamics** (this post): actors raise effects, the Harness handles them, and regulation operates on the interface, not the implementation

One question remains. We've said the Harness can regulate the Inferencer because it handles effects at the interface. We've said actors with lower interface ma are "more predictable." But what does predictability actually mean? When can one actor reason about what another might do?

---

*Previous: [Conversations Are Closures](03-conversations-are-closures.md)*
*Next: [Predictability as Embeddability →](05-predictability-as-embeddability.md)*
