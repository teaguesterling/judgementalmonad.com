# The Grade Lattice

*What ma is, how it composes, and why restriction is multiplicative.*

---

## The problem

Ma (間) is the space between what an actor receives and what it produces. We've said it's shaped by restriction, filled by the decision surface, measured by characterizability. But we haven't said what it IS — formally, as a mathematical object.

Previous attempts:
- **Co-domain characterizability** (K-complexity of the output space). This measures *interface* ma — how hard the output space is to describe. But it misses the interior: a lookup table and a neural network can have the same output type while having radically different path spaces.
- **The monad morphism preorder** (`M ≤ N iff ∃ η : M ~> N`). This compares ma — it tells you which actors can simulate which. But it's a comparison tool, not a measure.

Both are useful. Neither is the definition.

The definition: **ma is the computation's path space** — the space of possible ways inputs can be transformed into outputs, not the space of outputs themselves. Two actors with identical output types can have vastly different ma if one has a single execution path (a lookup table) and the other has billions (a neural network). The path space is what makes the neural network harder to reason about — not its outputs, but *how* it arrives at them.

---

## The grade lattice

Ma has two orthogonal components. They emerged from pressure-testing the original single-axis continuum against edge cases: a deterministic web search (high world coupling, small decision surface) and a temperature-0 LLM with no tools (zero world coupling, vast decision surface) are incomparable — different *kinds* of ma, not more or less.

### Axis 1: World coupling

How much external state can influence the computation at execution time. Not what it actually reads — what it *could* read. The pipe's diameter, not the water flowing through it.

Define `W` as a join-semilattice ordered by inclusion of accessible world state:

```
W_sealed ≤ W_pinhole ≤ W_scoped ≤ W_broad ≤ W_open
```

| Level | Meaning | Design lever |
|---|---|---|
| **Sealed** | No external reads. Pure computation over explicit inputs. | N/A — already minimal |
| **Pinhole** | Reads a specific, identifiable external datum. A file path, a config key, a sensor value. | Access control, allowed paths |
| **Scoped** | Reads a bounded, enumerable surface. A directory tree, a database with known schema, an API. | Sandboxing, `allowed_directories` |
| **Broad** | Reads a vast surface with known boundaries. A filesystem, a codebase, a search index. | Schema restrictions, API scoping |
| **Open** | Reads from the unbounded physical world. Human perception, embodied sensors, live feeds. | Network policy, physical access |

This axis maps to the parameterized IO family in the formal framework: `IO_null ≤ IO_sandbox ≤ IO_filesystem ≤ IO`. The Harness controls world coupling by choosing which `IO_W` each actor inhabits.

### Axis 2: Decision surface

How much of the computation's input-to-output mapping can be *steered* by its inputs at runtime. Not just what the function sees (that's Axis 1), but how many distinguishable paths through the computation an input can select.

Define `D` as a join-semilattice:

```
D_literal ≤ D_specified ≤ D_configured ≤ D_trained ≤ D_evolved
```

| Level | Meaning | Distinguishable paths |
|---|---|---|
| **Literal** | No decision-making. Output IS the input or a trivial transform. | 1 |
| **Specified** | Decision surface is explicit and readable. A `grep` pattern, a SQL query, an `if/else` chain. | Bounded by code complexity |
| **Configured** | Decision surface is parameterized from a known, enumerable space. Compiler flags, hyperparameters, feature toggles. | Bounded by parameter space |
| **Trained** | Decision surface was produced by high-dimensional optimization. Neural network weights, learned policies. | Exponential in activatable parameters |
| **Evolved** | Decision surface was shaped by lived experience, culture, biology. | Not formally bounded |

**The formal definition**: decision surface `d(A)` is the log of the number of distinguishable input-dependent execution paths through actor A's computation.

This connects to three established concepts:

1. **Ashby's variety** (1956) — log of the number of distinguishable states of a controller. Variety IS decision surface, measured in bits. Ashby's Law of Requisite Variety ("only variety can absorb variety") becomes: a controller's decision surface must match the system's world coupling. Our framework's key move: the Harness doesn't match the Inferencer's variety — it *reduces* the Inferencer's interface variety via tool restriction, so the Harness's small decision surface suffices.

2. **VC dimension** — the capacity of a function class, measuring how many distinct input-output patterns it can realize. Higher VC dimension = larger decision surface. For neural networks, VC dimension grows with the number of parameters.

