# The Configuration Ratchet

*How systems convert trained ma into specified ma — and why the specified band expands with use.*

---

## The accident

In early 2026, we were building [Fledgling](https://github.com/teaguesterling/fledgling) — a code navigation MCP server for AI agents. The first design question: which tools should it provide?

The naive approach: sit down, think about what a coding agent needs, design an API. The actual approach: we queried the logs.

Claude Code stores every conversation in a sqlite database. Every tool call, every bash command, every result. We wrote DuckDB macros that queried those logs:

```sql
-- What bash commands does the agent actually run?
-- Which ones succeed consistently?
SELECT command_pattern,
       count(*) as frequency,
       avg(success) as success_rate
FROM tool_calls
WHERE tool = 'bash'
GROUP BY command_pattern
ORDER BY frequency * success_rate DESC;
```

The results were clear. The agent ran `grep -r` constantly. `find . -name` constantly. `cat` on specific files. `wc -l`. Simple, predictable, read-only commands that succeeded almost every time.

Each of these was a Level 4 computation channel — an arbitrary string passed to a universal machine. The full weight manifold of a frontier LLM was engaged to produce... a grep call. Billions of pathways through the weights, and the destination was a specified operation on a bounded filesystem.

So we promoted them. Each frequently successful, low-risk bash pattern became a Fledgling SQL macro: `search(pattern, path)`, `find_definitions(name)`, `read_lines(path)`. Structured queries with known input languages, known effect signatures, known grades. The command that was `(broad, computation channel, level 4)` as a bash call became `(scoped, data channel, level 1)` as a Fledgling macro.

Same functionality. Categorically different grade.

We didn't realize what we were doing at the time. We were just being practical — giving the agent the tools it kept reaching for, in a form that didn't require shelling out to bash. It was only later, after developing the formal framework, that we recognized the pattern.

We were watching a system convert trained *ma* into specified *ma* in real time.

---

## The pattern

Here's what actually happened, step by step:

**Step 1: Exploration.** The LLM, operating with high *ma* (trained decision surface, broad world coupling via bash), explored the space of possible actions. It tried things. Some worked. Some didn't. The exploration was expensive — every bash call engaged the full inference machinery and operated at the highest computation channel level.

**Step 2: Capture.** The conversation logs recorded everything. Not just what the agent did, but what worked. The logs were an append-only record of the agent's exploration — successes, failures, patterns, frequencies.

**Step 3: Evaluation.** DuckDB queries identified which patterns were safe, successful, and frequent. This was specified analysis of captured data — zero trained judgment involved. The queries were simple aggregations over the log.

**Step 4: Promotion.** The winning patterns were crystallized into macros — specified tools with known grades. The knowledge that "agents frequently need to search codebases for patterns" moved from an implicit tendency in the weights to an explicit, named, auditable tool.

**Step 5: Replacement.** With the macros available, the agent no longer needed to shell out to bash for common operations. The same work now happened through specified tools at a lower grade. The system's effective *ma* decreased without any change to the model.

**Step 6: Repeat.** New bash patterns emerged — the agent's exploration continued at the frontier. The log captured them. New macros got written. The ratchet turned again.

Each cycle converts a piece of high-*ma* behavior into low-*ma* infrastructure. The trained judgment that chose `grep -r "TODO" ./src` is now encoded in the existence and interface of a structured search tool. The knowledge survived. The *ma* didn't.

---

## The principle

**Ma reduction**: the conversion of high-*ma* solutions into low-*ma* infrastructure that handles equivalent problems.

This is not fine-tuning. The weights never change. It's not in-context learning. The prompts are constructed fresh each conversation. It's a third kind of adaptation that operates at the configuration layer:

| | Weight training | In-context learning | Configuration accumulation |
|---|---|---|---|
| **What changes** | The decision surface itself | What the decision surface sees | What tools and constraints surround the decision surface |
| **Persistence** | Permanent (until retrained) | Ephemeral (one conversation) | Persistent and growing |
| **Opacity** | High — can't read the weights | Medium — can read the prompt | Zero — can read every configuration |
| **Auditability** | Low | Medium | Complete |
| **Ma of the learning process** | Trained | In-context | Specified |

The critical property: **the learning itself is specified.** The queries that identify good patterns are SQL. The promotion from pattern to tool is a code change reviewed by a human. At no point does opacity enter the learning loop. The system gets smarter, but the smartness is legible.

The principle has three components:

**1. A high-*ma* process that explores.** It must have enough decision surface to navigate the problem space and enough world coupling to discover what works. This is where trained judgment lives — the LLM choosing bash commands, the planner reasoning about tool selection, the human expert diagnosing a novel failure.

**2. An artifact that captures the result.** A macro. A cached configuration. A security profile. A diagnostic script. The artifact is specified — readable, auditable, deterministic. It encodes *what to do*, not *how the decision was made*.

**3. A low-*ma* process that applies the artifact.** A lookup. A pattern match. A SQL query. A rule evaluation. The applying process doesn't need the judgment that produced the artifact. It needs the artifact and the ability to match the current situation to its applicability conditions.

The transformation: `(high-ma explorer) → (specified artifact) → (low-ma applicator handling equivalent future cases)`.

---

## Why this is a ratchet

The ratchet only turns one way. Each promotion moves a behavior from high *ma* to low *ma*, and there's no mechanism that moves it back. The macro, once written, doesn't spontaneously become a bash call again. The cache, once populated, doesn't empty itself. The specified band expands monotonically. Each turn of the ratchet is a placement operation — it moves a piece of the problem from "requires judgment" to "handled by specification," which moves the remaining space to the frontier where judgment is most needed.

The ratchet is powered by friction. Every repeated failure at a boundary — a permission denial, a tool call that times out, a pattern the agent keeps trying that keeps not working — is a data point about where the system's configuration doesn't match the task's requirements. The crystallization eliminates the friction, either by opening the boundary (promote the access — the agent genuinely needs this capability) or by making the constraint visible (the agent is wasting decision surface probing something that should never open). Either way, the expensive middle state — knowledge without access, repeated probing, wasted inference — is eliminated.^[The companion essay [Coordination Is Not Control](coordination-is-not-control.md) develops this as the failure-driven controller: System 3 in Beer's Viable System Model, monitoring the failure stream and crystallizing patterns into configuration changes.]

