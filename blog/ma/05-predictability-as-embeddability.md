# Predictability as Embeddability

*When can one actor reason about what another might do? The answer gives the formalism its point.*

---

## Why formalize

Four posts in, a reasonable reader might ask: why the math? The intuitions are already good. Restrict the tool set. Put a deterministic orchestrator at the hub. Sandbox your executors. Practitioners know this works. Why do we need lattices and morphisms to say what experience already teaches?

Because experience tells you *what* works. It doesn't tell you *why*, and it doesn't tell you *what else* would work that you haven't tried.

The LangChain result — same model, better harness, 52.8% → 66.5% — is an existence proof that harness design matters. But which harness changes mattered most? Was it the scope construction? The tool selection? The output formatting? Experience says "all of it, probably." The grade lattice (post 2) says: the changes that reduced the supermodular cross-term between world coupling and decision surface had superlinear returns. That's a testable, prioritizable claim. It tells you where to invest next.

Post 4's regulation ≠ prediction distinction is another example. The intuition ("the Harness doesn't need to understand the model") is widespread. The formal version ("the handler pattern-matches on the effect signature, not the implementation") is precise enough to be *wrong* — and being precise enough to be wrong is the difference between an intuition and an engineering specification.

Conant and Ashby (1970) proved that every good regulator must be a model of the system it regulates. Harness engineering is building regulators. The question isn't "should we formalize?" — it's "what model does the regulator need?" The formalism is the specification for that model. Everything in this series either contributes to what the Harness needs to know or should be cut.

A necessary scope note: this framework characterizes the *space* of possible behaviors, not the *quality* of behaviors within that space. Internal ma determines how many paths exist; it does not determine which path is good. The grade tells you what kind of system you're running. It doesn't tell you whether the system is running well. That's the difference between a theory of structure and a theory of intelligence — and this is a theory of structure.

This post introduces the formal tool that makes the framework predictive rather than descriptive.

---

## The comparison problem

Post 2 gave us a vocabulary for individual actors: the grade (world coupling, decision surface). Post 4 showed how actors interact: raising effects, handling them. But neither answers a basic architectural question: when can one actor *reason about* what another might do?

The Harness can reason about the Executor — given the arguments and sandbox, you can describe the possible outputs. The Harness cannot reason about the Inferencer's specific output — given the input, you'd need the weights to predict what comes back. The Inferencer can reason about the Harness — given the proposal and the permission configuration, the Harness's response is deterministic.

These aren't just observations. They're an ordering — a systematic relationship between actors that determines who can model whom. The formal tool that captures this is the **monad morphism preorder**.

---

## The preorder

A monad morphism `η : M ~> N` is a structure-preserving map from one computational context to another. If it exists, then any M-computation can be translated into an N-computation that "does the same thing."

Concretely: if the Inferencer's effect type can be embedded in the Harness's effect type, then the Harness can simulate any computation the Inferencer can perform. The morphism IS the simulation.

The preorder: **M ≤ N** if and only if there exists a monad morphism from M to N. This means N is "at least as expressive" as M — it can represent everything M can do.^[Def. 6.2 in the [formal companion](formal-companion.md). The causal chain from configuration through grade to interface ma is Prop. 5.4.]

```
Either E ≤ State S ≤ IO
```

`Either E` (error handling) embeds in `State S` (stateful computation) — you can simulate errors using state. `State S` embeds in `IO` — you can simulate state using the real world. The morphisms compose: `Either E ≤ IO`.

For our actors:

| Actor | Interface effect type | Position in preorder |
|---|---|---|
| **Executor** | `Result \| Error` | Low — embeds in almost everything |
| **Harness** | `Extract \| Gate \| Inject \| Compact \| Yield` | Low — enumerable, embeds widely |
| **Bare Inferencer** | Text (no tool proposals) | Mid — rich output, but no world effects |
| **Agentic Inferencer** | Text + tool proposals (effects on the world) | High — can raise effects that modify the world through tools |
| **Principal** | Unbounded IO | Top — everything embeds in IO; IO embeds in nothing simpler |

The ordering for the Executor and Harness is grounded in their actual effect types — you can verify the embeddings. For the Inferencer and Principal, we model the interface boundary as if it were a morphism — a convention (Convention 6.6 in the [formal companion](formal-companion.md)) that enables uniform reasoning at the cost of treating internals as a black box. The trust/opacity flow claims below inherit this convention's assumptions.

