# Conversations Are Closures

*The structural correspondence between agent conversations and programming language closures isn't a metaphor. It's a design framework.*

---

## The observation

Here's what a multi-agent conversation looks like in practice:

A primary agent receives a task. It delegates to a subagent, passing along some context — a task description, some relevant files, a set of tools. The subagent works, produces results, and hands them back. Maybe the subagent delegates further. At each handoff, someone decides what context flows forward and what gets left behind.

Now here's what a closure looks like:

A closure is a function bundled with the variables it captured from its surrounding scope. When it executes, it can see those captured variables but not the rest of the environment. It produces a result that becomes available to whoever called it. Closures can nest — an inner closure captures from an outer closure's scope.

These aren't just analogous. They're the same structural pattern.

---

## The mapping

| Programming Language Concept | Multi-Agent Architecture |
|---|---|
| Shared heap | The full conversation log (append-only) |
| Lexical scope | Visibility rules for each agent |
| Closure | An agent + the context it can see |
| Capture list | What context an agent receives at spawn |
| Continuation passing | Handing the conversation to the next agent |
| Activation frame | An agent's current working window |

Multiple agents operate on a single, growing conversation log. Each agent is a closure: it captures a scoped subset of the log, operates within that scope, adds new state, and passes the whole log forward. The next agent closes over a different subset of the now-larger log.

The conversation is the shared heap. Each agent's visibility is its lexical scope. The handoff between agents is continuation passing.

### A concrete example

A user asks a primary agent to "review the auth module for security issues."

1. **The primary agent** appends the task to the conversation log and delegates. In closure terms, it creates a new closure whose capture list includes the task description and the file paths, but not the primary agent's other ongoing work.

2. **A tool-selection agent** receives that scoped view. It queries past sessions — "what tools were useful for security reviews?" — and assembles a kit: a static analysis tool, a dependency checker, the module's recent git history. It appends this kit to the log and hands off. In closure terms, it captured the task and tool history, produced new bindings (the kit), and passed a continuation.

3. **The worker agent** receives a closure over the task, the kit, and the code — but not the selection rationale or the primary agent's broader context. It does the review, appends findings to the log, and returns.

Each agent saw a different slice of the same growing log. The scoping was the architecture. In the grade lattice's terms: the capture list determines an agent's world coupling, and its internal logic determines its decision surface. A closure is an agent at a specific point on the lattice.

---

## Where the correspondence is exact

The closure framing gives concrete answers to questions the agent community is currently solving ad hoc.

### "What should a subagent see?"

This is the capture list question. When you spawn a closure, you decide which variables it captures from the enclosing scope. When you spawn a subagent, you decide which conversation history, tools, and context it receives.

Every multi-agent framework has a version of this. OpenAI's Agents SDK has `include_contents` parameters on handoffs. Google's context-aware framework treats context as a "compiled view over a richer stateful system." LangChain lets you scope what a callee sees.

They're all implementing capture lists. The closure framing makes this explicit: you're not "configuring context" — you're defining a scope.

### "How do agents share state?"

They don't share mutable state. They close over a shared, append-only log. Each agent reads from its scope and appends to the log. No coordination protocols, no locking, no race conditions. This is the same insight that makes persistent data structures and event sourcing work: if the log only grows, concurrent readers can't interfere with each other.

### "What happens when an agent gets stuck?"

In the traditional call-stack model, a stuck subagent fails, the error propagates up, the parent re-evaluates, and maybe retries with different parameters. Context is lost. Work is repeated.

In the closure/continuation model, a stuck agent doesn't fail — it passes a continuation: "Here's my state, here's what I need, resume me when you can provide it." The Harness fulfills the request — this is exactly the mediation role from post 1 — and the agent continues from where it left off. No unwinding, no lost context, no re-derivation.

This is continuation passing style (CPS) from PL theory, applied to agent orchestration. The conversation log preserves the agent's full state. The continuation is a request for resources plus a pointer to where to resume. The Harness is the continuation's target — the same entity that Fowler and OpenAI call the harness, now visible as a formal role in the computation.

---

## Where the correspondence breaks

The structural pattern is close enough to be a design guide, and the places where it breaks are themselves informative.

### Capture is not static

A real closure's capture list is fixed at creation. An agent's scope is not. A worker can request a new tool mid-task. A subagent can ask for broader context. The Harness can inject new information in response to what it observes.

In PL terms, this is **scope extrusion** — a concept from the pi-calculus where a private name is communicated outside its original scope, widening what's visible at runtime. It's what happens when a tool-selection agent grants access to a tool the worker didn't start with, or when a permission gate widens in response to a Principal's approval.

Milner's pi-calculus (1999) formalizes this precisely: names (capabilities, channels) can be sent along channels, allowing scope to grow dynamically. Every permission grant in a multi-agent system is a scope extrusion event — a name that was private to one actor enters another actor's visibility.

