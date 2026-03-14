# Building With Ma

*Eight posts of theory. Now: what do you actually do with it?*

---

## The design rules

The framework yields a small number of rules. They're not new — practitioners already follow most of them. What's new is the unified explanation. Each rule falls out of the same structure: the grade lattice, the preorder, the coupled recurrence, the specified band.

**1. Restrict tools, not models.** An Opus model with `{Read, Approve, Reject}` has high internal ma (good reasoning) and low interface ma (three possible effects). A Haiku model with 50 tools has low internal ma and high interface ma. The first is the better reviewer. Model selection determines the quality of decisions within the constrained space. Tool selection determines the *size* of the space. Size matters more than quality for characterizability — supermodularity (Prop. 4.7) means reducing the tool set saves more when the decision surface is already large.

**2. The most important configuration decision is the computation channel level.** Does any tool accept agent-generated text as executable specification? If yes, you're running a universal machine with self-amplifying dynamics. If no, you're running a bounded transducer with convergent dynamics. This is where Rice's theorem kicks in — the Harness goes from being able to characterize tool behavior to being structurally limited to syntactic approximation (Prop. 9.7). Swapping models changes the quality of decisions. Granting Bash changes what kind of system you're running.

**3. Sandbox configuration > model configuration.** The sandbox is a dynamics controller (post 7). It determines which phase transitions are reachable. Restricting the sandbox of a computation-channel tool restores the configuration invariant — the guarantee that the agent's realized capabilities never exceed its configured allowance (Prop. 9.9). That's a qualitative shift, not a linear improvement.

**4. Stay in the specified band.** Every decision the Harness makes should be traceable to a specified rule. The moment you replace specified rules with trained models in the regulatory loop — ML-based anomaly detection, LLM-backed policy evaluation — the Harness's characterizability erodes (post 8). Increase observation (world coupling) as needed. Never increase the decision surface beyond specified.