3. **Number of linear regions** in piecewise-linear functions (Montufar et al., 2014). For a ReLU network, each activation can be on or off, and each combination creates a distinct linear region — a distinct execution path. The number of regions grows *exponentially* with depth and polynomially with width. This gives a concrete formula for the decision surface of the most common neural architectures.

The levels are landmarks on a continuous dimension. An `if` statement is a tiny decision surface — one bit of steering capacity. A 50-branch case statement is a larger one. An expert system with 10,000 rules is larger still. A neural network is vastly larger — billions of parameters, each contributing to how inputs steer the processing. A human brings a lifetime of structure. It's the same *kind* of thing at every scale: **internal structure that inputs can influence at runtime**. The difference is quantitative — how many distinguishable paths — not qualitative.

One important clarification: the decision surface itself does NOT grow at runtime — the weights are fixed. What grows is the *reachable* decision surface: more context means more pairwise attention interactions, which means more distinguishable execution paths through the same fixed weights. Context accumulation is world coupling growth (more data entering through the input boundary), not decision surface growth. An LLM with 1,000 tokens and 100,000 tokens has the same total decision surface but different reachable decision surfaces. The Harness controls this indirectly through context management — compaction reduces reachable decision surface by shrinking context length. See [Conversations Are Folds](conversations-are-folds.md) for the full analysis.

### The grade

The ma grade of an actor A is the pair:

```
ma(A) = (w_A, d_A) ∈ W × D
```

ordered componentwise:

```
(w₁, d₁) ≤ (w₂, d₂)  iff  w₁ ≤ w₂  and  d₁ ≤ d₂
```

This is the product lattice. It's a *partial* order — `(broad, specified)` and `(sealed, trained)` are incomparable, which is correct. A deterministic web search and a temperature-0 LLM have different *kinds* of ma, not more or less. The original single-axis continuum couldn't express this; the product lattice can.

### The orthogonality test

The axes are genuinely independent. The four corners prove it:

|  | Low world coupling | High world coupling |
|---|---|---|
| **Small decision surface** | `1 + 1`. Trivial processing, touches nothing. | `cat /dev/urandom`. Trivial processing, reads from the open world. |
| **Large decision surface** | Temp-0 LLM, no tools. Vast decision surface, touches nothing at runtime. | Human expert doing a web search. Vast decision surface navigating vast world coupling. |

No corner is empty. No corner collapses to the other axis. The axes are orthogonal.

### The grid

| | **Sealed** | **Pinhole** | **Scoped** | **Broad** | **Open** |
|---|---|---|---|---|---|
| **Literal** | `echo "hello"` | `cat /etc/hostname` | `ls /src` | `SELECT * FROM t` | `curl` (fixed URL) |
| **Specified** | SHA-256 | Config parser | `grep -r "TODO" ./src` | Linter, static analysis | Web scraper (fixed logic) |
| **Configured** | GCC in Nix | Parameterized SQL query | Build with pinned deps | Search engine (tuned ranking) | Monitoring with alerts |
| **Trained** | Temp-0 LLM, no tools | LLM reading one file | LLM with Read+Grep | LLM querying a database | LLM with web search |
| **Evolved** | Mental arithmetic | Reading a document | Exploring a dataset | Reviewing a corpus | Two humans conversing |

---

## How ma composes

When Actor A uses Tool B, the compound system's ma reflects both contributions. The intuition has been "multiplicative" — but what does that mean on a lattice?

### Composition is join

The composition of grades is the join (least upper bound) on the product lattice:

```
ma(A using B) = (w_A ∨ w_B, d_A ∨ d_B)
```

The compound system's world coupling is at least as broad as either component's. Its decision surface is at least as large as either component's.

Check against examples:

| Compound | A's grade | B's grade | Join | Correct? |
|---|---|---|---|---|
| LLM using web search | (sealed, trained) | (broad, specified) | (broad, trained) | Yes — the LLM's decision surface navigates the web's world coupling |
| Makefile using GCC | (sealed, specified) | (scoped, specified) | (scoped, specified) | Yes — Makefile adds no decision surface, GCC adds scoped coupling |
| Human using LLM | (open, evolved) | (sealed, trained) | (open, evolved) | Yes — the human subsumes the LLM on both axes |
| Script using config file | (sealed, specified) | (pinhole, literal) | (pinhole, specified) | Yes — the script's logic processes the config value |

Join is clean: well-defined on any lattice, commutative, associative, idempotent.