The loop is self-sustaining:

```
Exploration (high ma)
    ↓ produces
Artifact (specified)
    ↓ consumed by
Application (low ma)
    ↓ outcomes captured
Evidence (data)
    ↓ informs
Exploration of next problem (high ma)
```

Each cycle converts a slice of the problem space from "requires inference" to "handled by configuration." The dynamics:

- **Positive feedback on the specified base**: more artifacts → more problems handled at low *ma* → more evidence → better artifacts. The base grows.
- **Negative feedback on exploration scope**: as the base grows, fewer problems require exploration. The frontier shrinks. The high-*ma* process is needed less often — but for harder problems.
- **Maintenance via the same loop**: when artifacts degrade (the world changed, the tool changed, the problem shifted), evidence detects the failure. Diagnosis may require high-*ma* reasoning. The diagnosis produces an updated artifact. The ratchet self-maintains.

---

## The escalation structure

The ratchet creates a natural escalation for how the system handles tasks:

**Tier 1: Cache hit.** The task matches a known type. The configuration is cached and validated. No inference needed. *Ma* of the selection process: zero.

**Tier 2: Parametric adaptation.** Same task type, different parameters. The template applies; the planner fills in specifics. Minimal inference. Low *ma*.

**Tier 3: Configuration update.** A tool changed or the environment shifted. The planner evaluates whether the cached configuration still holds. Moderate inference. Medium *ma*.

**Tier 4: Novel task.** Nothing in the cache matches. Full inference — reason about the task, evaluate candidate tools, assemble a new configuration. High *ma*.

**Tier 5: Escape hatch.** The cached configuration isn't working. The agent needs something it doesn't have. Escalation for approval.

The system lives at the bottom of this ladder most of the time. Early in deployment, everything is Tier 4 — novel tasks, full inference. Over time, the cache fills and the distribution shifts toward Tier 1-2. Inference retreats to the frontier. The center becomes specified.

---

## Why this is powerful

Three properties make *ma* reduction more than an engineering convenience.

### The reduction is auditable

Weight training improves a system by modifying billions of opaque parameters. You can measure that it got better. You can't read *how* it got better.

*Ma* reduction improves a system by adding specified artifacts. Each artifact is readable. Each has a provenance — which high-*ma* process produced it, based on what evidence, approved by whom. The improvement is both real and legible.

### The reduction compounds

Each *ma* reduction frees the high-*ma* process to work on the next unsolved problem. The agent that no longer needs bash for common file operations can spend its inference budget on the novel parts of the task.

