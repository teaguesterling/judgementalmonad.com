# Building With Ma

*Eight posts of theory. Now: what do you actually do with it?*

---

## The design rules

The framework yields a small number of rules. They're not new — practitioners already follow most of them. What's new is the unified explanation. Each rule falls out of the same structure: the grade lattice, the preorder, the coupled recurrence, the specified band.

**1. Restrict tools, not models.** An Opus model with `{Read, Approve, Reject}` has high internal ma (good reasoning) and low interface ma (three possible effects). A Haiku model with 50 tools has low internal ma and high interface ma. The first is the better auditor. Model selection determines the quality of decisions within the constrained space. Tool selection determines the *size* of the space. Size matters more than quality for characterizability (post 2's supermodularity).

**2. The most important configuration decision is the computation channel level.** Does any tool accept agent-generated text as executable specification? If yes, you're running a universal machine with self-amplifying dynamics. If no, you're running a bounded transducer with convergent dynamics. This is a qualitative difference (post 7). Swapping models changes the quality of decisions. Granting Bash changes what kind of system you're running.

**3. Sandbox configuration > model configuration.** The sandbox is a dynamics controller (post 7). It determines which phase transitions are reachable. Restricting the sandbox of a computation-channel tool eliminates phase transitions — it changes the dynamics from self-amplifying to convergent. That's a qualitative shift, not a linear improvement.

**4. Stay in the specified band.** Every decision the Harness makes should be traceable to a specified rule. The moment you replace specified rules with trained models in the regulatory loop — ML-based anomaly detection, LLM-backed policy evaluation — the Harness's characterizability erodes (post 8). Increase observation (world coupling) as needed. Never increase the decision surface beyond specified.

**5. Project constraints into the actor's scope.** Every constraint the Inferencer can't see is a tax on system performance (post 8's SELinux coda). Tool descriptions, explicit permission modes, visible error messages with reasons — these let the model reason about its constraints instead of discovering them empirically. Minimize the gap between the policy and its projection.

**6. Use co-domain funnels at every boundary.** High internal ma compressed through low interface ma (post 2). The auditor pattern (Opus + Approve/Reject), the sub-agent boundary (full conversation → summarized result), the tool-selection agent (inference-backed → finite kit). Deep reasoning, characterizable output. Every time you need high-quality decisions at a boundary, the funnel is the pattern.

---

## Multi-agent systems

The framework was built on a single-conversation model. How does it extend?

**Multiple Inferencers.** A planner, a worker, and a reviewer are three Inferencers with different tool sets and different scopes — different compound grades at each step of the fold. The Harness manages three grade trajectories, not one. Each trajectory has its own computation channel level. The planner might have only data channels (levels 0-2, convergent). The worker might have computation channels (level 4+, self-amplifying). The reviewer might have restricted output tools (Approve/Reject — a co-domain funnel).

The design question: which Inferencer gets which tools? The framework's answer: minimize the compound grade at each boundary. Give the planner enough to plan (scoped world coupling, no execution). Give the worker enough to work (computation channels, sandboxed). Give the reviewer the narrowest possible interface (high internal ma, low interface ma). Each actor's tool set determines its computation channel level, which determines its trajectory dynamics, which determines how hard it is to regulate.

A concrete example: a coding agent with a planning phase and an execution phase. The planner gets `{Read, Glob, Grep}` — data channels only, level 0-2, convergent dynamics. It reads the codebase, reasons about the change, and outputs a structured plan. The executor gets `{Read, Edit, Write, Bash}` — computation channels, level 4+, self-amplifying dynamics, sandboxed to the project directory with no network access. The sandbox caps the computation level: no `pip install` (level 5 blocked), no persistent processes reaching outside (level 6 bounded), no tool creation (level 7 impossible without network). A reviewer gets `{Approve, Reject, RequestChanges}` — three output tokens, high internal ma compressed through the narrowest possible interface. The reviewer is an Opus model; its reasoning quality is high but its interface ma is nearly zero.

```
Planner:   (scoped, trained) × {Read, Glob, Grep}     → level 0-2, convergent
Executor:  (scoped, trained) × {Read, Edit, Write, Bash} → level 4, sandboxed
Reviewer:  (scoped, trained) × {Approve, Reject, RequestChanges} → level 0, co-domain funnel
```

Three agents, three computation levels, three regulatory profiles — managed by one specified Harness. The planner's trajectory drifts gently upward (data accumulation). The executor's trajectory can self-amplify but is bounded by the sandbox. The reviewer's trajectory is nearly flat. The system's overall grade is the supremum across all three trajectories (post 6), which means the executor determines the regulatory burden. Everything else is designed to keep the executor's trajectory bounded while giving it enough capability to do useful work.

**Sub-agent boundaries.** A sub-agent is a composite entity (post 6) — it has its own fold, its own Conv_State, its own grade trajectory. At the boundary, it's a co-domain funnel: rich internal dynamics compressed to a summarized result. The outer Harness sees the summary, not the internal conversation. The sub-agent's internal Harness manages its own regulation. The outer Harness manages the sub-agent's interface ma.

This is why the framework is recursive. The turn cycle (extract → process → inject) applies at every level. The grade applies at every level. The specified band applies at every level. A well-designed multi-agent system is a tree of co-domain funnels, each managed by a specified Harness, each presenting a characterized interface to the level above.

**Agent-to-agent communication.** The star topology says all communication passes through the Harness. In a multi-agent system, that means agents don't talk to each other — they talk to their Harness, which constructs the next agent's input. This is the capability-based security parallel from post 5: the Harness controls capability grants, and peer-to-peer delegation breaks the supermodularity argument because actors can increase each other's grade without the Harness's knowledge.

If you need agent-to-agent communication, route it through the Harness as mediated handoffs. The Harness can scope what flows between agents (capture list construction from post 3), gate what effects carry over (handler composition from post 4), and manage the compound grade of the receiving agent.

---

## The decision checklist

When designing a multi-agent system, the framework suggests asking these questions in order:

**What computation channel level does each agent need?** This determines the dynamics. Start at the lowest level that achieves the task. A retrieval agent needs level 0 (structured queries). A code-writing agent needs level 3-4 (write + execute). A deployment agent might need level 5+ (environment modification). The level determines the regulatory burden.

**What sandbox configuration does each agent get?** This determines which phase transitions are reachable. Lock down what you can. Network isolation, filesystem bounds, resource limits. The sandbox is your primary dynamics controller.

**What tools does each agent get?** This determines the compound grade. Fewer tools = lower interface ma = easier to reason about from outside. Every tool you add raises the grade. The supermodularity means the cost of each additional tool is higher when the existing tool set is already broad.

**What does each agent see?** This is scope construction — the capture list. Include what the agent needs to do its work. Exclude everything else. Every token in the context window is world coupling that contributes to d_reachable.

**What does the outer system see of each agent?** This is the co-domain funnel. The sub-agent's interface should be as narrow as possible. A tool-selection agent should output a finite kit, not a narrative explanation. A reviewer should output Approve/Reject, not a detailed commentary. The interface determines where the agent sits in the preorder and therefore who can reason about it.

**Is the Harness staying in the specified band?** If any regulatory decision requires trained judgment (LLM-backed evaluation, ML anomaly detection), redesign. Use capability publishing (require declarations, evaluate with specified rules). Use layered regulation (constrain, observe, apply policy). The Harness's characterizability is the foundation — everything else depends on it.

---

## What the formalism buys

A practitioner who follows the design rules above will build good systems without ever reading a monad morphism. The rules are the practical output. So what does the formalism buy?

**Diagnosis.** When a system behaves unexpectedly, the framework gives you vocabulary to locate the problem. Is it a grade issue (wrong tools granted)? A dynamics issue (computation channels creating self-amplification)? A scope issue (the Inferencer seeing too much or too little)? A regulation issue (the Harness leaving the specified band)? The vocabulary turns "something went wrong" into a structured diagnosis.

**Prediction.** The supermodularity claim is testable: restriction should have superlinear returns when both axes are high. The computation channel taxonomy is testable: systems at level 4+ should show qualitatively different failure modes than systems at levels 0-2. The specified band claim is testable: Harness characterizability should degrade when trained judgment enters the regulatory loop. These are claims precise enough to be wrong — and being precise enough to be wrong is the difference between intuition and engineering.

**Transfer.** The framework connects agent architecture to programming language theory, cybernetics, and capability-based security. Solutions from those fields transfer. Algebraic effects give us handler composition. Object capabilities give us POLA. The fold model gives us compaction as a first-class operation. The specified band gives us the OS as a design template. Each connection is a bridge to decades of prior work.

The formalism isn't the theory. It's the skeleton that lets the theory be tested, communicated, and improved. The formal companion (forthcoming) provides the proofs. The blog series provides the intuitions. Building with ma is where both meet practice.

---

## The space between

We started with an observation: every multi-agent system has a deterministic orchestrator at its hub, and the good ones restrict their agents' tools. We asked why. Nine posts later, the answer is a single concept applied at multiple scales.

Ma — the space between what an actor receives and what it produces — determines what the actor can do, how hard it is to reason about, and where it belongs in the architecture. The Harness belongs at the hub because its ma is low enough for everyone to model. Restriction works because it reduces ma at the boundary where it matters most. The OS proves that regulation scales with world coupling as long as the decision surface stays transparent. And conversations aren't growing computations — they're folds, managed by the actor whose type IS the persistent identity of the system.

The space between things is itself functional. Measure it, and the architecture follows.

---

*Previous: [The Specified Band](08-the-specified-band.md)*
