# Critiquing *Ma*: How We Got to Co-domain Characterizability

*The path from intuition to definition, including the wrong turns.*

---

## Where we started

The first definition of *ma* was **total actor opacity** — everything that influences an actor's output but isn't observable by other participants. This unified several concepts that had been treated separately:

- Hidden state (how much internal state is unobservable)
- Temperature (how wide the output distribution is)
- Context (how much invisible state influences output)
- Judgment (ability to decide from inaccessible information)
- Predictability (how well output follows from observable inputs)

The claim was that these are "facets of one thing" — that they move together and can be treated as a single axis.

---

## Where the critique bit

### Problem 1: *Ma*-as-opacity conflated independent things

A **lookup table** has enormous hidden state (the full table) but is perfectly deterministic. High hiddenness, zero temperature. A **random number generator** has no hidden state worth mentioning but is maximally non-deterministic. Zero context, maximum temperature. A **human expert** has both — vast hidden context AND non-deterministic output — but their judgment quality comes from the *context*, not the *non-determinism*.

"More *ma*" was conflating at least two independent things: *how much is hidden* and *how variable the output is*. The facet table wasn't describing one axis — it was averaging over two.

### Problem 2: The role-*ma* claim was too strong

"You put the low-*ma* actor at the hub because you need the hub to be predictable." But is that *why*, or is it just *what happened to work*? You could put a high-*ma* actor at the hub if you had sufficient trust mechanisms. The constraint might reflect our current trust technology rather than a fundamental architectural law.

### Problem 3: Borrowed *ma* stretched the concept too far

If a file read has *ma* because the filesystem is hidden state, then *every* computation has *ma* because every computation depends on hardware, physics, and the state of the universe. "Everything has *ma*" becomes "nothing is usefully distinguished by *ma*."

### Problem 4: A priori predictability didn't work either

The next attempt defined *ma* as "a priori predictability" — how well you can predict the output before seeing it. This broke on the same cases: a temperature-0 LLM is technically predictable (given the weights), a SHA-256 is unpredictable (given only the input), but the LLM intuitively has more *ma* than the SHA. Predictability was the wrong axis.

---

## The turn: co-domain characterizability

The breakthrough came from asking: what do we **need** *ma* to be?

