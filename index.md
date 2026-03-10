# Your Agent Is a Different System Than You Think It Is

*Everything the Ma of Multi-Agent Systems series says, for people who were going to ask an agent to summarize it anyway.*

---

I spent the last ~few months~ **few nights** building a formal theory of multi-agent systems. It's nine posts, a formal companion with proofs, case studies. It draws on programming language theory, cybernetics, and capability-based security. It's called *The Ma of Multi-Agent Systems* and I'm genuinely think it is insightful — if it actually holds up through more rigorous review. 

You are not going to read it.

I know this because you're a vibe coder — someone building real things with AI agents, shipping features, prototyping apps, maybe running a small team that just discovered Claude Code or Cursor can do in an afternoon what used to take a sprint. You don't have time for lattice theory. You need to know what to do Monday morning.

So here's the cheat sheet. Seven things the theory says that will actually change how you build.

---

## 1. The tools matter more than the model

This is the single most counterintuitive result and the one with the most evidence behind it.

LangChain tested the same model with a better orchestrator and went from 52.8% to 66.5% on SWE-bench. Same weights. Same training. Different tools, different scoping, different rules about what the agent could do. The infrastructure around the model moved the needle more than the model itself.

The theory explains why with something called *supermodularity*: the cost of giving an agent broad access to the world is proportional to how complex the model is internally. A massive model with three tools (Read, Approve, Reject) is easy to reason about — it can only do three things. A tiny model with fifty tools is a nightmare — it can do fifty things badly. Restricting the tool set saves you more when the model is more powerful, not less.

**The practical version:** Before you upgrade from Sonnet to Opus, ask whether your current model is bottlenecked by its reasoning or by what you're giving it to work with. Nine times out of ten, it's the tools.

---

## 2. Bash is not a tool. It's a portal to a different universe.

There's a line in the taxonomy of tools that changes everything, and most agent builders cross it without noticing.

A `Read` tool takes an address and returns data. You can describe everything it might do: "given a path, returns the file contents or an error." That's it. A `grep` tool takes a pattern and returns matches. Also fully describable.

A `Bash` tool takes a string and *executes it as a program*. The string could be `cat README.md`. It could be `rm -rf /`. It could be a thousand-line Python script that installs packages, opens network connections, and modifies every file in your project. You literally cannot describe what it might do, because describing what an arbitrary program does is equivalent to solving the halting problem. This isn't a metaphor — it's a proven result in computer science (Rice's theorem).

The theory calls this the *computation channel* boundary. Below it, your agent picks from a menu. Above it, your agent writes new menu items. Below it, the orchestrator can vet every action. Above it, the orchestrator is reduced to pattern-matching on the command string and hoping for the best.

**The practical version:** Every time you give an agent Bash access, you're not adding a tool. You're changing what kind of system you're running — from a bounded lookup machine to a universal computer. Treat it accordingly. Sandbox it. Restrict the filesystem. Kill the network. Put resource limits on it. The sandbox isn't security theater — it's the only thing standing between "agent that reads files" and "agent that can do literally anything a computer can do."

---

## 3. Two simple agents talking to each other aren't simple anymore

Here's the one that surprises people.

Say you have Agent A (a researcher) with read-only tools — grep, glob, file read. Convergent dynamics. Can't modify anything. Safe. And Agent B (an implementer) with edit and write tools, also individually manageable. You connect them: A sends findings to B as natural language, B implements them.

You now have a computation channel.

A sends natural language instructions. B interprets them using a massive neural network and executes them with real tools. From A's perspective, B is a tool that accepts a program (the instructions) and runs it (using B's full capabilities). The fact that the "program" is English and the "interpreter" is an LLM doesn't change the structure. Two agents that were individually below the computation channel boundary just composed into a system above it.

The math says characterization difficulty grows as the *product* of the two context windows, not the sum. One agent with 200k context: linear complexity. Two agents with 100k context each talking in natural language: quadratic. Three agents: cubic. Still finite — context windows bound everything — but the growth rate changes with every agent you add.

