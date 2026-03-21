# The Ratchet Review

*Everything the Ma of Multi-Agent Systems series says, for people who build things.*

---

I spent a few months building a formal theory of multi-agent systems. Nine posts, a formal companion with proofs, case studies. It draws on programming language theory, cybernetics, and capability-based security. It's called [The Ma of Multi-Agent Systems](../ma/00-intro.md) and I think it holds up.

You are not going to read it.

I know this because you're building real things with AI agents — shipping features, prototyping apps, maybe running a small team that just discovered Claude Code or Cursor can do in an afternoon what used to take a sprint. You don't have time for lattice theory. You need to know what to do Monday morning.

So here's the cheat sheet. Seven things the theory says that will change how you build. And then the organizing principle that ties them together — the ratchet — which is what this series is actually about.

---

## The ratchet

Here's the thesis up front, before the rules: **your system will teach itself to need less AI over time, if you instrument it to learn from its own failures.**

Every failed tool call, every permission denial, every timeout, every pattern the agent tries that doesn't work — that's data about where your configuration doesn't match the task. Capture those failures. Analyze them. Crystallize the patterns into specified tools and constraints. Each cycle converts a piece of high-complexity behavior into low-complexity infrastructure.

The ratchet only turns one way. Each promotion moves a behavior from "requires inference" to "handled by lookup." The specified base grows monotonically. The system gets more trustworthy with use — not because the model improved, but because the configuration layer accumulated evidence.

Failures are the fuel. This series shows you how to burn them.

---

## Seven rules

### 1. The tools matter more than the model

LangChain tested the same model with a better orchestrator and went from 52.8% to 66.5% on SWE-bench. Same weights. Same training. Different tools, different scoping, different rules. The infrastructure moved the needle more than the model. Nate Crandall [found the same thing](https://natesnewsletter.substack.com/p/same-model-78-vs-42-the-harness-made) comparing coding harnesses: the same model scored 78% in one harness and 42% in another. Your harness determines your grade. Different grade, different outcomes.

The theory explains why: the cost of giving an agent broad access is proportional to how complex the model is internally. A massive model with three tools (Read, Approve, Reject) is easy to reason about — it can only do three things. A tiny model with fifty tools is a nightmare. Restricting the tool set saves you *more* when the model is more powerful.

**Before you upgrade from Sonnet to Opus, ask whether your current model is bottlenecked by its reasoning or by what you're giving it to work with.** Nine times out of ten, it's the tools.

### 2. Bash is not a tool — it's a portal to a different universe

A `Read` tool takes an address and returns data. You can describe everything it might do. A `Bash` tool takes a string and *executes it as a program*. The string could be `cat README.md`. It could be `rm -rf /`. You literally cannot describe what it might do — that's a proven result in computer science (Rice's theorem).

Below the computation channel boundary, your agent picks from a menu. Above it, your agent writes new menu items. Below it, the orchestrator can vet every action. Above it, the orchestrator is pattern-matching on command strings and hoping.

**Every time you give an agent Bash access, you're changing what kind of system you're running** — from a bounded lookup machine to a universal computer. Sandbox it. Restrict the filesystem. Kill the network. The sandbox isn't security theater — it's the only thing standing between "agent that reads files" and "agent that can do literally anything a computer can do."

### 3. Two simple agents talking to each other aren't simple anymore

Agent A (researcher) has read-only tools. Safe. Agent B (implementer) has edit and write tools. Manageable. Connect them with natural language — A sends findings, B implements them.

You now have a computation channel. A sends instructions. B interprets them with a massive neural network and executes them with real tools. The characterization difficulty grows as the *product* of the two context windows, not the sum.

**Put structure at every boundary between agents.** Define a schema. Agent A outputs structured findings. Agent B consumes structured input. The schema caps the complexity. Growth goes back to linear.

### 4. The boring orchestrator is the most important part

The Harness — the thing that connects the pieces — belongs at the center for one reason: it's the only participant whose behavior you can fully describe by reading its rules. The model's behavior requires the weights to describe. The human's behavior requires being the human. But the orchestrator? It's code. You can read it.

**Don't put an LLM in the execution loop.** No LLM-based routing, no LLM-based safety evaluation, no trained judgment making real-time orchestration decisions. Rules you can read. Rules you can audit. When you need more complexity, add more rules — don't add more intelligence to the rule-evaluator.

