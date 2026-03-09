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

## The Object-Capability Connection

### The parallel

Mark Miller's thesis (*Robust Composition*, 2006) argues that access control and concurrency control are unified under object-capabilities. Our framework argues that scope management and co-domain management are unified under the monad-comonad duality. These may be different formalizations of the same insight.

Miller's core abstraction: a **capability** is an unforgeable reference that grants authority to perform operations. Having the reference IS having the authority. No reference, no authority. Authority is determined by the transitive closure of your capabilities.

Our core abstraction: an actor's **interface ma** is determined by the effects it can produce, which is determined by its tool set. Having the tool IS having the effect. No tool, no effect. Interface ma is determined by the monad induced by the tool set.

| Miller (ocap) | Our framework | Formal correspondence |
|---|---|---|
| Capability (reference) | Tool in tool registry | Element of `T ∈ P(Tools)` |
| Authority (what you can do) | Interface ma (effect monad) | Position in monad morphism preorder |
| Attenuation (restrict a capability) | Tool restriction / sandbox config | Move down in preorder |
| POLA (minimize authority) | Ma minimization | Navigate to lowest viable preorder position |
| Confinement (prevent leakage) | Scope boundaries | Complementary scopes (Section 3) |
| Introduction (pass a reference) | Permission grant | Scope extrusion (Section 15.4) |
| Access control | Permission gates | Session type branches (Section 15.1) |
| Concurrency control | Parallel tool execution | π-calculus encoding (Section 15.3) |
| "Only connectivity begets connectivity" | Harness as sole mediator | Star topology with Harness at hub |

### POLA is ma minimization

Miller's POLA: give each actor only the capabilities needed for its task. Minimize authority to minimize damage from bugs or malice.

Our version: give each actor only the tools needed for its task. Minimize interface ma to maximize predictability.

These are the **same principle** seen from different angles:
- **Security** framing (Miller): minimize authority → minimize *damage* if the actor misbehaves
- **Architecture** framing (ours): minimize interface ma → maximize *predictability* for other actors

The convergence: damage is minimized BECAUSE predictability is maximized. If an actor's effects are embeddable in everyone else's, then everyone can *simulate* what it might do — and therefore *verify* what it did do. Auditability follows from embeddability.

POLA doesn't just limit damage — it enables **trust through simulation**. That's the deeper reason it works.

### Permission grants as capability introduction

In ocap, "introduction" is the act of passing a capability reference from one actor to another. The recipient gains authority it didn't previously have.

In our framework, a permission `Grant` is exactly this: the Harness introduces a tool (capability) to the Inferencer's scope. The configuration moves from `(s, T)` to `(s, T ∪ {tool})` — the tool set expands, the effect monad moves up in the preorder, interface ma increases.

And permission `Deny` is the refusal to introduce — the Harness withholds the capability, keeping interface ma where it is.

The session type for the permission protocol (Section 15.1) IS the capability introduction protocol formalized as a type. Each branch (`AutoAllow`, `Ask → Grant`, `Ask → Deny`, `AutoDeny`) corresponds to a different capability transfer outcome.

### Attenuation and the configuration lattice

Miller's **attenuation**: creating a restricted version of a capability. A read-write reference can be attenuated to a read-only reference. The attenuated capability grants strictly less authority.

In our framework: the Harness configures `allowed_directories` and tool parameters, creating attenuated versions of tools. `Bash(sandboxed)` is an attenuation of `Bash(full)`. The attenuated tool's effect monad is strictly lower in the preorder: `IO_sandbox ≤ IO_filesystem`.

The configuration lattice (Section 12.8) IS the attenuation lattice. Moving from `(s₁, T₁)` to `(s₂, T₂)` where `s₂ ≤ s₁` and `T₂ ⊆ T₁` is attenuation — less scope, fewer tools, lower ma.

### Composition of authority

Ocap has a known subtlety: combining capabilities can create authority that neither alone grants. Read access to a credentials file + network access = the ability to exfiltrate credentials. Neither capability alone is dangerous; their composition is.

The same problem exists in our framework: giving an agent `{Read, Bash}` creates more effect authority than `{Read}` alone or `{Bash}` alone. The agent can read a file path, then use it in a Bash command. The composed effect monad is potentially richer than either component.

Formally: if `M₁` is the effect monad for tool set `T₁` and `M₂` for `T₂`, is the effect monad for `T₁ ∪ T₂` necessarily ≤ some simple combination of `M₁` and `M₂`? Or can composition create effects not present in either?

In ocap, this is the "confused deputy" problem — an actor with multiple capabilities can be tricked into combining them in unintended ways. In our framework, it's the question of whether the configuration lattice (product of scope lattice and tool powerset) correctly models the actual authority lattice, or whether tool combinations create emergent authority.

This is an open problem in both frameworks. The key difference: in ocap, composition is unconstrained (any actor with two capabilities can combine them). In our framework, the Harness mediates all tool use, which provides a chokepoint for detecting dangerous combinations. The star topology isn't just architectural convenience — it's a **composition control** mechanism.

### Where the analogy deepens

