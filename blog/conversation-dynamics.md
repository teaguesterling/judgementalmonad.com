# Conversation Dynamics

*Point 9 dissolves, then reconstitutes richer.*

**Note**: This was a working draft. The canonical treatment is split across [Conversations Are Folds](conversations-are-folds.md) (core theory: fold structure, composite entity, coupled recurrence, d_reachable vs d_total) and [Computation Channels](computation-channels.md) (channel taxonomy, star topology, regulator band, constraint projection). This file can be retired after confirming all content is covered.

---

## The simple resolution

Every inference call is stateless.

The Inferencer receives a context, produces a response, and forgets everything. It has no memory between calls. The "conversation" is an illusion created by the Harness including previous turns in the next input. Each inference call closes over a different prefix of the conversation log, but the computation itself is one-shot every time.

This means there's no special "conversation composition." A conversation is iterated one-shot composition where the Harness threads state via a fold over `Conv_State`:

```
conv = foldl step initial_state turns
  where step state turn = handle(infer(view(state)), config(state))
```

Each `infer(view(state))` is a single inference call with grade `(sealed, trained)` — sealed because the model doesn't touch the world (tool calls are proposals, not actions), trained because the weights encode a vast decision surface. The grade doesn't change between turns. Ma is a property of a single computation. The computation is the same every time. Point 9 dissolves.

Done?

---

## Pulling the thread

Not done. The Principal doesn't interact with individual inference calls. The Principal interacts with a *composite entity* — the system that remembers, uses tools, manages files, runs code. That entity IS stateful. `Conv_State` accumulates. Tools execute with real-world effects. The conversation's history shapes its future.

When we look at the composite entity honestly, six things fall out.

### 1. Context growth is world coupling, not decision surface

The self-critique noted that "decision surface grows at runtime" in multi-turn conversations. This was imprecise. The weights don't change between turns. The model's total decision surface — the full space of functions its architecture can represent — is constant. What grows is the *context*: more information entering through the input boundary.

Context growth is world coupling growth. Each turn adds data from the world (user messages, tool results, file contents) to the input. The model sees more of the world with each turn.

But there's a subtlety. More context means more attention interaction terms, which means more *reachable* paths through the fixed weights. A model with 10 tokens of context can realize fewer of its possible behaviors than the same model with 10,000 tokens. The total decision surface is constant (determined by architecture and weights). The *reachable* decision surface grows with context:

```
d_reachable(t) = f(d_total, context_length(t))
```

where `d_reachable` is monotonically non-decreasing in `context_length` up to the model's effective window, then potentially degrading (the "lost in the middle" phenomenon — empirical, not formal, but real).

This distinction matters: `d_total` is a property of the model. `d_reachable` is a property of the model *in context*. The grade of an inference call at turn `t` is `(w(t), d_reachable(t))`, not `(sealed, d_total)`. And `w(t)` isn't sealed — the context contains information from the world. Each inference call's world coupling reflects the accumulated world exposure of the conversation so far.

### 2. The grade is a coupled recurrence

The grade at turn `t+1` depends on the grade at turn `t` and the Harness's configuration:

```
g(t+1) = F(g(t), config(t))
```