### Harness as grade reduction

A Harness operation `H` applied to actor `B` produces:

```
ma(H(B)) ≤ ma(B)   componentwise
```

| Harness operation | Effect on world coupling | Effect on decision surface |
|---|---|---|
| Sandboxing (`allowed_directories`) | Reduces: broad → scoped | — |
| Network lockdown | Reduces: open → sealed | — |
| Tool restriction | Reduces: fewer world-coupled tools | Indirectly reduces reachable paths |
| Fixed prompt template | — | Channels trained surface through specified template |
| Output format constraint (JSON schema) | — | Reduces distinguishable output paths |
| Nix (hermetic build) | Reduces: scoped → sealed | — |
| Security profile (both) | Reduces coupling | Reduces effective surface |

The Harness is a grade-reducing functor: it maps a high-grade computation to a lower-grade one. The compound `ma(A using H(B))` = `(w_A ∨ w_{H(B)}, d_A ∨ d_{H(B)})` is lower than `ma(A using B)` because `H(B) ≤ B` componentwise.

### But join alone doesn't capture the "multiplication"

Join says the compound (broad, trained) has the same grade regardless of whether the two components are interacting or sitting in separate rooms. That misses the architectural intuition: an LLM *navigating* web search results is harder to reason about than an LLM and a web search tool that happen to be in the same system but don't interact.

The missing piece isn't in the grade — it's in what the grade *means*.

### Characterization difficulty is supermodular

Define a characterization difficulty function `χ : W × D → ℝ` that measures how hard it is to describe the computation's behavior — to answer the question "what might this system do?"

This function has three properties:

1. **Monotone** in both arguments. More world coupling → harder to characterize. Larger decision surface → harder to characterize.

2. **Supermodular**:

```
χ(w₁ ∨ w₂, d₁ ∨ d₂) + χ(w₁ ∧ w₂, d₁ ∧ d₂) ≥ χ(w₁, d₁) + χ(w₂, d₂)
```

Supermodularity means: **the marginal value of increasing one axis is greater when the other axis is already high.**

3. **The cross-term dominates at high grades.** At low grades (sealed × specified), the axes contribute roughly independently. At high grades (broad × trained), the interaction between the axes — the decision surface *navigating* the world coupling — dominates both individual contributions.

Concretely:

- Going from (sealed, trained) to (broad, trained) — adding world coupling to a trained model — is a *larger* increase in characterization difficulty than going from (sealed, specified) to (broad, specified) — adding the same world coupling to a specified function. The trained model has more paths that the world state can steer.

- Going from (broad, specified) to (broad, trained) — adding decision surface to a world-coupled computation — is a *larger* increase than going from (sealed, specified) to (sealed, trained). The larger decision surface has more paths that the world state can activate.

- The cross-term is bounded by the *minimum* of the two axes: `amplification ≤ min(w, d)`. A specified function can't be amplified beyond its specification regardless of world coupling. A sealed tool can't amplify a trained surface regardless of the surface's capacity.

**This is what "multiplicative" means.** The composition on the grade lattice is join (additive, in lattice terms). The characterization difficulty of the resulting grade is supermodular (the axes interact superlinearly). When we said "tools multiply, not add," we were describing the supermodularity of characterization difficulty, not the grade algebra itself.

### Why restriction is the load-bearing operation

Supermodularity has a direct architectural consequence:

> **Reducing either component of an actor's grade has a larger effect on characterization difficulty when the other component is high.**

Sandboxing (reducing `w`) matters most when the caller's decision surface is large. Restricting a specified script to a sandbox is nice. Restricting a trained model to a sandbox eliminates the supermodular interaction between the model's vast decision surface and the world — which can dominate both individual contributions.

Tool restriction (reducing effective `w` or `d` through the compound) matters most when both axes are high. Removing web search from an LLM agent eliminates the (broad, trained) → (sealed, trained) transition — collapsing the world coupling axis and killing the cross-term.

This is the formal content of Fowler and OpenAI's empirical finding: harness engineering has more leverage than model improvement. The Harness operates on the *grade* (reducing world coupling and channeling the decision surface). The model operates *within* the grade. The supermodularity means grade reduction has superlinear returns — each restriction is more valuable in the presence of other high-grade components.

### Compositional depth is the exponent

A third candidate axis — how many layers of interaction produced the output — turns out to be structural rather than a grade axis. If `ma(A using B) = ma(A) ∨ ma(B)`, then a pipeline `A using B using C` has grade `ma(A) ∨ ma(B) ∨ ma(C)`. The depth is how many terms are in the join — the *exponent* of the composition — not a factor in it.

