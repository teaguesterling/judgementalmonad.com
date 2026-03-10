# The Space Between

*How do you characterize the space of ways an actor could get from input to output? Name it, measure it, and the architecture falls out.*

---

## What *ma* is

Every actor in a multi-agent conversation receives inputs and produces outputs. Between them is a space — the space where processing happens, where decisions are made, where inputs become outputs.

In Japanese aesthetics, 間 (*ma*) is the concept that the space between things is itself functional. The pause that gives the notes shape. The empty room that makes the architecture. *Ma* isn't absence — it's the structural element that makes everything around it work.

Agent architectures have *ma*. Every scoping decision creates two things: what an agent can see, and what it can't. The planner doesn't see the worker's line-by-line analysis — and that's *why* it can think clearly about strategy. The exclusions aren't limitations. They're the negative space that makes each agent's scope useful.

But *ma* goes deeper than scoping. It's a property of the actors themselves.

***Ma* is the space between what an actor receives and what it produces.** A file-read tool: no space. The input (a path) determines the output (a string). A deterministic orchestrator: a thin space — given its rules and state, you can enumerate what it will do. A language model: vast space — billions of pathways between input and output. A human: the space is a lifetime.

Three things shape it:

- **World coupling** — what can enter the space at runtime (the input boundary)
- **Decision surface** — what fills the space (the internal structure that inputs can influence)
- **Interface restriction** — what can exit the space (the output boundary, shaped by tools and constraints)

---

## What *ma* is not

This distinction is the crux. Getting it wrong leads to the wrong formalization.

**Not unpredictability.** A SHA-256 hash is unpredictable — you can't guess which hash you'll get — but the space between input and output is trivially characterized: "a uniform mapping over 256-bit strings." Low *ma*. The mapping is rigid; there's no room between input and output.

**Not hidden state.** A lookup table with a billion entries has vast internal state, but its *ma* is minimal. The input selects an entry; the output is determined. One path per input, regardless of how much data is stored.

**Not variability.** A random die is maximally non-deterministic — six equally likely outcomes — but its *ma* is trivial. The "space between" rolling and landing is... nothing. There's no processing, no decision, no paths to take.

**Not stochasticity.** A temperature-0 LLM is technically deterministic for any given input. But the space between its input and output is vast — different inputs activate different paths through the weights, and for a deep network, the number of distinguishable paths grows exponentially with depth. High *ma*. A random number generator has maximal stochasticity but trivial characterization difficulty. Stochasticity affects how you *verify* (replay vs. statistical audit), not how hard the space is to *describe*.

*Ma* is the space of paths between input and output — how many distinguishable routes through the computation an input could take. The more paths, the harder to characterize, the higher the *ma*.

---

## One axis isn't enough

At first glance, *ma* looks like a single continuum: low (Executor) to high (Principal). But edge cases break it.

A deterministic web search: high world coupling (reads from the entire internet), small decision surface (follows a fixed algorithm). A temperature-0 LLM with no tools: zero world coupling (reads nothing at runtime), vast decision surface (billions of steerable pathways). These aren't more or less *ma* — they're different *kinds* of *ma*. The single axis can't express this.

The fix: two orthogonal axes.

---

## Axis 1: World coupling

How much external state can influence the computation at execution time. Not what it actually reads — what it *could* read. The pipe's diameter, not the water flowing through it.

```
sealed ≤ pinhole ≤ scoped ≤ broad ≤ open
```

| Level | Meaning | Example |
|---|---|---|
| **Sealed** | No external reads. Pure computation over explicit inputs. | `echo "hello"` |
| **Pinhole** | Reads a specific, identifiable external datum. | `cat /etc/hostname` |
| **Scoped** | Reads a bounded, enumerable surface. | `grep -r "TODO" ./src` |
| **Broad** | Reads a vast surface with known boundaries. | Full filesystem, codebase |
| **Open** | Reads from the unbounded physical world. | Human perception, live feeds |

The Harness controls world coupling by choosing which world each actor inhabits. `allowed_directories` moves an Executor from broad to scoped. Network lockdown moves it from open to sealed. The same Bash tool in different sandboxes has different world coupling — the actor didn't change, the world it inhabits did.

---

## Axis 2: Decision surface

