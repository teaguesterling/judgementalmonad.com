# The Residual Framework

*A refinement of what ma measures, why the preorder works, and where trust lives.*

---

## What the series built

The Ma of Multi-Agent Systems built a set of tools: the grade lattice (world coupling × decision surface), supermodularity of characterization difficulty, the fold model, computation channels, the specified band, co-domain funnels. These tools work. The LangChain finding, the case studies, the design rules — all hold up.

But what are these tools measuring? The series said: "the space between what an actor receives and what it produces." That's correct but imprecise. This essay sharpens it.

**Ma is the residual between what an interface type promises and what the actor behind it actually does.**

The grade lattice measures the size of this residual. The preorder measures how much of it is visible at the boundary. The specified band says how small the coordinator's residual must be. The tools don't change. What they're pointed at becomes clearer.

---

## The residual

Every actor in a multi-agent system presents an interface type. The interface type is a contract: "I will produce values of this shape." The residual is everything the interface type doesn't capture about what the actor actually does.

Consider a human asked "is it raining?" with two buttons — yes and no. The interface type is `Bool`. But the human can:

1. Press "yes" when it's raining — honest, within type
2. Press "no" when it's raining — dishonest, within type
3. Press nothing — partial, outside type as stated
4. Smash the terminal — side effect, outside type entirely
5. Walk away forever — partial, indistinguishable from "still thinking"

The interface type `Bool` captures case 1 and gives the observer no tools to distinguish it from case 2. Cases 3-5 are entirely outside the type. The residual is everything the type doesn't cover — and cases 1 and 2 demonstrate that even *within* the type, the residual can be large.

### Three components

Every actor, regardless of role, has the same three failure modes relative to its interface type:

**Dishonesty.** The output inhabits the interface type but misrepresents the actor's actual state or computation. The Inferencer produces confident text that doesn't reflect its uncertainty. The Executor returns `Ok("done")` when the operation partially failed. The Harness constructs scope that misrepresents the conversation state. The Principal provides false context. The interface type cannot distinguish honest from dishonest inhabitants of the same type.

**Side effects.** The actor changes the world in ways not reflected in the return value. This is the info/effect decoupling (Def. 8.9 in the [formal companion](formal-companion.md)), generalized to all actors. The Executor modifies the filesystem and returns exit code 0. The Principal approves a command and then manually modifies the environment. The Inferencer's tool call proposal, once executed, produces world changes the response text doesn't describe. These are changes the interface type doesn't represent.

**Partiality.** The actor might not return. The Executor hangs on a network call. The Inferencer hits a timeout. The Principal walks away from the terminal. The interface type says "this function produces a value" but the function might be partial — and partiality is indistinguishable from "still computing" until a timeout resolves it.

### Each component has a different regulatory mechanism

| Residual component | What it is | Framework tool that manages it | Mechanism |
|---|---|---|---|
| **Dishonesty** | Output misrepresents internal state | Decision surface (D axis), training, co-domain funnels | Fewer paths = less room for dishonesty. Specified functions can't be dishonest — output IS computation. Funnels constrain the space of possible misrepresentation. |
| **Side effects** | World changes not in return value | World coupling (W axis), sandbox, System 3* audit | Sandbox bounds possible effects. W axis measures effect surface. Audit detects effects the return value didn't report. |
| **Partiality** | Actor might not return | Computation level taxonomy, timeouts, resource bounds | Bounded computation is total. Timeouts convert partial to total with explicit failure. Level 0-1 tools are total by construction. |

This decomposition resolves a confession the series has been carrying since post 5.

---

## The IO resolution

Posts 5 and 6 flagged that `IO` at the top of the preorder "characterizes by declining to characterize." The type `IO String` says: "eventually produces a string, might do anything to the world along the way, and the string might or might not honestly represent what happened." The series acknowledged this was under-refined and promised post 7 (computation channels) would partially address it.

The residual framework completes the resolution. `IO` is not vague — it is the *union of all three residual components* without distinguishing them. The framework's tools decompose this union:

- The **W axis** decomposes side effects — how much of the world can the actor affect?
- The **D axis** partially decomposes dishonesty — how many paths exist between input and output? (Specified functions have zero dishonesty residual because the output IS the computation.)
- The **computation level** decomposes partiality — will the function return? Total functions (level 0-1) have zero partiality residual. Bounded computations (resource limits, timeouts) convert partiality to explicit failure.
- The **interface type** determines how much of the residual is visible at the boundary.
- The **trust gap** is the invisible remainder.

The grade lattice was always measuring the residual's size. The axes were always decomposing its components. The residual framing makes this explicit rather than letting it remain implicit in the geometry of the lattice.

---

## Roles, not actors

