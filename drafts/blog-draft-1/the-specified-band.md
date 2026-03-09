# The Specified Band

*The OS already solved the regulation problem. The solution is vast world coupling with transparent decision surface.*

---

## The wrong worry

[Computation Channels](computation-channels.md) showed that at high computation levels — persistent processes, capability creation, controller modification — the Harness's regulatory model becomes incomplete. The star topology breaks. Side effects escape the fold. The natural response: the Harness should *observe more*. Monitor the process tree. Watch the filesystem. Track network connections. Audit system calls.

This seems to create a fundamental tension:

```
More capable agent  → needs more monitoring  → Harness world coupling rises
                    → Harness grade rises    → Harness becomes harder to characterize
                    → Principal's trust in   → system becomes harder to reason about
                      Harness decreases
```

The argument: a monitoring Harness moves rightward on the world coupling axis. Since characterization difficulty is supermodular, even moving on one axis increases it. The Harness's minimal ma — the property that makes it trustworthy at the hub — erodes. You can't increase the Harness's observational reach without sacrificing the characterizability that justifies its role.

This argument is wrong.

---

## The existence proof

The operating system manages every process, every file handle, every network socket, every memory page, every device. Its world coupling is essentially `IO_full` — it sees everything. Its decision surface is vast in absolute terms — the Linux kernel is millions of lines of specified logic. It coordinates huge numbers of concurrent, potentially adversarial entities with side effects, subprocess spawning, file mutation, network access, and inter-process communication.

And it's perfectly characterizable. You can read the source. You can predict what the scheduler will do given its state. You can audit the syscall interface. You can trace any decision the kernel makes back to a specified rule.

The OS lives at `(open, specified)`. Vast world coupling, transparent decision surface.

This disproves the tension. **World coupling growth does not inherently erode characterizability.** The supermodular cross-term between world coupling and decision surface is bounded by the *grade-relevant* measure of the decision surface, and "specified" means the decision surface is transparent. The cross-term doesn't activate because the processing is readable. The characterization difficulty of a specified function scales with the *size* of the specification, not exponentially with the world it observes.

A Harness that monitors the process tree, tracks filesystem events, and audits network connections is doing exactly what the OS already does. And it can do it with specified rules at high world coupling, maintaining full characterizability. The audit cost increases (more rules to read, more state to track), but the opacity doesn't (every rule is still transparent, every decision is still traceable).

---

## The specified band

The grade lattice has a band across the full width of the world coupling axis where characterization difficulty remains manageable:

```
                        World coupling
                        sealed → → → → → → → → open

Decision    evolved     |                        | Principal
surface     trained     |              Inferencer|
            configured  |                        |
            specified   | Harness     OS/Runtime | ← THE SPECIFIED BAND
            literal     | Executor               |
```

Every actor in the specified band — regardless of world coupling — has a transparent decision surface. Its behavior can be understood by reading its rules. The OS at `(open, specified)` is as characterizable *in kind* as the Harness at `(scoped, specified)`. The OS is harder to audit (more rules over more state) but not harder to characterize (still transparent).

The threat to regulation is never world coupling growth. It's **decision surface growth** — replacing specified rules with trained models in the regulator.

```
Specified Harness + process monitoring:    (broad, specified)  → characterizable
Specified Harness + filesystem auditing:   (broad, specified)  → characterizable  
ML-based anomaly detection on tool calls:  (broad, trained)    → opaque
```

The moment you replace specified rules with trained judgment in the regulator, the cross-term activates. A trained model making opaque decisions about process behavior over broad world state — that's the failure mode. Not because the world coupling is high, but because the decision surface became opaque.

This is the trajectory of real security systems. Start with sandboxing (constraint, specified). When sandboxing isn't enough, add monitoring (observation, specified). When monitoring generates too much data, add ML-based anomaly detection (inference, trained). And now the security system itself has high ma — trained models making opaque judgments. The regulator became as complex as what it regulates. Ashby's Law of Requisite Variety was satisfied, but at the cost of the regulatory model becoming uncharacterizable.

The framework's prescription: **stay in the specified band.** Increase world coupling as needed. Never increase the decision surface of the regulator beyond specified.