Interactive depth (multi-turn conversation) differs from sequential depth (pipeline) because each term is conditioned on previous results. The grade may shift between turns as the reachable decision surface grows (more context means more attention interactions through fixed weights) or as new tools are granted (scope extrusion). The trajectory through the grade lattice over time captures this — but it's a *sequence of grades*, not a single grade with depth as a component.

The dynamics of iterated composition depend critically on the tool set's properties — specifically, whether any tool accepts agent-generated text as executable specification. Data channels (file read, SQL query) create bounded, convergent dynamics. Turing-complete computation channels (Bash, `python -c`) create potentially self-amplifying dynamics where each step can increase the next step's computational reach. The computation level of the tool set is not a third grade axis — it's the *derivative* of the grade trajectory, characterizing how fast the grade can change between steps. See [Computation Channels](computation-channels.md).

---

## Three formal objects, one concept

Ma is the computation's path space. Three formal objects project different aspects of it:

| Object | What it captures | Where it's defined |
|---|---|---|
| **Grade** `(w, d) ∈ W × D` | The structural position — what kind of computation this is | This document |
| **Monad morphism preorder** `M ≤ N` | Embeddability — which actors can simulate which | Formal framework §11 |
| **K-complexity of co-domain** `K(desc(M(O)))` | Interface characterizability — how hard the output space is to describe | Formal framework §11.2 |

These relate through the interface boundary:

- **Grade** captures *internal* ma — the computation's path space, regardless of how the output is constrained.
- **K-complexity of co-domain** captures *interface* ma — the output space as seen through the interface typing.
- The **co-domain funnel** (formal framework §13.3) is the gap: a monad morphism from implementation to interface that compresses internal ma into constrained interface ma. An Opus model restricted to Approve/Reject has high grade (vast path space) and low interface K-complexity (two possible outputs). The funnel is the architectural mechanism; the grade/K-complexity gap is the measure of how much it compresses.
- The **monad morphism preorder** compares interface ma: `M ≤ N` means N can embed M's interface effects. It formalizes trust (who can model whom) and predictability (whose behavior is embeddable by others).

The grade is the definition. K-complexity is a projection onto the output boundary. The preorder is the comparison tool. All three are needed; none alone is ma.

---

## The Conant-Ashby connection

Conant and Ashby (1970): "Every good regulator of a system must be a model of that system."

The Harness regulates the Inferencer. What model does it need?

Not a model of the Inferencer's path space — that would require the weights (parametric inaccessibility). Not a model of the Inferencer's specific outputs — that would require running inference (computational intractability).

A model of the Inferencer's *interface*: the protocol structure (propose → gate → execute → collect), the output types (tool calls conforming to the schema), the grade bounds (world coupling limited by available tools, decision surface opaque but interface constrained). The session type from the formal framework (§15.1) IS this model.

The grade lattice tells the Harness what it's regulating: a (w, d) pair that it can reduce on the w axis (sandboxing, tool restriction) and channel on the d axis (prompt templates, output constraints). The supermodularity tells it where restriction has the most leverage: where both axes are high.

Ashby's variety is decision surface. His Law of Requisite Variety says the controller's variety must match the system's. Our framework's move: the Harness doesn't match — it *reduces*. Co-domain funnels are variety attenuators. The Harness is a grade-reducing functor that makes its own low variety sufficient by lowering the variety it needs to regulate.

This reframes the entire formalization effort: we're building the regulator's model. The grade lattice, the configuration lattice, the session types, the monad morphism preorder — these are the components of the minimum viable model that a Harness needs to be a good regulator. Conant-Ashby says this model must exist for regulation to work. We're specifying what it contains.

---

## The stochasticity parameter

Stochasticity — whether execution involves sampling from a distribution — is NOT a grade axis. The definitive test: a random number generator has high stochasticity but trivial characterization difficulty (output space = "uniform over the range"). A temperature-0 LLM has zero stochasticity but enormous characterization difficulty (output space requires the weights to describe).

**Stochasticity ≠ characterization difficulty.** This decoupling is what forced the move from the original single-axis "predictability" definition to the two-axis grade lattice.

What stochasticity affects is the *verification method*:
- **Deterministic**: can be replayed. Same inputs → same output. Audit by re-running.
- **Stochastic**: can only be statistically audited. Same inputs → different outputs. Need the distribution, not a single trace.