Miller's thesis subtitle: "Towards a Unified Approach to Access Control and Concurrency Control." His argument: both are about *who can affect what when*. Capabilities unify them because a capability is both an access token (who can affect what) and a synchronization primitive (when effects happen, via message passing).

Our framework has the same unification, in different language:
- **Access control** = permission gates = session types (Section 15.1) = which effects are authorized
- **Concurrency control** = parallel tool execution = π-calculus (Section 15.3) = when effects happen and how they compose

The monad-comonad duality (Section 12) is the formal structure underneath this unification:
- The **monad** (expansion, injection) handles "what effects happen" — access control
- The **comonad** (compression, extraction) handles "what actors see" — information flow control
- The **Harness** sits at the boundary, controlling both

Miller arrives at capabilities as the unifying primitive. We arrive at the monad morphism preorder. The question is whether these are the same primitive in different notation.

### Where the analogy might break

1. **Delegation is peer-to-peer in ocap, centralized in our framework.** In Miller's model, any actor with a capability can pass it to any other. In ours, only the Harness grants tool access. This is a design choice, not a limitation of the formalism — but it means our framework models a more constrained architecture than general ocap.

2. **Revocation.** Ocap supports capability revocation (withdraw a reference, sometimes via caretaker patterns). Our framework supports tool restriction changes at meta-level boundaries. The granularity differs: ocap can revoke mid-computation; we revoke between turns.

3. **Ambient authority.** Ocap is defined partly in opposition to ambient authority (global permissions, ACLs). Our framework doesn't model ambient authority explicitly — the Harness's configuration IS the authority model, and there's no "ambient" layer outside it. But in practice, things like the model's training data or the system prompt are a form of ambient authority not captured by the tool set.

4. **Dynamic capability creation.** In ocap, actors can create new objects (and therefore new capabilities) at runtime. In our framework, the tool set is relatively static within a session. MCP tool discovery is the closest analog to dynamic capability creation, and it happens at session setup, not mid-conversation.

### The Turing test connection, revisited