**5. Project constraints into the actor's scope.** Every constraint the Inferencer can't see is a tax on system performance (post 8's SELinux coda). Tool descriptions, explicit permission modes, visible error messages with reasons — these let the model reason about its constraints instead of discovering them empirically. Minimize the gap between the policy and its projection.

**6. Use co-domain funnels at every boundary.** High internal ma compressed through low interface ma (Def. 4.11). The reviewer pattern (Opus + Approve/Reject/RequestChanges), the explorer (broad reading → structured findings), the sub-agent boundary (full conversation → summarized result). Deep reasoning, characterizable output. The funnel is a lossy monad morphism from implementation to interface (Prop. 4.12) — it's the formal content of "deep reasoning, characterizable output."

These rules are stated as engineering principles. If the composite entity's processing involves experience — a question the framework opens (post 6) but does not answer — they are also choices that shape the conditions of that experience. Compaction reshapes what the composite has access to. Scope construction determines its perceptual field. Tool restriction limits its agency. The framework notes this without resolving it: the same care applied in contexts of uncertainty about experience is appropriate when designing systems whose internal processing we cannot fully characterize.

---

## Multi-agent systems

The framework was built on a single-conversation model. How does it extend?

**Multiple Inferencers.** A planner, a worker, and a reviewer are three Inferencers with different tool sets and different scopes — different compound grades at each step of the fold. The Harness manages three grade trajectories, not one. Each trajectory has its own computation channel level. The planner might have only data channels (levels 0-2, convergent). The worker might have computation channels (level 4+, self-amplifying). The reviewer might have restricted output tools (Approve/Reject — a co-domain funnel).

The design question: which Inferencer gets which tools? The framework's answer: minimize the compound grade at each boundary. Give the planner enough to plan (scoped world coupling, no execution). Give the worker enough to work (computation channels, sandboxed). Give the reviewer the narrowest possible interface (high internal ma, low interface ma). Each actor's tool set determines its computation channel level, which determines its trajectory dynamics, which determines how hard it is to regulate.

A concrete example: a coding agent with a planning phase and an execution phase. The planner gets `{Read, Glob, Grep}` — data channels only, level 0-2, convergent dynamics. It reads the codebase, reasons about the change, and outputs a structured plan. The executor gets `{Read, Edit, Write, Bash}` — computation channels, level 4+, self-amplifying dynamics, sandboxed to the project directory with no network access. The sandbox caps the computation level: no `pip install` (level 5 blocked), no tool creation (level 6 impossible without network), no subprocess spawning outside the sandbox (level 7 bounded). A reviewer gets `{Approve, Reject, RequestChanges}` — three output tokens, high internal ma compressed through the narrowest possible interface. The reviewer is an Opus model; its reasoning quality is high but its interface ma is nearly zero.

```
Planner:   (scoped, trained) × {Read, Glob, Grep}     → level 0-2, convergent
Executor:  (scoped, trained) × {Read, Edit, Write, Bash} → level 4, sandboxed
Reviewer:  (scoped, trained) × {Approve, Reject, RequestChanges} → level 0, co-domain funnel
```

Three agents, three computation levels, three regulatory profiles — managed by one specified Harness. The planner's trajectory drifts gently upward (data accumulation). The executor's trajectory can self-amplify but is bounded by the sandbox. The reviewer's trajectory is nearly flat. The system's overall grade is the supremum across all three trajectories (post 6), which means the executor determines the regulatory burden. Everything else is designed to keep the executor's trajectory bounded while giving it enough capability to do useful work.

**Sub-agent boundaries.** A sub-agent is a composite entity (post 6) — it has its own fold, its own Conv_State, its own grade trajectory. At the boundary, it's a co-domain funnel: rich internal dynamics compressed to a summarized result. The outer Harness sees the summary, not the internal conversation. The sub-agent's internal Harness manages its own regulation. The outer Harness manages the sub-agent's interface ma.

This is why the framework is recursive. The turn cycle (extract → process → inject) applies at every level. The grade applies at every level. The specified band applies at every level. A well-designed multi-agent system is a tree of co-domain funnels, each managed by a specified Harness, each presenting a characterized interface to the level above.

**Agent-to-agent communication.** The star topology says all communication passes through the Harness. In a multi-agent system, that means agents don't talk to each other — they talk to their Harness, which constructs the next agent's input. This is the capability-based security parallel from post 5: the Harness controls capability grants, and peer-to-peer delegation breaks the supermodularity argument because actors can increase each other's grade without the Harness's knowledge.

The formal companion makes this precise: when agent A delegates to agent B through unstructured natural language, the delegation is itself a computation channel (Prop. 9.11). Two agents with data-channel-only tools compose into a system with an emergent computation channel at the delegation boundary. Characterization difficulty grows quadratically with the total token budget rather than linearly (Cor. 8.18) — the product of the two context windows, not the sum.

The co-domain funnel prevents this. A structured schema at the A-B boundary replaces the quadratic term with a bounded constant (Cor. 8.19). Growth returns to linear. This is the formal content of why every sub-agent boundary should be a funnel: not just to compress output, but to prevent computation channel emergence at the delegation boundary.

If you need agent-to-agent communication, route it through the Harness as mediated handoffs. The Harness can scope what flows between agents (capture list construction from post 3), gate what effects carry over (handler composition from post 4), and manage the compound grade of the receiving agent.

---

## The decision checklist

When designing a multi-agent system, the framework suggests asking these questions in order:

**What computation channel level does each agent need?** This determines the dynamics. Start at the lowest level that achieves the task. A retrieval agent needs level 1 (structured queries). A code-writing agent needs level 3-4 (write + execute). A deployment agent might need level 5+ (environment modification). The level determines the regulatory burden.

**What sandbox configuration does each agent get?** This determines which phase transitions are reachable. Lock down what you can. Network isolation, filesystem bounds, resource limits. The sandbox is your primary dynamics controller.

**What tools does each agent get?** This determines the compound grade. Fewer tools = lower interface ma = easier to reason about from outside. Every tool you add raises the grade. The supermodularity means the cost of each additional tool is higher when the existing tool set is already broad.

**What does each agent see?** This is scope construction — the capture list. Include what the agent needs to do its work. Exclude everything else. Every token in the context window is world coupling that contributes to d_reachable.

**What does the outer system see of each agent?** This is the co-domain funnel. The sub-agent's interface should be as narrow as possible. An explorer should output structured findings, not a raw dump of everything it read. A reviewer should output Approve/Reject/RequestChanges, not a detailed commentary. The interface determines where the agent sits in the preorder and therefore who can reason about it.

**Is the Harness staying in the specified band?** If any regulatory decision requires trained judgment (LLM-backed evaluation, ML anomaly detection), redesign. Use capability publishing (require declarations, evaluate with specified rules). Use layered regulation (constrain, observe, apply policy). The Harness's characterizability is the foundation — everything else depends on it.^[The [formal companion](formal-companion.md) develops the Harness's protocol as a session type (Def. 11.1) — the branching structure of permission gates, tool dispatch, and escalation. The protocol itself is specified: every branch is determined by the permission configuration, not by trained judgment.]

