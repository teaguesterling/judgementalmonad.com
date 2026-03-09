# The Four Actors

*Draft B: Taxonomic. Start with the API roles, derive the actors, define each.*

---

## Four roles

Every LLM API has the same message roles: `user`, `assistant`, `tool`, `system`. Every agent framework — LangChain, CrewAI, AutoGen, Claude Code — uses all four. The roles aren't arbitrary. They reflect four structurally distinct kinds of participant.

| API role | Actor | What it does |
|---|---|---|
| `user` | **Principal** | Directs. Authorizes. Provides goals and judgment. |
| `assistant` | **Inferencer** | Proposes. Reasons over context. Generates structured output. |
| `tool` | **Executor** | Computes. Reads, writes, transforms within a bounded world. |
| `system` | **Harness** | Connects. Constructs scope, gates permissions, manages state. |

The first three get most of the attention. The fourth — the `system` role made concrete — is the most consequential and least understood.

---

## The Principal

The entity on whose behalf the conversation happens. In Claude Code, that's you — the developer at the terminal. In a pipeline, it might be another agent, or a cron job, or an API caller.

**What it sees:** The rendered output. Formatted markdown, tool call summaries, status indicators. NOT the system prompt, NOT token counts, NOT permission configuration internals.

**What it provides:** Goals, context, authorization decisions. The Principal is the source of intent and the final authority on permissions. When the Harness encounters a tool call that requires approval, it asks the Principal. When the conversation needs direction, the Principal provides it.

**What makes it structurally unique:** The Principal's output space is unbounded. It can say anything, paste anything, decide anything. It brings the physical world — expertise, intent, context that no other participant can access. Its contribution cannot be characterized by a type signature. In the framework's terms: its *ma* is constitutive. You'd need the person to describe what they might produce.

---

## The Inferencer

The entity that performs non-deterministic inference. The language model.

**What it sees:** A token window — a flat sequence constructed by the Harness from the structured conversation state. System prompt, conversation history, tool descriptions, project context. Filtered, compacted, arranged. The Inferencer doesn't know what was excluded.

**What it produces:** A structured response: text blocks and tool call proposals. The key word is *proposals*. The Inferencer cannot execute tools. It cannot read files, write code, or run commands. It can only propose that these things happen, and receive results in its next input.

**What makes it structurally unique:** Each call is stateless. The model has no memory between turns — what feels like continuity is the Harness including previous outputs in the next input. The model's output space is rich (any token sequence the weights would produce) but bounded (by the weights, which are fixed). Its *ma* is intrinsic — you'd need the weights to describe what it might produce.

**A common confusion:** "The model is the agent." No. The model is one participant in a conversation that the Harness constitutes. The model proposes; the Harness disposes. The model doesn't even know what tools are available until the Harness tells it.

---

## The Executor

An entity that performs specific computation within a bounded world. Read, Write, Bash, Grep, Glob — each is an Executor.

**What it sees:** Its arguments and its sandbox. Nothing else. Not the conversation, not the user's message, not the model's reasoning. An Executor is invoked with inputs and returns a result.

**What it produces:** A typed result — typically `Either Error Result`. The output space is trivially describable: "a string, or a file listing, or an error." This simplicity is the point — everyone can reason about what an Executor might produce.

**What makes it structurally unique:** The Executor's complexity comes from the *world*, not from the actor. A Read tool's output depends on what's in the file — that's world coupling. The tool itself is simple. Its *ma* is borrowed — the interesting part is what world the Harness lets it inhabit. The same Bash tool in `IO_sandbox` (restricted directories) and `IO_filesystem` (full access) has radically different output spaces. The Harness made that choice, not the tool.

---

## The Harness

The entity that connects the other three. In Claude Code, this is the client process itself — the thing running in your terminal.

**What it sees:** Everything. The structured conversation state: system prompt, instructions, history with turn boundaries, tool registry, token budget, permission configuration. It sees the compartments that the Inferencer sees flattened and the Principal sees rendered.

**What it does:**
- **Constructs scope** — decides what the Inferencer sees (which messages to include, what to compact, which tools to describe)
- **Gates permissions** — decides whether tool proposals are executed (auto-allow, ask the Principal, auto-deny)
- **Manages state** — tracks budget, triggers compaction, maintains tool registry
- **Dispatches execution** — sends arguments to Executors, collects results
- **Renders output** — transforms raw responses into what the Principal sees

**What makes it structurally unique:** The Harness's output space is *characterizable*. It's a tagged union of operations: construct a view, check a permission, dispatch a tool, inject a result, compact history, yield. You can enumerate what the Harness might do given its configuration and state. You can read its rules. You can audit its decisions.

This is why it sits at the hub.

---

## The star topology

No actor communicates directly with any other. Every message passes through the Harness:

```
                    Principal
                       ↕
Executor ←→ Harness ←→ Inferencer
                       ↕
                    Executor
```

The Inferencer proposes a tool call → the Harness checks permissions → the Harness dispatches the Executor → the Executor returns a result → the Harness injects the result → the Inferencer sees it in its next input. The Principal is only consulted when the permission mode requires it.

The star topology is not incidental. It falls out of a structural property: the hub must be the participant whose behavior other participants can reason about. The Harness is the only actor whose output space is fully characterizable given its configuration. The model's output requires the weights to describe. The Principal's output requires the person. The Executor's output depends on the world. The Harness's output follows from its rules and state.

Put a high-characterizability actor at the hub, and other actors can reason about what mediation will do. Put a low-characterizability actor at the hub (an LLM doing orchestration), and the system becomes opaque to everyone — including itself.

---

## A concrete trace

To make this tangible: "What's in src/main.py?"

**Step 1: The Harness constructs the Inferencer's view.**

```
Conv_State = {
  system:       [system prompt, CLAUDE.md instructions],
  instructions: [tool descriptions, permission config],
  history:      [...previous turns..., user: "What's in src/main.py?"],
  tools:        {Read, Edit, Write, Bash, Grep, Glob, ...},
  budget:       87000
}
```

The Harness flattens and tokenizes this into the model's input. The model sees a token sequence. The Harness sees structured compartments.

**Step 2: The Inferencer proposes.**

The model produces: `Read("src/main.py")`. A proposal, not an action.

**Step 3: The Harness gates.**

Permission check: Read is auto-allowed for project files. No Principal consultation needed. (If this were `Bash("rm -rf /")`, the Harness would ask you.)

**Step 4: The Executor runs.**

Read receives `("src/main.py", sandbox_config)`. It returns the file contents. It never knew why it was asked.

**Step 5: The Harness injects.**

The result enters `Conv_State`. History grows. Budget decreases. The Harness reconstructs the Inferencer's view, now including the file contents.

**Step 6: The Inferencer responds.**

The model sees the updated view and produces: "Here's what's in src/main.py: ..."

**Step 7: The Harness renders.**

The response is formatted and displayed in your terminal. You see markdown. You don't see the token cost, the permission check, or the scope construction.

Seven steps, four actors, three scope boundaries. Every boundary mediated by the Harness. The most routine interaction in the system, and the architecture is already fully present.

---

## What this post doesn't explain

We've described *what* happens. We haven't explained *why* this architecture works — why the Harness belongs at the hub, why the star topology outperforms alternatives, why restricting what the model sees often improves its output.

The answer is a property that all four actors have in different degrees: the space between what they receive and what they produce. The next post gives it a name.

---

*Next: [The Space Between →](02-the-space-between.md)*
