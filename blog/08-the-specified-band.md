# The Specified Band

*The OS already solved the regulation problem. The solution is vast world coupling with transparent decision surface.*

---

## The wrong worry

Post 7 showed that at high computation levels — persistent processes, capability creation, controller modification — the Harness's regulatory model becomes incomplete. The star topology breaks. Side effects escape the fold. The natural response: the Harness should *observe more*. Monitor the process tree. Watch the filesystem. Track network connections. Audit system calls.

This seems to create a fundamental tension:

```
More capable agent  → needs more monitoring  → Harness world coupling rises
                    → Harness grade rises    → Harness becomes harder to characterize
                    → Principal's trust in   → system becomes harder to reason about
                      Harness decreases
```

The argument: a monitoring Harness moves rightward on the world coupling axis. Since characterization difficulty is supermodular (post 2), even moving on one axis increases it. The Harness's low ma — the property that makes it trustworthy at the hub (post 1) — erodes. You can't increase the Harness's observational reach without sacrificing the characterizability that justifies its position.

This argument is wrong.

---

## The existence proof

The operating system manages every process, every file handle, every network socket, every memory page, every device. Its world coupling is essentially unbounded — it sees everything. Its decision surface is vast in absolute terms — the Linux kernel is millions of lines of specified logic. It coordinates huge numbers of concurrent, potentially adversarial entities with side effects, subprocess spawning, file mutation, network access, and inter-process communication.

And it's perfectly characterizable. You can read the source. You can predict what the scheduler will do given its state. You can audit the syscall interface. You can trace any decision the kernel makes back to a specified rule.

The OS lives at `(open, specified)`. Vast world coupling, transparent decision surface.

This disproves the tension. **World coupling growth does not inherently erode characterizability.** The supermodular cross-term between world coupling and decision surface is bounded by the decision surface's transparency, and "specified" means transparent. The cross-term doesn't activate because the processing is readable. The characterization difficulty of a specified function scales with the *size* of the specification — more rules to read, more state to track — not exponentially with the world it observes.

A Harness that monitors the process tree, tracks filesystem events, and audits network connections is doing exactly what the OS already does. And it can do it with specified rules at high world coupling, maintaining full characterizability. The audit cost increases. The opacity doesn't.

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