This matters for Harness design (different audit strategies for deterministic vs stochastic actors) without changing the grade's position in the lattice. Temperature, K-means initialization, Monte Carlo methods — all stochastic, all varying in degree, none changing how hard the computation's *path space* is to describe.

Stochasticity is a parameter on the grade, not a component of it: `ma(A) = (w_A, d_A; σ_A)` where `σ_A` modifies verification requirements without moving the grade's position.

---

## What this resolves

From the [self-critique](self-critique-formalisms.md):

**"Ma is three things wearing one name."** → Resolved. Ma is the computation's path space. Grade measures it. K-complexity projects it onto the output boundary. The preorder compares it. Three tools, one concept.

**"The grade lattice product ⊗ is undefined."** → Resolved. Composition is join on the product lattice. "Multiplicative" refers to the supermodularity of characterization difficulty, not the grade algebra. The cross-term (decision surface navigating world coupling) is a property of interpretation, not composition.

**"Decision surface has no formal definition."** → Resolved. Decision surface = log of distinguishable input-dependent execution paths. Connects to Ashby's variety, VC dimension, and number of linear regions in neural architectures.

---

## Engineering maturity asymmetry

We have mature engineering for controlling world coupling: sandboxes, containers, hermetic builds, `allowed_directories`, network access controls. The `W` axis is well-tooled.

We have almost nothing comparable for controlling decision surfaces directly. The `D` axis is not. The "model evaluation" and "interpretability" industries are building it, but they're primitive compared to the sandboxing toolchain.

The framework explains why: to control world coupling, you constrain the *environment* (what data is reachable). To control decision surface directly, you'd need to constrain the *function's internal structure* (which paths through the computation are reachable). Sandboxing controls the pipe; there's no equivalent operation that controls what the function does with what flows through the pipe.

What we have are indirect controls:
- **Prompt engineering**: constrains what the decision surface attends to (channels steering through a narrow input)
- **Tool restriction**: limits what actions the decision surface can take (reduces the effective world coupling of the compound)
- **Output format constraints**: narrows the co-domain regardless of the decision surface (reduces interface ma without touching internal ma)

These all work by restricting the decision surface's *inputs and outputs*, not the surface itself. They're Harness operations on the grade boundary — grade reduction from the outside. Whether that's sufficient, or whether we'll eventually need to manage decision surfaces from the inside (interpretability, steering vectors, fine-tuning as a regulation tool), is an open question. The grade lattice makes the question precise: we're well-tooled on `W` and under-tooled on `D`.

---

## Open questions

1. **Is characterization difficulty literally supermodular, or just "supermodular-flavored"?** The claim is that `χ(w, d)` satisfies the formal supermodularity inequality. This should be testable: measure how often a system surprises an observer as you vary world coupling and decision surface independently and jointly. If the interaction term is positive, supermodularity holds empirically.

2. **What's the right formal measure of decision surface?** "Log of distinguishable input-dependent execution paths" is well-defined for circuits and piecewise-linear networks. For general computations (Turing machines, humans), it may not be — the number of paths could be infinite or undecidable. Ashby's variety sidesteps this by measuring *distinguishable states* rather than paths. VC dimension sidesteps it by measuring *capacity of the function class* rather than the specific function. The right formalization may depend on the level of analysis.

3. **How does the grade lattice connect to the graded monad from formal-framework §7?** That section uses `(Scope × Budget)` as the grade monoid — tracking what you can see and what you spend. The new grade tracks how much room the computation has. These are different graded monads on the same underlying conversation monad. Whether they compose into a single richer grade monoid is open.

4. **Does the supermodularity have a categorical interpretation?** Supermodularity is a property of functions on lattices, not a categorical concept. Is there a categorical structure (enriched category, quantale, 2-category) where the supermodular interaction between world coupling and decision surface arises from the structure itself rather than being imposed as a separate property?

5. **How does the `(open, specified)` band interact with the grade lattice?** The OS existence proof shows that world coupling growth preserves characterizability when decision surface stays specified. Does this imply a formal partition of the grade lattice into a "regulable" band (specified decision surface) and an "opaque" band (trained/evolved)? The supermodular cross-term scales linearly with specification size in the specified band but combinatorially in the trained band — the same world coupling creates qualitatively different characterization difficulty depending on the decision surface level. See [The Specified Band](the-specified-band.md).