Ocap adds precision to the Turing test angle. In ocap terms: can an observer, given only the *interface* (the capability's operations), determine what *implementation* backs the capability? The answer is no — that's the point of encapsulation. The capability's interface IS the contract; the implementation is hidden.

In our terms: can an actor, observing only the *interface monad*, determine the *implementation monad*? The monad morphism `η : M_impl ~> M_iface` is surjective and lossy — many implementations map to the same interface. You cannot distinguish implementations from the interface alone.

This is why the Inferencer is a black box: its interface (token sequences) doesn't reveal its implementation (which model, which weights, which reasoning process). The interface monad (`Distribution` over tokens, or even just `FreeText`) is the same regardless of whether it's Opus, Sonnet, or a lookup table.

The Turing test is precisely the question: is the implementation monad distinguishable through the interface? The answer, by the lossy surjectivity of the interface boundary, is no.

---

## Other examples to explore

### In conversation architecture

1. **Sub-agent as co-domain compression**: Parent spawns a sub-agent. The sub-agent has a full conversation loop (high internal ma). The parent sees only the result (low interface ma). The Executor boundary is a monad morphism from Conv_s to Either Result Error. The parent can't simulate the sub-agent's internal conversation — it's a black box with a predictable interface type.

2. **Tool restriction as preorder navigation**: Give an Inferencer access to {Read, Write, Bash} vs. {Read}. The first has interface ma bounded by IO_filesystem. The second has interface ma bounded by IO_readonly. IO_readonly ≤ IO_filesystem — the restricted agent is *more predictable* (its effects can be simulated by a wider range of observers). This is why tool restriction improves reliability: it moves the agent down the preorder.

3. **Permission gates as embeddability checks**: The Harness grants or denies tool access. A Grant moves the conversation's effect monad upward in the preorder (new effects become available). A Deny keeps it where it is. The Harness is managing the *predictability budget* — each Grant makes the system less predictable by expanding the effect space.

### In other monadic structures

4. **Database transactions**: `ReadOnly ≤ ReadWrite ≤ Serializable ≤ Full`. A read-only query is embeddable in any richer transaction mode. Its effects are predictable to any observer that can do at least read-only operations.

5. **Type systems as ma management**: A function `Int → Int` has lower ma than `∀a. a → a` (parametric polymorphism). The monomorphic type's co-domain is structurally embeddable in the polymorphic one, but not vice versa. Type systems restrict co-domains to make programs more predictable.

6. **Information-theoretic channels**: A channel with capacity C bits can transmit any message encodable in C bits. A channel with capacity C' > C can embed everything the smaller channel can send. Shannon capacity gives a total order on channels; our monad morphism preorder gives a partial order on computational effects. Both measure "what can be expressed."

---

## What could go wrong

The thesis "predictability = embeddability" could fail if:

1. **The monad morphism exists but doesn't correspond to meaningful simulation.** Pathological morphisms that technically preserve monad structure but don't map effects to "equivalent" effects. This seems unlikely for the standard computational monads but isn't ruled out in general.

2. **Parametric accessibility is binary (accessible or not) when it should be graded.** In practice, you might have partial parameter knowledge — you know some of the Inferencer's behavior (its system prompt, its temperature) without knowing the weights. The current framework doesn't capture this gradation.

3. **The preorder is too coarse.** Two actors with the same interface monad (both `Either E Result`) might have very different predictability in practice — one is a lookup table, the other calls an external API. The preorder says they're at the same level, but intuitively they're not. This is the "borrowed ma" problem from Part 3: the Executor's complexity comes from the world, not the effect type.

4. **Composition doesn't preserve embeddability.** If M ≤ N and M' ≤ N', is (M composed with M') ≤ (N composed with N')? For monad transformers this should hold (lift composes), but for arbitrary composition it's not obvious. The compositional grading thread (below) suggests the right framing: composition is multiplicative on grades, and the grade lattice may not be componentwise under `⊗` — cross-terms from directed entanglement (A's choices shaping B's world) create compound effects exceeding componentwise products.

---

## Relationship to existing work

- **Moggi (1991)**: Defines the monads as "notions of computation." Lists them as separate examples (partiality, nondeterminism, side-effects, exceptions, continuations, interactive I/O). Does NOT define the monad morphism preorder or compare monads by expressiveness. Our ordering is an extension of his framework. He identifies "how different monads relate" as a goal (Section 2) but pursues the metalanguage approach (one monad at a time) instead.

- **Liang, Hudak, Jones (1995)**: Monad transformers. The `lift` operation IS a monad morphism from M to T(M), witnessing M ≤ T(M). But they don't frame this as an expressiveness ordering.

- **Zhang & Wang (2025, MCE)**: Uses the transformer stack as engineering infrastructure. Their `AgentMonad = StateT S (EitherT E IO)` with `lift` between layers IS a chain of monad morphisms, but they don't name it as such or use it for architectural reasoning. The paper focuses on composability and error handling, not on comparing effect expressiveness.

- **Miller (2006)**: *Robust Composition: Towards a Unified Approach to Access Control and Concurrency Control.* The object-capability model formalizes authority as capability possession, with POLA as the design principle. The mapping to our framework is deep: capabilities ↔ tools, authority ↔ interface ma, POLA ↔ ma minimization, capability introduction ↔ permission grants as scope extrusion. Miller unifies access control and concurrency control under capabilities; we unify scope management and co-domain management under the monad-comonad duality. These may be different formalizations of the same structure. If so, our framework inherits decades of capability-security results, and the capability-security community gets a formal connection to monadic effect theory.

- **Saltzer (1974) / Saltzer & Schroeder (1975)**: Original formulation of the principle of least privilege. "Every program and every privileged user of the system should operate using the least amount of privilege necessary to complete the job." This is our "minimize interface ma" in security language.

- **Algebraic effects (Plotkin & Power, 2003; Kammar et al., 2013)**: Effect theories with morphisms between them. The algebraic effects ordering (sub-theory inclusion) is related to our monad morphism preorder. This literature should be checked more carefully — they may have formalized the effect ordering already, in the language of algebraic theories rather than monads. The connection between algebraic effect handlers and our "co-domain funnels" (Section 13.3) is also worth exploring.

- **Dennett (1971) / Turing (1950)**: The Turing test as an indistinguishability argument. Our framework recasts this: can an N-actor, observing only the interface, determine the implementation monad? The interface boundary (Prop 13.3 / Conv 13.3a) is lossy and surjective — many implementations map to the same interface. Indistinguishability through the interface is a direct consequence of the morphism's lossy surjectivity.

---

## Thread: the star topology as composition control

The confused deputy problem in ocap: an actor holding capabilities A and B can combine them in ways neither grantor intended. Read(credentials) + Network(exfiltrate) = data breach, even though each capability was granted for legitimate reasons.

In general ocap (peer-to-peer delegation), this is hard to prevent. In our framework, the Harness mediates ALL tool use. This means:
- The Harness sees every tool call before it executes
- The Harness can check combinations (Read followed by Bash with the file contents)
- The star topology provides a natural chokepoint for composition auditing

This reframes the star topology: it's not just "the low-ma actor goes at the hub." It's "centralized mediation enables composition control." The Harness's low ma is what makes it trustworthy as a composition controller — everyone can simulate what the Harness will do with their tool requests, so the Harness's composition checks are themselves predictable.

Contrast: if you put a high-ma actor at the hub (an LLM deciding which tool combinations are safe), you've lost the ability to audit the composition controller. The composition checks become as opaque as the actor making them. This is the formal reason "Harness = low ma" isn't just about simplicity — it's about **auditable composition control**.

## Thread: the Turing test as interface indistinguishability

The monad morphism `η : M_impl ~> M_iface` is surjective and lossy. Multiple implementation monads map to the same interface monad. You cannot invert η — you cannot recover the implementation from the interface.

This is exactly the Turing test condition: given only the interface outputs, you cannot determine the implementation. But our framework makes the structure precise:

- **Distinguishable implementations**: If two implementations produce *different distributions* over interface outputs for the same inputs, an observer with enough samples can distinguish them statistically. The implementations are distinguishable *through* the interface even though η is lossy.
- **Indistinguishable implementations**: If two implementations produce the *same distribution* over interface outputs, no observer can distinguish them. They are in the same equivalence class under η.

The Turing test asks: is there an implementation (machine) in the same η-equivalence class as a human? If yes, the machine "passes." The question is about the *fiber* of η — how many implementations map to the same interface behavior?

For low-ma actors (Harness, Executors), the fiber is small — the interface almost determines the implementation (deterministic given state/inputs). For high-ma actors (Inferencer), the fiber is enormous — many different models could produce the same interface behavior.

This connects to the **parametric accessibility** condition: if you can access the parameters, you can locate the specific implementation within the fiber. If you can't, you know only the equivalence class.

## Thread: formal framework implications

If this analysis holds, Section 11 of formal-framework.md should be restructured:

1. **Def 11.2** (K-complexity) stays as motivation but is explicitly informal
2. **Def 11.4** (monad morphism preorder) becomes the formal definition, BUT with the payoff stated upfront: "the preorder formalizes **predictability through embeddability** — an actor is predictable by another when its effects can be simulated within the other's effect monad"
3. A new subsection should state the two conditions for actual predictability: structural embeddability + parametric accessibility
4. The connection to POLA / ocap should at minimum be noted in Section 17 (design principles), even if the full analysis stays in this working doc
5. The K-complexity remark should note that K-complexity measures description length (a property of the *name*) while the monad morphism preorder measures expressiveness (a property of the *effects*) — these are genuinely different things and the preorder is the one that matters for architecture

The Prop 13.3 revision (genuine morphism vs convention) also benefits: Convention 13.3a (opaque actors) maps to the Turing test — you can't formalize the implementation monad precisely BECAUSE the interface boundary is lossy and the parameters are inaccessible. The convention isn't a weakness of the formalism; it's the formalism correctly reflecting an architectural reality.

## Thread: compositional grading and the GCC examples

The product composition from the latitude analysis isn't just abstract — it shows up everywhere once you look for it.

### The GCC progression

GCC called directly by a human typing `gcc -O2 main.c`: the human is at (open, organic). GCC is at (scoped, specified) — it reads headers, libraries, and architecture within a bounded tree. The compound grade is the product: the human's organic grade multiplied with GCC's world-coupled grade.

GCC called by a Makefile: the human's degrees of freedom are now mediated through the Makefile, a fixed artifact at (sealed, specified). The Makefile *constrains* the human's latitude — they chose once, and now the build is more determined. The compound grade drops because the Makefile is acting as a Harness — it reduces the caller's grade before multiplication.

GCC called by an LLM agent that decided which flags to use: the LLM is at (sealed, trained) — no runtime world coupling, but a vast decision surface from training. Its grade multiplies with GCC's (scoped, specified). The compound grade is higher than either alone because the LLM's decision surface (training shaped which flags to pick) multiplies with GCC's world coupling (which headers and libraries exist). The cross-term activates: the LLM's decision surface *navigates* GCC's world coupling.

GCC called by an LLM agent inside a Nix build: Nix collapses GCC's world coupling from (scoped, specified) to (sealed, specified) — everything is hash-addressed, hermetic, pinned. The LLM's grade (sealed, trained) still multiplies, but it's multiplying with a much smaller factor on the world-coupling axis. The compound grade is lower than the non-Nix version. Nix is a grade-reducing functor on the world coupling axis.

Every step is a familiar engineering decision. Makefiles, Docker, Nix — these are all grade-reducing functors and every practitioner already knows this intuitively. Naming it makes it usable.

### The compositional grading formula

The grade of a compound system:

```
grade(A calls B) = grade(A) ⊗ grade(B)
```

where `⊗` is the product operation on grades. A Harness-like operation (Makefile, Nix, Docker, security profile) reduces the grade of B before the multiplication happens:

```
grade(A calls Harness(B)) = grade(A) ⊗ grade(Harness(B))
    where grade(Harness(B)) ≤ grade(B)
```

The Harness is a grade-reducing functor. It takes a high-graded computation and produces a lower-graded one. The product then multiplies with the reduced grade instead of the original. The reduction happens *independently of the caller* — Nix collapses GCC's world coupling regardless of whether A is a human, a Makefile, or an LLM.

*Ma* as a grade is a pair:

```
ma = (world_coupling, accumulated_influence)
```

And composition operates on both axes:

```
ma(A using B) = (coupling_A ⊗ coupling_B, surface_A ⊗ surface_B)
```

where `⊗` is multiplicative on each axis. The Harness reduces both: a sandbox reduces world coupling, a restricted tool set reduces world coupling, a fixed prompt template reduces the effective decision surface (it channels the LLM's vast navigational capacity through a narrow specification). A security profile reduces both — it limits which data is reachable (coupling) and which processing paths are expressible (decision surface, by constraining what the agent can decide to do).

This is a graded monad. The grade monoid is a 2D lattice with multiplicative composition — richer than natural numbers with addition, but tractable:

- Each actor contributes a grade (a point in the lattice)
- Composition multiplies grades on both axes (product, not sum)
- Harness operations reduce grades before composition (grade-reducing functors)
- The ordering on grades determines architectural role

### The grade lattice: two axes and a parameter

Part 3's informal continuum (`sealed → pinhole → window → ... → constitutive`) is a path through a richer structure, not a line. A live web search and a temperature-0 LLM are both "complex" but in incomparable ways — one is entangled with the world right now, the other was shaped by the world during training. The grade structure is a **lattice** (partial order), not a line (total order).

Two axes emerge as genuinely orthogonal, plus a parameter that modifies the grade without adding a full dimension.

**Axis 1: World coupling.** How much of the outside world is *reachable* by this computation at runtime. Not what it actually reads — what it *could* read. The pipe's diameter, not the water flowing through it.

| Level | Meaning | Design lever |
|---|---|---|
| **Sealed** | No external reads. Pure computation. | N/A — already minimal |
| **Pinhole** | Reads a single identified datum (one file, one env var, one sensor) | Access control, allowed paths |
| **Scoped** | Reads a bounded, enumerable collection (a directory, a DB with known schema) | Sandboxing, `allowed_directories` |
| **Broad** | Reads a large surface with known boundaries (a filesystem, a codebase, an API ecosystem) | Schema restrictions, API scoping |
| **Open** | Reads from an unbounded or opaque surface (the web, live feeds, the physical world) | Network policy, physical access |

**Axis 2: Decision surface.** How much the computation's processing can be *influenced by its inputs* — how much navigational capacity the function brings to bear at runtime. Not just what it sees (that's Axis 1), but how much what it sees can *steer* what it does.

| Level | Meaning | What you'd need to fully characterize it |
|---|---|---|
| **Literal** | No decision-making. Output IS the input or a trivial transform (`echo`, `identity`, constant). Inputs cannot steer the processing — there is no processing. | Nothing — it's identity-like |
| **Specified** | Decision surface is explicit and readable. A `grep` pattern, a SQL query, an `if` statement. Inputs steer the processing, but the steering mechanism is transparent — read the code, know how any input will be handled. | The source code |
| **Configured** | Decision surface is parameterized from a known, enumerable space. Compiler flags, regex options, hyperparameters. The steering mechanism is transparent given the parameter values. | The source + the parameter values |
| **Trained** | Decision surface was produced by high-dimensional optimization. Neural network weights, learned policies. Inputs steer the processing through a vast, opaque decision surface — the same input can be processed differently depending on how it interacts with the weights. | The architecture + training data + process |
| **Organic** | Decision surface was shaped by lived experience, culture, biology. Inputs steer the processing through a lifetime of accumulated structure. Whether this is bounded or unbounded is an open question (and a very old one); what matters architecturally is that it's *beyond system characterizability* — no other actor can model it. | The person |

These levels are landmarks on a *continuous* dimension, not discrete categories. The key insight: an `if` statement is a tiny decision surface — one bit of navigational capacity, one point where inputs can steer the processing. A 50-branch case statement is a larger decision surface. A hand-written expert system with 10,000 rules is larger still. A neural network is vastly larger — billions of parameters, each contributing to how inputs get processed. A human expert brings a lifetime of structure to bear on every input. It's the same *kind* of thing at every scale: **internal structure that inputs can influence at runtime**. The difference is quantitative — how much decision-making capacity is active during execution — not qualitative.

The structure was *accumulated* before runtime (by programming, by training, by living), but the *exercise* of that structure is a runtime property. This matters for agents: an LLM in a multi-turn conversation is accumulating decision surface *in real time*. Each turn adds context that shapes how it processes subsequent inputs. The conversation history becomes part of the active decision surface. In-context learning is decision surface growth happening at runtime, not just before it.

The "organic" level is not necessarily a claim about infinity. It's a claim about **characterizability relative to the system**. A human's decision surface might be finite (bounded by neurons, by physics) but it's still beyond what any other actor in the system can model. The boundary between "trained" and "organic" isn't a boundary of size — it's a boundary of *parametric accessibility*. We have the weights. We don't have the person.

**Stochasticity parameter.** Whether execution involves sampling from a distribution. This is NOT a full axis because it doesn't determine characterization difficulty — the key insight that decouples stochasticity from *ma*:

A random number generator has high stochasticity but zero characterization difficulty — its output space is trivially described ("uniform over the range"). A temperature-0 LLM has zero stochasticity but enormous characterization difficulty — its output space requires the weights to describe. **Stochasticity ≠ characterization difficulty.** This is the RNG vs temp-0 LLM test, and it's definitive.

What stochasticity *does* affect is the **verification method**:
- Deterministic: can be replayed. Same inputs → same output. Audit by re-running.
- Stochastic: can only be statistically audited. Same inputs → different output each time. Need the distribution, not a single trace.

This matters for Harness design (different strategies for deterministic vs stochastic executors) without changing the grade's position in the lattice. Temperature, K-means random initialization, sampling-based algorithms — all stochastic, all varying in degree, none fundamentally changing how hard the output space is to *describe*.

### The orthogonality test

The axes are genuinely independent. The four corners prove it:

|  | Low world coupling | High world coupling |
|---|---|---|
| **Small decision surface** | `1 + 1`. Trivial processing, touches nothing. Inputs can't steer it (no decisions) and there's nothing external to read. | `cat /dev/urandom`. Trivial processing, reads from the open world. The world provides raw data, but the function can't be *steered* by it — it just passes it through. |
| **Large decision surface** | Temp-0 LLM, no tools. Touches nothing at runtime, but brings a vast decision surface to bear on its inputs. The *same prompt* processed by different weights produces different output — the decision surface IS what matters, not the world. | Human expert doing a web search. Vast decision surface navigating vast world coupling. The expert's lifetime of accumulated structure determines what to search for, how to interpret results, when to stop. Both axes maximal. |

No corner is empty. No corner is reducible to the other axis. The axes are orthogonal.

### The grade grid

The two axes form a plane. Each cell is a single actor or computation, not a compound:

| | **Sealed** | **Pinhole** | **Scoped** | **Broad** | **Open** |
|---|---|---|---|---|---|
| **Literal** | `echo "hello"`, `identity` | `cat /etc/hostname` | `ls /src` | `SELECT * FROM t` (no WHERE) | `curl` (fixed URL, no processing) |
| **Specified** | `strlen("hello")`, SHA-256 | Config file parser | `grep -r "TODO" ./src`, test suite | Linter, static analysis tool | Web scraper with fixed logic, cron job |
| **Configured** | GCC in Nix (hermetic) | Parameterized SQL (one bind var) | Build with pinned deps in a tree | Search engine with tuned ranking | Monitoring system with configurable alerts |
| **Trained** | Temp-0 LLM, no tools | LLM reading one file | LLM with Read+Grep on a project | LLM querying a database | LLM with web search |
| **Organic** | Mental arithmetic, reciting a poem | Reading a specific document | Exploring a dataset | Reviewing a literature corpus | Browsing the web; two humans conversing |

Selected examples with both coordinates stated explicitly:

| Actor | World coupling | Decision surface | Notes |
|---|---|---|---|
| `1 + 1` | Sealed | Literal | Both axes zero. The origin. |
| `Read(file)` | Pinhole | Literal | Reads one datum, trivial transform. Inputs pass through; they can't steer the processing. |
| `gcc main.c` | Scoped (headers, libs in tree) | Specified | The compiler has a complex but fully readable decision surface. Inputs (source code, flags) steer processing through explicit, inspectable rules. |
| Deterministic web search | Open | Specified | The search algorithm is written code — its decision surface is transparent. But the world it searches is unbounded. High on one axis, low on the other. |
| K-means clustering | Scoped (dataset) | Specified (stochastic) | Specified decision surface, scoped data, but random initialization means non-deterministic execution. Stochasticity parameter, not axis movement. |
| Smart thermostat | Pinhole (sensor) | Configured–Trained | Learned schedule from usage patterns. Moderate decision surface — inputs (temperature readings) steer behavior through a learned model, not just explicit rules. |
| Temp-0 LLM, no tools | Sealed | Trained | Zero world coupling, vast decision surface. Hard to characterize despite being deterministic — the same prompt processed by different weights produces different output. The decision surface IS what makes it hard to model. |
| Temp > 0 LLM, no tools | Pinhole (entropy source) | Trained (stochastic) | Sampling adds a pinhole of world coupling (entropy) and stochasticity. The decision surface dominates the grade. |
| LLM in multi-turn conversation | Scoped (conversation history) | Trained (growing) | Decision surface *grows at runtime* — each turn adds context that changes how subsequent inputs are processed. In-context learning is decision surface accumulation in real time. |
| LLM with web search | Open | Trained | Both axes high. The web coupling passes *through* the vast decision surface — this is where the cross-term is strongest. The LLM's decision surface determines what to search for and how to interpret results. |
| Agent writing + executing a tool | Broad–Open | Trained | The agent *bootstraps world coupling through its decision surface* — its training shapes what code it writes, which determines what world the tool touches. Dynamic capability creation. |
| Two humans conversing | Open | Organic | Both axes maximal. Each turn compounds: the other person's output (open world coupling) is processed through a lifetime of accumulated decision surface (organic). |
| Human expert doing a web search | Open | Organic | The expert's decision surface *navigates* the world coupling. Same web, different search, different interpretation. |

Reading the grid:

- **Origin** (sealed, literal): fully determined. The Harness's ideal — trivially characterizable on both axes. Inputs can't steer the processing and there's nothing external to read.
- **Far corner** (open, organic): maximally graded. The Principal. Two humans conversing live here — vast decision surfaces navigating vast world coupling, compounding across turns.
- **Left column** (sealed): output depends entirely on the decision surface, not on what the function touches. A temp-0 LLM with no tools: enormous decision surface, zero world coupling. Deterministic but hard to characterize — because of the navigational capacity it brings to bear, not because of external data.
- **Bottom row** (literal/specified): the decision surface is transparent — read the code, know how any input will be handled. World coupling alone determines the grade. A web scraper with fixed logic: easy to understand the processing, hard to predict what it will encounter.
- **Diagonal**: both axes contribute, and the cross-term activates. An LLM with web search: world coupling passing through a vast decision surface. The world can *steer* the processing in ways it can't steer a specified function.
- **Agent writing tools**: the most interesting cell. The agent's decision surface (trained) creates new world coupling (the tool it writes determines what world is reachable). This is *grade escalation through specification* — the decision surface bootstraps world coupling. The Harness's job is to prevent unauthorized escalation.
- **LLM in conversation**: the decision surface level *changes over time*. In-context learning means the trained decision surface grows with each turn as conversation context accumulates. The grade isn't static — it's a trajectory through the lattice.

The grid replaces the informal continuum from Part 3. What was called "sealed" is (sealed, literal). What was loosely called "ocean" was conflating open world coupling with large decision surfaces — the two-axis structure separates them. A deterministic web search is (open, specified) — high on one axis, low on the other. A temp-0 LLM is (sealed, trained) — the opposite pattern. The old continuum couldn't distinguish these; the grid can.

### The cross-term: world coupling × decision surface

The two axes interact through composition. When an actor with a large decision surface (LLM) makes a call with high world coupling (web search), the *result* carries both — and they're not independent. The LLM's decision surface shaped which query it issued, which determined which slice of the live web it saw. The world coupling passes *through* the decision surface rather than through a fixed algorithm. This is the multiplicative cross-term, and it's where the real architectural complexity lives.

**The blue-website example.** Consider a Python script that checks 10,000 websites, picks some at random, and reports whether any of them include the color blue. High world coupling (10,000 sites), stochastic (random selection), but trivially characterizable — the output is yes/no. Now consider an LLM agent doing the same task. Same world coupling, same stochasticity (if we add sampling), same *intended* output space. But the agent has a vastly larger decision surface — its weights create navigational capacity the script doesn't have. Maybe the agent encounters a page that says "green is a kind of blue" and its decision surface causes it to reason differently about what counts as blue. Maybe it decides to explain its reasoning instead of giving yes/no. The *possibility exists* for the agent's processing to be influenced by what it sees in a way the script's processing cannot be.

The script's decision surface is **transparent** — read the code, know exactly how inputs steer the processing. The agent's decision surface is **opaque** — the same inputs could steer the processing differently depending on how the weights interact with the content. World coupling through a small decision surface (specified function, predictable steering) vs through a vast decision surface (trained function, opaque steering).

This is the cross-term in action: world coupling alone doesn't determine the compound grade. World coupling × decision surface does. The agent and the script see the same world, but the world can *steer* the agent in ways it can't steer the script. The steering capacity is precisely the decision surface — how much the function's behavior can be influenced by what flows through it.

### Compositional depth is structural, not a grade axis

A third candidate axis — compositional depth (how many layers of actor interaction produced the output) — turns out to be structural rather than a grade axis. If `grade(A calls B) = grade(A) ⊗ grade(B)`, then depth is how many terms are in the product. It's the *exponent* — how many times `⊗` gets applied — not a factor in it.

A three-step pipeline has grade `g₁ ⊗ g₂ ⊗ g₃` where each `gᵢ` has its own position in the 2D lattice. Interactive depth (multi-turn conversation) differs from sequential depth (pipeline) because each term is conditioned on previous results — the product is of *conditional* grades, not independent ones. Recursive depth (sub-agents) interposes a co-domain funnel that compresses the inner grade before it enters the outer product. These are properties of *how ⊗ works*, not properties of the grades being composed. Depth belongs in the composition algebra, not the grade lattice.

### Connection to the existing framework

This grading connects to the graded monad from formal-framework §7 and §10.3, which uses `(Scope × Budget)` as the grade monoid. The new grading tracks navigational latitude rather than resource consumption. These are *different graded monads on the same underlying conversation monad* — one tracks what you spend, the other tracks how much room you have. The Harness manages both simultaneously: it reduces the latitude grade (fewer tools, tighter scope) while consuming the resource grade (budget spent on each turn). Whether these compose into a single richer grade monoid or remain separate graded structures is an open question.

The connection to the monad morphism preorder (§11): the preorder `M ≤ N` orders monads by expressiveness. The lattice grade orders *compound systems* by navigational latitude. The preorder is a property of individual effect types. The grade is a property of compositions. The preorder determines how tool-set-induced grades compose — if `M ≤ N`, then replacing an M-tool with an N-tool moves the compound grade up in the lattice.

### Asymmetry in engineering maturity

We have mature engineering for controlling world coupling: sandboxes, containers, hermetic builds, `allowed_directories`, network access controls. We have almost nothing comparable for controlling decision surfaces. The "model evaluation" and "interpretability" industries are attempting to build it, but they're primitive compared to the sandboxing toolchain.

This asymmetry maps directly to the two axes: one is well-tooled, the other isn't. The framework explains *why* decision surfaces are harder to manage — to control them, you'd need to intervene in the internal structure of the function (its weights, its learned patterns, its accumulated experience), not just the environment it runs in. Sandboxing controls the pipe; there's no equivalent operation that controls what the function *does* with what flows through the pipe.

The closest we have: prompt engineering (constrains what the decision surface attends to), tool restriction (limits what actions the decision surface can take), and output format constraints (narrows the co-domain regardless of the decision surface). These are all *indirect* — they work by restricting the decision surface's inputs and outputs, not by changing the surface itself. The Harness manages decision surfaces from the outside, through scope and tool restriction. Whether that's sufficient, or whether we'll eventually need to manage decision surfaces from the inside (interpretability, steering vectors, fine-tuning), is an open architectural question.

## Thread: where to look next

### Cybernetics and control theory

The decision surface axis connects deeply to the cybernetics tradition:

- **Ashby, Law of Requisite Variety (1956)**: "Only variety can absorb variety." A controller's range of possible actions must match the system's range of possible disturbances. "Variety" in Ashby's sense is essentially decision surface size. Our framework's key move: the Harness doesn't match the Inferencer's variety — it *reduces* the Inferencer's interface variety (via tool restriction) so the Harness's low variety suffices. Co-domain funnels ARE variety attenuators.

- **Conant-Ashby Good Regulator Theorem (1970)**: "Every good regulator of a system must be a model of that system." This IS the embeddability claim — but with a critical precision. The Harness can *model* the Inferencer's interface behavior. It cannot *emulate* the Inferencer. The distinction is load-bearing:

  The Harness's model of the Inferencer is small: "it accepts a token window and produces structured output conforming to the tool-use protocol." That's enough to regulate. The session type from §15.1 IS this model — it describes the protocol structure (propose → gate → execute → collect) without describing the content. The Harness knows the *shape* of what will come back without knowing the *content*.

  Formally, two morphisms do different work:
  - `η_interface : M_iface_inferencer ~> M_harness` — EXISTS. The Harness can model the Inferencer's *interface* (protocol structure, output types). This is what enables regulation.
  - `η_impl : M_impl_inferencer ~> M_harness` — does NOT exist. The Harness cannot model the Inferencer's *implementation* (inference, reasoning). This is what makes the Inferencer a black box.

  The co-domain funnel (Prop 13.3 / Conv 13.3a) is the gap between these two: the interface morphism compresses the implementation into a regulable type. The Harness regulates the compressed type. The compression is lossy — the Harness can't recover the reasoning from the interface — and that's fine, because Conant-Ashby requires a model, not a replica. Regulation doesn't require emulation.

- **Beer, Viable System Model (1972)**: Extends Ashby to organizations. Identifies variety attenuators (our co-domain funnels) and variety amplifiers (our tool grants). Management (our Harness) mediates between them. The structural correspondence with our four-actor model is worth examining in detail.

- **Tishby, Information Bottleneck (1999)**: Formalizes the trade-off between compression and prediction. The Harness's scope construction IS an information bottleneck — filtering what reaches the Inferencer, keeping relevant signal, discarding noise. Too little filtering drowns the Inferencer in variety. Too much starves it of information. The "right" scope is the one that captures task-relevant information and nothing more.

The cybernetics connection is potentially the strongest external validation: Ashby's variety is our decision surface. His Law of Requisite Variety explains why the Harness works by reduction rather than matching. The Good Regulator Theorem explains why embeddability (our monad morphism preorder) is the right criterion for mediation. These aren't analogies — they may be the same theory in different notation, sixty years apart.

**Why formalize: the regulator's model.** Conant-Ashby says a good regulator must be a model of the system it regulates. The formal framework we're building in Parts 1–4 IS that model. The monad morphism preorder, the configuration lattice, the session types, the grade lattice — these are the components of the model that a Harness needs in order to regulate a multi-agent system. We're not formalizing for formalization's sake. We're building the minimum viable model that the regulator requires.

This reframes the entire series: the question isn't "can we formalize agent architecture?" It's "what model does the Harness need to be a good regulator, and can we build it?" The answer is: a model of interface types (the monad morphism preorder tells you which effects embed in which), a model of scope (the Store comonad tells you how to project the conversation), a model of authorization (the session types tell you the protocol structure), and a model of composition (the grade lattice tells you how tool grants multiply latitude). That's the minimum. Everything in the formal framework either contributes to this regulatory model or should be cut.

The practical implication: harness engineering is building regulators. The formal framework tells you what the regulator needs to know. A Harness that understands the grade lattice can make better tool-granting decisions. A Harness that understands the configuration lattice can navigate scope/tool trade-offs. A Harness that understands the interface morphism can audit actors it can't emulate. The formalism isn't downstream of the engineering — it's the specification for better engineering.

### PL theory and effects

- **Plotkin & Power (2003), Kammar et al. (2013)**: Algebraic effects. They have a notion of "sub-theory" that's like our monad morphism preorder but in algebraic language. If they've already formalized the effect ordering, we should cite them. If not, the connection is novel.
- **Abramsky (1993)**: Computational interpretations of linear logic. Linear types and capabilities share structure — both track resources that can't be duplicated. Our budget model (Section 10.3) might connect.
- **Dennis & Van Horn (1966)**: Original capability concept. Pre-dates Miller by 40 years. Worth checking if there's formal structure there.
- **Filinski (1994)**: "Representing monads." Shows any monad can be expressed via continuations + state. Relevant because it implies Cont is a kind of "universal" monad — top of the preorder in a different sense than IO. This might complicate our ordering.

## Open: is this actually a preorder on *effects* or on *actors*?

The monad morphism preorder is defined on monads. But what we care about is actors. An actor's position depends on:
- Its interface monad (structural)
- Its parameter visibility (accessibility)
- Its actual behavior (which computations it runs, not just which it *could* run)

The preorder captures the first. The interface boundary captures the second. The third is... the actor's program, which is outside the type system entirely.

Is there a richer structure that captures all three? Something like a *dependent* preorder where the ordering depends on the specific computation, not just the type?