The bare/agentic distinction matters. A bare Inferencer — no tools, sealed — is a three-actor system: Principal, Harness, Inferencer. The Principal controls all world interaction. An agentic Inferencer has tools, which means Executors, which means the Inferencer can reach the world through the Harness's mediation. That's the full four-actor system, and the regulation challenge is qualitatively different: the Harness must now manage not just what the Inferencer sees (scope) but what it can *do* (tool set). The grade shifts from (sealed, trained) to (sealed–broad, trained) — the tools grant world coupling that the model alone doesn't have.

A note on `IO` at the top: this is more of a confession than a characterization. Assigning the Principal "unbounded IO" says "can do anything" — which is true but not informative. It characterizes by declining to characterize.

And `IO` is doing too much work lower in the preorder, too. It collapses at least three things that matter for regulation: how much world can *enter* the computation (post 2's world coupling axis handles this), what the computation can *do to* the world (observe it? modify it? generate new computations that act on it?), and what shape exits as *output* (the interface restriction that funnels address). An Executor that reads a file and an Executor that executes arbitrary shell commands both "do IO," but they're qualitatively different on the second dimension — one observes, the other can reshape the world. Post 2 refined the first. The funnel pattern partially addresses the third. The second — what the computation can do to the world, from observation through modification to generation — is where the real regulatory challenge lives. A later post takes this up directly.

The consequence: the preorder is most informative in the lower half — where it confirms that the Harness belongs at the hub and the Executor is universally modelable. For actors above the Harness, the ordering reflects modeling conventions rather than proven embeddings. The framework's strongest claims (the star topology, the specified band) rest on the lower half, which is also the half where the formal grounding is tightest.^[[The Residual Framework](the-residual-framework.md) resolves both confessions — the IO under-refinement and the preorder's vague upper half — by restating the ordering as interface enumerability: how much of a role's interface supports exhaustive specified policy. The monad morphism is retained in the [formal companion](formal-companion.md) for compositionality proofs but is stronger than what the framework's practical claims require.]

**Trust flows down the preorder.** If M ≤ N, then N can simulate M — so N can reason about what M might do. An agentic Inferencer (high) can model the Harness (low). The Harness can model the Executor. Everyone can model the Executor. Nobody can model the Principal without being the Principal.

**Opacity flows up.** If M ≤ N but N ≰ M, then M cannot simulate N. The Harness cannot model the Inferencer's internal computation — bare or agentic. The Executor cannot model anyone above it. The gaps are structural, not incidental — they're determined by which effect types embed in which.

This is why the star topology (post 1) works: the Harness sits at a low point in the preorder, so every other actor can reason about what the Harness will do. If you put an agentic Inferencer at the hub — an LLM deciding which agents run, managing state, routing messages — nobody below it could model the hub's behavior. The topology falls out of the preorder.

---

## Three conditions for prediction

The monad morphism is necessary but not sufficient for actual prediction. You need three things:^[Prop. 6.7 in the [formal companion](formal-companion.md).]

**1. Structural embeddability** — the morphism η : M ~> N exists. N's effect type can represent M's effects. This is a property of the types, not the specific computation.

**2. Parametric accessibility** — the specific parameters of M are known. Which state? Which sandbox configuration? Which weights? The morphism tells you M-computations *can* be simulated in N. The parameters tell you *which* M-computation to simulate.

**3. Computational tractability** — the simulation `η ∘ f` is cheaper to run than the original computation `f`. If simulating the actor costs as much as running the actor, you haven't gained anything.

All three are needed:

| Actor | Embeddable? | Accessible? | Tractable? | Predictable? |
|---|---|---|---|---|
| **Executor** | Yes | Yes — sandbox config visible | Yes — bounded computation | **Yes** |
| **Harness** | Yes — embeds in everything | Yes — `Conv_State` in the log | Yes — enumerable actions | **Yes** |
| **Bare Inferencer** (open weights) | Yes | Yes — weights published | **No** — simulation = running the model | **No** |
| **Bare Inferencer** (closed weights) | Yes | **No** — weights proprietary | N/A | **No** |
| **Agentic Inferencer** | Yes | Partially — weights may be closed, tool config is visible | **No** — simulation = running model + tools | **No** |
| **Principal** | Top of preorder | **No** — mind inaccessible | **No** — unbounded | **No** |

The open-weights bare Inferencer is the critical case for understanding the three conditions. It has conditions 1 and 2 — the effect type embeds, and the weights are published. But condition 3 fails: simulating what the model will produce for a given input requires... running the model. The simulation costs as much as the original. That's not prediction; it's replication.

The agentic Inferencer is the critical case for regulation. It's *harder* than the bare case because the model's proposals can trigger real-world effects through tools. The Harness can't predict which tool calls will be proposed (condition 3 still fails), but it can handle whatever arrives (post 4). The tool set determines which effects are *possible* — and that's what the Harness regulates. Granting `{Read}` creates a different regulatory challenge than granting `{Read, Write, Bash}`, even with the same model behind the proposals.

