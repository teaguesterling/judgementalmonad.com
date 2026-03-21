# The Two-Stage Turn

*How systems convert exploration into infrastructure — discovery first, then crystallization.*

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

Each of these was a computation channel — an arbitrary string passed to a universal machine. The full weight manifold of a frontier LLM was engaged to produce... a grep call. Billions of pathways through the weights, and the destination was a specified operation on a bounded filesystem.

So we promoted them. Each frequently successful, low-risk bash pattern became a Fledgling SQL macro: `search(pattern, path)`, `find_definitions(name)`, `read_lines(path)`. Structured queries with known input languages, known effect signatures, known grades. The command that was broad, high-*ma* as a bash call became scoped, low-*ma* as a Fledgling macro.

Same functionality. Categorically different grade.

We didn't realize what we were doing at the time. We were just being practical — giving the agent the tools it kept reaching for, in a form that didn't require shelling out to bash. It was only later that we recognized the two-stage mechanism hiding in what felt like routine engineering.

---

## The two stages

The ratchet ([introduced in Post 0](01-fuel.md)) turns in two distinct stages. Every turn has both. Skip either and nothing happens.

### Stage 1: Discovery

The LLM, operating with high *ma* (trained decision surface, broad world coupling via bash), explores the space of possible actions. It tries things. Some work. Some don't. The exploration is expensive — every bash call engages the full inference machinery.

The conversation logs record everything. Not just what the agent did, but what worked. The logs are an append-only record of the agent's exploration — successes, failures, patterns, frequencies.

This is the stage that requires judgment. You can't skip it. You can't spec it in advance. The agent has to *try things* in the actual environment, with all its mess and contingency, to discover what works.

### Stage 2: Crystallization

DuckDB queries identify which patterns are safe, successful, and frequent. This is specified analysis of captured data — zero trained judgment involved. The queries are simple aggregations over the log.

The winning patterns get promoted into macros — specified tools with known grades. The knowledge that "agents frequently need to search codebases for patterns" moves from an implicit tendency in the weights to an explicit, named, auditable tool.

With the macros available, the agent no longer needs to shell out to bash for common operations. The same work now happens through specified tools at a lower grade. The system's effective *ma* decreases without any change to the model.

Then new bash patterns emerge — the agent's exploration continues at the frontier. The log captures them. New macros get written. The ratchet turns again.

Each cycle converts a piece of high-*ma* behavior into low-*ma* infrastructure. The trained judgment that chose `grep -r "TODO" ./src` is now encoded in the existence and interface of a structured search tool. The knowledge survived. The *ma* didn't.

---

## Type honesty

There's something deeper happening in the crystallization stage than just "make it a named tool."

Consider `Bash("date")`. What's the type of this operation? It's honestly `IO String`. You're invoking a shell, which resolves `date` through PATH lookup, alias expansion, whatever binary happens to be installed. The output is an arbitrary string. You can't narrow that type, because any of those resolution steps could change underneath you. The type *is* broad, and pretending otherwise would be dishonest.

Now consider `CurrentTime()` — a structured tool that calls the system clock directly and returns a `Timestamp`. The type narrowing is real. It's not a fiction imposed by the interface. It's backed by an implementation that makes specific commitments: this calls the system clock, this returns a timestamp, this doesn't depend on PATH or aliases or shell configuration.

This is what the crystallization stage actually does. You don't just rename `Bash("grep -r pattern path")` to `Search(pattern, path)`. You build a *new implementation* whose type commitments are backed by its internals. The Fledgling `search()` macro doesn't shell out to grep — it runs a SQL query against an indexed codebase. The interface promise (takes a pattern and path, returns matching lines) is backed by machinery that can keep that promise.

The commitments can stack. Consider git workflows. The bash version is `Bash("git add . && git commit -m 'fix' && git push && gh pr create ...")` — honestly `IO String`. The push might be rejected. The PR creation might fail halfway. You get a string back and hope.