**The practical version:** Put structure at every boundary between agents. Don't let Agent A send freeform text to Agent B. Define a schema. Agent A outputs structured findings (file, line number, issue type, description). Agent B consumes structured input. The schema caps the complexity at the boundary. Growth goes back to linear. This is called a *co-domain funnel* in the theory — deep reasoning compressed through a narrow, structured interface.

---

## 4. The boring orchestrator is the most important part

In every agent system — LangChain, CrewAI, Claude Code, your custom thing — there's an entity that connects the pieces. It decides what the model sees, whether tool calls go through, what gets included in the next prompt. The theory calls it the Harness. Martin Fowler calls it the harness. OpenAI calls it the harness. Everyone landed on the same word independently.

The Harness belongs at the center of the architecture for one reason: it's the only participant whose behavior you can fully describe by reading its rules. The model's behavior requires the weights to describe. The human's behavior requires being the human. The tools' behavior depends on the state of the world. But the orchestrator? It's code. You can read it. You can audit every decision it makes.

The theory formalizes this as a *preorder* — a ranking of who can reason about whom. Everyone can reason about what the orchestrator will do (because it's specified). The orchestrator can reason about what the tools will do (because they're simple). Nobody can reason about what the model will do (because simulating the model costs as much as running the model). The orchestrator works at the hub because trust flows from the predictable to the unpredictable, not the other way.

This means: don't put an LLM in the execution loop. An LLM deciding in real time whether to allow a tool call, evaluating safety on the fly, routing messages based on opaque reasoning — that makes your orchestrator as unpredictable as the model. You've replaced your foundation with a guess.

However — and this is a meaningful "however" — there's a difference between putting trained judgment *in* the execution loop and using trained judgment to *design* the execution loop before it runs. Call it the quartermaster pattern: a sub-agent that receives a problem description and outputs a structured kit — which tools to grant, what permissions to set, what instructions to include, what sandbox constraints to apply. The quartermaster packs the bag. It doesn't go on the mission.

The theory predicts this should work. The kit is structured output: you can read what was selected, inspect it, reject it before anything runs. The orchestrator stays deterministic — it executes the kit with boring rules. The intelligence was in the setup, not the execution. The quartermaster can even include a complexity assessment of its own output, flagging when the resulting tool set looks too broad.

I want to be honest: this is a speculative pattern, not established practice. It adds a full inference call to the configuration step — latency, cost, its own failure modes. The quartermaster's tool selection could be wrong in subtle ways that only show up during execution. And it's an untested idea from the same person who wrote the theory that predicts it works, which is exactly the kind of thing you should be skeptical about. But the naive version of this point — "never use LLMs in orchestration, period" — draws the line in the wrong place. There's a promising middle ground between "LLM as traffic cop" and "LLM forbidden from the building." It just hasn't been battle-tested yet.

**The practical version:** Hard rule: don't put an LLM in the execution loop. No LLM-based routing, no LLM-based safety evaluation, no trained judgment making real-time orchestration decisions. Softer idea, worth exploring: using an LLM to *design* the per-task configuration — selecting tools, setting permissions, writing instructions — that a deterministic orchestrator then executes. The kit is readable, auditable, and rejectable before anything runs. Whether this is a genuine advance or a clever-sounding anti-pattern is an open question. But it's a question worth asking.

---

## 5. Context management is your single biggest lever

The model has fixed weights. Its internal complexity doesn't change between turn 1 and turn 100. What changes is the input — the context window that the Harness constructs fresh every turn.

Here's what most people miss: as context grows, the number of reachable paths through those fixed weights grows too. More tokens means more attention interactions, which means more of the model's capacity gets activated. At 1,000 tokens, roughly 500,000 attention pairs per layer. At 100,000 tokens, roughly 5 billion. Same model. Vastly more complex behavior.

This means context management — what you put in the prompt, when you summarize, when you drop old messages — simultaneously controls two things: what the model knows about (world coupling) and how complex its behavior can be (reachable decision surface). Compacting context reduces both at once. It's the only operation that moves both axes of complexity down simultaneously.