This is the formal content of post 4's regulation ≠ prediction distinction. The Harness doesn't predict the Inferencer because prediction is intractable (condition 3 fails). It *regulates* by handling at the interface — which only requires knowing the effect signature (condition 1), not the parameters or the simulation cost.

One more case deserves attention: the Principal. The preorder places it at the top — unbounded IO, evolved decision surface. But "unbounded" doesn't mean "unconstrained." The Principal has a finite attention span, limited domain knowledge, fatigue, competing demands on their time, organizational constraints on what they can authorize. These constraints are as real as the sandbox constraints on an Executor — but they're opaque to the agent. A Principal who stops responding may be thinking deeply, may have been interrupted, or may have lost interest. The Inferencer has no way to distinguish these.

This opacity is the mirror of the framework's central insight. The agent's internal processing is opaque to the Harness; the Principal's constraints are opaque to the agent. The framework develops the first opacity extensively — that's what the grade, preorder, and specified band are about. The second opacity is equally real and follows the same transparency principle (post 8): error messages with reasons, explicit time constraints, stated preferences, and declared expertise are all projections of the Principal's constraints into the agent's scope. Scope construction matters upward as much as downward.

A note on the preorder and configuration: the preorder ranks *configured* actors, not abstract actor categories. The same human with sudo access sits higher than the same human on a restricted account. The same Inferencer with Bash sits higher than the same Inferencer with only Read. The grade is always a property of actor-plus-configuration, not the actor alone.

---

## The capability parallel

The preorder has a striking parallel to a different formal tradition.

Mark Miller's *Robust Composition* (2006) argues that access control and concurrency control are unified under **object capabilities**. A capability is an unforgeable reference that grants authority. Having the reference IS having the authority. No reference, no authority.

Our framework argues that scope management and interface management are unified under the monad-comonad duality. A tool in the tool registry grants the ability to raise effects. Having the tool IS having the effect. No tool, no effect.

| Object capabilities (Miller) | Our framework |
|---|---|
| Capability (reference) | Tool in tool registry |
| Authority (what you can do) | Interface ma (effects you can raise) |
| Attenuation (restrict a capability) | Tool restriction / sandbox config |
| Principle of Least Authority | Ma minimization |
| Composition control | Star topology — all capability grants through the Harness |

Miller's **Principle of Least Authority** (POLA): grant each component only the capabilities it needs. Our framework says: minimize each actor's interface ma — grant only the tools needed, scope only the world needed. POLA IS ma minimization, expressed in different vocabulary.

The parallel isn't just structural — it validates a design principle. Decades of security research have converged on capability-based architectures for exactly the reason our framework predicts: the hub must be the entity that controls capability grants, and capability restriction has superlinear returns when the components are complex. The ocap community arrived at this through security analysis. We arrived through characterizability analysis. Same architecture, different paths.

Where the parallel breaks: capability delegation is peer-to-peer in Miller's model (any actor with a capability can pass it), but centralized in ours (only the Harness grants tools). This is a design choice that reflects the star topology — and it's the more conservative choice. The framework explains why: peer-to-peer delegation means actors can increase each other's grade without the Harness's knowledge, which breaks the supermodularity argument. Centralized delegation keeps grade management in the hands of the entity best positioned to reason about it.

---

## Co-domain funnels as design principle

Post 2 introduced the interface/internal ma distinction and noted the pattern: high internal ma compressed to low interface ma. With the preorder, this becomes a design principle.

A **co-domain funnel** is an actor whose internal effect type is rich but whose interface effect type is constrained. The actor has its own internal handler (post 4) that compresses its effects before the outer handler sees them.

| Funnel | Internal ma | Interface ma | What the compression buys |
|---|---|---|---|
| Reviewer (Opus + `{Approve, Reject, RequestChanges}`) | Trained — deep reasoning over code/logs | Three possible outputs | Everyone can model the reviewer's interface |
| Explorer (reads broadly, reports findings) | Trained — navigates entire codebase | Structured summary | The planner receives a characterized view |
| Sub-agent boundary | Full conversation loop | Summarized result | The outer conversation sees a bounded contribution |
| The Executor itself | IO within sandbox | `Result \| Error` | The Harness handles a simple type |

In preorder terms: the funnel creates an actor whose interface effect type is *lower* in the preorder than its internal effect type. The reviewer's internal computation is at the Inferencer's level in the preorder (high — trained, opaque). Its interface is at the Executor's level (low — three values, trivially embeddable). The funnel IS the gap between internal and interface position.

