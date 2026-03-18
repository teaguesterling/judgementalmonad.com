# Extensions to the Ma Framework

*Five refinements to the published series, developed in conversation. Each one connects to specific posts and resolves an identified gap.*

---

## 1. World decoupling: the W axis is at least two axes

**Resolves:** The IO confession (posts 5, 6, 7) — `IO` collapses three things into one type.

**The insight.** Read coupling and write coupling are independent controls. The published series treats world coupling as a single scalar: sealed through open. But the most interesting architectural patterns live in the off-diagonal.

A debugging sandbox snapshots the codebase (broad read), seals the copy (zero persistent write), lets the agent modify freely inside the seal (full local write that rolls back), and emits a structured diagnosis (narrow output through a co-domain funnel). That's three independent values — broad inward, zero outward to the real world, structured through the funnel — not one scalar.

The framework called this "world coupling." The better word is **world decoupling** — the design move is to *separate* what was previously one channel into two. The snapshot operation decouples the moment of reading from the lifetime of writing. In normal execution they're interleaved — read, write, read what you wrote, path-dependent trajectory. The snapshot breaks that loop.

**What changes.** The grade of an actor isn't `(w, d)` where `w` is a scalar. It's `(filter, d)`, where `filter : WorldProjection → AccessMode` maps each accessible slice of the world to a specific access profile. For most practical purposes the scalar approximation holds. But the architecture that matters — the snapshot-seal-funnel, the mode taxonomy, tiered access — lives in the decomposed version.

The formal companion's Definition 4.1 should be extended. Composition becomes join on the filter: `filter(A using B)(proj) = max(filter_A(proj), filter_B(proj))` per projection. Supermodularity (Prop. 4.7) generalizes — each projection's access mode contributes independently.

---

## 2. The capability graph: four edge types between sandboxes

**Resolves:** The preorder's vague upper half (post 5) and the star topology's enforcement mechanism.

**The insight.** Every actor sits in its own sandbox — often literally in a different location, authenticated with different credentials, touching a different slice of the world. The connections between sandboxes aren't a matrix (too uniform) or a scalar (too coarse). They're a sparse graph with four edge types:

**Access** — the actor can read or write the projection. Real data flow.

**Knowledge** — the actor knows the projection exists and its interface, but can't touch it. Shapes reasoning (the agent writes a better diagnosis if it knows the output will become a GitHub issue). But has a cost: the agent may attempt to use the projection and fail. That failure is itself coupling.

**Failure visibility** — when an attempt fails, information leaks back. A silent denial versus a detailed permission error are different bandwidths of coupling through the failure channel. Even "permission denied" is information — it tells the agent the boundary exists and roughly where it is.

**Absence** — the actor doesn't know the projection exists. Zero coupling. Zero wasted decision surface. But also zero ability to shape output for downstream consumption.

The expensive state is knowledge-without-access. The agent knows a capability exists, tries to use it, fails, adjusts, tries again. Each attempt is a full inference cycle spent navigating a boundary that a specified rule could have prevented. The SELinux anti-pattern from post 8, realized at the graph level.

The star topology constrains the graph enough that it doesn't become intractable. Every edge goes through the Harness. The Harness manages the graph with specified rules — opening and closing edges, changing access modes, projecting constraints into actor scope.

---

## 3. The failure-driven ratchet: failures are fuel, not waste

**Resolves:** The System 3 gap (posts 8, 9) and the ratchet's input stream (configuration ratchet essay).

**The insight.** The published ratchet captures *successes* — patterns that work get promoted to tools. But the ratchet is actually driven by *friction*. The repeated failures are the expensive signal. They're where the system burns decision surface against boundaries that should either be opened or made invisible.

Every failed tool call is an agent spending trained reasoning to arrive at a proposal that a specified rule rejects. That's the most expensive possible way to discover a constraint — the full weight manifold produced something that a simple lookup could have prevented.

The failure-driven ratchet has two crystallization targets from the same data:

- If the agent keeps failing because it needs access, **promote the access** — open the edge, add the capability. (System 4 direction: explore.)
- If the agent keeps failing because it's trying something that should never work, **promote the constraint** — make the boundary visible or remove the knowledge. (System 3 direction: exploit.)

Either way, the expensive middle state — knowledge without access, repeated probing, wasted inference — is eliminated. The failure gets crystallized into specified infrastructure.

This is why the ratchet only turns one way: a failure that gets crystallized into either "now allowed" or "now explicitly forbidden" removes the conditions that generated friction. You can't unlearn a specification back into an expensive failure.

**The reframe for trust.** The trust gap (reachable minus expected) isn't only a risk to minimize. It's also the *learning surface*. If reachable exactly equals expected, the system never discovers anything — perfectly safe, permanently static. You need some gap. You need the agent to occasionally try things that fail. What you don't want is *uncontrolled* gap. What you want is *instrumented* gap — failures that are cheap, visible, and informative.