The frontier of unsolved problems shrinks as the specified base grows. And the specified base grows monotonically — artifacts accumulate, caches fill, tool libraries expand. The compound effect: the system gets both more capable (the frontier is where the interesting work happens) and more specified (the base handles routine work without inference).

### A higher-*ma* system can generate its lower-*ma* successor

This is the piece that feels fundamental.

A language model generates bash commands. Analysis of those commands produces structured macros. The macros replace the bash commands. The LLM's trained judgment produced the training data for a specified system that now handles the same job.

A planner with full inference assembles tool configurations for novel tasks. Successful configurations get cached. Future planners do a cache lookup instead of inference. The trained planner's judgments become the training data for a lookup table.

A human expert diagnoses a novel failure. The diagnosis becomes a runbook. Future responders follow the runbook. The expert's judgment became the training data for a specified procedure.

In each case: the higher-*ma* system doesn't just solve the problem. It produces an artifact that *teaches* a lower-*ma* system to solve equivalent problems. The direction is always downward: trained produces artifacts for specified. Specified produces artifacts for literal.

---

## The Ashby connection

Ashby (1956) distinguished between variety *matching* and variety *destruction*. A thermostat doesn't model the weather. It destroys the weather's variety by maintaining a fixed temperature regardless of what happens outside. The thermostat's variety is trivial. Its regulatory power comes from *reducing* the portion of environmental complexity that reaches the controlled system.

The configuration ratchet is Ashby's variety destruction, applied as a learning process. Each promoted tool *destroys variety* — it replaces an operation with unbounded variety (arbitrary bash) with one of bounded variety (a specified macro). The agent's effective variety decreases. The Harness's specified rules, which were insufficient to regulate the full variety of bash, are now sufficient to regulate the reduced variety of the macro.

Conant and Ashby (1970) proved that every good regulator must be a model of the system it regulates. The configuration cache IS that model — not a model of the agent's weights (impossible) or its reasoning (opaque), but a model of *what works*. Which tools, which constraints, which configurations produce good outcomes for which task types. That's the minimum viable model. And it grows automatically through use.

Post 8's resolution — the Harness reduces variety rather than matching it — is a static design principle. The ratchet makes it dynamic: the variety reduction improves over time, automatically, using the system's own exploration as evidence.

---

## The operations management lineage

This is not a new idea. Operations management has been doing it systematically for seventy years:

**Deming's PDCA** (Plan-Do-Check-Act) is the ratchet:
- Plan = the explorer provides intent (high *ma*)
- Do = implementation runs (specified)
- Check = testing captures outcomes (specified)
- Act = crystallize what worked, adjust what didn't (the ratchet turns)

**Six Sigma's DMAIC** maps precisely:
- Define = intent (what are we trying to accomplish?)
- Measure = capture outcomes with specified instruments
- Analyze = specified analysis over captured data (the crystallizer)
- Improve = promote the validated pattern
- Control = the cached configuration, now monitored by specified tools — the *ma*-reduced steady state

**Toyota's production system** makes the ratchet continuous. *Kaizen* is the ongoing crystallization of floor workers' judgment into standardized work procedures. Each *kaizen* event converts a high-*ma* observation into a specified process change. The *andon* cord is the escalation path — when the specified process encounters something it can't handle, production stops and the high-*ma* actors re-engage.

What the *ma* framework adds to these established methodologies: **a formal measure of where you are in the reduction process.** Deming says "improve continuously." The grade lattice says "your process is currently at (broad, configured) — here's specifically what improvement means: reduce world coupling by standardizing inputs, reduce the decision surface by replacing judgment calls with lookup tables." The improvement has a direction and a metric, not just an aspiration. And the supermodularity of characterization difficulty tells you *where to invest*: restriction on either axis has larger returns when the other axis is high.

---

## The cognitive science lineage

Operations management recognized this pattern in organizational processes. Cognitive science recognized it earlier, in individual cognition — under the umbrella term **speedup learning**.

**Chunking** (Laird, Newell & Rosenbloom, 1986) is the most precise match. In Soar, the system hits an impasse, deliberates through subgoals (high *ma*), and when deliberation succeeds, the result is *chunked* into a production rule. Future encounters fire the rule directly. The chunk set grows monotonically. Soar even has the escalation structure: chunks handle the routine, deliberation handles the novel, and the boundary shifts over time. Newell called chunking a "universal learning mechanism" (*Unified Theories of Cognition*, 1990). **Knowledge compilation** in ACT-R (Anderson, 1983) describes the same conversion — slow declarative knowledge into fast procedural knowledge through practice. Declarative → procedural is literally inference → lookup.

