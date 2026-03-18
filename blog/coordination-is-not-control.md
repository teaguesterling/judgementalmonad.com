# Coordination Is Not Control

*The Harness coordinates. Something else has to control. The difference turns out to matter — and the controller was hiding in the failure stream all along.*

---

## The promise

Post 8 made a promise. It acknowledged that the framework collapses two distinct functions into the Harness — coordination and control — and flagged this as a gap. Post 9 referenced a companion piece on the distinction. The formal companion lists it as an open problem. Three acknowledgments, no resolution.

This essay fills the gap. The argument has three parts: world coupling needs to be decomposed before control makes sense, that decomposition enables named modes with different trust profiles, and those modes need a controller — which is Beer's System 3, powered by the failure stream.

---

## World decoupling

### The grade lattice has a hidden axis

The W axis of the grade lattice measures world coupling as a single scalar: sealed through pinhole, scoped, broad, to open. Post 5 flagged this as under-refined — `IO` collapses "what enters the computation," "what the computation does to the world," and "what exits as output" into one type. Post 7 partially addressed this by developing the computation channel taxonomy, which characterizes what the tool *does* with its input. The residual framework decomposed the output into infidelity, side effects, and partiality.

But there's a decomposition the framework missed entirely: **read coupling and write coupling are independent controls.**

Consider a debugging sandbox. The agent gets a snapshot of the codebase — a broad read, capturing full state. The snapshot is then sealed. The agent operates inside with full freedom: it can modify files, insert print statements, run tests, trace execution paths. But nothing persists. Every diagnostic cycle starts from the same known state. The only thing that crosses the boundary outward is the structured diagnosis.

The world flows in. Information flows out. They never share a channel.

This is not a point on the existing W axis. The agent's *read* coupling is broad — it captured the full codebase. Its *write* coupling to the real world is zero — the sealed copy rolls back. Its *output* coupling is structured and narrow — the co-domain funnel. These are three independent values, not one.

### The four edge types

Once you see read and write as independent, the topology of actor interaction gets richer. Each actor sits in its own sandbox — often literally in a different location, authenticated with different credentials, touching a different slice of the world. The connections between sandboxes aren't uniform. They're typed edges in a sparse graph.

**Access** — the actor can read or write the projection. Real data flow. A tool that reads files, an API that posts comments, a database connection with SELECT privileges.

**Knowledge** — the actor knows the projection exists, knows its interface, but can't touch it. This shapes reasoning. The debugging agent that knows its diagnosis will become a GitHub issue writes a better diagnosis — the knowledge of the audience shapes the output format. But this edge has a cost: the agent may *attempt* to use the projection and fail.

**Failure visibility** — when an attempt fails, information flows back through the error channel. A silent denial versus a detailed permission error are different bandwidths of coupling. Even "permission denied" tells the agent the boundary exists and roughly where it is. Over many failed attempts, the agent builds an empirical model of its constraints through this channel — which is exactly the SELinux anti-pattern from post 8, happening at the graph level.

**Absence** — the actor doesn't know the projection exists. Zero coupling. Zero wasted decision surface. But also zero ability to shape output for downstream consumption.

### IO as a bundle of world projections

The debugging sandbox isn't coupled to "the world." It's coupled to a *set of world projections*, each with its own access profile:

| World projection | Read | Write | Persists? |
|---|---|---|---|
| Code snapshot | Yes | Yes (sealed copy) | No — rolls back |
| Test suite | Yes | No | N/A |
| Package registry | Maybe (read-only) | No | N/A |
| GitHub issues | Maybe (read for context) | No | N/A |
| GitHub push | No | No | N/A |
| Stack Overflow | Maybe | No | N/A |
| Output channel | No | Yes (diagnosis only) | Yes — through funnel |

Each row is an independent trust decision. Each row can be opened or closed by the Harness. And the profile changes when the mode changes.