Three design variables: how much gap (sandbox configuration), where the gap lives (mode and projection filter), and what happens when the gap produces a failure (System 3 monitoring and crystallization).

---

## 4. The snapshot-seal-funnel pattern

**Resolves:** Computation channel regulation at level 4+ (post 7) and the info/effect decoupling (post 6, Def. 8.9).

**The insight.** A named, reusable pattern that decouples computation level from persistence level:

1. **Snapshot** — broad read coupling. Capture the relevant world state at a point in time.
2. **Seal** — zero write coupling to the real world. The copy is isolated. Effects happen inside and evaporate.
3. **Operate** — full computation channel access inside the sealed copy. No caution needed. Maximum exploratory freedom.
4. **Funnel** — structured output through a narrow interface. The only thing that crosses the boundary outward is the co-domain funnel output.

The agent operates at level 4 (writing and executing code) with level 0 persistence (nothing survives the cycle). The trajectory resets every cycle. No path dependence. The Harness only evaluates the funnel output, which has trivial interface ma.

The critical property: the agent *knows* it has an experimental copy. That knowledge — projected into its scope per the SELinux transparency principle — changes how it reasons. It doesn't need to be careful. It can be maximally invasive because consequences are zero. The sandbox gives both freedom and safety by putting them in different channels.

**Applications beyond debugging.** Trying multiple approaches (snapshot, try A, roll back, try B, compare, output the winner). What-if analysis (snapshot, make a change, trace consequences, report without committing). Adversarial testing (snapshot, try to break the system, report vulnerabilities, roll back). Each puts the broad exploratory space where consequences are zero and the narrow constrained output where consequences are real.

---

## 5. The star topology is substrate-independent

**Resolves:** The framework's scope limitation (it describes AI agent systems but claims structural generality).

**The insight.** The four actors — Principal, Inferencer, Executor, Harness — are roles defined by interface properties, not by what fills them. A human can be an Executor. A script can be a Principal. An organization can be a multi-actor system with human Inferencers, software Executors, and a mixture of specified process and human coordination as the Harness.

**A person managing their own productivity** is a multi-actor system where the same human fills different roles at different times. The planning phase is the Inferencer role — broad reasoning, many possible approaches. The execution phase is the Executor role — bounded task, clear inputs, characterized output. The challenge, particularly with ADHD, is that executive function IS the Harness function: scope construction, permission gating, state management, deciding what to work on next. When the internal Harness is unreliable, the design move is to externalize it — calendar blocks, task lists, structured routines, AI collaboration. Each is a piece of Harness infrastructure that makes the extract step (constructing the right scope at the right time) cheaper.

The placement principle applies: put the space for judgment and exploration in the planning role (where quality matters most), and minimize the space in the execution role (where starting and finishing matter most). Every decision the person has to make during an execution block is a context switch that costs disproportionately. The Harness's job is to pre-decide.

**A data business division** is a multi-actor system where:
- System 1 (operations) = the data platform, the pipelines, the governance apparatus
- System 2 (coordination) = the technical Harness plus organizational protocols
- System 3 (control) = the team captain monitoring the failure stream, adjusting configurations
- System 4 (intelligence) = bioinformaticians and researchers doing novel analysis
- System 5 (identity) = the institutional mission

The ratchet operates at this scale: every time a bespoke collaboration produces a reusable pattern, the organizational computation channel level drops. The interaction that was "researcher describes question in natural language, analyst interprets and translates" — computation channel at the delegation boundary — becomes "researcher selects a structured tool with typed parameters" — data channel, level 1. The system gets more predictable, auditable, and efficient with every promotion.

The through-line: the framework isn't about AI agents. It's about any system where actors with different capabilities and different views of the world coordinate through a mediating layer. Same structure, different substrates. The insight is in the shape, not the material.

---

## How these connect to the published series

| Extension | Resolves gap in | Suggested integration |
|---|---|---|
| World decoupling | Posts 5, 6, 7 (IO confession) | Revise Def. 4.1 in formal companion; note in post 2 |
| Capability graph | Post 5 (preorder upper half) | Section in "Coordination Is Not Control" companion |
| Failure-driven ratchet | Posts 8, 9 (System 3 gap) | Core of "Coordination Is Not Control" companion |
| Snapshot-seal-funnel | Post 7 (computation channel regulation) | Named pattern in post 7 or formal companion |
| Substrate independence | Post 9 (practical scope) | Closing section of "Building With Ma" |

Each extension was developed by applying the framework to cases it hadn't been tested against — human productivity, organizational design, B2B data platforms, debugging workflows — and noticing where the vocabulary broke. The breaks pointed at the gaps. The gaps pointed at the refinements.

---

*These extensions accompany the companion essay [Coordination Is Not Control](coordination-is-not-control.md) and the practical guide [Seeding the Ratchet](seeding-the-ratchet-b2b.md). Together, the three documents extend the published [Ma of Multi-Agent Systems](blog/00-intro.md) series with System 3, the failure-driven ratchet, and concrete tools for applying the framework beyond AI agent architecture.*