### 5. Context management is your single biggest lever

As context grows, the number of reachable paths through the model's fixed weights grows too. More tokens means more attention interactions. At 1,000 tokens, roughly 500,000 attention pairs per layer. At 100,000 tokens, roughly 5 billion. Same model. Vastly more complex behavior.

Context management simultaneously controls what the model knows about *and* how complex its behavior can be. Compacting context reduces both at once.

**When things go weird in a long conversation, the first thing to try is a fresh context with a better-constructed summary of what matters.**

### 6. The orchestrator can get smarter without getting less predictable

The trap: as the monitored system gets more complex, you add ML-based anomaly detection, and now your *monitor* is as opaque as the thing it monitors.

The escape: the orchestrator can increase what it *observes* without increasing how it *decides*. Monitor the process tree — with specified rules. Track filesystem changes — with specified rules. More eyes, same brain. Linux manages every process, file handle, network socket, and memory page on the machine, and you can read every line of code that does it.

**Permission rules should be `if tool == "bash" then ask_user`. Not `if llm_thinks_this_is_dangerous then deny`.**

### 7. Your system will teach itself — if you let it

We built [Fledgling](https://github.com/teaguesterling/fledgling) by querying conversation logs. What bash commands did the agent run most? Which succeeded consistently? Turns out: `grep -r` constantly. `find . -name` constantly. Simple, predictable, read-only operations.

Each was a Bash call — the full weight manifold of a frontier model engaged to produce a grep. So we promoted them into structured tools: `search(pattern, path)`, `find_definitions(name)`. Same functionality. The command that was an arbitrary string sent to a universal machine became a structured query with a known interface.

**Log everything. Look at what your agents actually do. The patterns that emerge are candidates for promotion into specified tools.** Every pattern you promote moves a piece of the system from "requires AI judgment" to "handled by a lookup."

---

## The one-sentence version

The tools you give an agent define a harder problem than the model you choose to solve it, so pick your tools carefully, put structure at every boundary, keep your orchestrator boring and readable, and log everything so the system can teach itself to need less AI over time.

---

## This series

The rules tell you what to do. This series tells you *how* — with code that ships, patterns that transfer, and metrics that tell you whether it's working.

**[Fuel](01-fuel.md)** — The failure stream as product roadmap. What your agent's failures are telling you, and DuckDB queries to extract the signal.

**[The Two-Stage Turn](02-the-two-stage-turn.md)** — Discovery and crystallization. You can't skip either one. The Fledgling origin story.

**[Where the Failures Live](03-where-the-failures-live.md)** — The placement principle. Where do you want the failures to happen? In planning (cheap) or in execution (expensive)?

**[The Failure-Driven Controller](04-the-failure-driven-controller.md)** — Four modes, failure-triggered transitions, and a controller that stays specified. Prototype mode controller ships.

**[Closing the Channel](05-closing-the-channel.md)** — The hinge. You build a tool, watch a computation channel close, and understand why the grade dropped. Complete tool ships.

**[The Segment Builder](06-the-segment-builder.md)** — Data platform case study. The ratchet applied to population segments. DuckDB segment builder ships.

**[The Classification Engine](07-the-classification-engine.md)** — Second case study. Access control as co-domain funnel. DuckDB access control layer ships.

**[Teaching Without Theory](08-teaching-without-theory.md)** — How to bootstrap agents and teams without explaining lattice theory. CLAUDE.md files, onboarding docs, and code review checklists are all ratchet artifacts.

**[The Organizational Star](09-the-organizational-star.md)** — The framework isn't about AI. Person, team, and organization as multi-actor systems.

**[Ratchet Metrics](10-ratchet-metrics.md)** — What to measure: ratchet rate, trust gap, failure stream composition, mode utilization. DuckDB dashboard ships.

---

## Two paths

Want to build? [Keep reading](01-fuel.md).

Want the theory? [The Ma of Multi-Agent Systems](../ma/00-intro.md) develops the formal framework — nine posts of lattice theory, a formal companion with proofs, and case studies. Everything here has a formal treatment there.

Now go build something.

---

*This is the practitioner companion to [The Ma of Multi-Agent Systems](../ma/00-intro.md). The theory is a work in progress. The ratchet is already turning.*