---

## Layered regulation

The OS doesn't solve its regulation problem with a single mechanism. It layers them. Each layer stays in the specified band independently.

### Layer 1: Constraints (preventive)

Permissions. Capabilities. Namespaces. Cgroups. Seccomp filters. These don't observe — they bound. A process in a network namespace can't reach the host network regardless of what it tries. A seccomp filter blocks forbidden syscalls at the kernel level. The constraint doesn't need to understand the process's intent. It limits what's *possible*.

For the conversation architecture: `IO_W` — the sandbox. `allowed_directories`, network isolation, resource limits. These are world coupling ceilings. The sandbox IS the regulator at this layer. Its ma is essentially zero — it's a boundary, not an actor. It doesn't need to observe the world because it constrains what's reachable.

### Layer 2: Observation (detective)

Process table. `/proc` filesystem. Audit logs. `strace`. These observe the world but don't decide. They produce data for the regulator. The observation mechanisms themselves are specified — they report what happened, not what it means.

For the conversation architecture: the Harness observing tool inputs and outputs. The fold. Conv_State tracking. The Harness records what happened at each step. Specified observation over accumulating state.

### Layer 3: Policy (regulatory)

SELinux. AppArmor. Firewall rules. Specified policy over observed state. The policy is a set of rules — read them, understand the enforcement. The rules operate over vast observed state (all process interactions, all file accesses, all network connections). But the rules themselves are transparent.

For the conversation architecture: the permission configuration. The session type (AutoAllow / Ask / AutoDeny per tool). The compaction thresholds. Budget management. All specified. All auditable. Operating over growing conversation state.

**Each layer stays in the specified band independently.** The constraint layer is `(open, literal)` — vast world coupling but the constraint mechanism has no decisions, just boundaries. The observation layer is `(open, literal)` — it reports, it doesn't decide. The policy layer is `(open, specified)` — rules over observed state. None requires trained judgment. The composition of three specified layers is still specified.

---

## What the Harness actually needs

The computation level taxonomy from the previous post identified where the Harness's regulatory model breaks down. The layered regulation pattern shows how to restore it without leaving the specified band.

**For levels 0–2 (data channels):** Layer 2 suffices. The Harness observes tool inputs and outputs. The fold is intact. No additional monitoring needed.

**For levels 3–4 (mutation and computation amplification):** Layer 1 + Layer 2. The sandbox constrains what the computation can access and modify (`IO_W` ceiling). The Harness observes the tool interface. The agent can write and execute within the sandbox, but the sandbox bounds the blast radius regardless of what the agent computes.

**For level 5 (environment modification):** Layer 3 enters. The Harness needs a policy for evaluating environment changes — "is this `pip install` acceptable?" This is specified: a whitelist, a capability check against a policy, a constraint that the installed package can't exceed the sandbox bounds. The policy is readable and auditable.

**For levels 6–8 (persistent processes, capability creation, controller modification):** All three layers, with the critical distinction between what each layer handles:

```
Layer 1 (constraint):   the sandbox bounds what ANY process can do.
                         Persistent processes, agent-created tools,
                         modified configurations — all operate within
                         the sandbox. The sandbox doesn't need to know
                         about them. It bounds them by construction.

Layer 2 (observation):   the Harness observes tool calls and their
                         direct outputs. It may not see subprocess
                         side effects. It reports what it can observe.

Layer 3 (policy):        specifies how to handle observed events.
                         Tool creation → evaluate effect signature.
                         Config modification → check against immutable core.
                         New process detected → apply resource limits.
```

The gap between Layer 2 (what the Harness observes) and Layer 1 (what the sandbox constrains) is the region of *unmediated but bounded* activity. Persistent processes, filesystem mutations between turns, background state accumulation — these happen in the gap. The Harness doesn't mediate them but the sandbox constrains them.