Every actor in the specified band — regardless of world coupling — has a transparent decision surface. Its behavior can be understood by reading its rules.^[The [formal companion](formal-companion.md) develops this as Def. 10.1 and Props. 10.2–10.3. The supermodular cross-term (Prop. 4.7) doesn't activate in the specified band because `log P(specified)` is bounded by the log of the rule count.] The OS at `(open, specified)` is as characterizable *in kind* as the Harness at `(scoped, specified)`. The OS is harder to audit (more rules over more state) but not harder to characterize (still transparent). Auditability is quantitative — how much specified logic do you need to read? Characterizability is qualitative — is the logic specified at all, or is it opaque? The difference is the whole point.

The threat to regulation is never world coupling growth. It's **decision surface growth** — replacing specified rules with trained models in the regulator.

```
Specified Harness + process monitoring:    (broad, specified)  → characterizable
Specified Harness + filesystem auditing:   (broad, specified)  → characterizable
ML-based anomaly detection on tool calls:  (broad, trained)    → opaque
```

The moment you replace specified rules with trained judgment in the regulator, the cross-term activates. A trained model making opaque decisions about process behavior over broad world state — that's the failure mode. Not because the world coupling is high, but because the decision surface became opaque.

This is the trajectory of real security systems. Start with sandboxing (constraint, specified). When sandboxing isn't enough, add monitoring (observation, specified). When monitoring generates too much data, add ML-based anomaly detection (inference, trained). And now the security system itself has high ma — trained models making opaque judgments. The regulator became as complex as what it regulates. The Ashby trap.

The framework's prescription: **stay in the specified band.** Increase world coupling as needed. Never increase the decision surface of the regulator beyond specified.

---

## Layered regulation

The OS doesn't solve its regulation problem with a single mechanism. It layers three kinds of regulation, each staying in the specified band independently.

### Layer 1: Constraints

Permissions. Capabilities. Namespaces. Cgroups. Seccomp filters. These don't observe — they *bound*. A process in a network namespace can't reach the host network regardless of what it tries. A seccomp filter blocks forbidden syscalls at the kernel level. The constraint doesn't need to understand the process's intent. It limits what's *possible*.

For the conversation architecture: the sandbox. `allowed_directories`, network isolation, resource limits. These are world coupling ceilings. The sandbox IS the regulator at this layer. Its ma is essentially zero — it's a boundary, not an actor.

### Layer 2: Observation

Process table. `/proc` filesystem. Audit logs. `strace`. These observe the world but don't decide. They produce data for the policy layer. The observation mechanisms themselves are specified — they report what happened, not what it means.

For the conversation architecture: the Harness observing tool inputs and outputs. The fold from post 6. `Conv_State` tracking. The Harness records what happened at each step.

### Layer 3: Policy

SELinux. AppArmor. Firewall rules. Specified policy over observed state. The policy is a set of rules — read them, understand the enforcement. The rules operate over vast observed state (all process interactions, all file accesses, all network connections). But the rules themselves are transparent.

For the conversation architecture: the permission configuration (auto-allow Read, ask for Bash, auto-deny network). Compaction thresholds. Budget management. All specified. All auditable. Operating over growing conversation state.

**Each layer stays in the specified band independently.** The constraint layer doesn't decide — it bounds. The observation layer doesn't decide — it reports. The policy layer decides, but with specified rules over observed state. None requires trained judgment. The composition of three specified layers is still specified.^[Def. 10.4 and Prop. 10.5 in the [formal companion](formal-companion.md).]

The gap between Layer 2 (what the Harness observes) and Layer 1 (what the sandbox constrains) is the region of *unmediated but bounded* activity. Persistent processes, filesystem mutations between turns, background state accumulation — these happen in the gap. The Harness doesn't mediate them, but the sandbox constrains them.

This is honest regulation. Not the fiction that the Harness mediates everything (it doesn't, once computation channels are granted). Not the abdication that anything goes within the sandbox (the Harness still gates tool calls, manages budget, constructs scope). A realistic layered model: constrain what you can't observe, observe what you can, apply specified policy to observations.

---

## Capability publishing

Post 7's level 6 (capability creation) poses a specific challenge: the agent creates new tools. How does the Harness evaluate them without leaving the specified band?

The naive approach requires the Harness to *infer* the tool's safety — read its code, reason about its effects. This requires trained judgment in the regulatory loop. The Harness jumps from `(broad, specified)` to `(broad, trained)`. The cross-term activates. The regulator becomes opaque.

The alternative: **require the tool to declare its effects.** The new tool provides an effect signature — what world it accesses, what it can modify, what computation level it operates at. The Harness evaluates the declaration with specified rules: does the declared effect signature conform to the current policy? Does it create new phase transitions with existing tools?

The declaration might be wrong — the tool might do more than it claims. But that's what Layer 1 handles. The sandbox constrains the tool to what's *possible* regardless of what it *declares*. Verification of the declaration's honesty is delegated to the constraint layer. The policy layer operates on declarations with specified rules. The constraint layer operates on reality with hard boundaries.

```
Without capability publishing:
  Harness must INFER tool safety → trained judgment → leaves specified band

With capability publishing:
  Tool DECLARES effect signature → Harness checks with specified rules → stays in band
  Sandbox ENFORCES bounds        → tool can't exceed sandbox regardless of declaration
```

The Harness stays specified. The sandbox stays literal. The declaration is a variety attenuator — it compresses the tool's actual complexity into a characterizable interface. Another co-domain funnel (post 2), this time applied to the tool's own self-description.

---

## The SELinux coda

There's a catch. Regulation by constraint works — but the constraints must be at least partially visible to the constrained actor.

SELinux is specified. You can read the policy. A system administrator can audit every rule. It's `(broad, specified)` — a paradigmatic example of effective regulation within the specified band.

But from the *process's* perspective — the actor operating under the policy — SELinux is an invisible constraint that makes the environment behave inconsistently. `write()` works in `/tmp` but fails in `/var/log` with a permission denied that has nothing to do with Unix permissions. The process can't model its own environment because the policy isn't in its scope.

The policy is in the Harness's scope. It's NOT in the Inferencer's scope.

For the conversation architecture: when the Harness enforces a complex, opaque policy, it creates exactly the SELinux experience for the Inferencer. The model proposes a tool call. It gets denied. It doesn't know why — the permission policy isn't in its token window. It adjusts, tries something else, gets denied again for a different invisible reason. The model is doing inference against an environment it can't characterize because the constraints are invisible to it.

The distinction:

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

Opaque policies don't reduce the Inferencer's ma. They reduce the portion of its decision surface spent on proposals that could actually succeed, while keeping the total decision surface the same. The model churns against invisible constraints — exploring paths the policy will reject, re-deriving boundaries it could have respected from the start. The grade stays high but the effective work output drops. The worst combination: high regulatory cost with low regulatory benefit. Opaque constraints don't reduce the space — they misplace it. The agent's decision surface is consumed by navigating invisible boundaries rather than doing useful work. Transparent constraints move the space from "guessing what's allowed" to "choosing what's best."

The design principle: **minimize the gap between the full policy and its projection into the actor's scope.** Not all policies can be fully projected — some security constraints shouldn't be visible. But unnecessary opacity is a direct tax on system performance.^[Def. 10.7 and Prop. 10.8 in the [formal companion](formal-companion.md).]

Mick Ashby's Ethical Regulator Theorem (2020) validates this distinction independently. The theorem identifies nine requisites for effective and ethical regulation, and proves that transparency is formally separable from effectiveness: a regulator *can* be effective without transparency — SELinux regulates — but it cannot be ethical without it, because the governed actor can't adapt to constraints it can't see. The theorem also requires *integrity* — the regulator's actual behavior must match its declared rules — which is the specified band argument expressed differently. Specified means both readable and faithful. The nine requisites map surprisingly well onto the framework's own components: purpose (task configuration), truth (observation layer), variety (tool set), predictability (specified band), influence (tool dispatch), and transparency (constraint projection into the actor's scope).

---

## The Ashby resolution

Post 2 introduced Conant-Ashby: every good regulator must be a model of the system it regulates. And Ashby's Law of Requisite Variety: a controller's range of possible actions must match the system's range of possible disturbances.

The naive reading: as the agent gets more capable, the Harness must get more capable to match. The regulator tracks the regulated system upward in complexity. This is the Ashby trap — and it's how security systems actually fail, replacing specified rules with trained models to keep up.

The framework's counter-move, now fully stated:

**The Harness doesn't match variety. It reduces it.** Co-domain funnels (post 2) are variety attenuators. Tool restriction reduces the agent's effective variety. Sandboxing reduces it further. The Harness makes its own low variety sufficient by lowering the variety it needs to regulate.

**When reduction isn't enough, the Harness increases observation — not inference.** More world coupling (monitoring), same decision surface (specified rules). Move right in the specified band, not up into the trained row. The OS proves this is viable at any scale.

**Capability publishing shifts the variety burden to the regulated system.** Instead of the regulator developing enough variety to evaluate arbitrary new capabilities, the capabilities declare their own variety. The regulator evaluates declarations with specified rules. Another variety attenuator.

**The sandbox is the backstop.** Layer 1 bounds variety regardless of what the regulator can observe. The sandbox doesn't need variety — it's a constraint, not a controller. It works by limiting what's possible, not by matching what's happening.

The full resolution: the Harness can regulate agents at any computation level by combining variety reduction (tool restriction, sandboxing), specified observation (monitoring within the specified band), declared capabilities (shifting evaluation from inference to verification), and hard constraints (the sandbox as backstop). At no point does the Harness need to leave the specified band. At no point does it need trained judgment. At no point does its decision surface need to grow.^[Prop. 10.6 in the [formal companion](formal-companion.md). The regulatory convergence criteria — when specified processing can keep pace with the system's evolution — are Prop. 8.13 and Cor. 8.15.]

---

## The pragmatic objection

Many real-world agent systems use LLM-backed guardrails — an LLM evaluating whether a proposed tool call is safe, or routing messages based on inferred intent. The framework says this is wrong: trained judgment in the regulator activates the supermodular cross-term and the regulator becomes as opaque as the regulated system. But the practice is widespread. Is the framework too strict?

The answer requires a distinction the series has been building toward but hasn't yet made explicit. What the Harness does at runtime is *coordination*: routing messages, applying protocols, gating permissions, constructing scope. These are Beer's System 2 functions — anti-oscillation, protocol enforcement, coherent operation. The specified band argument holds for coordination: it must be transparent and readable.

But there's a different function — *control* — that asks whether the current approach is working, whether tools should be restricted or expanded, whether the task needs to pivot. In Beer's Viable System Model, this is System 3: operational control that dynamically monitors performance and reallocates resources. The framework as presented collapses coordination and control into the Harness. They may have different design requirements. Coordination must be specified. Control may legitimately require richer judgment, because "is this approach working?" is not always decidable by specified rules — especially at computation channel levels 4+, where the space of possible failures is too vast for enumerated rules.

The prohibition on trained judgment holds for the coordination layer — the Harness's runtime protocol. The companion essay [Coordination Is Not Control](coordination-is-not-control.md) develops the specified alternative: the failure-driven controller that monitors the failure stream, triggers mode transitions at specified thresholds, and audits for state divergence — without trained judgment in the control loop.

---

## The loop closes

Post 1 placed the Harness at the hub of the star topology because "you can describe what it will do." Post 2 measured why: the Harness has low ma — specified decision surface, characterizable actions. Posts 3 and 4 showed the structure: closures, effects, handlers. Post 5 formalized the ordering: the preorder determines who can reason about whom, and the Harness is low enough that everyone can model it. Post 6 revealed the dynamics: the grade trajectory evolves via a coupled recurrence. Post 7 showed where the trajectory can self-amplify: computation channels, phase transitions, the halting-problem shape of regulating Turing-complete specifications.

And this post resolves the tension. The Harness can stay characterizable — stay in the specified band — even as the agents it regulates grow more capable. The trick was never to match their complexity. It was to reduce theirs until specified regulation suffices, observe what escapes reduction, and constrain what escapes observation.

The Harness belongs at the hub not because it's simple. It belongs there because it's *transparent* — and transparency scales with world coupling in a way that trained judgment does not. The OS proved it. The framework explains why.

---

*Previous: [Computation Channels](07-computation-channels.md)*
*Next: [Building With Ma →](09-building-with-ma.md)*