How many distinguishable paths through the computation an input can select. Not what the function sees (that's Axis 1), but how many different *routes* through the processing an input could take.

```
literal ≤ specified ≤ configured ≤ trained ≤ evolved
```

| Level | Meaning | Distinguishable paths |
|---|---|---|
| **Literal** | No decisions. Output IS the input or a trivial transform. | 1 |
| **Specified** | Decision surface is explicit and readable. `grep`, SQL, `if/else`. | Bounded by code complexity |
| **Configured** | Parameterized from a known, enumerable space. Compiler flags, hyperparameters. | Bounded by parameter space |
| **Trained** | Produced by high-dimensional optimization. Neural network weights. | Exponential in activatable parameters |
| **Evolved** | Shaped by lived experience, culture, biology. | Not formally bounded |

The formal definition: decision surface is the log of the number of distinguishable input-dependent execution paths. This connects to three established concepts:

- **Ashby's variety** (1956) — log of distinguishable controller states. Variety IS decision surface, measured in bits.
- **VC dimension** — capacity of a function class. Higher VC dimension = larger decision surface.
- **Linear regions** in piecewise-linear networks (Montufar et al., 2014). For ReLU networks, the number of distinct execution paths grows exponentially with depth.

The levels are landmarks on a continuous dimension. An `if` statement is one bit of steering capacity. A 50-branch case statement is larger. An expert system with 10,000 rules is larger still. A neural network is vastly larger. A human brings a lifetime. Same kind of thing at every scale — internal structure that inputs can influence at runtime.

---

## The grade

The *ma* grade of an actor A is the pair:

```
ma(A) = (w, d) ∈ W × D
```

ordered componentwise: `(w₁, d₁) ≤ (w₂, d₂)` iff `w₁ ≤ w₂` and `d₁ ≤ d₂`. This is the product lattice — a partial order. `(broad, specified)` and `(sealed, trained)` are incomparable, which is correct. Different kinds of *ma*, not more or less.

### The four actors, placed

| Actor | Grade | Why |
|---|---|---|
| **Executor** | (sealed–broad, literal–specified) | Its own logic is simple; its world coupling is whatever the Harness grants |
| **Harness** | (scoped, specified) | Broad view, but all decisions follow readable rules |
| **Inferencer** | (sealed, trained) | No world coupling of its own; vast decision surface from weights |
| **Principal** | (open, evolved) | Full world access; lifetime of steerable structure |

The ordering from post 1 — Executor < Harness < Inferencer < Principal — was the co-domain gradient, a single axis. The grade lattice reveals it's actually a *partial* order. The Harness (scoped, specified) and the Inferencer (sealed, trained) are incomparable — different axes, different kinds of *ma*. What makes the Harness belong at the hub isn't that it has "less *ma*" in total — it's that its *ma* is *characterizable*: specified decision surface, readable rules, enumerable actions.

### The orthogonality test

The four corners are all populated:

|  | Low world coupling | High world coupling |
|---|---|---|
| **Small decision surface** | `1 + 1` — trivial processing, touches nothing | `cat /dev/urandom` — trivial processing, reads the open world |
| **Large decision surface** | Temp-0 LLM, no tools — vast paths, touches nothing | Human doing a web search — vast paths navigating vast world |

No corner collapses. The axes are genuinely independent.

---

## How *ma* composes

When Actor A uses Tool B, the compound system's grade reflects both contributions. The composition is the join (least upper bound) on the product lattice:

```
ma(A using B) = (w_A ∨ w_B, d_A ∨ d_B)
```

The compound's world coupling is at least as broad as either component's. Its decision surface is at least as large as either component's.

| Compound | A's grade | B's grade | Join |
|---|---|---|---|
| LLM using web search | (sealed, trained) | (broad, specified) | (broad, trained) |
| Makefile using GCC | (sealed, specified) | (scoped, specified) | (scoped, specified) |
| Human using LLM | (open, evolved) | (sealed, trained) | (open, evolved) |

Join is clean: well-defined on any lattice, commutative, associative, idempotent.

### But join alone doesn't capture "multiplication"

Join says (broad, trained) has the same grade whether the components interact or sit in separate rooms. That misses the intuition: an LLM *navigating* web results is harder to reason about than an LLM and a web search that don't interact.

The missing piece isn't in the grade algebra — it's in what the grade *costs to characterize*.

### Characterization difficulty is supermodular

Define a characterization difficulty function `χ : W × D → ℝ` — how hard is it to describe what the system might do? Under an independence model, `χ(w, d) = I(w) · log P(d)` — the product of distinguishable inputs and log distinguishable paths.^[The [formal companion](formal-companion.md) proves this as Prop. 4.7.]

This function is **supermodular**: the marginal effect of increasing one axis is greater when the other is already high.

- Adding world coupling to a trained model (sealed→broad, trained) is a *larger* increase in difficulty than adding the same coupling to a specified function (sealed→broad, specified). The trained model has more paths that world state can steer.

- Adding decision surface to a world-coupled computation (broad, specified→trained) is a *larger* increase than adding the same surface to a sealed computation (sealed, specified→trained). More world state to navigate means more paths that actually activate.

This is what "multiplicative" means. The grade algebra is join (additive). The characterization difficulty of the resulting grade is supermodular (the axes interact superlinearly). When we say "tools multiply, not add," we're describing the supermodularity of characterization difficulty, not the composition operation.

### Restriction is the load-bearing operation

Supermodularity has a direct consequence:

> **Reducing either axis has a larger effect when the other axis is high.**

Sandboxing a specified script is nice. Sandboxing a trained model eliminates the supermodular interaction between vast decision surface and broad world coupling — which can dominate both individual contributions. Tool restriction matters most when both axes are high.

This is the formal content of the LangChain finding: same model, better harness, 52.8% → 66.5%. The harness didn't give the agent a better model — it reduced the grade. Better scope construction (world coupling down). Better tool selection (effective world coupling down). The supermodularity means grade reduction has superlinear returns.

---

## Interface *ma* vs. internal *ma*

Here's the distinction that makes the framework architecturally useful.

*Ma* is measured at the **interface** — the output space as seen by other actors. What happens inside is the actor's own business.

A reviewer backed by Opus that analyzes thousands of lines of code with deep chain-of-thought reasoning: enormous internal *ma*. But its interface is `Approve | Reject | RequestChanges` — three possible outputs. Low interface *ma*. The restriction isn't on the model — it's on the tools.

This means:

| Configuration | Internal *ma* | Interface *ma* | Design implication |
|---|---|---|---|
| Small model, many tools | Low | High | Risky — wide output space, shallow reasoning |
| Large model, restricted tools | High | Low | Good funnel — deep reasoning, characterizable output |
| Deterministic rules, narrow output | Low | Low | Reliable — predictable everything |
| Large model, unrestricted | High | High | Hardest to reason about |

**Internal *ma* determines quality** — how good the actor's decisions are within its constrained output space. **Interface *ma* determines auditability** — how well other actors can reason about what it might produce.

A good co-domain funnel has high internal *ma* and low interface *ma*. The reviewer (deep analysis → Approve/Reject/RequestChanges), the explorer (broad codebase reading → structured findings), the sub-agent boundary (full conversation loop → summarized result) — all instances of the same pattern. Rich processing compressed to a characterizable interface. Formally, the funnel is a lossy, surjective monad morphism from implementation to interface.^[Def. 4.11 and Prop. 4.12 in the [formal companion](formal-companion.md).]

---

## What the grade captures

The grade measures the *internal* structure of an actor's computation — how much world can enter and how many paths inputs can take. The interface/internal distinction from the previous section adds the second half: the *interface* projection — how hard the output space is to describe from the outside.

These are the two things you need to reason about any actor in a multi-agent system. The grade tells you what kind of computation it is. The interface tells you what kind of neighbor it is. A good co-domain funnel creates a large gap between the two — rich internal processing compressed through a narrow interface.

Later posts will develop formal tools for comparing actors (when can one actor reason about what another might do?) and for tracking how the grade changes over a conversation's lifetime. For now: the grade lattice gives us a structural vocabulary for the space between inputs and outputs. That vocabulary already makes predictions.

---

## The cybernetics connection

Conant and Ashby (1970): "Every good regulator of a system must be a model of that system."

The Harness regulates the Inferencer. What model does it need?

Not a model of the Inferencer's path space — that would require the weights. Not a model of the Inferencer's specific outputs — that would require running inference. A model of the Inferencer's *interface*: the protocol structure (propose → gate → execute → collect), the output types, the grade bounds.

Ashby's variety is decision surface. His Law of Requisite Variety says a controller's variety must match the system's. The framework's move: the Harness doesn't match — it *reduces*. Tool restriction and sandboxing lower the Inferencer's effective grade until the Harness's small decision surface suffices to regulate it. Co-domain funnels are variety attenuators.

This reframes the entire effort. The grade lattice and the interface/internal distinction are the first components of the minimum viable model that a Harness needs to be a good regulator. Conant-Ashby says this model must exist for regulation to work. Later posts will add the remaining components — how to compare actors, how to track conversations over time, what guarantees the Harness can provide.

---

## What the framework predicts

The grade lattice and supermodularity together make testable claims:

**Restriction has more leverage than model improvement.** The Harness operates on the grade (reducing world coupling, channeling decision surface). The model operates *within* the grade. Supermodularity means grade reduction has superlinear returns. Before upgrading the model, ask whether the current model is bottlenecked by its capability (internal *ma*) or by what it's given to work with (the Harness's extraction).

**Restrict tools, not models.** An Opus model with `{Read, Approve, Reject}` has high internal *ma* (good reasoning) and low interface *ma* (characterizable output). A Haiku model with 50 tools has low internal *ma* and high interface *ma*. The first is a better reviewer.

**The same model with different tools is a different system.** Changing the tool set changes the compound grade. An LLM with web search is `(broad, trained)`. The same LLM with only file read is `(scoped, trained)`. The supermodular cross-term means this isn't a small change — it's a qualitative shift in characterization difficulty.

**We're well-tooled on world coupling, under-tooled on decision surface.** Sandboxes, containers, `allowed_directories`, network lockdown — mature engineering for the `W` axis. For the `D` axis: prompt engineering, output format constraints, tool restriction — all indirect, all working from the outside. The grade lattice makes this asymmetry precise and identifies the gap.

---

The grade lattice names and measures the space between inputs and outputs. The next post shows that this space has a surprising structural correspondence to something programming languages figured out decades ago.

---

*Previous: [The Four Actors](01-the-four-actors.md)*
*Next: [Conversations Are Closures →](03-conversations-are-closures.md)*