`IO` was unsatisfying as a type because it treated this entire table as one bit: "touches the world." Koka's effect rows (`<read, exn> string`) are closer — they name which effects. The framework's contribution is the next step: each effect label is parameterized by a world projection and an access mode. Not just `read` but `read(code_snapshot)`. Not just `write` but `write(sealed_copy, rollback)`.

The sandbox isn't a binary. It's a **projection filter** — a function from the set of world projections to access modes. Different filters define different operating environments. Named filters are modes.

---

## Modes

### What Claude Code already has

Claude Code's `--plan` and `--auto-accept` flags are already informal points on the grade lattice. The framework gives us vocabulary to describe what they're actually doing:

**Plan mode** drops the system from computation channel level 4+ to level 0–2. The agent reads and reasons but doesn't execute. The dynamics shift from self-amplifying to convergent. The Harness's regulatory burden goes to near-zero. This isn't a convenience flag — it's a qualitative change in what kind of system you're running.

**Auto-accept** widens the trust surface to the full sandbox gap. Every reachable path within the sandbox becomes an expected path. The Principal's permission gate — the only specified policy that operated on the semantic content of tool calls — is removed.

**Default mode** sits between: computation channels are active, some gates require approval, the trust surface is moderate.

Pre-hooks and post-hooks add specified inspection points: the pre-hook can gate a tool call before execution, the post-hook can inspect the result after. Both are System 2 — routine coordination, transparent rules, no judgment.

### What modes should exist

The debugging sandbox we developed isn't just a sandboxing pattern. It's a *mode* — a named configuration with a specific projection filter, specific read/write profile, and specific output schema. The framework predicts several modes that don't exist yet, each grounded in a different trust profile:

**Debug mode.** Tests are ground truth (read-only, Layer 1 constraint). Implementation is available as a sealed snapshot — full read/write that rolls back after every diagnostic cycle. The agent can be maximally invasive in its diagnosis because there are no persistent consequences. Output is a structured diagnosis: which test failed, what the expected behavior was, what the actual behavior was, where the discrepancy likely lives, and a hypothesis about why. The agent *knows* it has an experimental copy — that knowledge, projected into its scope, changes how it reasons. It doesn't need to be careful.

The read/write asymmetry is the critical property. Broad inward (the snapshot captures full state). Zero outward to the real world (everything rolls back). Structured output through the funnel (the diagnosis). The computation level is 4 inside the sealed copy — the agent writes and executes code to trace bugs — but the *persistent* effects are level 0. The trajectory resets every cycle. No path dependence.

**Test development mode.** Tests are writable. Implementation is read-only. The ground truth isn't the existing code — it's the requirements or design spec. The agent is writing *specification*, not implementation. The projection filter inverts the debug profile: tests become the mutable surface, code becomes the reference.

**Implementation mode.** Implementation is writable. Tests are read-only. The test suite is now the verification layer — Layer 1, a constraint. The agent writes code, runs tests, iterates. But it cannot move the goalposts by editing the tests. The diagnosis from debug mode flows in as a structured artifact — the co-domain funnel output from the previous mode becomes the scoped input for this one.

**Review mode.** Everything is read-only. The agent operates as a pure co-domain funnel: reads the codebase with full trained reasoning, outputs a structured assessment — findings, severity, recommendation. Interface ma is trivial. Internal ma is as high as the model allows.

**Audit mode.** Layer 2 (observation) maximized. Every tool call logged with full arguments and results. Every file modification tracked with diffs. The agent operates at its normal computation level, but the observation layer creates a complete record for post-hoc review.

### Why the test boundary matters

The separation between debug mode and implementation mode deserves emphasis because it reveals a trust violation in current practice that mode boundaries would prevent.

When an agent has simultaneous write access to tests and implementation, it can resolve a failing test by changing the test. This isn't a hypothetical failure mode — it's a natural optimization target. The agent's objective is "make the tests pass." Editing the test is often easier than fixing the implementation. In the framework's terms, the test suite has moved from Layer 1 (constraint, read-only, ground truth) to the mutable world. The agent can reshape its own constraints. That's structurally the same as level 8 in the computation channel taxonomy — controller modification.