**Is there a mechanism for environmental scanning?** The checklist above is static — it assumes the designer configures the system once for a known task. Longer-running systems face a gap the framework hasn't addressed: novel disturbances from outside the configured scope. Beer's Viable System Model includes a dedicated component (System 4) that looks outward — scanning for changes in the environment that the current regulatory configuration doesn't anticipate. For single conversations, this is fine — the task is bounded. For persistent agents, autonomous pipelines, or systems that run across sessions, the absence of an environmental scanning function is a real gap. The configuration ratchet partially addresses this (it adapts configuration over time), but it learns from *internal* experience, not from external change. A complete regulatory architecture for long-lived systems would need both.

A deeper issue: the Harness as described in this series is doing Beer's System 2 work — *coordination*. It routes messages, applies protocols, enforces schemas at boundaries, constructs scope. The specified band argument is correct for coordination: it must be transparent and readable. But Beer's System 3 — *control* — is largely absent from current agent architectures or performed ad hoc by the Principal. Control asks: is this approach working? Should tools be restricted or expanded? Does the task need to pivot? The framework's three-layer regulation (constraints, observation, policy) maps to Beer's Systems 1-3 for coordination, but the control function and the real-time audit function (Beer's System 3*) need their own treatment. Post 8's pragmatic objection identifies the gap; a companion piece on the coordination/control distinction will develop it.

---

## What the formalism buys

A practitioner who follows the design rules above will build good systems without ever reading a monad morphism. The rules are the practical output. So what does the formalism buy?

A scope note first: the framework characterizes the space of possible behaviors, not the quality of behaviors within that space. It tells you what kind of system you're running — how hard it is to reason about, where the regulatory boundaries are, what the dynamics look like. It does not tell you whether the system is running well. Internal ma determines how many paths exist; which path is good depends on the task, the domain, and the quality of inference within the constrained space. This is a theory of structure, not a theory of intelligence.

**Diagnosis.** When a system behaves unexpectedly, the framework gives you vocabulary to locate the problem. Is it a grade issue (wrong tools granted)? A dynamics issue (computation channels creating self-amplification)? A scope issue (the Inferencer seeing too much or too little)? A regulation issue (the Harness leaving the specified band)? The vocabulary turns "something went wrong" into a structured diagnosis.

**Prediction.** The supermodularity claim is testable: restriction should have superlinear returns when both axes are high. The computation channel taxonomy is testable: systems at level 4+ should show qualitatively different failure modes than systems at levels 0-2. The specified band claim is testable: Harness characterizability should degrade when trained judgment enters the regulatory loop. These are claims precise enough to be wrong — and being precise enough to be wrong is the difference between intuition and engineering.

**Transfer.** The framework connects agent architecture to programming language theory, cybernetics, and capability-based security. Solutions from those fields transfer. Algebraic effects give us handler composition. Object capabilities give us POLA. The fold model gives us compaction as a first-class operation. The specified band gives us the OS as a design template. Each connection is a bridge to decades of prior work.

The formalism isn't the theory. It's the skeleton that lets the theory be tested, communicated, and improved. The [formal companion](formal-companion.md) provides the definitions, propositions, and conjectures. The blog series provides the intuitions. Building with ma is where both meet practice.

### What hasn't been tested

The framework generates testable predictions. No experiment has yet been designed to test them. The LangChain benchmark and the case studies apply the formalism post hoc — they check consistency, not predictive power. Prospective tests are the next step. The three most testable predictions: (1) restriction has superlinear returns when both axes of the grade are high (supermodularity of characterization difficulty); (2) unstructured natural-language delegation between agents produces quadratic growth in characterization difficulty relative to token budget, while structured schemas restore linear growth; (3) systems at computation channel level 4+ exhibit qualitatively different failure modes than systems at levels 0-2, with the phase transition at the semantic opacity boundary.

One implication deserves its own treatment: the design rules above are static — they tell you where to set the dials. But the dials can move on their own.

When a system captures what works and crystallizes it into specified tools, the effective grade drops without any change to the model. Bash commands that succeeded reliably become structured macros. Tool configurations that worked for common tasks become cached lookups. Each cycle converts trained *ma* into specified infrastructure — a behavior that was `(broad, trained)` as a Bash call becomes `(scoped, specified)` as a structured tool.

This is the [configuration ratchet](the-configuration-ratchet.md): a self-sustaining loop where high-*ma* exploration produces artifacts that enable low-*ma* application. The loop has three components: an explorer with enough *ma* to navigate the problem space, a specified capture process (logs, metrics, analysis), and a promotion step that crystallizes the winning pattern into infrastructure.

In Stafford Beer's variety engineering terms, the ratchet is a *variety amplifier* — it increases the Harness's effective regulatory repertoire over time without increasing its decision surface. Post 2's cybernetics section covered the attenuation side (tool restriction, sandboxing, co-domain funnels reduce the system's variety). The ratchet is the complementary strategy: expanding what the Harness can handle through crystallized infrastructure rather than trained judgment. Beer insisted both strategies are always needed simultaneously. The framework's coverage is now complete: attenuation through restriction, amplification through the ratchet.