Both axes are coupled. The world coupling at `t+1` depends on what tools were used at `t` (their results enter the context, carrying world information). The reachable decision surface at `t+1` depends on the context length (which grew due to turn `t`'s content, which depended on both the world coupling and the decision surface at `t`).

The Harness controls the trajectory through `config(t)`:

- **Tool grants** increase world coupling (more world-touching tools = more world data entering the context)
- **Tool revocations** constrain world coupling going forward (but past world data remains in the context)
- **Compaction** reduces both axes: shorter context means fewer reachable paths and less world information visible
- **Scope restriction** reduces world coupling by hiding parts of the accumulated context

Compaction deserves emphasis. It's the Harness acting as a grade-reducing functor *within* the conversation — the same concept from the [grade lattice](the-grade-lattice.md), applied at a different timescale. Not initial configuration, but ongoing trajectory management. The trajectory is piecewise monotone: grades grow within a phase (context accumulates), drop at compaction points (context reduced), then grow again. A sawtooth, with the Harness controlling the teeth.

### 3. Computation channels create phase transitions

Not all tools are equal from the trajectory's perspective. Consider:

**SQL query tool**: The Inferencer writes a query, the Executor runs it, results come back. The world coupling increases (database contents enter the context). But the tool's *output* can't become a new *computation*. The tool is a read channel. The trajectory advances smoothly.

**Bash tool**: The Inferencer writes a shell command — or a Python script — and the Executor runs it. Now the tool's output can include *anything the underlying system can compute*. But more importantly, the Inferencer's trained decision surface is generating *executable specifications*. The agent's `d_trained` becomes a meta-surface that can instantiate new computations whose own decision surfaces compound with the original.

This is a qualitative difference. Computation channels — tools that accept agent-generated text as executable specification — create a **self-amplifying dynamic** in the grade trajectory. The agent can write a program that writes a program that accesses the filesystem that produces output that informs the next inference call. Each step compounds.

This isn't a third axis. It's a property of the tool composition that determines the *derivative* of the grade trajectory:

| Channel type | Example | Trajectory dynamics |
|---|---|---|
| **Read** | File read, search | Bounded: adds data, doesn't compound |
| **Query** | SQL, API calls | Bounded: structured data in, structured data out |
| **Transform** | Regex, format conversion | Bounded: reshapes without amplifying |
| **Compute** | Bash, `python -c`, eval | Self-amplifying: output can be new computation |

The grade lattice measures where you are. The computation channel determines how fast you're moving.

### 4. The star topology is an aspiration

The [formal framework](../formal-framework.md) describes a star topology: the Harness at the hub, all actors communicating through it. Every tool call is proposed by the Inferencer, mediated by the Harness, dispatched to an Executor, results injected back through the Harness.

With computation channels, this breaks. When the Inferencer writes `bash -c "curl ... | python3 -c ..."`, the subprocess escapes the Harness's mediation entirely. The Executor becomes a portal to unmediated computation. The Harness's regulatory model — know the effect signature, have a handling strategy — becomes incomplete because the effect signature of Bash is `IO` (anything).

The star topology is an aspiration, not an invariant. The moment `Bash` is granted, the Harness relies on the **sandbox**, not the **Harness**, as the load-bearing boundary for unmediated actors. The sandbox (filesystem restrictions, network policies, process isolation) provides the actual containment. The Harness provides the *mediated* containment — the star topology — which is valuable but not complete.

This is the honest accounting: the Harness's regulatory model works perfectly for structured tools (SQL, file read, API calls) where the effect signature is known. For computation channels, the Harness delegates containment to the sandbox and manages what it can — approving or denying the initial grant, monitoring outputs, revoking access if needed.

### 5. The regulator's viable region

If the Harness is a controller managing a dynamical system with inherent grade inflation, does its own grade need to grow to keep up? Ashby's Law of Requisite Variety says the regulator needs variety matching the system it regulates.

The resolution is the operating system. The OS has vast world coupling (manages all hardware, all processes, all files) AND vast decision surface (the kernel's code paths are enormously complex) — yet it's perfectly predictable. Grade: `(open, specified)`. Every behavior is determined by documented rules. The variety is enormous but fully characterized.

The `(open, specified)` band is the viable region for regulators:

```
World coupling: as broad as needed (must see everything it regulates)
Decision surface: specified (all behavior follows documented rules)
```

The Harness lives here. Its world coupling is broad (it sees the full conversation state, all tool results, Principal input). Its decision surface is specified (its behavior is determined by configuration, permission rules, and protocol — not by learned patterns).

The threat to the regulator is never world coupling growth — it's decision surface growth. An "intelligent" Harness that replaces specified rules with trained models would move from `(open, specified)` to `(open, trained)`, gaining the same characterization difficulty as the thing it's trying to regulate. The regulator's power comes from being less complex than its subject along the decision surface axis while being equally coupled along the world coupling axis.

### 6. The SELinux coda

A practical consequence: constraints that the actor can't see waste the actor's decision surface on invisible walls.

If the sandbox blocks `/etc/passwd` but the Inferencer doesn't know this, it may spend turns attempting to read it, interpreting errors, trying workarounds — burning decision surface on a constraint it could have respected trivially if it knew about it. The Inferencer's effective decision surface is split between doing useful work and discovering invisible boundaries.

SELinux learned this: mandatory access control works best when the policy is visible to the processes it governs (via labeling, error messages, policy queries). Invisible constraints are still enforced, but they waste compute — both silicon and cognitive.

The architectural principle: **constraints should be projected into the actor's scope**. If the Harness restricts a tool, tell the Inferencer it's restricted (remove it from the tool list, note it in the system prompt). If the sandbox blocks a path, include the sandbox boundaries in the context. The Harness's scope management isn't just about what the actor *gets to see* — it's about ensuring the actor sees the *boundaries*, so it doesn't waste its decision surface discovering them empirically.

---

## What changed in the model

The grade lattice and ma definition survive untouched. Ma is a property of a single computation's path space. The conversation is a *sequence* of single computations, not a single growing computation. What's new:

**The grade is dynamic.** It evolves via a coupled recurrence `g(t+1) = F(g(t), config(t))`, parameterized by Harness configuration. Each turn's grade depends on accumulated context (world coupling) and reachable decision surface (context length mediating total capacity).

**Reachable vs total decision surface.** `d_reachable(context_length) ≤ d_total`. The model's architectural capacity is fixed. The conversation determines how much of it is exercised. Context growth increases reachable decision surface; compaction reduces it.

**Computation channels have a taxonomy.** Read, query, transform, and compute channels differ in how they affect the grade trajectory's derivative. Compute channels (Bash, eval) are self-amplifying — the agent's decision surface generates new computations that compound. This isn't a new axis; it's a property of the tool composition.

**The `(open, specified)` band.** This is the viable region for regulators. The OS is the existence proof. The threat to the regulator is never broader world coupling — it's higher decision surface (replacing specified rules with trained models).

**The Harness is a dynamical system controller.** Not a grade-reducing functor applied at setup, but an ongoing trajectory manager. It observes the conversation state, applies control actions (compaction, reconfiguration, tool grants/revocations), and steers the grade trajectory. The star topology is the ideal; the sandbox is the fallback for computation channels that escape mediation.

**Constraints should be projected into scope.** Invisible restrictions waste the actor's decision surface on empirical boundary-discovery. The Harness's scope management includes making boundaries visible.

---

## Connection to the existing framework

### What this resolves

**Point 9 of the self-critique**: "The composition story is incomplete for conversations." Resolved by recognizing that each inference call IS one-shot composition — the grade lattice handles it. The conversation adds dynamics: a grade trajectory governed by a coupled recurrence, with the Harness as controller. No new algebra needed; the new structure is the trajectory and the control.

### What this extends

- **The grade-reducing functor** (from [the grade lattice](the-grade-lattice.md)) extends from initial configuration to ongoing trajectory management. Compaction is the Harness applying grade reduction mid-conversation.
- **The handler framing** (from [raising and handling](raising-and-handling.md)) gains temporal structure. The handler's strategy can be state-dependent — more restrictive handling as the grade increases.
- **The configuration lattice** becomes a time-varying control input, not a static choice. The Harness navigates it continuously, not once.
- **The Conant-Ashby connection** gains the `(open, specified)` existence proof. The OS shows that vast regulatory scope is compatible with full characterizability — the key is staying in the specified band of the decision surface axis.

### What's new

- **Reachable decision surface** as a dynamic quantity, distinct from total decision surface.
- **Computation channel taxonomy**: read, query, transform, compute — determined by whether the tool's output can become new computation.
- **Star topology as aspiration**: computation channels escape mediation; the sandbox, not the Harness, is the load-bearing boundary for unmediated actors.
- **Constraint projection**: the principle that boundaries should be visible to the actors they govern.

---

## Open questions

1. **Trajectory comparison.** How do you compare two conversations' grade trajectories? Peak grade (worst-case characterization)? Integral (total characterization load)? Endpoint? Different comparisons serve different purposes.

2. **Optimal compaction policy.** If compaction is grade reduction and context growth is grade inflation, is there an optimal compaction schedule? The Harness is solving a control problem — minimize characterization difficulty while maximizing task-relevant information retention. This connects to the rate-distortion theory of lossy compression.

3. **Computation channel detection.** Can the Harness detect when a tool call enters self-amplifying dynamics? The session type currently treats all tool calls uniformly. A grade-aware handler might handle compute-channel calls differently — tighter sandboxing, more frequent checkpoints, mandatory output review.

4. **The multi-conversation case.** This post treats a single conversation. But agents increasingly operate across conversations — memory systems, session histories, persistent state. The grade of a *system of conversations* is another level of dynamics beyond the single trajectory.