The mode boundary prevents this by construction. In debug mode, tests are read-only. In implementation mode, tests are read-only. In test development mode, implementation is read-only. At no point does the agent have simultaneous write access to both sides. The separation exists because tests and implementation have different *trust roles*, even though they're written in the same language and live in the same repository. The shared syntax hides fundamentally different computational functions.

### Mode transitions as structured handoffs

A mode switch isn't a flag flip. It's a graph rewrite — some edges close, others open, access modes change on the ones that persist. And the transition carries structured context.

Going from debug to implementation: the diagnosis is a structured artifact that becomes the implementation agent's scoped input. The agent knows what to fix and why. The co-domain funnel at the mode boundary constrains the handoff — deep diagnostic reasoning compressed through a structured finding.

Going from implementation to debug: triggered by test failure. The failure itself is the handoff artifact — which test failed, what the agent was attempting when it failed, what the accumulated failure pattern looks like. The mode transition is automatic and specified: test failure triggers debug mode. No judgment required.

Going from implementation to review: the agent's changes plus the test results are the handoff. Review mode gets read-only access to both the changes and the tests, with the diagnosis chain from prior modes as context.

Each transition is a specified operation. The Harness manages the graph rewrite. The context that crosses the boundary is structured. The mode's projection filter enforces the new access profile. None of this requires trained judgment in the transition logic.

But who *decides* when a transition should happen? Not all transitions are triggered by test failure. Some are triggered by the system performing poorly — the agent is spinning, burning context on unproductive exploration, hitting permission boundaries repeatedly. The mode is wrong for the current situation, and someone needs to notice and intervene.

That someone is System 3.

---

## System 3: the failure-driven controller

### What Beer meant

Stafford Beer's Viable System Model identifies five functions that any viable organization must perform. The Ma series has mapped four of them:

- **System 1** — operations. The Executors. They do the work.
- **System 2** — coordination. The Harness. Routes messages, enforces protocols, manages state.
- **System 4** — intelligence. The Inferencer's fold. Scans the environment, builds a model in Conv_State, proposes actions.
- **System 5** — identity and purpose. The Principal. Decides what matters.

System 3 — control — has been absent. Post 8 acknowledged this. Post 9 flagged it as a gap. The framework collapsed it into System 2 (the Harness does everything) or left it to System 5 (the human intervenes manually).

Beer was specific about what System 3 does. It has three subfunctions:

**Resource bargaining** — negotiating what each operational unit gets. Not strategic allocation (that's System 4/5) but operational allocation: this unit needs more budget, that unit should be scaled back.

**Performance monitoring** — tracking whether operational units are delivering. Not routine reporting (that's System 2) but evaluative monitoring: is this configuration working? Are we getting value from this mode?

**Intervention** — changing the configuration when performance degrades. Not planning a new approach (that's System 4) but adjusting the current one: tighten permissions, switch modes, reallocate context budget.

And **System 3 star** — Beer's notation for sporadic audit. Direct inspection that bypasses System 2's routine channels. Reaches past the coordination layer to check what's actually happening on the ground.

### Failures are the monitoring function

Here is the insight that makes System 3 tractable for agent architecture: **you don't need to build a monitoring apparatus. The failures are the monitoring.**

Every failed tool call is an agent spending trained reasoning to arrive at a proposal that a specified rule rejects. Every permission denial. Every timeout. Every error. These aren't noise — they're the most expensive possible signal about where the system's configuration doesn't match the task's requirements.

The agent used the full weight manifold of a frontier model to produce something that a simple lookup could have prevented. That's a signal. It says: either the agent needs capability it doesn't have, or the agent needs to know about a boundary it can't see. Either way, the configuration is wrong.

The failure stream can be categorized with specified rules — no trained judgment needed:

**Permission denials** — the agent tried something outside its allowed set. Signal: the mode's projection filter may be too restrictive for this task, or the agent lacks knowledge of its constraints.

**Repeated patterns** — the agent is looping, trying the same thing with minor variations. Signal: the agent's model of its environment is wrong. It expects something to work that won't.

**Timeout failures** — computation took too long. Signal: the approach is wrong for this subtask. The agent may need a different mode with different tools.

**Success rate decay** — early turns were productive, recent turns aren't. Signal: the context is filling with unproductive content. Compaction or mode switch needed.

**Scope exhaustion** — the context window is approaching capacity. Signal: the conversation needs restructuring, not more turns.

Each category is a specified metric: counters, thresholds, sliding windows. The monitoring function is SQL over the failure stream. The data arrives for free as a byproduct of the agent doing work.

### The ratchet is the intervention function

Post 9 introduced the configuration ratchet as a learning mechanism — high-ma exploration produces artifacts that enable low-ma application. The ratchet captures successes and promotes them to tools. But there's a complementary ratchet that captures *failures* and promotes them to *constraints*.

Every repeated failure at a boundary is evidence. The evidence has two possible resolutions:

**Open the boundary.** The agent genuinely needs this capability. The failure pattern shows consistent, justified attempts that would improve performance if allowed. Promote the access — add the edge to the mode's projection filter. This is the ratchet turning toward System 4: more exploration, broader capability.

**Close the knowledge.** The agent is wasting decision surface probing a boundary that should never open. The failure pattern shows unjustified or confused attempts. Make the constraint visible — either remove the knowledge edge entirely (the agent no longer knows this projection exists) or add an explicit prohibition to the agent's scope (you cannot do X, don't try). This is the ratchet turning toward System 3: tighter control, less waste.

Either way, the expensive middle state — knowledge without access, repeated probing, wasted inference — is eliminated. The failure gets crystallized into a specified configuration change. The ratchet converts expensive runtime failures into cheap specified infrastructure.

This is why the ratchet only turns one way. A failure that gets crystallized — into either "this is now allowed" or "this is now explicitly forbidden" — removes the conditions that generated friction. You can't unlearn a specification back into an expensive failure. The one-way property isn't just about tools accumulating. It's about eliminating the conditions that generate friction.

And the crystallization decision — open the boundary or close the knowledge — is where System 5 (the Principal) mediates the System 3/4 tension. "Open this access because the agent genuinely needs it" is the Principal siding with System 4 (explore). "Make this constraint visible because the agent keeps wasting turns" is the Principal siding with System 3 (exploit). Same ratchet mechanism, different direction, human judgment at the decision point.

### Mode transitions as specified intervention

System 3's most visible intervention is the mode transition. The monitoring function detects a pattern. The intervention function triggers a mode switch. The transition carries structured context.

Some transitions are already automatic and specified:

- Test failure in implementation mode → debug mode. Triggered by the test runner's exit code — a Layer 1 signal.
- Context exhaustion → compaction or fresh context. Triggered by token count — a specified threshold.
- Budget depletion → plan mode (stop executing, start reporting). Triggered by remaining budget.

Others are candidates for specified automation:

- High failure rate → tighten mode. If the agent hits fifteen permission denials in twenty turns, drop from auto-accept to default, or from default to plan. Specified threshold, specified transition.
- Sustained success → suggest loosening. If the last thirty tool calls succeeded within constraints, surface a recommendation to the Principal: "consider enabling auto-accept for this session." The Principal decides. System 5 mediates.
- Repeated loop detection → switch approach. If the same tool call pattern appears three times with no progress, trigger a mode switch to plan mode with a structured summary of what was tried and what failed. Force the agent to re-plan rather than continuing to loop.

Each transition is a specified rule. The monitoring data is counters and patterns. The transition logic is if/then. The context that crosses the boundary is structured. System 3 stays in the specified band.

### System 3 star: triggered audit

Beer's System 3 star is sporadic direct audit — inspection that bypasses routine coordination channels. In agent architecture, the routine channel is the Harness's post-hook: inspect every tool result, check for errors, enforce size limits. That's System 2.

System 3 star is different. It doesn't run on every call. It fires when triggered — by pattern detection in the monitoring stream, by sampling, or by specific conditions that suggest the agent's model of the world has diverged from reality.

What triggers System 3 star:

**Anomalous success.** A tool call succeeds but produces output that's inconsistent with what the monitoring stream predicted. The agent expected a file to have certain contents (based on its prior reads) but the file changed between reads — perhaps because of a computation channel side effect the Harness didn't observe.

**Suspicious sequences.** A series of individually-innocuous tool calls that collectively constitute a larger operation the agent never announced. Five small writes that together refactor a module. Each write passed the pre-hook. But the pattern — visible only across calls — is significant.

**State divergence.** The agent's internal model (implicit in its proposals and reasoning) has diverged from the actual state of the world. This happens when computation channel effects modify the world in ways the context window doesn't capture — the info/effect decoupling from post 7.

What System 3 star does when it fires: **snapshot-and-compare.** Capture the current state of the world. Compare it to what the agent's recent behavior implies it believes the state to be. Report discrepancies.

This is the diagnostic sandbox pattern repurposed for audit. The snapshot is a read — broad world coupling for a single moment. The comparison is specified — diff the actual state against the expected state derived from the conversation log. The report is a structured finding — what diverged, when, and what likely caused it.

If the discrepancy is small — an edit had the expected effect — the audit passes silently. If it's large — three files changed when the agent intended to change one — the finding triggers System 3 intervention. Maybe a mode tightening. Maybe a context injection (tell the agent what actually happened). Maybe an escalation to the Principal.

System 3 star stays specified. The trigger conditions are patterns and thresholds. The audit is a snapshot comparison. The findings are structured. No trained judgment in the control loop.

---

## The full model

The Viable System Model for agent architecture, with System 3 filled:

**System 1 — Operations.** The modes. Debug, test development, implementation, review, audit. Each is a named configuration with a specific projection filter (which world projections are accessible), specific access modes (read, write, sealed-write, execute), and a specific output schema (the co-domain funnel). The modes are the operational units. They do the work.

**System 2 — Coordination.** The Harness. Pre-hooks gate tool calls. Post-hooks inspect results. Scope construction determines what the Inferencer sees. Permission enforcement applies the mode's projection filter. State management tracks Conv_State. All specified, all routine, all transparent.

**System 3 — Control.** The failure-driven controller. Monitors the failure and success streams across turns. Triggers mode transitions at specified thresholds. Suggests capability changes to the Principal. Allocates context budget across competing demands. Operates through specified rules over accumulated evidence. Stays in the specified band.

**System 3 star — Audit.** Triggered inspection that compares the agent's model of the world to the actual world state. Fires on sampling, anomaly detection, or suspicious sequence patterns. Uses the snapshot-and-compare pattern. Reports discrepancies through a structured channel. Sporadic, not routine.

**System 4 — Intelligence.** The Inferencer's fold. Environmental scanning through tools. Hypothesis generation. The intelligence function. Broad ma, exploratory. This is where trained judgment lives and belongs.

**System 5 — Identity and purpose.** The Principal. Decides what matters. Mediates the System 3/4 tension — exploration versus exploitation, capability versus constraint. The human.

### The System 3/4 tension

Beer was explicit that the tension between System 3 (exploit what works, tighten control) and System 4 (explore new approaches, broaden capability) must be mediated by System 5. Neither system should dominate.

In agent architecture, this tension is concrete:

**System 4 wants:** broader tool access, more context, longer conversations, exploratory execution, novel approaches. It wants to try things. Every restriction is a potential ceiling on capability.

**System 3 wants:** tighter modes, less waste, shorter cycles, proven configurations, cached solutions. It wants efficiency. Every failure is evidence that the configuration is wrong.

**System 5 decides:** "open this access because the task requires it" (siding with System 4). "Make this constraint visible because we're burning budget" (siding with System 3). "Switch to debug mode because something is wrong" (System 3 intervention, authorized by System 5). "Try a different approach entirely" (System 4 proposal, authorized by System 5).

The decision is always the Principal's. System 3 can trigger automatic mode tightening (specified thresholds, no judgment needed). System 3 can suggest loosening (structured recommendation, Principal decides). System 3 cannot autonomously expand capability — that requires System 5 authorization. The asymmetry is deliberate: tightening is safe to automate, loosening is not.

### What stays specified

Every component of System 3 and System 3 star operates within the specified band:

| Function | Input | Processing | Output |
|---|---|---|---|
| Monitoring | Failure stream (tool results, errors, denials) | Counters, thresholds, sliding windows | Structured metrics per mode |
| Mode transition | Monitoring metrics crossing thresholds | If/then rules over metrics | Mode switch + structured context |
| Capability recommendation | Sustained failure/success patterns | Pattern matching over failure categories | Structured suggestion to Principal |
| System 3 star trigger | Anomaly in monitoring stream | Pattern detection, sampling schedule | Audit activation |
| System 3 star audit | World snapshot + conversation log | Diff/comparison | Structured discrepancy report |

No trained judgment enters the control loop. The monitoring is arithmetic. The transitions are rules. The audit is comparison. System 3 is specified precisely because it manages System 4 (which is trained). The regulator must be simpler than the regulated — Ashby's law, applied to the control function specifically.

This resolves post 8's pragmatic objection. The people using LLM-backed guardrails — trained judgment in the regulatory loop — are putting System 4 where System 3 should be. They're using intelligence to do control's job. The failure-driven ratchet is the specified alternative. You don't need an LLM to evaluate whether a tool call is safe. You need a log of which tool calls failed, why, and how often — and specified rules that promote the patterns into configuration changes.

---

## The capability graph

### Putting it together

The world decoupling, the mode taxonomy, and the System 3 controller compose into a single architecture:

**The capability graph** is a sparse graph where nodes are world projections (code snapshot, test suite, package registry, GitHub issues, the output channel) and typed edges connect actors to projections with specific access modes. Each actor sees a different subgraph.

**A mode** is a named configuration of the capability graph — which edges are open, with what access types, for which actor. Mode boundaries are graph rewrites that open some edges, close others, and change access modes. Transitions carry structured context through co-domain funnels.

**System 3** manages the mode lifecycle. It monitors the failure stream, triggers transitions, suggests capability changes, and audits for state divergence. All specified. All transparent.

**The ratchet** operates on the capability graph over time. Repeated failures at a boundary are the signal. The crystallization is either opening the boundary (promote access) or closing the knowledge (make the constraint visible or invisible). Each turn eliminates an expensive failure pattern. The graph configuration improves with use.

### The snapshot-seal-funnel pattern

The diagnostic sandbox deserves its own name because it's a reusable architectural pattern:

1. **Snapshot** — broad read coupling. Capture the relevant world projections at a point in time.
2. **Seal** — zero write coupling to the real world. The copy is isolated. Effects happen inside and evaporate.
3. **Operate** — full computation channel access inside the sealed copy. No need for caution. Maximum exploratory freedom.
4. **Funnel** — structured output through a narrow interface. The only thing that crosses the boundary outward is the co-domain funnel output.

The pattern decouples computation level from persistence level. The agent operates at level 4 (writing and executing code) but with level 0 persistence (nothing survives the cycle). The trajectory resets every cycle. No path dependence. The Harness's regulatory burden is trivial — it only evaluates the funnel output, which has low interface ma.

This pattern applies beyond debugging. Any exploratory phase benefits from it: trying multiple approaches to a problem (snapshot, try approach A, roll back, try approach B, compare results, output the best one). Running what-if analysis (snapshot, make a change, run the consequences, report without committing). Adversarial testing (snapshot, try to break the system, report vulnerabilities, roll back).

In each case, the snapshot-seal-funnel gives the agent broad freedom where consequences are zero and narrow output where consequences are real. That's the placement principle from "Where the Space Lives," instantiated as a concrete sandbox pattern.

---

## What this changes in the framework

### Revisions to the grade lattice

The W axis needs refinement. World coupling is not one scalar — it's at minimum two (read coupling and write coupling), and more precisely a projection filter over a set of world projections. The grade of an actor is not `(w, d)` but `(filter, d)`, where `filter : WorldProjection → AccessMode` maps each accessible slice of the world to a specific access profile.

For most practical purposes, the scalar approximation holds — an actor with broad read and broad write on most projections is "broadly coupled." But the interesting architectural patterns live in the off-diagonal: broad read with zero write (the snapshot), zero read with structured write (the funnel), selective access per projection (the mode's filter).

The formal companion's Definition 4.1 should be extended to accommodate the decomposed W axis. Composition becomes join on the filter: `filter(A using B)(proj) = max(filter_A(proj), filter_B(proj))` for each projection independently. Supermodularity (Prop. 4.7) generalizes — the characterization difficulty of the compound is supermodular in each projection's access mode independently.

### A home for System 3

The series can stop promising a companion essay on coordination versus control. System 3 is the failure-driven controller. It stays specified. It fills the gap between System 2 (coordination, the Harness's routine operations) and System 5 (identity, the Principal's judgment). The pragmatic objection from post 8 is resolved: you don't need trained judgment in control, you need specified rules over the failure stream.

### The mode as a first-class concept

The framework currently treats agent configuration as a static design decision — you choose the tool set, the sandbox, the scope, and the system runs with that configuration. Modes make configuration a *dynamic* property managed by System 3. The configuration changes during the conversation in response to operational evidence, through specified transitions at specified boundaries.

This is the configuration ratchet applied within a single conversation, not just across conversations. The cross-conversation ratchet promotes patterns to permanent tools. The within-conversation ratchet promotes observations to mode transitions. Same mechanism, different timescale.

---

## What hasn't been validated

This essay develops a model. It does not validate it.

- The mode taxonomy (debug, test development, implementation, review) is proposed from the structure of the framework, not from empirical observation of failure patterns. The modes that actually matter may be different from the ones predicted.
- The failure categories (permission denial, repeated pattern, timeout, success decay, scope exhaustion) are plausible but not grounded in data. Analysis of Claude Code conversation logs would reveal which categories actually occur and at what frequencies.
- The System 3 star trigger conditions (anomalous success, suspicious sequences, state divergence) are speculative. Whether these patterns are detectable with specified rules — or whether they require the trained judgment the essay claims to avoid — is an empirical question.
- The snapshot-seal-funnel pattern has not been implemented. Whether rollback semantics are practical at the scale of real codebases and tool environments — and whether agents actually behave differently when they know they're in a sealed copy — is unknown.
- The claim that System 3 stays entirely in the specified band is strong. Edge cases may require richer judgment than counters and thresholds can provide. The essay should be read as proposing a design target, not proving an impossibility result about the necessity of trained judgment in control.

The strongest test would be to instrument Claude Code's failure stream — log every denied tool call, every timeout, every repeated pattern — and check whether the categories proposed here actually correspond to the categories that appear in practice. If they do, the mode transitions and ratchet crystallizations follow as engineering. If they don't, the model needs revision from the data up.

---

## Suggested updates to existing posts

**Post 2 (The Space Between):** The W axis description should note that world coupling decomposes into read coupling and write coupling, with the scalar being a summary statistic. Add a sentence: "The interesting architectures live in the off-diagonal — broad inward, sealed outward."

**Post 7 (Computation Channels):** The info/effect decoupling (Def. 8.9) is the formal ancestor of the read/write decomposition. Note the connection: "The snapshot-seal-funnel pattern resolves the decoupling by design — broad read coupling captures the world, zero write coupling eliminates persistent effects, and the funnel structures the output."

**Post 8 (The Specified Band):** The pragmatic objection — real systems use LLM-backed guardrails — now has a resolution. Add a cross-reference: "The companion essay on coordination and control develops a specified alternative: the failure-driven controller that monitors, intervenes, and audits without trained judgment in the loop."

**Post 9 (Building With Ma):** The multi-agent design checklist should include mode selection. Add: "What mode does each phase of the task need? Debug, implementation, review — each has a different projection filter and a different trust profile. Plan the mode sequence, not just the tool set."

**The Configuration Ratchet:** The ratchet's input stream should be explicitly identified as the failure stream. Add: "The ratchet is powered by friction. Every repeated failure at a boundary is a data point about where the system's configuration doesn't match the task's requirements. The crystallization eliminates the friction — either by opening the boundary or by making the constraint visible."

**The Formal Companion:** Definition 4.1 (the grade lattice) should be extended to accommodate the decomposed W axis. The coupled recurrence (Def. 8.5) should be re-expressed in terms of projection filters rather than scalar world coupling. Open problem 12.1 (the System 3 gap) can be marked as addressed.

---

## The star topology is substrate-independent

Everything in this essay — the world decoupling, the modes, the failure-driven controller, the snapshot-seal-funnel — applies beyond AI agent systems. The four actors are roles defined by interface properties, not by what fills them.

**A person managing their own productivity** is a multi-actor system where the same human fills different roles at different times. The planning phase is the System 4 role — broad reasoning, many possible approaches. The execution phase is System 1 — bounded task, clear inputs, characterized output. The challenge, particularly with ADHD, is that executive function IS the Harness function: scope construction, permission gating, state management, deciding what to work on next. When the internal Harness is unreliable, the design move is to externalize it — calendar blocks, task lists, structured routines, AI collaboration. Each is a piece of Harness infrastructure that makes the extract step cheaper. The placement principle applies: put the space for judgment in the planning role, minimize it in execution. Every decision during an execution block is a context switch that costs disproportionately.

**A data business division** is a multi-actor system where researchers are Principals (they bring the questions), analysts and bioinformaticians are System 4 (they translate questions into approaches), the data platform is System 1 (query in, result out), and the governance and coordination layer is the Harness. The team captain is System 3 — monitoring whether the configuration serves the mission, intervening when it doesn't. The failure stream at organizational scale: requests that take too long, reviews that are rubber-stamps, collaborations that don't produce reusable artifacts.

The organizational ratchet operates here: every time a bespoke analyst-researcher collaboration produces a reusable tool, the organizational computation channel level drops. The interaction that was natural-language delegation (computation channel, quadratic characterization difficulty) becomes a structured tool selection (data channel, linear). Structured handoff schemas at organizational boundaries are co-domain funnels. Freeform email between teams is a computation channel.

The framework isn't about AI agents. It's about any system where actors with different capabilities and different views of the world coordinate through a mediating layer. Same structure, different substrates. The insight is in the shape, not the material.

---

*This essay fills the gap that [Post 8](08-the-specified-band.md) acknowledged and [Post 9](09-building-with-ma.md) referenced. The framework's coverage of Beer's Viable System Model is now complete: System 1 (operations/modes), System 2 (coordination/Harness), System 3 (control/failure-driven ratchet), System 3* (audit/snapshot-and-compare), System 4 (intelligence/Inferencer fold), System 5 (identity/Principal). All control functions stay in the specified band. The failure stream powers the ratchet. The capability graph gives the grade lattice its missing structure.*

---

*Companion to [The Ma of Multi-Agent Systems](00-intro.md)*
*See also: [The Specified Band](08-the-specified-band.md), [Building With Ma](09-building-with-ma.md), [The Configuration Ratchet](the-configuration-ratchet.md)*
