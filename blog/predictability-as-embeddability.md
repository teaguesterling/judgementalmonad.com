# Predictability as Embeddability

*Working notes — developing the central payoff of the monad morphism preorder for ma.*

---

## The claim

The monad morphism preorder on computational effects (`M ≤ N iff ∃ η : M ~> N`) formalizes a notion of **predictability**: an actor operating in N can *simulate* an actor operating in M. The morphism is the simulation.

This is the thesis underlying "ma determines role." It's not that low-ma actors are *simple* — it's that they are *embeddable*, and embeddability is what makes mediation trustworthy.

---

## What the morphism gives you

If `η : M ~> N` exists, then for any M-computation `f : A → M(B)`:

    η ∘ f : A → N(B)

is an N-computation that "does the same thing." The monad morphism laws ensure this simulation preserves sequential composition:

    η(f >>= g) = η(f) >>= (η ∘ g)

So simulating (f then g) equals (simulate f) then (simulate g). The simulation is *compositional* — you don't lose structural information by embedding.

### What this means architecturally

If every actor in the system has effects ≥ M, then every actor can simulate M-actors. An M-actor's behavior can be modeled by all participants. This is the property you want from a hub: **everyone can reason about what the Harness will do.**

The asymmetry matters:
- The Harness (`State Conv_State`) can be simulated by the Inferencer (which has richer effects). The Inferencer can "model" the Harness.
- The Inferencer (`Distribution` over token sequences) CANNOT be simulated by the Harness. `Distribution` doesn't embed in `State`. The Harness must treat inference as a **black box**.

**Trust flows down the preorder. Opacity flows up.**

---

## The two conditions for predictability

Simulation (the monad morphism) is necessary but not sufficient for *actual* predictability. You also need access to the parameters:

1. **Structural embeddability**: `η : M ~> N` exists — N's effect type is rich enough to represent M's effects
2. **Parametric accessibility**: the specific parameters of M are known — which state, which world, which weights

Both are needed:

| Actor | Structural embeddability | Parametric accessibility | Predictable? |
|---|---|---|---|
| Harness (`State Conv_State`) | Embeds in everything | `Conv_State` visible via log | Yes — by everyone |
| Executor (`IO_sandbox`) | Embeds in `IO_full` | Sandbox config visible | Yes — by actors with ≥ IO_sandbox |
| Inferencer (`Distribution`) | Embeds in `IO` | Weights NOT accessible | No — black box |
| Principal (`IO`/cognition) | Top of preorder | Mind NOT accessible | No — constitutively opaque |