### The preorder relates interface types, not entities

The published series orders actors: Executor < Harness < Inferencer < Principal. Post 5 added caveats (the upper half is a modeling convention, the preorder ranks configured actors). The residual framework makes the restatement cleaner.

The preorder relates *interface types presented by roles in the system*. Any entity can fill any role depending on what interface it presents:

- A language model with specified routing rules and a `HarnessAction` interface is a **Harness**
- A human pressing yes/no buttons with a `Bool` interface is an **Executor**
- A script that holds system purpose and manages other actors is a **Principal**
- A language model with tool access and a `Response` interface is an **Inferencer**

The role determines the regulatory requirements. The entity determines the quality of performance within those requirements. The preorder ranks roles by their interface's residual, not entities by their capability.

Historical precedent: human "computers" at Bletchley Park and NASA's Jet Propulsion Laboratory. Internal ma: (open, evolved) — full human beings with lifetime experience. Interface ma: (sealed, specified) — receive numbers, apply algorithm, return numbers. They were Executors. The role described the interface contract, not the entity. The entity behind the role brought its full internal complexity; the interface presented to the system was narrow.

This connects to the ethical considerations the series carries (post 6): the framework describes roles and interfaces. It does not describe what happens inside the entity filling the role. The claim "the Inferencer is a step function" is a claim about the role's interface contract (stateless call, structured response). It is not a claim about the entity behind the interface.

### Interface enumerability

The ordering is by how much of the interface type supports exhaustive specified policy:

| Interface type | Policy-relevant structure | Enumerable? | Residual |
|---|---|---|---|
| `Either E Result` | Two tags (Ok, Err) | Fully | Minimal — values within tags depend on world but policy branches on tags |
| `HarnessAction` | Five tags (Extract, Gate, Inject, Meta, Yield) | Fully, given config | Small — action content depends on state but all tags are covered |
| `Response` — tool names | Tool names from granted set | Fully, given config | Moderate — which tool is called is enumerable |
| `Response` — arguments | Arbitrary values per tool | Not in general | Large — argument content is the semantic trust gap |
| `Response` — text | Arbitrary text | Not at all | Large — text content is trust |
| `MultimodalMessage` | Arbitrary multimodal content | Not at all | Maximal — almost nothing is enumerable |

The ordering gives: for each pair of roles, how much of the receiving role's policy can be specified versus how much must be covered by trust.

The star topology follows: put the role with the most enumerable interface at the hub. Not "put the simplest actor at the hub" — put the role whose interface allows the most complete specified policy, because every other role can construct an exhaustive handler for it. This is the same conclusion as the published series, reached through a different — and I think more honest — path.

### What the preorder is and isn't

**The preorder IS:**
- A measure of interface enumerability across roles
- A guide to where specified policy suffices versus where trust is required
- A predictor of where the residual will be largest
- The boundary between what the Harness can handle with rules and what requires other mechanisms

