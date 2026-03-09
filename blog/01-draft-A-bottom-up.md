# The Four Actors

*Draft A: Bottom-up. Start with a specific interaction, discover the actors empirically.*

---

## A file read

You're using Claude Code. You type: "What's in src/main.py?"

What happens next involves four participants, three scope boundaries, a permission check, and a comonad extraction. But from where you're sitting, it looks like this:

```
You:     "What's in src/main.py?"
Claude:  [reads the file]
Claude:  "Here's what's in src/main.py: ..."
```

Two messages. One action. Simple.

It isn't simple. Between your message and that response, four distinct entities participated — each seeing a different projection of the same underlying state, each with different capabilities, each contributing something the others can't.

---

## Who's in the room

### You (the Principal)

You see the terminal. Rendered markdown, tool call summaries, status indicators. You don't see the system prompt. You don't see token counts or budget remaining. You don't see the permission configuration or compaction decisions. You see what the Harness decides to render.

Your capabilities are unique: you can grant or deny permissions, provide goals, share context from the physical world (paste a file, describe a bug, reference a conversation from yesterday). No other participant has access to your intent, your expertise, or your judgment about what matters.

Your contribution to this interaction: the question. But also: the implicit authorization context (you're in a project directory, you've been working on this code, the question is routine). The system knows this because the Harness constructed a context that includes your project's CLAUDE.md, your recent conversation history, your permission settings.

### The model (the Inferencer)

The model sees a token window — a flat sequence of tokens constructed by the Harness. This includes the system prompt (you never see this), your message, tool descriptions, conversation history, and project context. It's filtered, compacted, and arranged. The model doesn't know what was excluded.

The model performs a single forward pass through fixed weights. It has no memory of previous turns — what feels like memory is the Harness including previous messages in the current input. It proposes an action: "I'd like to call the Read tool with the argument 'src/main.py'."

This is a *proposal*, not an action. The model can't read files. It can't execute tools. It can only propose that something be done, and wait for the result to appear in its next input.

### The Read tool (an Executor)

The Read tool sees exactly two things: a file path and a sandbox. It doesn't see your message, the conversation history, the system prompt, or the model's reasoning. It receives arguments, does its work within its allowed world (the sandbox — `allowed_directories`, no network access), and returns a result: the file contents, or an error.

The Read tool's output space is trivially describable: "a string, or an error." This is important — it means everyone can reason about what the tool might produce without knowing anything about the tool's implementation.

### The client (the Harness)

The Harness is Claude Code itself — the process running in your terminal. It sees everything: the structured conversation state with compartment boundaries, token counts, budget remaining, permission configuration, tool registry, system prompt, your message, the model's response.

Before the model sees anything, the Harness:
1. Took your message and constructed `Conv_State` — the structured conversation state
2. Chose which messages to include and which to compact
3. Decided which tools to make available
4. Flattened and tokenized the whole thing into the model's input

After the model proposed Read("src/main.py"), the Harness:
5. Checked the permission configuration — Read is auto-allowed for project files
6. Dispatched the Read tool in its sandbox
7. Received the result
8. Injected the result into the conversation state
9. Reconstructed the model's input (now including the file contents)
10. Sent it back for the model to produce the final response

After the model responded, the Harness:
11. Rendered the response for you — formatted markdown in the terminal

The Harness touched every boundary. It mediated every message. It constructed what the model saw, gated what the model could do, and rendered what you saw. And every one of those decisions is *characterizable* — you could describe what the Harness will do given its configuration and the current state. It follows rules, not intuition.

---

## What nobody sees

The most interesting thing about this interaction is the information that *didn't* cross boundaries.

**You didn't see:** The system prompt. The token budget. The compaction decisions. Whether the Harness considered compacting history before this turn. What temperature the model ran at.

**The model didn't see:** The raw `Conv_State` structure. The token count. The budget. The permission configuration details. Which previous messages were compacted vs. preserved verbatim. What you look like, what time it is, whether you're frustrated.

**The Read tool didn't see:** Anything except its arguments and its sandbox. Not your question. Not the model's reasoning. Not the conversation history.

**The Harness didn't see:** Your intent. Your expertise. Your judgment about whether this is the right file to read. Your physical world. What you'll do with the answer.

Each actor operates in a different projection of the same underlying reality. The gaps between projections aren't bugs — they're the architecture. The model doesn't see the token budget because that would waste tokens on metacognition instead of the task. The tool doesn't see the conversation because it doesn't need it. You don't see the system prompt because it's not for you.

The negative space — what each actor *can't* see — is what makes each actor's scope useful. This is the structural insight the series formalizes.

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

The model never talks to the tool. You never talk to the model (you talk to the Harness, which constructs the model's input). The tool never talks to you (the Harness renders its output).

This isn't just an implementation detail — it's load-bearing architecture. The Harness mediates every boundary because the Harness is the only participant whose behavior is fully characterizable given its configuration. You can describe what the Harness will do. You can audit it. You can read its rules. You cannot do this for the model (too complex), for you (too unbounded), or for the tool's world interactions (too dependent on external state).

The star topology puts the most characterizable actor at the hub. This is not a coincidence.

---

## The turn cycle

Every turn follows the same pattern:

1. **Extract** — The Harness constructs a view for the actor (scope selection, context assembly, flattening)
2. **Process** — The actor does its thing (opaque to everyone else)
3. **Inject** — The result enters the conversation through the Harness (permission gating, result formatting, state update)

Extract → process → inject. Compress → compute → expand. The Harness controls steps 1 and 3. Step 2 is the actor's own business — its internal space, its *ma*.

This cycle repeats at every scale. The outer conversation is extract → infer → inject. A sub-agent call is extract → sub-conversation → inject. A tool call is extract → execute → inject. Same structure, different actors. The Harness at every boundary.

---

## The most powerful participant

The Harness is the least discussed and most consequential participant in any agent system. It determines:

- What the model sees (scope construction)
- What the model can do (tool availability)
- Whether the model's proposals are executed (permission gating)
- What you see (rendering)
- When context is compressed (compaction)
- How budget is spent (resource management)

Every one of these is a design decision that shapes the conversation's trajectory. The LangChain result — same model, better harness, 52.8% → 66.5% on SWE-bench — is a Harness story. Nothing about the model changed. Everything about what the model saw and could do changed.

Martin Fowler calls this harness engineering. OpenAI built a methodology around it. We're asking the next question: *what makes a good Harness good?*

The answer has to do with the space between what each actor receives and what it produces — a concept the next post calls *ma*. But the observation comes first: four actors, four different views, one star topology, and the most characterizable actor at the hub.

---

*Next: [The Space Between →](02-the-space-between.md)*