The Inferencer is structurally embeddable (you *could* simulate inference if you had the weights) but parametrically opaque (you don't have the weights). This is the formal content of "high internal ma": the implementation parameters are hidden behind the interface.

### Connection to interface ma vs internal ma

- **Structural embeddability** is about the **interface monad** — what effect type does the actor present?
- **Parametric accessibility** is about the **interface boundary** — are the monad's parameters visible externally?

Interface ma (Section 13) captures both: the interface monad determines structural embeddability, and the interface boundary (Prop 13.3 / Conv 13.3a) determines what parameters leak through.

An actor with low interface ma is one where:
- The interface monad is low in the preorder (structurally embeddable by many), AND
- The parameters visible at the interface are sufficient to reconstruct behavior (parametrically accessible)

---

## The parameterization matters

The preorder is not just `State ≤ IO` abstractly. It's `State S ≤ IO_W` for specific S and W, and the relationship between S and W is where the content lives.

- `State Bool ≤ State (Bool × Int)` — simpler state embeds in richer state
- `IO_sandbox ≤ IO_filesystem ≤ IO` — smaller world embeds in larger world
- `Either E ≤ StateT S (Either E)` — error handling embeds in error handling + state (this is the `lift` in transformer stacks)

**The Harness controls the parameterization** (Section 12.8, configuration lattice). When the Harness configures `allowed_directories` or restricts the tool set, it's choosing which `IO_W` the Executor inhabits — moving the Executor's position in the parameterized preorder. The Harness is a **preorder navigator**: it places actors at specific positions by choosing their effect parameters.

---

## Co-domain format and the diagonalization observation

An important consequence: this ordering is NOT just about output *format*. Consider two tools:

- Tool A returns structured JSON: `{"status": "ok", "value": 42}`
- Tool B returns free text: `"The status is ok and the value is 42"`

The free text co-domain *contains* the JSON co-domain — any JSON string is a valid free text string. There exists an embedding `JSON ~> FreeText` (the inclusion). But there is no embedding `FreeText ~> JSON` that preserves the structure — arbitrary prose doesn't parse as JSON.

So `JSON ≤ FreeText` in the co-domain preorder. A JSON-returning tool is more predictable (its output space is structurally embeddable in any text-processing context), while a free-text tool is less predictable (its output space is richer, can't be embedded back into structured formats without loss).

This generalizes: for any structured format S and a "universal" format U that contains S, `S ≤ U`. The structured format is more predictable because it's embeddable. The universal format has higher ma because it can express things the structured format can't.

The diagonal flavor: suppose you could enumerate all possible structured outputs. Free text can always produce something *not* in that enumeration (it can talk *about* the enumeration, or produce malformed/adversarial content, or shift to a different language). The free-text co-domain is "larger" in a way that resists enumeration — it's not just bigger, it's *a different kind of bigger*. Whether this is literally a diagonalization argument or merely analogous to one is an open question, but the structural parallel is suggestive: the richer co-domain can always "escape" any attempt to fully characterize it from within the poorer one.

---

## The Turing test angle

There may be a deep connection to indistinguishability arguments.

The classic Turing test asks: can an observer, communicating only through a text interface, distinguish a human from a machine? The observer has access only to the *interface* — the channel outputs. The implementation is hidden.

Reframe this in our language: can an N-actor, observing only the interface outputs, determine whether it's communicating with an M-actor (where M ≤ N) or another N-actor simulating M?

If `η : M ~> N` exists and the N-actor has access to the parameters, it can run the simulation internally and compare. **The monad morphism is the distinguisher** — or rather, it's what makes the simulation possible, and the comparison between actual output and simulated output is what reveals (or fails to reveal) the difference.

For predictable actors (low ma, parameters accessible): the simulation matches. The N-actor can predict the M-actor's behavior and verify it. This is why you can *audit* the Harness — you can simulate its state transitions and check that it's doing what it should.

For unpredictable actors (high ma, parameters hidden): no simulation is possible. The N-actor can't distinguish between the actual Inferencer and any number of alternative Inferencers that would produce different outputs from the same inputs. This is the Turing test condition: **the interface hides the implementation precisely when the implementation monad is too rich to embed in the observer's monad, or the parameters are inaccessible.**

The Principal is the limit case: no other actor can simulate a human. Not because the effect type can't be embedded (IO embeds in... well, IO is the top), but because parametric accessibility is zero — you'd need to be the person.

### Implications for agent architecture

If predictability = embeddability + accessibility, then:

- **Auditing** is possible exactly when the auditor's effects are ≥ the auditee's AND the auditee's parameters are accessible. An Opus model auditing a Harness: yes (Distribution ≥ State, and Conv_State is in the log). An Opus model auditing another Opus model: structurally yes (same effect type), but parametrically no (different weights, inaccessible).

- **Deterministic replay** is possible exactly when embeddability holds and ALL parameters are captured. This is why conversation logs enable replay of the Harness's decisions but not the Inferencer's — the log captures Conv_State but not the model weights.

- **The interface boundary IS the predictability boundary.** Convention 13.3a (opaque actors) isn't a limitation of our framework — it's a reflection of a real architectural fact. You can't formalize the implementation monad of an actor whose parameters you can't access. The modeling convention is the honest response to parametric inaccessibility.

---

## Examples to explore

### In conversation architecture

1. **Sub-agent as co-domain compression**: Parent spawns a sub-agent. The sub-agent has a full conversation loop (high internal ma). The parent sees only the result (low interface ma). The Executor boundary is a monad morphism from Conv_s to Either Result Error. The parent can't simulate the sub-agent's internal conversation — it's a black box with a predictable interface type.

2. **Tool restriction as preorder navigation**: Give an Inferencer access to {Read, Write, Bash} vs. {Read}. The first has interface ma bounded by IO_filesystem. The second has interface ma bounded by IO_readonly. IO_readonly ≤ IO_filesystem — the restricted agent is *more predictable* (its effects can be simulated by a wider range of observers). This is why tool restriction improves reliability: it moves the agent down the preorder.

3. **Permission gates as embeddability checks**: The Harness grants or denies tool access. A Grant moves the conversation's effect monad upward in the preorder (new effects become available). A Deny keeps it where it is. The Harness is managing the *predictability budget* — each Grant makes the system less predictable by expanding the effect space.

### In other monadic structures

4. **Database transactions**: `ReadOnly ≤ ReadWrite ≤ Serializable ≤ Full`. A read-only query is embeddable in any richer transaction mode. Its effects are predictable to any observer that can do at least read-only operations.

5. **Type systems as ma management**: A function `Int → Int` has lower ma than `∀a. a → a` (parametric polymorphism). The monomorphic type's co-domain is structurally embeddable in the polymorphic one, but not vice versa. Type systems restrict co-domains to make programs more predictable.

6. **Capability systems**: Object-capability security (ocap) is exactly preorder navigation. Each capability token grants access to specific effects. Holding fewer capabilities = lower position in the preorder = more predictable behavior = easier to audit. The ocap principle "principle of least authority" is "place actors as low in the preorder as possible."

7. **Information-theoretic channels**: A channel with capacity C bits can transmit any message encodable in C bits. A channel with capacity C' > C can embed everything the smaller channel can send. Shannon capacity gives a total order on channels; our monad morphism preorder gives a partial order on computational effects. Both measure "what can be expressed."

---

## What could go wrong

The thesis "predictability = embeddability" could fail if:

1. **The monad morphism exists but doesn't correspond to meaningful simulation.** Pathological morphisms that technically preserve monad structure but don't map effects to "equivalent" effects. This seems unlikely for the standard computational monads but isn't ruled out in general.

2. **Parametric accessibility is binary (accessible or not) when it should be graded.** In practice, you might have partial parameter knowledge — you know some of the Inferencer's behavior (its system prompt, its temperature) without knowing the weights. The current framework doesn't capture this gradation.

3. **The preorder is too coarse.** Two actors with the same interface monad (both `Either E Result`) might have very different predictability in practice — one is a lookup table, the other calls an external API. The preorder says they're at the same level, but intuitively they're not. This is the "borrowed ma" problem from Part 3: the Executor's complexity comes from the world, not the effect type.

4. **Composition doesn't preserve embeddability.** If M ≤ N and M' ≤ N', is (M composed with M') ≤ (N composed with N')? For monad transformers this should hold (lift composes), but for arbitrary composition it's not obvious.

---

## Relationship to existing work

- **Moggi (1991)**: Defines the monads as "notions of computation." Lists them as separate examples. Does NOT define the monad morphism preorder or compare monads by expressiveness. Our ordering is an extension of his framework.

- **Liang, Hudak, Jones (1995)**: Monad transformers. The `lift` operation IS a monad morphism from M to T(M), witnessing M ≤ T(M). But they don't frame this as an expressiveness ordering.

- **Zhang & Wang (2025, MCE)**: Uses the transformer stack as engineering infrastructure. Their Figure 1 (IO → EitherT E IO → StateT S (EitherT E IO)) IS a chain of monad morphisms via lift, but they don't name it as such or use it for architectural reasoning.

- **Object-capability security**: The connection to ocap/POLA is, as far as we know, new. If it holds up, it would connect our framework to a well-studied area of security research.

- **Algebraic effects (Plotkin & Power, Kammar et al.)**: Effect theories with morphisms between them. The algebraic effects ordering (sub-theory inclusion) is related to our monad morphism preorder. This literature should be checked more carefully — they may have formalized the ordering already, just in different language.

---

## Open: is this actually a preorder on *effects* or on *actors*?

The monad morphism preorder is defined on monads. But what we care about is actors. An actor's position depends on:
- Its interface monad (structural)
- Its parameter visibility (accessibility)
- Its actual behavior (which computations it runs, not just which it *could* run)

The preorder captures the first. The interface boundary captures the second. The third is... the actor's program, which is outside the type system entirely.

Is there a richer structure that captures all three? Something like a *dependent* preorder where the ordering depends on the specific computation, not just the type?