This is honest regulation. Not the fiction that the Harness mediates everything (it doesn't, once computation channels are granted). Not the abdication that anything goes within the sandbox (the Harness still gates tool calls, manages budget, constructs scope). But a realistic layered model: constrain what you can't observe, observe what you can, apply specified policy to observations.

---

## Capability publishing as staying specified

The handler pattern for levels 7–8 from the previous post has a specific mechanism that keeps the Harness in the specified band: **capability publishing**.

When an agent creates a new tool (level 7), the naive Harness has two options:

**Option A: Evaluate the tool with trained judgment.** The Harness reads the tool's code, reasons about its effects, assesses its safety. This requires a trained model in the regulatory loop. The Harness jumps from `(broad, specified)` to `(broad, trained)`. The cross-term activates. The regulator becomes opaque. Bad.

**Option B: Require the tool to declare its effects.** The new tool must provide an effect signature — what world it accesses, what it can modify, what computation level it operates at. The Harness evaluates the declaration with specified rules: does the declared effect signature conform to the current policy? Does it create new phase transitions with existing tools? The Harness stays specified.

The declaration might be wrong — the tool might actually do more than it declares. But that's what Layer 1 handles. The sandbox constrains the tool to what's *possible* regardless of what it *claims*. Verification of the declaration's honesty is delegated to the constraint layer, not the policy layer. The policy layer operates on declarations with specified rules. The constraint layer operates on reality with hard boundaries.

```
Without capability publishing:
  Harness must INFER tool safety → trained judgment → leaves specified band

With capability publishing:
  Tool DECLARES effect signature → Harness checks with specified rules → stays in band
  Sandbox ENFORCES bounds        → tool can't exceed sandbox regardless of declaration
```

This is the architectural pattern behind AIDR and the TTAM SQL boundary. The SQL schema IS the capability declaration. The agent knows what's expressible. The Harness enforces the query language with specified rules. The database engine enforces data access constraints. Layers 1 and 3 compose to provide regulation without any layer leaving the specified band.

---

## The SELinux coda

There's a catch. Regulation by constraint works — but the constraints must be at least partially visible to the constrained actor.

SELinux is specified. You can read the policy. A system administrator can audit every rule. It's `(broad, specified)` — a paradigmatic example of effective regulation within the specified band.

But from the *process's* perspective — the actor operating under the policy — SELinux is an invisible constraint that makes the environment behave inconsistently. `write()` works in `/tmp` but fails in `/var/log` with a permission denied that has nothing to do with Unix permissions. The process can't model its own environment because the policy isn't in its scope.

The policy is in the Harness's scope. It's NOT in the Inferencer's scope.

For the conversation architecture: when the Harness enforces a complex, opaque policy, it creates exactly the SELinux experience for the Inferencer. The model proposes a tool call. It gets denied. It doesn't know why — the permission policy isn't in its token window. It adjusts, tries something else, gets denied again for a different invisible reason. The model is doing inference against an environment it can't characterize because the constraints are invisible to it.

This is the difference between two kinds of specification:

```
Transparent specification:  the rules are visible to the governed actor.
                            The actor can model its own constraints.
                            Tool descriptions, explicit permission modes,
                            visible error messages with reasons.

Opaque specification:       the rules are specified but invisible to the governed actor.
                            The actor can't model why things fail.
                            SELinux policies, hidden permission logic,
                            silent denials, context-dependent constraints.
```

Both are specified. Both are characterizable by the administrator. But they create radically different environments for the actor. A transparent specification lets the Inferencer reason about its constraints — avoid proposing things it knows will be denied. An opaque specification forces the Inferencer to learn the constraints empirically, through trial and error, wasting budget on proposals that will fail.

The design principle: **minimize the gap between the full policy and its projection into the actor's scope.**

Not all policies can be fully projected — some security policies shouldn't be visible to the governed actor. But unnecessary opacity is a direct tax on system performance. The Inferencer burns the same compute exploring dead-end paths. From the system perspective, this is pure waste — the supermodular interaction between the trained decision surface and the world is spent discovering invisible walls instead of doing useful work.

Opaque policies don't reduce the Inferencer's ma. They reduce its *useful* ma while keeping its *total* ma the same. The decision surface churns against invisible constraints. The grade stays high but the effective work output drops. This is the worst combination: high regulatory cost (the policy must be maintained and enforced) with low regulatory benefit (the actor can't use the policy information to improve its behavior).

The SQL boundary gets this exactly right. The constraint IS the specification language. The agent sees the schema, knows the query language, and can characterize what's expressible. There's no gap between the policy and its projection — the projection IS the policy. The schema is simultaneously the security boundary, the capability declaration, and the agent's model of its own constraints. Zero opacity, zero wasted inference, zero SELinux surprises.

---

## The Ashby resolution

Ashby's Law of Requisite Variety: "Only variety can absorb variety." A controller's range of possible actions must match the system's range of possible disturbances.

The naive reading: as the agent gets more capable, the Harness must get more capable to match. The Harness's variety must grow to match the agent's variety. The regulator tracks the regulated system upward in complexity.

The framework's counter-move, now fully stated:

**The Harness doesn't match variety. It reduces it.** Co-domain funnels are variety attenuators. Tool restriction reduces the agent's effective variety. Sandboxing reduces it further. The Harness makes its own low variety sufficient by lowering the variety it needs to regulate.

**When reduction isn't enough, the Harness increases observation — not inference.** More world coupling (monitoring), same decision surface (specified rules). Move right in the specified band, not up into the trained row. The OS proves this is viable at any scale of world coupling.

**Capability publishing shifts the variety burden to the regulated system.** Instead of the regulator developing enough variety to evaluate arbitrary new capabilities, the capabilities declare their own variety (effect signatures). The regulator evaluates declarations with specified rules. The declaration is a variety attenuator — it compresses the tool's actual complexity into a characterizable interface.

**The sandbox is the backstop.** Layer 1 bounds variety regardless of what the regulator can observe. The sandbox doesn't need variety — it's a constraint, not a controller. It works by limiting what's possible, not by matching what's happening.

The full Ashby resolution: the Harness can regulate agents at any computation level by combining **variety reduction** (tool restriction, sandboxing), **specified observation** (monitoring within the specified band), **declared capabilities** (shifting evaluation from inference to verification), and **hard constraints** (the sandbox as backstop).

At no point does the Harness need to leave the specified band. At no point does it need trained judgment. At no point does its decision surface need to grow. Its world coupling may grow — and that's fine. The OS proved it. The specified band is wide enough for any world.

---

## What this means for architecture

The three posts in this sequence — [Conversations Are Folds](conversations-are-folds.md), [Computation Channels](computation-channels.md), and this one — resolve the conversation composition problem (Point 9 from the [self-critique](self-critique-formalisms.md)) while revealing new structure:

**Ma doesn't change.** It was always a property of a single computation. The conversation is a fold of single computations. The grade evolves, but ma is measured per step.

**The grade is dynamic.** It evolves via a coupled recurrence parameterized by Harness configuration. The computation level of the tool set determines the dynamics — bounded or self-amplifying.

**The specified band is the viable region for regulators.** World coupling can grow without limit. Decision surface must stay transparent. The OS is the existence proof.

**Constraint over observation. Observation over inference.** The Harness's regulatory strategy: sandbox first (bounds everything, observes nothing, zero ma). Observe what you can within the fold (tool inputs and outputs, Conv_State). Apply specified policy to observations. Never replace specified rules with trained models in the regulatory loop.

**The SQL boundary is optimal for high-trust data access** because it holds the conversation at computation level 0, keeps the Harness in the specified band, and projects the full policy into the agent's scope. It's not just a security choice — it's a *dynamics* choice. It selects the convergent regime of the grade recurrence.

---

## References

- Ashby, W. R. (1956). *An Introduction to Cybernetics*. Chapman & Hall.
- Conant, R. C., & Ashby, W. R. (1970). Every good regulator of a system must be a model of that system. *International Journal of Systems Science*, 1(2).
- Miller, M. S. (2006). *Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control*. PhD thesis, Johns Hopkins University.
- Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. *Proceedings of the IEEE*, 63(9).
- Smalley, S., Vance, C., & Salamon, W. (2001). Implementing SELinux as a Linux security module. *NAI Labs Report #01-043*.

---

*Previous: [Computation Channels](computation-channels.md)*