This gives a design rule: **when you need high-quality decisions at a boundary, use a funnel — not a simple actor.** A specified function at the boundary gives you low interface ma but also low internal ma (shallow reasoning). A large model at the boundary gives you high internal ma but also high interface ma (hard to reason about from outside). A funnel gives you both: deep reasoning compressed through a narrow interface.

The Harness itself is the ultimate funnel. It sees everything (broad internal scope), processes through specified rules (characterizable decision surface), and presents a finite action type at its interface. High internal ma on the world-coupling axis, low interface ma on both axes.

---

## The causal chain

The framework now has enough structure to trace how design decisions propagate:

**Configuration** (what the Harness chooses) → **Grade** (structural position) → **Interface ma** (what other actors experience)

The Harness configures each actor by choosing:
- Which tools to provide (determines which effects can be raised)
- Which world to grant access to (determines world coupling)
- What output constraints to impose (determines interface restriction)

These choices determine the actor's grade in the lattice (post 2). The grade, filtered through the interface boundary (post 4), determines the actor's interface ma — which determines where it sits in the preorder and therefore who can reason about it.

This is the chain that makes the framework actionable. A harness engineer isn't just "configuring an agent." They're navigating a path through the configuration space, where each choice moves the actor's grade in the lattice, which moves its interface position in the preorder, which changes what every other actor can infer about it. The formalism makes this chain explicit and navigable.

---

## Design principles

The preorder, combined with the grade lattice and supermodularity, yields concrete principles:

**Restrict tools, not models.** An Opus model with `{Read, Approve, Reject}` has high internal ma (good reasoning) and low interface ma (three possible effects). A Haiku model with 50 tools has low internal ma and high interface ma. The first is the better reviewer — and the preorder explains why: its interface effect type is lower in the ordering, so more actors can model it.

**Funnels beat flat architectures.** A flat architecture where every agent has the same tools puts every agent at the same point in the preorder. A funnel architecture creates agents at different levels — some with restricted interfaces that others can reason about, some with rich internals that do the hard work. The preorder gives you the vocabulary to design the levels intentionally.

**Grade reduction compounds.** Post 2's supermodularity means reducing an actor's grade has larger effects when the other axis is high. The preorder adds: reducing an actor's interface effect type makes it modelable by more actors. These compound — a well-restricted actor is both easier to characterize (grade) and easier to reason about from outside (preorder position).

**The Harness's job is grade management.** Every configuration choice the Harness makes is a grade operation. Tool grants raise the grade. Sandbox restrictions lower it. Scope construction determines what world coupling the actor experiences. The formalism doesn't tell the Harness which choices to make — it tells the Harness what each choice costs and what it buys, in terms that are precise enough to be wrong.

---

## What the formalism is for

Return to Conant-Ashby: every good regulator must be a model of the system it regulates.

The grade lattice models what kind of computation each actor is. The preorder models who can reason about whom. The handler structure (post 4) models how effects flow through the system. The interface/internal distinction models what's visible at each boundary.

Together, these are the components of the minimum viable model that a Harness needs to be a good regulator. Not a complete model — you can't completely model a system that includes trained models and human principals. A *sufficient* model: enough structure to make configuration decisions, enough vocabulary to describe trade-offs, enough formalism to make predictions that can be tested and found wrong.

That last part is the point. An intuition that "restriction helps" can't be wrong — it's too vague. A claim that "restriction has superlinear returns due to supermodularity of characterization difficulty on the product lattice" can be wrong. It can be tested against specific systems with specific configurations and specific performance measurements. If it holds, it tells you where to invest. If it fails, it tells you where the model breaks.

The formalism isn't the theory. It's the part of the theory that can be tested, and therefore the part that can be improved.

But everything so far describes a static picture — actors with fixed grades, a preorder that doesn't change, configurations that hold still long enough to reason about. Real conversations aren't static. Each turn changes the world for the next turn. Tool results enter the log, widening what future inferences can see. The Inferencer's response reshapes the context that the Harness will extract from next. The grade isn't a fixed point — it's a trajectory, and the trajectory is a coupled recurrence: each actor's output feeds the next actor's input, and the composite system's reachable space evolves with every step.

An actor with a vast decision surface that can change its own world through its actions, operating iteratively in a loop — that's not just hard to reason about. It's a system whose grade can grow over time, where each step potentially amplifies the next step's reach. The static tools we've built (grade, preorder, handler structure) are necessary but not sufficient. The next question is how conversations evolve.

---

*Previous: [Raising and Handling](04-raising-and-handling.md)*
*Next: [Conversations Are Folds →](06-conversations-are-folds.md)*