Static closures are a special case: scope extrusion that happens to be empty. Agent closures are the general case.

### The log only grows

A closure captures a fixed snapshot. The conversation log is append-only but monotonically growing — new entries arrive between when an agent starts and when it finishes. The agent's "capture" isn't a moment-in-time snapshot; it's a *view* over a living structure.

This is closer to the Store comonad than to a simple closure. The Store comonad represents a data structure with a focus — you can look at the focused position, or shift the focus elsewhere, but the underlying structure is always there. The Harness's scope construction (post 1's "extract" step) is exactly this: choosing where to focus within the full conversation state.

### Handoffs carry more than values

A closure returns a value. An agent handoff returns a value *and* reshapes the heap. When the worker appends findings to the log, it hasn't just returned a result — it has changed the environment that future closures will capture from.

In PL terms, these aren't pure functions. They're effectful computations — they produce values while also modifying shared state, requesting external resources, and raising conditions that need to be handled. Each handoff is a Kleisli composition: the output of one effectful computation becomes the input to the next, with the effects accumulating.

---

## The conversation is the program

The conversation log has a reflective property: it's simultaneously a record of what happened and an input that shapes what happens next.

When a tool-selection agent reads past sessions to configure a new worker, the log is functioning as an input to a meta-level program. When the worker adds findings that future agents will read, execution traces are becoming future inputs. The conversation is simultaneously the record of past behavior and a source of future behavior.

This isn't homoiconicity in the strict sense — the log isn't a syntactically transformable program in its own language. But it's a form of reflection: the system can inspect its own execution history and adapt. Named patterns — "find the most complex functions in recently changed files" — are encoded expert thinking, compressed into reusable forms that capture a *way of looking at code* rather than a static query.

The log accumulates these patterns. Each successful task completion adds an example of "here's how this kind of problem was solved." Future agents close over these examples. The system's vocabulary grows.

---

## The spectrum

Once you see conversations as closures, something else comes into focus.

A pure function is deterministic. Given the same inputs, it always produces the same output. Nothing about the world is left unspecified — the inputs fully determine the result. One set of inputs, one possible world, one result.

Now raise the temperature. Literally — set an LLM's temperature above zero. Suddenly there's a distribution of possible outputs. The inputs no longer fully determine the result; sampling introduces unspecified choices. Same input, multiple possible worlds, weighted by how much you left to chance.

Add a conversation history. The context now includes everything that was said before — every previous closure's contribution, every accumulated decision. The number of possible worlds grows with every turn, because each participant's response depends on state the system can't fully observe.

Add a human. The context now includes the entire lived experience of a person — their expertise, their intuitions, their physical state, what happened at work, whether they slept well. The degree of underspecification is enormous. Most of what determines the output is invisible to the other participants.

But at every point on this spectrum, it's the same structure: a value generated within a context. The only thing that changes is how much of the world is left unspecified by the inputs — how many possible worlds are consistent with what you can observe.

Moggi's insight (1991) was that computational effects — side effects, exceptions, nondeterminism, state — could all be modeled uniformly: as computations that produce values within contexts that carry additional structure. The `Maybe` context: a value might not exist. The `IO` context: the outside world matters. The `List` context: multiple values are possible. A probability context: outcomes are weighted.

Not all of these fit the underspecification framing cleanly — `Writer` accumulates output, `State` threads mutable bindings, `Cont` reifies control flow. The spectrum isn't universal. But for the contexts that model *what the computation can't see or control*, the pattern holds: each one handles a different degree of openness to the world outside the function's inputs.

A deterministic function is a trivial point on the spectrum. A temperature-controlled LLM is a probability context. A conversation is an `IO`-like context with an append-only log. A human in a conversation is a participant whose inputs include the entire physical world.

The boundary between "programming" and "conversation" is not a boundary. It's a dial.

---

## What this means for agents

If conversations have the same structure as closures — scoped access to shared state, continuation-based handoffs, effectful computation — then agent orchestration frameworks don't need to invent new abstractions for context management, scoping, and handoffs. The abstractions exist. The formal tools exist. Church gave us lambda calculus in the 1930s. Landin gave us closures in the 1960s. Hewitt gave us the actor model in the 1970s. Moggi gave us computational effects in the 1990s.

The scoping decisions, the context management, the handoff protocols — they're all implementations of concepts with rigorous foundations. The opportunity is in connecting the communities that built them with the communities that need them.

But there's a question the closure framing raises without answering. Agent closures aren't pure — they read external state, modify shared logs, request resources, widen scope. These are *effects*. And the question of who handles effects, how they're scoped, and what guarantees the handler provides — that's a question PL theory has a precise answer to.

---

*Previous: [The Space Between](02-the-space-between.md)*
*Next: [Raising and Handling →](04-raising-and-handling.md)*