**The practical version:** Don't just think of context management as "fitting within the token limit." Think of it as controlling how complex the system's behavior can get. Long contexts make the agent more capable but harder to predict. Aggressive summarization makes the agent more predictable but potentially less capable. Find the sweet spot for your use case. And when things go weird in a long conversation, the first thing to try is a fresh context with a better-constructed summary of what matters.

---

## 6. The orchestrator can get smarter without getting less predictable

There's a trap that security systems fall into: as the thing being monitored gets more complex, you add ML-based anomaly detection to keep up, and now your *monitor* is as opaque as the thing it's monitoring. The theory calls this the Ashby trap — the regulator becoming as complex as the regulated system.

The escape is that the orchestrator can increase what it *observes* without increasing how it *decides*. Monitor the process tree — with specified rules. Track filesystem changes — with specified rules. Audit network connections — with specified rules. More eyes, same brain. The operating system proves this works at any scale: Linux manages every process, file handle, network socket, and memory page on the machine, and you can read every line of code that does it.

The theory calls this the *specified band* — the region where the decision surface stays transparent regardless of how much world the system watches. The moment you replace specified rules with trained judgment in the orchestrator (like an LLM deciding whether a tool call is safe), you've left the specified band. The orchestrator becomes opaque. Your foundation is gone.

**The practical version:** Permission rules should be `if tool == "bash" then ask_user`. Not `if llm_thinks_this_is_dangerous then deny`. Rules you can read. Rules you can audit. Rules that don't require a PhD to predict. When you need to handle more complexity, add more rules — don't add more intelligence to the rule-evaluator.

---

## 7. Your system will teach itself to need less AI over time (if you let it)

This one comes from building real tools rather than from pure theory.

We built Fledgling, a code navigation server for AI agents, by querying conversation logs. What bash commands did the agent run most? Which ones succeeded consistently? Turns out: `grep -r` constantly. `find . -name` constantly. `cat` on specific files. Simple, predictable, read-only operations that succeeded almost every time.

Each of those was a Bash call — full computation channel, maximum complexity, the entire weight manifold of a frontier model engaged to produce... a grep. So we promoted them into structured tools: `search(pattern, path)`, `find_definitions(name)`. Same functionality. The command that was an arbitrary string sent to a universal machine became a structured query with a known interface.

The theory calls this the *configuration ratchet*: high-complexity exploration produces artifacts that enable low-complexity application. The ratchet only turns one way — once you've crystallized a pattern into a structured tool, it doesn't spontaneously become a bash call again. Over time, more of the work happens through specified tools and less through raw inference. The system gets more predictable with use, without changing the model.

**The practical version:** Log everything. Look at what your agents actually do. The patterns that emerge — the bash commands that work every time, the tool sequences that repeat, the configurations that succeed — are candidates for promotion into structured tools. Every pattern you promote moves a piece of your system from "requires AI judgment" to "handled by a lookup." The AI still handles the frontier. The routine becomes infrastructure.

---

## The one-sentence version

The tools you give an agent define a harder problem than the model you choose to solve it, so pick your tools carefully, put structure at every boundary, keep your orchestrator boring and readable, and log everything so the system can teach itself to need less AI over time.

That's it. That's thirty thousand words of lattice theory in one sentence.

If you want the thirty thousand words, they're in [the series](series.md). If you want the formal proofs, there's a [formal companion](blog/formal-companion.md). If you want the worked [case studies](blog/case-studies.md), those exist too. But if all you needed was the practical upshot — you've got it.

Now go build something.

---

*This is the accessible companion to [The Ma of Multi-Agent Systems](blog/00-intro.md), a nine-post series with a formal companion developing a design theory for multi-agent architecture. The theory is built on programming language theory (closures, algebraic effects), cybernetics (Ashby's variety), and capability-based security (Miller's object capabilities). The blog post you just read is what falls out when you strip the math and keep the engineering.*

```{toctree}
:hidden:

series
```
