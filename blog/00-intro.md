# The Ma of Multi-Agent Systems

*A design theory for the space between agents.*

---

## The short version

Every multi-agent system has four kinds of participant: the **Principal** (the human), the **Inferencer** (the model), the **Executor** (the tool), and the **Harness** (the orchestrator that connects them). Every message passes through the Harness. This is the star topology, and it works because the Harness is the only participant whose behavior you can fully describe by reading its rules.

Between what each actor receives and what it produces, there's a space — the space of ways it could get from input to output. We call this *ma* (間), borrowing the Japanese concept that the space between things is itself functional. Ma is shaped by two axes: **world coupling** (how much external state can enter) and **decision surface** (how many paths through the computation an input can take). These form a grade lattice. Composition is join. Characterization difficulty is supermodular — restricting either axis has larger returns when the other is high.

Conversations aren't growing computations. They're **folds** — sequences of stateless inference calls over managed state. The Harness threads state, constructs scope, and simulates continuity through context reconstruction. The grade evolves via a coupled recurrence, and the dynamics of that recurrence depend on what the tools can do: **data channels** (input is an address) create convergent trajectories, while **computation channels** (input is a program) create potentially self-amplifying ones.

The Harness stays characterizable by staying in the **specified band** — transparent decision surface at any scale of world coupling. The operating system is the existence proof: Linux regulates arbitrary code execution while remaining fully readable. The strategy is layered: constrain what you can't observe, observe what you can, apply specified policy to observations. Variety reduction, not variety matching.

---

## Why this exists

The industry has strong intuitions about agent architecture. Restrict the tool set. Put a deterministic orchestrator at the hub. Sandbox your executors. Martin Fowler calls it harness engineering. OpenAI built a methodology around it. LangChain demonstrated it empirically: same model, better infrastructure, 52.8% → 66.5% on SWE-bench. Zhang and Wang's MCE provides a composition algebra for multi-agent systems.

The practice works. The composition algebra works. What's missing is a *design theory* underneath both — one that explains why restriction helps, why determinism belongs at the hub specifically, and why these are the same insight.

This series proposes one. It draws on programming language theory (closures, algebraic effects, monads), cybernetics (Ashby's variety, Conant-Ashby's Good Regulator Theorem), and capability-based security (Miller's object capabilities). The formalism isn't the theory — it's the part of the theory that can be tested, and therefore the part that can be improved.

---

## The series

1. **[The Four Actors](01-the-four-actors.md)** — Who's in the room. Principal, Inferencer, Executor, Harness. The star topology. The turn cycle.

2. **[The Space Between](02-the-space-between.md)** — Ma: world coupling × decision surface. The grade lattice. Composition as join. Supermodularity. Interface vs. internal ma.

3. **[Conversations Are Closures](03-conversations-are-closures.md)** — The PL correspondence. Where it's exact (scoping, handoffs). Where it breaks (scope extrusion, effectful computation). The monadic spectrum.

4. **[Raising and Handling](04-raising-and-handling.md)** — Algebraic effects. Actors raise effects, the Harness handles them. Context reconstruction, not computation suspension. Regulation ≠ prediction.

5. **[Predictability as Embeddability](05-predictability-as-embeddability.md)** — The monad morphism preorder. Three conditions for prediction. The capability parallel. Co-domain funnels. Why formalize.

6. **[Conversations Are Folds](06-conversations-are-folds.md)** — Stateless calls over managed state. d_reachable vs d_total. The composite entity. The grade as a coupled recurrence.

7. **[Computation Channels](07-computation-channels.md)** — Data channels vs. computation channels. The nine-level taxonomy. Three phase transitions. The derivative, not a new axis. The sandbox as dynamics controller.

8. **[The Specified Band](08-the-specified-band.md)** — The OS existence proof. Layered regulation. Capability publishing. The SELinux coda. The Ashby resolution.

9. **[Building With Ma](09-building-with-ma.md)** — What this means for practice. Multi-agent design. Scaling. The design rules that fall out.

---

**[Formal Companion](formal-companion.md)** — Definitions, propositions, conjectures, and open problems. The tight version.

**[The Configuration Ratchet](the-configuration-ratchet.md)** — How systems convert trained ma into specified ma. The dynamic complement to the specified band.
