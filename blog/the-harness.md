# The Harness

*How the fourth actor got its name — and why the industry already agreed.*

---

## The naming problem

Every multi-agent conversation has four kinds of participants. Three have obvious names: the **Principal** (directs), the **Inferencer** (proposes), the **Executor** (computes). The fourth — the entity that connects them all, constructs the Inferencer's scope, gates permissions, manages state, and constitutes the conversation as a thing that exists — resisted naming.

We tried: Mediator (undersells it — a mediator passes messages, this actor constructs realities). Orchestrator (implies coordination of equals — this actor is privileged). Kernel (too OS-loaded). Runtime (misses the agency). Conductor (overclaims artistic interpretation). Steward (too passive). Clerk (right power structure, wrong connotation). System (accurate — it's the `system` API role — but ambiguous with "the system" meaning everything).

None captured the key property: **this actor connects capability to direction**.

---

## The metaphor

A harness doesn't do the work — the horse does. A harness doesn't decide where to go — the driver does. But without the harness, the horse's power isn't connected to anything. The harness is what turns capability into directed action.

- The **Principal** is the driver — direction, judgment, authority
- The **Inferencer** is the horse — power, inference, *ma*
- The **Executors** are the implements — plow, cart, mill
- The **Harness** connects them — translates the driver's intent into the horse's motion into the implement's work

The *ma* signature is exactly right. A harness is fully characterizable — straps and buckles, no inference, no judgment. Low co-domain complexity. But it's the most structurally consequential piece. A poorly fitted harness wastes the horse's power. A well-fitted one multiplies it. The Harness is powerful *because* its output space is characterizable, not despite it.

---

## The industry already agreed

When we searched for prior art, we found [harness engineering](https://martinfowler.com/articles/exploring-gen-ai/harness-engineering.html) — an emerging discipline that Martin Fowler defines as "the tooling and practices we can use to keep AI agents in check." OpenAI built [an engineering methodology](https://openai.com/index/harness-engineering/) around it. The consensus headline: ["The agent harness is the architecture, and your model is not the bottleneck."](https://dev.to/epappas/the-agent-harness-is-the-architecture-and-your-model-is-not-the-bottleneck-3bjd)

LangChain demonstrated this empirically: their coding agent jumped from 52.8% to 66.5% on Terminal Bench 2.0 by changing *only the harness, not the model*. Same horse, better harness, dramatically better results.

The industry frames harness engineering as a practice. We frame the Harness as a **formal actor** — a participant in the conversation with a specific *ma* signature (minimal co-domain complexity) that explains *why* it works at the hub. These aren't competing: the practice says "build a good harness," the theory says "a good harness is one whose output space is characterizable, so other actors can reason about what it will do."

### What the *ma* framework adds

| Question | Harness engineering (practice) | *Ma* framework (theory) |
|---|---|---|
| What is the harness? | Infrastructure and tooling | A formal actor with minimal *ma* |
| Why does the harness matter? | "It helped" (empirical) | Low co-domain complexity makes mediation trustworthy |
| What makes a good harness? | Best practices, iteration | Characterizable output space — other actors can reason about it |
| Why the harness at the hub? | Convention | *Ma* determines role — the most characterizable actor mediates |
| Why not an LLM orchestrator? | "It's less reliable" | High *ma* at the hub makes the system uncharacterizable |

The LangChain result — better harness, same model, better outcomes — is exactly what the *ma* framework predicts. The lowest-*ma* actor is the most structurally consequential. Improving the characterizable component has more impact than improving the inference component, because the Harness determines *what's possible* while the Inferencer works within what the Harness constructs.

---

## The four actors

| Actor | Role | *Ma* | API role |
|---|---|---|---|
| **Principal** | Authorize, direct | Constitutive — co-domain requires the person to describe | `user` |
| **Inferencer** | Propose, infer | Intrinsic — co-domain requires the model to describe | `assistant` |
| **Executor** | Execute, compute | Borrowed — co-domain complexity comes from the world | `tool` |
| **Harness** | Connect, construct, manage | Minimal — co-domain is characterizable by rules | `system` |

The full treatment — formal definitions, the co-domain gradient, compositions, and the shared read → infer → respond structure — is in [Actor Taxonomy](actor-taxonomy.md).

---

*For how we arrived at co-domain characterizability as the definition of *ma*, including the wrong turns: [Critiquing *Ma*](ma-critique.md).*
