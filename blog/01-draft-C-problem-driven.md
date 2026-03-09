# The Four Actors

*Draft C: Problem-driven. Start with the harness engineering gap, introduce the actors as the answer.*

---

## The question nobody asks

LangChain's coding agent scored 52.8% on SWE-bench. They changed nothing about the model. They changed how the model was connected to the world — what it could see, what tools it had, how results were formatted. The score jumped to 66.5%.

This is a 26% relative improvement from pure infrastructure. The model didn't get smarter. The *harness* got better. And nobody can explain precisely why.

Martin Fowler defines harness engineering as "the tooling and practices we can use to keep AI agents in check." OpenAI built an engineering methodology around it. The emerging consensus: the harness is the architecture, the model is not the bottleneck. But the field's explanations for WHY certain harness designs work are ad hoc: "it reduces errors," "it keeps the agent focused," "it worked."

To build a theory, you need to know what you're theorizing about. So: what IS a harness? What are the participants in a multi-agent conversation, and what structural properties distinguish them?

---

## The participants

Strip away the framework-specific terminology — LangChain's "chains," CrewAI's "crews," AutoGen's "agents" — and every multi-agent system has the same four kinds of participant. They map to the four message roles in any LLM API (`user`, `assistant`, `tool`, `system`):

**The Principal** — the entity on whose behalf the conversation happens. Provides goals, grants permissions, brings judgment from outside the system. In Claude Code: you. In a pipeline: whatever entity initiated the work and holds accountability.

**The Inferencer** — the entity that performs non-deterministic inference. The language model. It receives a constructed input and produces structured output: text and tool call proposals. Each call is stateless — the model has no persistent state between invocations.

**Executors** — entities that perform specific computations within bounded worlds. Read, Write, Bash, Grep. Each sees only its arguments and its sandbox. Each returns a typed result.

**The Harness** — the entity that connects the other three. It constructs the Inferencer's input, gates the Inferencer's proposals, dispatches Executors, manages conversation state, and renders output for the Principal. The `system` role made concrete.

These aren't metaphors. They're structurally distinct participants with different capabilities, different views of the conversation state, and different output spaces. Understanding what makes them different — and why those differences determine the architecture — is what this series is about.

---

## Four views of one state

The same conversation state looks different to each actor. This is by design.

**The Principal sees:** rendered output. Formatted markdown in a terminal. Tool call summaries ("Read src/main.py"). Status indicators. The Principal does NOT see the system prompt, the token budget, the compaction history, or the permission configuration.

**The Inferencer sees:** a token window. The conversation state, flattened and tokenized — system prompt, history, tool descriptions, context. Filtered through a scope the Harness chose. The Inferencer does NOT see the raw compartment structure, the budget, or what was excluded.

**Each Executor sees:** its arguments and its sandbox. Nothing else. Not the conversation, not the user's question, not the model's reasoning.

**The Harness sees:** the structured `Conv_State` — compartments with boundaries, token counts, budget, tool registry, permission tables. It sees what every other actor sees (because it *constructs* those views) and metadata none of them see.

Nobody sees the same thing. The gaps between views are functional — they're what makes each actor's scope useful. The model doesn't see the token budget because metacognition about budget is less valuable than reasoning about the task. The tool doesn't see the conversation because it doesn't need it. The negative space is the architecture.

---

## The star

Every message passes through the Harness. The Inferencer never talks to an Executor. The Principal never talks to the Inferencer directly. The topology is a star with the Harness at the hub:

```
                    Principal
                       ↕
Executor ←→ Harness ←→ Inferencer
                       ↕
                    Executor
```

Why? Because the hub must be the participant that everyone else can reason about. If you put the model at the hub (an LLM deciding which agents run, managing state, routing messages), the system's behavior becomes as hard to characterize as the model itself. If you put the Principal at the hub, every decision requires human attention. If you put an Executor at the hub, you get a static pipeline with no adaptation.