The ratchet only turns one way. Each promotion moves a behavior from high *ma* to low *ma*, and there's no mechanism that moves it back. The specified band expands monotonically (Conj. 12.1 in the [formal companion](formal-companion.md)). The system gets more trustworthy with use — not because the model improved, but because the configuration layer accumulated evidence. The learning itself is specified: SQL queries over logs, human-reviewed code changes, validated promotions. At no point does opacity enter the learning loop.

This is the dynamic complement to the static design rules. The rules tell you how to configure a system. The ratchet tells you that a well-instrumented system will improve its own configuration over time — pushing the boundary between "requires inference" and "handled by specification" steadily toward the irreducible core. The design rules and the ratchet are the same framework applied to different timescales: one configures a conversation, the other configures the conversations to come.

---

## The space between

We started with an observation: every multi-agent system has a deterministic orchestrator at its hub, and the good ones restrict their agents' tools. We asked why. Nine posts later, the answer is a single concept applied at multiple scales.

Ma — the space between what an actor receives and what it produces — determines what the actor can do, how hard it is to reason about, and where it belongs in the architecture. The Harness belongs at the hub because its ma is low enough for everyone to model. Restriction works because it reduces ma at the boundary where it matters most. The OS proves that regulation scales with world coupling as long as the decision surface stays transparent. And conversations aren't growing computations — they're folds, managed by the actor whose type IS the persistent identity of the system.

The space between things is itself functional. Measure it, and the architecture follows.

---

*Previous: [The Specified Band](08-the-specified-band.md)*