[JetSam](https://github.com/teaguesterling/jetsam) crystallizes this into three layers, each with its own type commitments:

- **Planning**: `save(message="fix")` takes a `RepoState` snapshot and returns a `Plan` — a structured, inspectable list of steps with a TTL and a state hash. The plan knows what repo state it was computed against. No shell involved in planning.
- **Execution**: `confirm(plan_id)` executes the plan and returns an `ExecutionResult` with per-step `ok: bool`, not a string to parse. Each step maps to a specific git operation. The result tells you what completed and what didn't.
- **Recovery**: if push fails with "rejected," the recovery suggestion is `sync`. If rebase hits conflicts, it tells you what to do. The error-to-recovery mapping is specified, not hopeful.

Three crystallization layers, each backed by implementation. The plan generation doesn't touch git. The executor doesn't guess about failures. The recovery classifier doesn't require judgment. Each layer's type commitments are structural — narrower than `IO String` because the implementation behind each layer can actually keep the promises its interface makes.

We call this **type honesty**: the tool's interface contract is backed by its implementation. The narrower type isn't aspirational — it's structural. And that's what makes the *ma* reduction real rather than cosmetic.

---

## The ratchet is powered by friction

The ratchet doesn't turn on success. It turns on *friction*.

Every repeated failure at a boundary — a permission denial, a tool call that times out, a pattern the agent keeps trying that keeps not working — is data about where the system's configuration doesn't match the task's requirements. The failure stream is the signal.

The crystallization eliminates the friction in one of two ways:

- **Open the boundary.** The agent genuinely needs this capability. Promote the access — build a tool that provides it cleanly.
- **Make the constraint visible.** The agent is wasting decision surface probing something that should never open. Make the wall explicit so inference stops hitting it.

Either way, the expensive middle state — knowledge without access, repeated probing, wasted inference — gets eliminated. The failures aren't noise. They're the fuel.

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

- **Positive feedback on the specified base**: more artifacts means more problems handled at low *ma*, which means more evidence, which means better artifacts. The base grows.
- **Negative feedback on exploration scope**: as the base grows, fewer problems require exploration. The frontier shrinks. The high-*ma* process is needed less often — but for harder problems.
- **Maintenance via the same loop**: when artifacts degrade (the world changed, the tool changed, the problem shifted), evidence detects the failure. Diagnosis may require high-*ma* reasoning. The diagnosis produces an updated artifact. The ratchet self-maintains.

---

## The principle

The two-stage turn has three components:

**1. A high-*ma* process that explores.** It must have enough decision surface to navigate the problem space and enough world coupling to discover what works. This is where trained judgment lives — the LLM choosing bash commands, the planner reasoning about tool selection, the human expert diagnosing a novel failure.

**2. An artifact that captures the result.** A macro. A cached configuration. A security profile. A diagnostic script. The artifact is specified — readable, auditable, deterministic. It encodes *what to do*, not *how the decision was made*. And its type commitments are honest — backed by implementation, not just interface.

**3. A low-*ma* process that applies the artifact.** A lookup. A pattern match. A SQL query. A rule evaluation. The applying process doesn't need the judgment that produced the artifact. It needs the artifact and the ability to match the current situation to its applicability conditions.

The transformation: `(high-ma explorer) → (specified artifact) → (low-ma applicator handling equivalent future cases)`.

This is not fine-tuning. The weights never change. It's not in-context learning. The prompts are constructed fresh each conversation. It's a third kind of adaptation that operates at the configuration layer:

| | Weight training | In-context learning | Configuration accumulation |
|---|---|---|---|
| **What changes** | The decision surface itself | What the decision surface sees | What tools and constraints surround the decision surface |
| **Persistence** | Permanent (until retrained) | Ephemeral (one conversation) | Persistent and growing |
| **Opacity** | High — can't read the weights | Medium — can read the prompt | Zero — can read every configuration |
| **Auditability** | Low | Medium | Complete |

The critical property: **the learning itself is specified.** The queries that identify good patterns are SQL. The promotion from pattern to tool is a code change reviewed by a human. At no point does opacity enter the learning loop. The system gets smarter, but the smartness is legible.

---

## The escalation structure

The ratchet creates a natural escalation for how the system handles tasks:

**Tier 1: Cache hit.** The task matches a known type. The configuration is cached and validated. No inference needed.

**Tier 2: Parametric adaptation.** Same task type, different parameters. The template applies; the planner fills in specifics. Minimal inference.

**Tier 3: Configuration update.** A tool changed or the environment shifted. The planner evaluates whether the cached configuration still holds. Moderate inference.

**Tier 4: Novel task.** Nothing in the cache matches. Full inference — reason about the task, evaluate candidate tools, assemble a new configuration.

**Tier 5: Escape hatch.** The cached configuration isn't working. The agent needs something it doesn't have. Escalation for approval.

The system lives at the bottom of this ladder most of the time. Early in deployment, everything is Tier 4 — novel tasks, full inference. Over time, the cache fills and the distribution shifts toward Tier 1-2. Inference retreats to the frontier. The center becomes specified.

---

## Why this is powerful

Three properties make the two-stage turn more than an engineering convenience.

### The reduction is auditable

Weight training improves a system by modifying billions of opaque parameters. You can measure that it got better. You can't read *how* it got better.

The two-stage turn improves a system by adding specified artifacts. Each artifact is readable. Each has a provenance — which high-*ma* process produced it, based on what evidence, approved by whom. The improvement is both real and legible.

### The reduction compounds

Each turn frees the high-*ma* process to work on the next unsolved problem. The agent that no longer needs bash for common file operations can spend its inference budget on the novel parts of the task.

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

Each row is the same loop: explore, capture, crystallize, exploit, repeat.

---

## The lineage

### Operations management

This is not a new idea. Operations management has been doing it systematically for seventy years.

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

### Cognitive science

Cognitive science recognized this pattern in individual cognition — under the umbrella term **speedup learning**.

**Chunking** (Laird, Newell & Rosenbloom, 1986) is the most precise match. In Soar, the system hits an impasse, deliberates through subgoals (high *ma*), and when deliberation succeeds, the result is *chunked* into a production rule. Future encounters fire the rule directly. The chunk set grows monotonically. Soar even has the escalation structure: chunks handle the routine, deliberation handles the novel, and the boundary shifts over time.

**Knowledge compilation** in ACT-R (Anderson, 1983) describes the same conversion — slow declarative knowledge into fast procedural knowledge through practice. Declarative to procedural is literally inference to lookup.

**Explanation-Based Learning** (Mitchell et al., 1986; DeJong & Mooney, 1986) learns from a single example by explaining *why* it works and generalizing into a rule. The DuckDB queries over logs are a simpler version — statistical identification rather than causal explanation, but the same destination. **Macro learning** in STRIPS (Fikes & Nilsson, 1971) compiles successful action sequences into reusable operators — literally what happens when bash patterns become named macros.

What the *ma* framework contributes is the regulatory framing: the compiled artifacts aren't just faster, they're lower grade — easier to regulate, auditable, with provenance. Classical chunking produces opaque production rules. The ratchet produces specified artifacts with honest types. Each compilation step improves not just the agent's performance but the Harness's ability to regulate it.

---

## The limit

The two-stage turn has a floor. Some problems are constitutively high-*ma* — they can't be reduced because the judgment they require is irreducibly contextual.

"Should we refactor this module?" is an architectural judgment that depends on the codebase's trajectory, team priorities, and factors no configuration can enumerate. "Is this the right abstraction?" requires taste that resists specification.

The two-stage turn doesn't claim everything is reducible. It claims that the *boundary* between "requires inference" and "handled by configuration" can be pushed — incrementally, practically, measurably — and that pushing it is almost always worth doing.

The irreducible core is where humans belong. The reducible periphery is where specified systems belong. And the boundary between them shifts toward the core with every turn of the ratchet.

That's the two-stage turn. Discovery finds the boundary. Crystallization moves it. The system doesn't get smarter — it gets more honest about what requires judgment and what doesn't. The judgment retreats to where it's needed. The specified base handles the rest.

Every tool you've ever built did this. The two-stage turn just names the mechanism and tells you where to look for the next one: in the failure stream, where the friction lives.

---

For the formal treatment of the grade lattice and *ma* reduction, see [The Ma of Multi-Agent Systems](../ma/00-intro.md).

---

Previous: [Fuel](01-fuel.md) | Next: [Where the Failures Live](03-where-the-failures-live.md)

