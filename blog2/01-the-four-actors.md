# The Four Actors

*What makes a good interaction between multiple agents? Start by noticing who's in the room.*

---

## The question

2025 proved agents could work. 2026 is proving that the interesting problems aren't about individual agents — they're about how agents interact.

Consider: a coding agent that can read files, run tests, and write code. Useful. Now consider three of them — a planner that selects tools, a worker that writes code, and a reviewer that checks it — each with a different model, different tool set, and different view of the conversation. Which tools does the planner need? What should the reviewer be allowed to see? If the worker can run Bash, can it install packages? Who decides?

These aren't implementation details. They're architectural questions with security and reliability implications. Give the wrong tool to the wrong agent and you get a system that's hard to reason about, hard to audit, and hard to trust. Get the boundaries right and you get a system where each participant does exactly what it's good at, with exactly the access it needs.

The industry has strong intuitions here. Restrict the tool set. Put a deterministic orchestrator at the hub. Sandbox your executors. Martin Fowler calls it [harness engineering](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html). OpenAI built [a methodology](https://openai.com/index/harness-engineering/) around it. LangChain demonstrated it empirically: same model, better infrastructure, [52.8% → 66.5%](https://blog.langchain.dev/langchain-swebench-verified/) on SWE-bench. Zhang and Wang brought [monadic composition theory](https://arxiv.org/abs/2512.22431) from Princeton.

What's missing isn't the practice — it's a unified theory underneath the practice. Each best practice has its own justification ("restricting tools keeps the agent focused," "deterministic orchestration is more reliable"). But why does restriction help? Why does determinism belong at the hub specifically? Why are these the same insight? A formal account — grounded in properties of the participants rather than case-by-case experience — would connect the intuitions and make them predictive.

This series proposes one. It starts by noticing that every multi-agent system, regardless of framework, has the same four kinds of participant.

---

## Who's in the room

Strip away the framework-specific terminology — LangChain's "chains," CrewAI's "crews," AutoGen's "agents" — and every multi-agent system has the same four kinds of participant. They map to the four message roles in any LLM API (`user`, `assistant`, `tool`, `system`), and they're present in every agent framework whether or not the framework names them.

### The Principal

The entity on whose behalf the conversation happens. In Claude Code: you, the developer at the terminal. In a pipeline: whatever entity initiated the work and holds accountability.

The Principal sees rendered output — formatted markdown, tool call summaries, status indicators. It does NOT see the system prompt, token counts, budget remaining, or permission configuration internals.

The Principal's contribution is unique: goals, context, authorization. It brings the physical world — expertise, intent, information that no other participant can access. When a tool call requires approval, the Principal decides. When the conversation needs direction, the Principal provides it.

What makes the Principal structurally distinct: its output space is unbounded. It can say anything, paste anything, decide anything. You'd need the person to describe what they might produce.

### The Inferencer

The entity that performs non-deterministic inference. The language model.

The Inferencer sees a token window — a flat sequence constructed from the structured conversation state. System prompt, history, tool descriptions, project context. Filtered, compacted, arranged. The Inferencer doesn't know what was excluded.

Each call is stateless. The model has no memory between turns — what feels like continuity is previous outputs included in the next input. The model produces structured output: text blocks and tool call proposals. The key word is *proposals*. The Inferencer cannot read files, execute commands, or take actions. It can only propose that these things happen, and receive results in its next input.

What makes the Inferencer structurally distinct: its output space is rich but bounded by fixed weights. You'd need the weights to describe what it might produce — billions of pathways, but the same billions every time.

### The Executor

An entity that performs specific computation within a bounded world. Read, Write, Bash, Grep, Glob — each is an Executor.

The Executor sees exactly two things: its arguments and its sandbox. Not the conversation, not the user's question, not the model's reasoning. It receives inputs, does its work, and returns a result.

What makes the Executor structurally distinct: its output space is trivially describable — "a string, or an error." The complexity comes from the *world*, not the actor. A Read tool's output depends on what's in the file. The tool itself is simple. And crucially, the *same* tool in different sandboxes has different output spaces — the Executor's complexity is borrowed from whatever world it's allowed to inhabit.

### The Harness

The entity that connects the other three. In Claude Code, this is the client process — the thing running in your terminal. The name comes from the same place Fowler and OpenAI landed independently: a harness doesn't do the work (the horse does) and doesn't decide where to go (the driver does). It connects capability to direction. The language model is the horse; the Principal is the driver; the Harness is what makes the connection.

The Harness sees everything the others see and more. It sees the structured conversation state — what we'll call `Conv_State` — with compartment boundaries, token counts, budget, tool registry, permission tables, system prompt. It sees what each actor sees (because it *constructs* those views) plus metadata none of them have access to.

What the Harness does:
- **Constructs scope** — decides what the Inferencer sees (which messages to include, what to compact, which tools to describe)
- **Gates permissions** — decides whether tool proposals are executed (auto-allow, ask the Principal, auto-deny)
- **Manages state** — tracks budget, triggers compaction, maintains tool registry
- **Dispatches execution** — sends arguments to Executors, collects results
- **Renders output** — transforms raw responses into what the Principal sees

What makes the Harness structurally distinct: its output space is *characterizable*. Given its configuration and state, you can describe what it will do. You can enumerate its possible actions. You can read its rules. You can audit its decisions. The Harness is the most powerful participant precisely because it's the least autonomous — its power is architectural, not inferential.

---

## What nobody sees

The most interesting thing about a multi-agent interaction is the information that *doesn't* cross boundaries.

**The Principal doesn't see:** the system prompt. The token budget. The compaction decisions. Which previous messages were summarized vs. preserved. What temperature the model ran at. The internal structure of the conversation state.

**The Inferencer doesn't see:** the raw structured state. Token counts. Budget. Permission configuration. What was excluded from its input. What the Principal looks like, what time it is, whether the user is frustrated or delighted.

**Each Executor doesn't see:** anything except its arguments and its sandbox. Not the question that prompted the call. Not the reasoning that selected it. Not what other Executors are doing in parallel.

**The Harness doesn't see:** the Principal's intent. The Principal's expertise. The Principal's judgment about whether this is the right approach. The physical world beyond what's been explicitly provided.

Each actor operates in a different projection of the same underlying reality. The gaps between projections aren't limitations — they're the architecture. The model doesn't see the token budget because metacognition about budget is less valuable than reasoning about the task. The tool doesn't see the conversation because it doesn't need it. The Principal doesn't see the system prompt because it's not for them.

The negative space — what each actor *can't* see — is what makes each actor's scope useful. The tool-selection agent doesn't see the worker's line-by-line analysis, and that's *why* it can think clearly about tool selection. The worker doesn't see the selection rationale, and that's *why* it can focus on the code.

This is the structural insight the series formalizes: the exclusions aren't incidental. They're load-bearing.

---

## The star topology

Every message passes through the Harness. No actor communicates directly with any other:

```
                    Principal
                       ↕
Executor ←→ Harness ←→ Inferencer
                       ↕
                    Executor
```

The Inferencer never talks to an Executor. The Principal never talks to the Inferencer directly (it talks to the Harness, which constructs the Inferencer's input). The Executor never talks to the Principal (the Harness renders its output).

Why this topology? Because the hub must be the participant whose behavior everyone else can reason about. If you put the model at the hub — an LLM deciding which agents run, managing state, routing messages — the system's behavior becomes as hard to characterize as the model itself. If you put the Principal at the hub, every decision requires human attention. If you put an Executor at the hub, you get a static pipeline with no adaptation.

The Harness works at the hub because you can describe what it will do. Its rules are readable. Its decisions are traceable. Other actors can reason about what mediation will do to their proposals. This isn't an accident — it's the central architectural principle that the rest of this series explains.

---

## The turn cycle

Every interaction follows the same pattern:

**Extract:** The Harness constructs a view for an actor. For the Inferencer: scope the conversation state, flatten, tokenize. For an Executor: package the arguments. For the Principal: render the response.

**Process:** The actor does its work. For the Inferencer: a forward pass through the weights. For an Executor: computation in its sandbox. For the Principal: reading, thinking, typing. This step is opaque to everyone else — it's the actor's own space, and it's where the actors differ most.

**Inject:** The result enters the conversation through the Harness. The Harness checks permissions (for tool proposals), formats results, updates the conversation state, and decides what to include in the next extraction.

Extract → process → inject. Compress → compute → expand. The Harness controls the first and last steps. The middle step is the actor's business.

This cycle repeats at every scale. A tool call: extract arguments → execute → inject result. A sub-agent conversation: extract scope → run conversation → inject summary. The outer conversation itself: extract the Principal's message → process (possibly many internal cycles) → inject the rendered response. Same structure, different actors, every level.

---

## A concrete trace

The planner/worker/reviewer system from the opening has all four actors at every level — Principals, Inferencers, Executors, and Harnesses nested inside each other. Before we get to that complexity, here's the simplest case: one user, one model, one tool call. All four actors are already present.

| Step | Actor | Action | What it sees |
|---|---|---|---|
| 1 | Principal | Types the question | The terminal, the project, their intent |
| 2 | Harness | Constructs `Conv_State`, extracts the Inferencer's view | Full structured state |
| 3 | Inferencer | Forward pass → proposes Read("src/main.py") | Token window (flattened, scoped) |
| 4 | Harness | Permission check → auto-allow. Dispatches Read. | `Conv_State` + permission config |
| 5 | Read (Executor) | Reads the file in its sandbox | File path + sandbox config |
| 6 | Harness | Injects result, re-extracts for the Inferencer | Updated state |
| 7 | Inferencer | Forward pass → "Here's what's in src/main.py: ..." | Updated token window |
| 8 | Harness | Renders response for Principal | Updated state |
| 9 | Principal | Reads the answer | Rendered markdown |

Nine steps. Four actors. Three complete extract → process → inject cycles. Every boundary mediated by the Harness.

Step 4 is where the architecture becomes visible. The model *proposed* reading a file. The Harness *decided* to allow it. The Executor *did* it. The Harness *injected* the result. If the proposal had been `Bash("rm -rf /")`, step 4 diverges — the Harness asks the Principal for permission, and the Principal's judgment determines whether the conversation's scope expands to include that tool's output space.

The permission gate isn't just security — it's *scope management*. Every permission decision shapes what the conversation can become. Every denial is a future the conversation won't explore. Every grant widens the space of possible outcomes.

---

## The question, sharpened

We've identified the participants. Four actors, four different views of one state, one star topology with the most characterizable actor at the hub.

Here's what's interesting. Each of these actors takes an input and produces an output. Between input and output, there's a space — the space of ways the actor could get from one to the other. For the Read tool, there's essentially one way: look up the file, return the contents. For the Harness, there are several ways, but you can enumerate them from its rules. For the Inferencer, there are billions of ways — every path through the weights. For the Principal, there are... more.

Can we measure that space? Not the outputs — the *ways of arriving at outputs*. Not unpredictability (a hash function is unpredictable but has one way). Not hidden state (a lookup table has vast state but one way). The actual space of paths between input and output — how many distinguishable routes through the computation an input could take.

If you can measure it, everything we've observed falls out. Why the Harness belongs at the hub. Why restriction helps. Why the same model with different tools is a different system. Why some architectures are auditable and others aren't. One property, one axis, four actors at different positions on it.

The next post gives it a name.

---

*Next: [The Space Between →](02-the-space-between.md)*