The Harness works at the hub because its behavior is *characterizable*. Given its configuration and state, you can describe what it will do — enumerate its possible actions, trace its decision logic, audit its rules. This isn't true of the model (you'd need the weights), the Principal (you'd need the person), or the Executor's world interactions (you'd need the filesystem).

This is the first hint of the structural property this series formalizes: the Harness belongs at the hub because it has the *least space* between its inputs and its outputs. Its processing is transparent. Its output follows from its rules. The space between receiving a tool call proposal and deciding what to do with it is characterizable by reading the permission configuration.

---

## The turn

Every interaction follows the same cycle:

**Extract:** The Harness constructs a view for an actor. For the Inferencer: flatten Conv_State through a scope, tokenize. For an Executor: package the arguments. For the Principal: render the response.

**Process:** The actor does its work. For the Inferencer: a forward pass through the weights. For an Executor: computation in its sandbox. For the Principal: reading, thinking, typing. This step is opaque to everyone else — it's the actor's own space.

**Inject:** The result enters the conversation through the Harness. The Harness checks permissions (for tool proposals), formats results, updates Conv_State, and decides what to include in the next extraction.

Extract → process → inject. The Harness controls the first and last steps. The middle step is the actor's business. This cycle is the atom of the architecture — it repeats at every scale (a tool call, a sub-agent conversation, the outer conversation) with the same structure and different actors.

---

## The worked example

"What's in src/main.py?" — traced through the four actors.

| Step | Actor | Action | What it sees |
|---|---|---|---|
| 1 | Principal | Types the question | The terminal, the project, their intent |
| 2 | Harness | Constructs Conv_State, extracts Inferencer's view | Full structured state |
| 3 | Inferencer | Forward pass → proposes Read("src/main.py") | Token window (flattened, scoped) |
| 4 | Harness | Permission check → auto-allow. Dispatches Read. | Conv_State + permission config |
| 5 | Executor (Read) | Reads the file in its sandbox | File path + sandbox config |
| 6 | Harness | Injects result into Conv_State, re-extracts | Updated state |
| 7 | Inferencer | Forward pass → "Here's what's in src/main.py: ..." | Updated token window |
| 8 | Harness | Renders response for Principal | Updated state |
| 9 | Principal | Reads the answer | Rendered markdown |

Nine steps. Four actors. Three complete extract→process→inject cycles (Inferencer twice, Executor once). Every boundary mediated by the Harness.

Step 4 is where the architecture is most visible: the model *proposed* reading a file. The Harness *decided* to allow it. The Executor *did* it. The Harness *injected* the result. If the proposal had been `Bash("rm -rf /")`, step 4 would have diverged — the Harness would have asked the Principal for permission, and the Principal's judgment would have determined whether the conversation's scope expanded to include that tool's output.

The permission gate isn't security (though it serves that function). It's *scope management* — the Harness controlling which external information enters the conversation. Every permission decision shapes what the conversation can become.

---

## The naming

Why "Harness"?

A harness doesn't do the work — the horse does. A harness doesn't decide where to go — the driver does. The harness connects capability to direction. Without it, the horse's power is unattached and the driver's intent has no effect.

The language model is the horse — immense capability, no direction of its own. The Principal is the driver — clear intent, no direct access to the capability. The Harness connects them: translating the Principal's direction into the Inferencer's scope, and the Inferencer's proposals into actions in the world.

Fowler and OpenAI landed on the same word independently. The industry converged because the metaphor captures the structural role: the Harness is the most powerful participant precisely because it's the least autonomous. Its power is architectural — connecting, constraining, mediating — not inferential.

---

## What comes next

We've identified the participants. We've seen that they have different views, different capabilities, and one shared topology. The Harness sits at the hub because its behavior is characterizable.

But "characterizable" is doing a lot of work in that sentence. What does it mean precisely? Is there a single property that distinguishes the Harness from the Inferencer, the Executor from the Principal? Can we measure it?

There is. It's the space between what an actor receives and what it produces — a concept from Japanese aesthetics that turns out to have a formal definition in programming language theory.

---

*Next: [The Space Between →](02-the-space-between.md)*