**Explanation-Based Learning** (Mitchell et al., 1986; DeJong & Mooney, 1986) learns from a single example by explaining *why* it works and generalizing into a rule. The DuckDB queries over logs are a simpler version — statistical identification rather than causal explanation, but the same destination. **Macro learning** in STRIPS (Fikes & Nilsson, 1971) compiles successful action sequences into reusable operators — literally what happens when bash patterns become named macros. In modern ML, the closest analogues are policy distillation and behavioral cloning.

The learning mechanism is not novel. What the *ma* framework contributes is the regulatory framing: the compiled artifacts aren't just faster, they're lower grade — easier to regulate, auditable, with provenance. Classical chunking produces opaque production rules. The ratchet produces specified artifacts. Each compilation step improves not just the agent's performance but the Harness's ability to regulate it — connecting knowledge compilation to Ashby's law via the grade lattice.

---

## Instances

The substrate changes — parts, code, queries, decisions — but the mechanism is identical:

| Domain | Explorer | Capture | Artifact |
|---|---|---|---|
| **Manufacturing** | Process engineer | QC data, yield | Work instruction |
| **Software** | Senior developer | Version control, CI | Shipped code, API |
| **Agent architecture** | LLM with full tool access | Conversation logs | Structured tool, cached config |
| **Operations** | Incident responder | Incident logs, postmortems | Runbook |
| **Education** | Expert practitioner | Literature, practice records | Textbook, course |
| **Scientific method** | Novel experimental design | Lab notebooks, publications | Validated protocol |

Each row is the same loop: explore → capture → crystallize → exploit → repeat.

Crandall [documents](https://natesnewsletter.substack.com/p/same-model-78-vs-42-the-harness-made) the ratchet's consequences at team scale: a developer built six workflow automation layers over months, each depending on the previous. Switching harnesses would reset all layers to zero — multiplied across an engineering team. This is the ratchet's cost: the specified base grows monotonically, which makes the system more capable and more trustworthy, but also more expensive to abandon. The lock-in is real, and it's a feature viewed from inside (accumulated capability) and a risk viewed from outside (switching cost). The framework doesn't resolve this tension — it names it. The specified base is the system's memory of what works. Discarding it discards the learning.

---

## The limit

*Ma* reduction has a floor. Some problems are constitutively high-*ma* — they can't be reduced because the judgment they require is irreducibly contextual.

"Should we refactor this module?" is an architectural judgment that depends on the codebase's trajectory, team priorities, and factors no configuration can enumerate. "Is this the right abstraction?" requires taste that resists specification.

The *ma* reduction principle doesn't claim everything is reducible. It claims that the *boundary* between "requires inference" and "handled by configuration" can be pushed — incrementally, practically, measurably — and that pushing it is almost always worth doing.

The irreducible core is where humans belong. The reducible periphery is where specified systems belong. And the boundary between them shifts toward the core with every turn of the ratchet.

---

## What the framework adds

The individual instances are well known. Runbooks, cached configurations, API patterns, textbooks — familiar engineering and educational artifacts. What the *ma* framework provides:

**A unified account.** These are all instances of the same structural transformation.

**A formal measure.** The grade lattice gives a formal object for the reduction. The movement from `(broad, trained)` to `(scoped, specified)` is measurable.

**A prediction.** Systems that implement *ma* reduction will outperform equivalent systems that don't, and the gap will compound. This is testable.

**A design principle.** When building any system that involves trained judgment, ask: can the judgment's *conclusions* be cached as specified artifacts? If yes, design the loop. Inference at the frontier, lookup at the center.

**A connection to Ashby.** Variety destruction as a learning process. The regulator doesn't need to get smarter. The system needs to get more specified.

**A direction for safety.** The hardest version of the alignment question is: how do you ensure an opaque system behaves well? *Ma* reduction offers a partial answer: convert the opaque behaviors into specified artifacts, incrementally, using the system's own outputs as evidence. You don't need to solve alignment in general. You need to solve it at the frontier and cache the solutions. The specified base grows. The opaque frontier shrinks. The system becomes more trustworthy with use — legibly, auditably, without modifying a single weight.

---

*This essay connects the formal framework developed in [The Ma of Multi-Agent Systems](00-intro.md) to the practical tool suite that motivated it. The tools are open source. The theory is a work in progress. The ratchet is already turning.*