Not "what will the output be" (epistemic — depends on what you know).
Not "how much is hidden" (state — doesn't predict role).
Not "how predictable is the output" (breaks on SHA vs. LLM).

But: **how well-characterized is the *set* of possible outputs?**

A SHA-256 is unpredictable, but its output space is trivially described: "uniform over 256-bit strings." A die is random, but its co-domain is `{1,2,3,4,5,6}`. A lookup table has vast hidden state, but its output space is bounded and enumerable. All low *ma*.

A temperature-0 LLM is deterministic for any given input, but its output space *across inputs* is all possible token sequences — you need the weights to describe it. A human expert might consistently give the right answer, but the *set of things they could possibly say* is vast and uncharacterizable. Both high *ma*.

***Ma* is the descriptive complexity of the output space** — how much information is needed to characterize not what the actor will output, but what it could output.

---

## Every problem case resolves

| Case | Old problem | Co-domain resolution |
|---|---|---|
| **Lookup table** | High hidden state → should be high *ma*? | Output space is enumerable → low *ma* |
| **Random die** | Maximum non-determinism → should be high *ma*? | `{1,2,3,4,5,6}` is trivially characterized → low *ma* |
| **SHA-256** | Unpredictable → should be high *ma*? | "Uniform over 256-bit strings" → low *ma* |
| **Temperature-0 LLM** | Deterministic → should be low *ma*? | Output space requires the weights to describe → high *ma* |
| **Human expert** | Predictable (often right) → should be low *ma*? | Could say anything; co-domain is unbounded → high *ma* |
| **Borrowed *ma* boundary** | Everything depends on physics → everything has *ma*? | Co-domain characterizability is relative to the *interface* → only relevant complexity counts |

The "at least two axes" problem dissolves: hidden state, variability, judgment, predictability, and identity are all **correlates** of co-domain complexity, not independent components of *ma*. They cluster in practice because rich output spaces tend to require rich internals, tend to be less predictable, tend to resist separation from the actor. But the underlying quantity is one thing.

The role claim becomes precise: you put the low-*ma* actor at the hub not because its outputs are "predictable" (vague) but because its **output space is characterizable** — other actors can reason about what the hub could do, which is what trust requires.

Borrowed *ma* gets a clean boundary: the Executor's co-domain is simple *given its interface* (`Read(path) → string`). The world behind it expands the actual outputs, but the interface constrains the *kind* of output. "Borrowed" means the co-domain complexity comes from the world, not the actor — and it's bounded by the interface typing.

---

## What the formal object is

*Ma* maps to the **entropy of the co-domain under the interface typing** — a Kolmogorov-flavored measure rather than a Shannon-flavored one:

- **Shannon entropy** measures uncertainty about *which* output you'll get from a known distribution. This is temperature.
- **Kolmogorov complexity of the co-domain description** measures how compressible the *description of the output space* is. This is *ma*.

A fair die has high Shannon entropy (uniform distribution over outcomes) but low Kolmogorov complexity of the co-domain description (six possible values). An LLM has high Shannon entropy AND high Kolmogorov complexity — you can't compress the description of what it might say without having the model.

This connects directly to the monadic framework. Each monad determines a co-domain structure:

| Monad | Co-domain | Characterizability | *Ma* |
|---|---|---|---|
| `Identity` | Just `A` | Complete | None |
| `Maybe` | `A + 1` | Complete | Minimal |
| `List` | `[A]` | Enumerable | Low |
| `Probability` | `Distribution(A)` | Describable (support + density) | Medium |
| `IO` | `World → (A, World)` | Depends on entire world | High |
| `Free F` (open algebra) | Unbounded | Irreducible | Maximal |

The monadic continuum IS a *ma* gradient: each step up makes the co-domain harder to characterize.

---

## Remaining honest caveats

### Observer-relative characterizability

A SHA's co-domain is well-characterized *if you know it's a SHA*. To an observer who doesn't know the algorithm, the output is uncharacterizable. Is *ma* a property of the actor or the observer?

Answer: *ma* is a property of the actor *relative to its interface*. The SHA's interface specifies it returns a 256-bit hash. The LLM's interface specifies it returns a string. The co-domain characterizability follows from the interface + the actor's nature. This makes *ma* structural (good) while acknowledging that it depends on the level of description (honest).

### Composition isn't additive

Composing two low-*ma* actors doesn't guarantee a low-*ma* result. A pipeline of SHA → lookup-table-keyed-on-hash could have emergent co-domain complexity. So *ma* doesn't compose additively — it depends on how the co-domains interact. This is consistent with the monadic framework (monad transformer composition can change the co-domain structure non-additively) but means *ma* isn't a simple additive metric.

### The aesthetics aren't just decoration — they're the definition

The co-domain characterizability framing is precise but incomplete. It focuses on the *output side*: how hard is the output space to describe? But the aesthetic 間 is about something more fundamental: **the space between**. The space between notes. The space between walls. The space between what goes in and what comes out.

The final refinement: ***ma* is the space between what an actor receives and what it produces.** Not just the output space — the entire space between inputs and outputs, shaped by restriction, filled by the actor's decision surface, measured by characterizability. Three things determine it: world coupling (what can enter), decision surface (what fills the space), interface restriction (what can exit).

This resolves the lingering tension between the aesthetic concept (negative space, exclusion, the gaps between things) and the formal concept (output space complexity). They're the same thing: the Harness creates the gaps (restriction), and the gaps shape the space (ma). The architecture lives in the restrictions, not in the actors. The aesthetic was pointing at the structural insight all along — we just needed the formal framework to see it clearly.

The name *ma* isn't evocative decoration on a formal concept. It IS the concept. The space between.

---

## What survives

1. **Co-domain complexity matters for architecture.** This is robust. How characterizable an actor's output space is genuinely affects where it should sit in the system topology.

2. **Role follows from *ma*.** The claim is now precise: actors with characterizable output spaces mediate; actors with uncharacterizable output spaces authorize; actors with rich-but-bounded output spaces propose. This is testable and grounded in the co-domain formalism.

3. **The shared structure (read → infer → respond) is real.** Principals and Inferencers have the same process. The difference is co-domain width, not process structure.

4. **The design vocabulary is valuable.** Asking "what's the *ma* of this component?" — meaning "how characterizable is its output space, and how does that affect the system?" — is a productive question for system design.

5. **The monadic connection is precise.** *Ma* = Kolmogorov complexity of the co-domain description under the interface typing. This maps directly to the monad hierarchy. The monadic continuum is the *ma* gradient.