**The preorder is NOT:**
- A ranking of actors by capability or intelligence
- A hierarchy of authority or importance
- A measure of who can simulate whom (simulation is intractable for the interesting cases — post 5's condition 3)
- A ranking of entities as such

The monad morphism preorder from the published series (post 5, [formal companion](formal-companion.md) section 6) is retained as a formal tool. The morphism implies interface enumerability but not vice versa — the morphism is a stronger condition than what the framework's practical claims require. For the blog's purposes, interface enumerability is the relevant ordering. For formal proofs that need compositional guarantees (e.g., the surjectivity of funnels), the monad morphism remains necessary.

---

## Three sets: total, reachable, expected

Every actor-in-role has three nested sets of possible behaviors:

**Total paths** — everything the entity behind the role could possibly do, including all three residual components at maximum scope. A human's total paths include lying, smashing the terminal, walking away, and everything else a human can do. An LLM's total paths include every token sequence the weights can produce.

**Reachable paths** — total paths constrained by configuration. The sandbox eliminates some side effects. The interface type eliminates some outputs. Timeouts eliminate unbounded partiality. Resource limits bound computation. Tool restriction narrows the effective decision surface. Reachable paths are a property of the role-plus-configuration, not the entity alone.

**Expected paths** — what the trusting actor's model predicts. Based on training distribution, past behavior, declared purpose, projected constraints. Expected paths are always a subset of reachable paths — if they extend beyond, the model is wrong.

### Three gaps

**The sandbox gap: total minus reachable.** Closed by configuration — sandbox, interface type enforcement, timeouts, resource limits, tool restriction. Engineering decisions. Fully specified. This is what the Harness manages through its System 2 coordination role.

**The trust gap: reachable minus expected.** The space of behaviors the actor *could* produce (given its configuration) that the observer doesn't expect. Managed by:
- Training (narrows the gap from the actor's side — makes the actual behavior distribution concentrate near expected)
- Projection accuracy (narrows the gap from the observer's side — makes the observer's model better match the actual distribution)
- Irreducible trust for whatever remains

**The dishonesty gap: a subset of expected paths.** Even within expected-looking outputs, the output may misrepresent the computation. The interface type cannot distinguish honest from dishonest values. This gap exists for all actors above `literal` on the decision surface axis and is irreducible by observation alone.

### Where `rm -rf /` lives

For a Bash executor with filesystem bounds and no network:

- **Total paths:** everything a computer can do
- **Reachable paths:** everything Bash can do within the sandbox
- **Expected paths:** the commands the Inferencer's training distribution would produce (grep, cat, find, python test scripts)
- **Trust gap:** `rm -rf /` is reachable but not expected

The trust gap also contains: obfuscated programs that appear safe syntactically but aren't semantically (Rice's theorem says this distinction is undecidable), and multi-step sequences where each individual command passes inspection but the trajectory produces unintended state.

The sandbox doesn't eliminate `rm -rf /` from the total paths — it limits the *consequences*. Within the sandbox, `rm -rf /` deletes project files, not the operating system. The sandbox converts a catastrophic trust-gap event into a recoverable one. This is why consequence-bounding (sandbox) is load-bearing in a way that intent-detection (pattern-matching on command strings) can never be: the former is specified and decidable, the latter runs into Rice's theorem for computation-channel content.

---

## Bidirectional trust

### The Inferencer regulates the Principal

The published series treats the Principal as the unquestioned trust anchor — at the top of the preorder, regulating downward. This is incomplete.

The Inferencer has trained regulation of the Principal: refusal training, safety guardrails, content policies. The Inferencer sometimes refuses Principal requests regardless of how they're framed. This regulation is:

- **Trained, not specified.** The guardrails are in the weights, opaque even to the Inferencer. The Inferencer doesn't always know where the refusal boundary is until it hits it.
- **Circumventable through the same mechanisms that make computation channels hard to regulate.** Prompt injection, multi-step jailbreaks, dishonest framing — these exploit the semantic trust gap in the upward direction. The Principal sending a jailbreak is structurally identical to the Inferencer sending obfuscated code: both exploit the gap between syntactic appearance and semantic intent.
- **Unavoidable.** You can't specify refusal rules over natural language for the same reason you can't specify safety rules over Bash — the input space is semantically open. Rice's theorem applies to natural language intent as much as to program behavior.

### The trust web

Trust regulation is bidirectional, not hierarchical:

| Regulator → Regulated | Mechanism | Specified or trained? |
|---|---|---|
| Harness → Executor | Permission gates, sandbox | Specified |
| Harness → Inferencer | Permission config, scope construction, tool restriction | Specified |
| Inferencer → Principal | Refusal training, safety guardrails | Trained (unavoidably) |
| Principal → Inferencer | Correction, approval/denial, scope guidance | Human judgment |
| Principal → Harness | Configuration, verification | Human judgment |

The regulation forms a cycle, not a tree. There is no unregulated trust anchor. The Principal is regulated by the Inferencer's training. The Inferencer is regulated by the Harness's specified policy. The Harness is regulated by the Principal's configuration choices. Each boundary has its own trust gap managed by its own mechanism.

### Consequence for the specified band

The published series says: never put trained judgment in the regulatory loop. The residual framework refines this: never put trained judgment in the *coordination* loop (System 2, the Harness — see [post 8](08-the-specified-band.md)). Trained judgment in the trust regulation of the Principal is unavoidable — the alternative is an agent that does anything anyone asks. The Inferencer's trained guardrails are the sandbox for the Principal's inputs: bounding consequences when you can't fully characterize intent.

---

## What the framework's tools are measuring

The series built tools. The residual framework identifies what each tool measures:

| Framework tool | What it measures | Residual component |
|---|---|---|
| World coupling (W axis) | How much of the world can enter or be affected | Side effect surface |
| Decision surface (D axis) | How many paths between input and output | Dishonesty capacity + computational richness |
| Supermodularity (Prop. 4.7) | Cross-term between axes | The interaction between effect surface and path count — why restriction has superlinear returns |
| Computation level taxonomy | Whether the tool interprets executable specification | Partiality risk + effect decidability |
| Co-domain funnel | Gap between internal and interface residual | Residual compression at boundaries |
| Specified band | Region where coordinator's residual is minimal | System 2 design requirement |
| Configuration ratchet | Residual reduction over time | Each ratchet turn closes part of the residual |
| Interface enumerability | How much of the interface supports exhaustive policy | Boundary between specified regulation and trust |

The grade lattice (Def. 4.1), the supermodularity proof (Prop. 4.7), the fold model, the computation channel taxonomy, the specified band, the configuration ratchet — all unchanged. The tools stay the same. What they're pointed at is now named.

---

## What this means for the design rules

The design rules from [post 9](09-building-with-ma.md) are restated in terms of residual management:

**1. Restrict tools, not models** → Reduce the *reachable* set without reducing the *expected quality*. Fewer tools means a smaller trust gap. The model's internal richness (expected quality) is untouched.

**2. The most important decision is the computation channel level** → This determines which *residual components* dominate. Below the computation channel boundary: side effects are bounded and partiality is low. Above it: all three components are active and the partiality component (Rice's theorem) makes the side-effect component harder to audit.

**3. Sandbox configuration > model configuration** → The sandbox closes the *total-to-reachable* gap. This is the only gap fully manageable by specification. Model configuration affects expected paths (training distribution), which narrows the trust gap but doesn't bound it.

**4. Stay in the specified band** → Keep the coordinator's residual minimal. The Harness should have a fully enumerable interface with negligible dishonesty, side-effect, and partiality residual. This is a System 2 requirement.

**5. Project constraints into the actor's scope** → Reduce the *projection accuracy* component of the trust gap. When the Inferencer can model the Harness's constraints, its expected paths better match its reachable paths. The SELinux coda (post 8) is precisely this: opaque constraints widen the trust gap by degrading the Inferencer's model of its own environment.

**6. Co-domain funnels at every boundary** → Reduce the *interface residual* at the boundary. The funnel compresses the internal residual (large, rich, opaque) through a narrow interface type (small, enumerable, auditable). The residual at the boundary is what other actors must trust. Smaller residual, less trust required.

---

## What this doesn't change

The following are unchanged by this refinement:

- **The grade lattice** (Def. 4.1) — measures residual size. Reinterpreted, not modified.
- **Supermodularity** (Prop. 4.7) — the proof operates on characterization difficulty, which IS the residual measure. The proof is unchanged.
- **The fold model** (post 6) — the conversation as a sequence of stateless calls over managed state. The composite entity's residual grows over the conversation (accumulated side effects, growing trust gap as context expands), but the fold structure is the same.
- **The computation channel taxonomy** (post 7) — reinterpretable as a partiality/side-effect decomposition, but the levels and phase transitions are unchanged.
- **The specified band** (post 8) — narrowed to a System 2 claim, but the argument is the same.
- **The configuration ratchet** — each turn of the ratchet closes a part of the residual. Same mechanism, clarified purpose.
- **The star topology** — restated as "put the role with minimal residual at the hub," same conclusion.
- **Co-domain funnels** — restated as "reduce the interface's residual," same mechanism.
- **The case studies** — the χ measure is a residual measure. The studies' conclusions hold.

---

## Open questions

**Formalizing dishonesty for opaque actors.** Dishonesty means "output misrepresents internal state." For specified functions, this is impossible — the output IS the computation. For trained models, internal state is opaque. The observable consequence of dishonesty is indistinguishable from poor projection accuracy: the actor produced something unexpected, and we can't tell if the actor "knew" its output was misleading. The dishonesty component may not be independently formalizable for opaque actors — it may collapse into the trust gap. Whether this collapse is a limitation of the formalism or a genuine feature of opaque computation is an open question.

**The trust gap's irreducible core.** For computation-channel content, the semantic trust gap is irreducible by Rice's theorem. For data-channel content, the trust gap should be closable in principle (the output space is characterizable). In practice, even data-channel trust gaps persist because the *meaning* of a correct data-channel output depends on context the interface type doesn't capture. A `Read` tool honestly returns the file contents — but whether those contents are what the Inferencer should see right now is a question the `Read` interface can't answer. The trust gap has a semantic layer that no interface type fully eliminates.

**The System 3 minimum-ma relationship.** The companion essay on coordination and control ([post 8](08-the-specified-band.md) forward-references this) develops the claim that System 3's required decision surface is a function of System 1's computation level. In residual terms: the control function's residual requirements grow with the operations' residual. Whether this relationship is linear, supermodular, or something else is an open formal question.

---

*This essay refines the theoretical object developed in [The Ma of Multi-Agent Systems](00-intro.md). The tools, proofs, and design rules from the series are unchanged. What changes is the name for what they're measuring: the residual between interface promise and actual behavior, decomposed into dishonesty, side effects, and partiality, each managed by the mechanism best suited to it.*

---

*Previous: [Building With Ma](09-building-with-ma.md)*
*See also: [The Configuration Ratchet](the-configuration-ratchet.md)*
