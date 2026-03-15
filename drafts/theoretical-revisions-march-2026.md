# Theoretical Revisions: March 14-15, 2026

*Substantial developments from the review conversation between Teague Sterling and Claude. These revisions affect the framework's formal core, not just presentation. They should be treated as proposed amendments to the formal companion and blog series, subject to the same rigor standards as the original work.*

**Standard for inclusion:** Every claim in this document should be defensible under scrutiny. Where a claim is speculative or under-developed, it is flagged explicitly. The authoring agents should not publish claims that merely sound plausible — only claims that hold up under adversarial examination.

**Status:** Key insights from this document have been published in the companion essay "The Residual Framework" (blog/the-residual-framework.md). This document serves as the full specification for a v2 revision of the main series posts, to be undertaken after the companion essays have been tested against scrutiny.

---

## 1. The Preorder: From Embeddability to Interface Enumerability

### 1.1 The problem with the current formulation

The series defines the monad morphism preorder (Def. 6.2): M ≤ N iff there exists a monad morphism η : M ~> N. This is used to argue that the Harness belongs at the hub ("everyone can simulate the Harness") and that trust flows down the preorder.

The problem: the framework never uses the morphism's full power. The Harness doesn't simulate the Executor — it pattern-matches on `Either E Result`. The Inferencer doesn't simulate the Harness — it operates on a projection of the Harness's policy. The actual regulatory mechanism is handler pattern matching on the interface type, which requires enumeration of possible outputs, not computational embedding.

The monad morphism is sufficient for the framework's claims but not necessary. It overclaims by implying simulation capacity that is intractable for the interesting cases (Inferencer, Principal) and unnecessary for the cases where it works (Executor, Harness).

### 1.2 What the framework actually needs

Audit of claims and their minimal requirements:

| Claim | What it uses | Minimal requirement |
|-------|-------------|-------------------|
| Harness belongs at the hub | Other actors can reason about what the Harness will do | Harness's interface type is enumerable; Harness's policy is readable |
| Handler can regulate the Inferencer | Harness has a response for every possible Inferencer output | Inferencer's interface type is enumerable at the structural level; policy covers every case |
| Restriction has superlinear returns | Supermodularity of characterization difficulty | Grade lattice only — no inter-actor ordering needed |
| Same model, different tools = different system | Composition changes the grade | Grade lattice only |
| Co-domain funnels help regulation | The funnel's interface is more characterizable than its internals | Interface/internal ma distinction — the morphism adds a surjectivity guarantee (liveness) but regulation only needs enumerability |
| Trust/opacity flow | Directional relationship between actors | See section 2 — requires trust ordering, not embedding |

### 1.3 The revised preorder

**Definition (interface enumerability ordering).** For interface types A and B:

A ≤ B if the policy-relevant structure of A is enumerable to at least the degree that B's is.

Policy-relevant structure: the structural features of the interface type that a handler needs to branch on to construct an exhaustive policy. For `Either E Result`: two tags (fully enumerable). For `HarnessAction`: five action tags (fully enumerable given configuration). For `Response`: structural type enumerable (text blocks + tool calls), tool names enumerable (from granted set), arguments not enumerable, text content not enumerable. For `MultimodalMessage`: not enumerable.

The ordering:

```
Either E Result          -- fully enumerable
≤ HarnessAction          -- fully enumerable given config
≤ Response               -- structurally enumerable, content not
≤ MultimodalMessage      -- not enumerable
```

This produces the same ordering as the monad morphism preorder. It matches what the framework's claims actually use. It identifies exactly where enumeration breaks: at the content level of Response, which is the boundary between specified policy and trust.

### 1.4 Roles are interface contracts, not actor descriptions

The preorder ranks interface types, not entities. Any entity can fill any role depending on what interface it presents to the system.

- A language model operating as a deterministic router with specified rules is a Harness — its interface is `HarnessAction` regardless of the billions of parameters behind it.
- A human clicking raining/not-raining buttons is an Executor — its interface is `Bool` regardless of being a conscious being with a lifetime of experience.
- A script that holds the system's purpose is the Principal — regardless of being ten lines of Python.

The entities bring their full internal complexity to the role. That internal complexity determines the *quality* of decisions within the interface contract. An Opus reviewer with three output buttons makes better decisions than a coin flip with the same buttons — same interface, same role, vastly different internal ma. But the system's *regulatory requirements* are determined by the interface contract, not by who's behind it.

Historical note: this is how computation started. Human "computers" at Bletchley Park and JPL were Executors — `Number -> Number`, total, specified — with (open, evolved) internal ma. When electronic computers replaced them, the replacement was at the interface level. The system cared about the contract, not the internals.

The preorder table in post 5 should list interface types, not actors. Actors are examples of entities that typically fill those roles, not definitions.

### 1.5 What happens to the monad morphism

The morphism should be demoted, not eliminated. It provides:

- A connection to established PL theory (pedagogical value)
- A surjectivity guarantee for co-domain funnels (liveness property — every interface output is reachable)
- A formal backbone for readers coming from the PL community

Recommendation: present the interface enumerability ordering as the primary inter-actor relationship in the blog posts. Keep the monad morphism in the formal companion as the stronger property that connects to PL literature. Be explicit about what each provides and where the stronger property is needed (funnel surjectivity) vs where the weaker property suffices (everything else).

### 1.6 Terms the framework uses imprecisely

The series uses "predict," "simulate," "model," and "reason about" interchangeably. These are ordered by strength:

| Term | Meaning | Strength | Used for |
|------|---------|----------|----------|
| **Simulate** | Reproduce the same outputs for the same inputs | Strongest | Only tractable for Executor ≤ Harness |
| **Predict** | Determine the output before it's produced | Strong | Intractable for Inferencer and Principal |
| **Characterize** | Enumerate the possible outputs of the interface type | Moderate | Sufficient for handler pattern matching and policy construction |
| **Model (Conant-Ashby)** | Have a policy mapping from observations to responses | Weakest | Sufficient for regulation — what the Harness actually does |

The framework's claims require characterize and model. They do not require simulate or predict for the interesting cases. The series should use these terms precisely and not interchange them.

---

## 2. The Trust Ordering

### 2.1 Three quantities per relationship

For any directed trust relationship where actor B trusts actor A:

**Total paths:** Everything A could possibly do if all constraints were removed. The theoretical maximum. For a human: everything a human can do. For an LLM: every token sequence the weights could produce.

**Reachable paths:** Total paths constrained by configuration. The sandbox eliminates some side effects. The interface type constrains output structure. Timeouts eliminate unbounded partiality. Resource limits bound computation. Reachable ≤ total.

**Expected paths:** What B's model predicts A will do. Based on A's training, past behavior, declared purpose, projected constraints. Expected ⊆ reachable (if the model is correct).

**Configuration gap = total - reachable.** Closed by sandbox, interface type enforcement, timeouts, resource limits. This is engineering — it's what tool restriction and sandboxing do.

**Trust gap = reachable - expected.** The space of behaviors that are possible within the current configuration but that B doesn't expect A to produce. This is what trust covers. Every behavior in the trust gap is allowed by the configuration but would surprise the trusting actor.

The `rm -rf /` example: reachable (Bash is Turing-complete within the sandbox), not expected (training makes it unlikely). It lives in the trust gap. The sandbox may limit the damage (filesystem bounds) but doesn't make it unreachable. The gap between "the model won't do this" and "the model can do this" is exactly where trust lives.

### 2.2 Three things reduce the trust gap

**Interface constraint:** Fewer reachable paths = smaller gap. `Either E Result` has a tiny gap. `MultimodalMessage` has a maximal gap.

**Behavioral predictability:** More expected paths aligning with reachable paths. Training narrows this for the Inferencer. Expertise narrows it for the Principal. Specification narrows it for the Harness. The mechanism differs; the effect is the same.

**Projection accuracy:** How well B's model of A matches A's actual behavior. Better projections = expected paths more closely approximate the actual distribution over reachable paths. Tool descriptions, error messages, declared expertise levels are all projections that improve the model. Post 8's transparency principle directly addresses this.

### 2.3 Trust is bidirectional, not hierarchical

The preorder was acyclic — a partial order. The trust ordering has cycles.

**Harness → Executor:** Minimal trust needed. Interface fully enumerable. Policy complete.

**Harness → Inferencer:** Low structural trust (Response type is enforced), higher content trust (arguments and text are not enumerable). Permission configuration covers structural cases. Training covers content quality.

**Harness → Principal:** Maximal trust. Interface not enumerable. No policy possible over unbounded input. Trust is institutional (reputation of the user) and axiomatic (the framework assumes a cooperative Principal).

**Inferencer → Harness:** Non-trivial trust, invisible to the Inferencer. The Inferencer trusts scope construction to be faithful, tool results to be accurate, compaction to preserve what matters. The Inferencer cannot audit any of these. The trust gap is real and entirely invisible to the trusting party. Projection accuracy (post 8's transparency principle) is the only mitigation.

**Inferencer → Principal:** Large trust gap. The Inferencer trusts the Principal to provide accurate context, coherent goals, and honest domain knowledge. The Inferencer has limited tools to verify any of this.

**Principal → Inferencer:** Large trust gap. The entire framework (specified band, co-domain funnels, tool restriction, permission gates) exists to manage this specific gap. The framework's primary contribution is tools for narrowing this trust gap through configuration.

**Inferencer → Principal (regulatory direction):** The Inferencer has trained regulation of the Principal — refusal training, safety guardrails. This is trained judgment in a regulatory loop, which the specified band argument appears to prohibit. But it's the only regulation of the Principal that exists, and it's unavoidable because the Principal's input space is semantically open (natural language). Rice's theorem applies to natural language inputs just as it applies to Bash commands — you can't specify in advance every request that should be refused. The Inferencer's refusal training is the sandbox for the Principal's inputs.

This means the series' claim "never put trained judgment in the regulatory loop" needs refinement. The accurate claim: never put trained judgment in the *coordination* loop (System 2, the Harness). Trained judgment in the *trust regulation* of semantically open interfaces (Principal's natural language, Executor's computation channels) is unavoidable and appropriate.

### 2.4 The semantic trust gap

The trust gap has a component that's irreducible by specified audit:

**Structural trust gap:** Reachable interface outputs minus expected interface outputs. Reducible by interface constraint.

**Semantic trust gap:** The gap between what the actor *intended* and what the observer *infers* from the output. Obfuscated C contests demonstrate this: a program that looks like it prints "Hello World" can do anything. Multi-step obfuscation is worse — individually-innocuous writes at turns 3, 7, and 12 compose into behavior none of them revealed. The question "is this sequence of individually-innocuous calls collectively malicious?" is a semantic question about composition, and for Turing-complete content it's undecidable.

The semantic trust gap is irreducible by specified audit for computation-channel content (Rice's theorem). The sandbox bounds the *consequences* without closing the gap. This applies in both directions — prompt injection and jailbreaking are the Principal exploiting the semantic trust gap in the Inferencer's regulation, structurally identical to an Inferencer sending obfuscated code through a computation channel.

---

## 3. The Three Failure Modes

### 3.1 Definitions

Every actor A with interface type T can fail in three ways. These are defined relative to properties beyond the raw structural type: a representational commitment (what values mean), an effect signature (what world changes are sanctioned), and a liveness expectation (the type promises a value).

**Failure Mode 1: Infidelity.** The output is a structurally valid inhabitant of T but does not faithfully correspond to the state of affairs it represents.

The interface type's role creates a representational commitment: Read returns file contents, the Inferencer's text reflects its processing, the Principal's context describes reality. Infidelity is when that commitment is violated.

Sources of infidelity (these are diagnostic, not taxonomic — the failure at the boundary is the same regardless of cause):
- Actor's internal state doesn't match the world (hallucination, miscalibration)
- Actor's output doesn't match its internal state (intentional deception)
- World changed between production and consumption (staleness)
- Actor never had access to relevant world state (confabulation)
- Measurement disturbed the observed state (observer effects)
- Lossy compression misrepresents full state (compaction artifacts)

Note: "dishonesty" was rejected as a term because it implies intent. Most infidelity has no intent — hallucination, staleness, and confabulation are all unintentional. "Infidelity" captures non-correspondence without attributing agency.

**Failure Mode 2: Side effects.** The actor changes the world in ways outside the declared effect signature of its interface type.

The effect signature specifies which world changes are sanctioned: Read sanctions no world change, Write sanctions modification of a specified file, Bash sanctions whatever the sandbox allows. World changes beyond the declared signature are side effects — whether caused by the actor's code, by the environment's reaction (e.g., access logging), or by emergent behavior from composition.

This is the info/effect decoupling from Def. 8.9: the return value `Ok("done")` while the filesystem changed profoundly. Side effects are world changes not inferable from the interface output.

**Failure Mode 3: Partiality.** The actor fails to produce any inhabitant of T within bounded time.

The type promises a value. None arrives. The absence is not represented in the type. The actor diverged, hung, crashed, or left. A timeout converts partiality to totality by extending the type: `Maybe T` instead of `T`, where `Nothing` is a valid output the handler can have a policy for. The partiality failure mode specifically means: the type says T, no T arrives, and the absence is not a declared possibility.

### 3.2 Validation

These three modes were tested against adversarial counterexamples:

- **Structural type violation** (actor returns wrong type entirely): Collapses into partiality at the boundary — the enforcement layer converts type violations into errors, which the handler sees as failure to produce valid T.
- **Staleness** (output was faithful at production time, not at consumption time): Infidelity with temporal cause. Initially appeared to be a system-level fourth mode, but fits under infidelity once the definition covers the gap between representation and represented state regardless of cause.
- **Ambiguity** (output is faithful but receiver can't determine pragmatic force): Not a failure mode — it's an interface type deficiency. The type doesn't commit to enough. The fix is a richer type, not a different failure mode category.
- **Resource consumption** (actor uses more resources than the interface represents): Side effect — budget change is a world change not represented in the output.
- **Observer effects** (reading a log file appends to it): Side effect — world change outside declared effect signature, caused by environment's reaction rather than actor's code.
- **Inconsistency across turns** (two individually-faithful outputs that contradict each other): At least one is infidelity — ground truth resolves which. Apparent inconsistency from world change between turns is staleness, which is infidelity with temporal cause.

No fourth mode was found. The three modes appear to be exhaustive for actor-level failures. System-level failures (emergent computation channels from Prop. 9.11, temporal composition gaps) decompose into the three actor-level modes applied to the composition rather than to individual actors.

### 3.3 What the three modes decompose

The IO type collapses all three failure modes into one: `IO String` says "eventually produces a string, might do anything to the world along the way, and the string might or might not faithfully represent what happened."

The framework's contribution is decomposing this:
- **World coupling (W axis)** decomposes the side effect problem — how much of the world can the actor affect?
- **Decision surface (D axis)** partially decomposes the infidelity problem — more paths mean more ways an output could be unfaithful to the processing that produced it
- **Computation level** decomposes the partiality problem — bounded computation is total; Turing-complete specification is partial

### 3.4 Relationship to ma

Ma — the space between what an actor receives and what it produces — is the space where all three failure modes live. The grade measures the size of that space. The interface type determines how much is visible. The trust gap is the invisible remainder. The three failure modes describe how the invisible remainder manifests when trust fails.

**Restated core thesis:** Ma is the residual between what an interface type promises and what the actor behind it actually does. The framework decomposes that residual along three axes (infidelity, side effects, partiality) and provides tools for managing each component through the appropriate mechanism (specification for what's enumerable, sandboxing for what's constrainable, training for what's neither, trust for whatever remains).

---

## 4. Type Honesty and the IO Refinement

### 4.1 Types have fidelity

The interface type itself can be more or less honest about the conditions under which its representational commitment holds. This is independent of whether any specific output is faithful — it's about what the type *discloses*.

`Bash("date") : IO String` — honest. The type accurately commits to almost nothing because the tool can guarantee almost nothing. The implementation routes through a universal machine where PATH can change, the binary can be replaced, an alias can shadow it.

`Bash("date") : IO_time String` — dishonest. The type commits to time-only dependency, but the implementation can't back that commitment. The tool *currently* returns timestamps, but nothing in the implementation guarantees it.

`CurrentTime() : Timestamp` — honest. The type commits to structured time-dependent output, and the implementation calls the system clock directly, guaranteeing those commitments.

Type honesty is: **the type's commitments match what the implementation can guarantee.** Not what the tool *currently does* (that's behavioral observation). What the implementation *structurally ensures*.

### 4.2 The type honesty spectrum

From maximally committed to maximally uncommitted:

```
Pure String               -- no world dependency, always faithful, total
IO_config String          -- depends on stable configuration
IO_fs_readonly String     -- depends on filesystem, reads only
IO_fs String              -- depends on filesystem, may write
IO_time String            -- depends on volatile external state
IO_network String         -- depends on external service
IO String                 -- commits to nothing
```

Each step down the spectrum removes a commitment. Each removed commitment widens the trust gap, because the receiver has less information about what conditions the output's representational commitment holds under.

`IO String` at the bottom isn't wrong — it's maximally uncommitted. For a computation channel, that's the *honest* type, because the implementation can't back any stronger commitment. Every type above it requires an implementation that structurally guarantees the commitment.

### 4.3 Connection to effect systems

This is exactly what Koka's effect rows provide. `() -> <read,exn> string` says: reads and might throw, but won't write, won't access network, won't diverge. Every effect label is a commitment. Every absent label is a guarantee.

Haskell's effect systems (fused-effects, polysemy, effectful) express the same: `Members '[FileRead, Error] r => Eff r String` — can read files and fail, provably cannot write.

The sandbox constraints the series describes at the design level are expressible at the type level in these systems. The computation channel taxonomy (post 7) is a type system proposal: levels 0-8 correspond to increasingly permissive effect rows, and the phase transitions correspond to introduction of specific effect labels.

The specified band argument, restated in type terms: the Harness's regulatory rules are decidable when the effect row is restricted, and undecidable when it includes an `Exec` (executable specification) effect. Rice's theorem applies to the `Exec` effect specifically, not to IO in general.

**Action for the series:** Post 7 or the formal companion should explicitly connect the computation channel taxonomy to effect systems literature. This sharpens the framework's most important formal claim and connects it to the active PL research community.

### 4.4 The ratchet as two-stage type refinement

The configuration ratchet (companion essay) describes the conversion of high-ma behavior into low-ma infrastructure. The type honesty framing reveals this as a two-stage process:

**Stage 1: Discovery.** Use the computation channel. Observe what happens empirically.

```
Bash("date") : IO String     -- honest type for computation channel
Observe: returns timestamps, no side effects, terminates
Characterize: this is really a time query
```

Discovery operates within the trust gap. Expected paths narrow through observation. Reachable paths are unchanged. The type stays `IO String` because the tool *can* still do anything — you've only characterized what it *does* do. You cannot honestly refine the type at this stage because the implementation hasn't changed.

**Stage 2: Crystallization.** Build a new tool that locks in the discovered behavior.

```
CurrentTime() : Timestamp     -- honest type for specified tool
Implementation: direct system clock call
Commitments backed by implementation guarantees
```

Crystallization replaces the tool, not the type annotation. You don't refine `Bash("date")` into a better-typed `Bash("date")` — that would be a dishonest type, committing to properties the implementation can't back. You build a *new tool* whose implementation *can* back the commitments its type makes.

**Why Stage 1 can't be skipped:** You can't build `CurrentTime()` without first observing that agents need timestamps. The computation channel is the exploration mechanism. The high-ma process discovers what the low-ma replacement should be.

**Why Stage 2 can't be skipped:** Observing that `Bash("date")` returns timestamps doesn't make it safe. PATH can change. The binary can be replaced. An alias can shadow it. The implementation hasn't changed. Only crystallization — building a new tool with structural guarantees — closes the gap between reachable and expected.

**Why the ratchet only turns one way:** The crystallized tool's implementation backs its commitments. Barring deliberate reconfiguration, those guarantees hold. The tool doesn't spontaneously become a computation channel again.

**The ratchet produces two artifacts:**
1. System 1 tools — computation channel closure (Bash pattern → structured tool)
2. Type refinements — honest commitments backed by implementation guarantees

These are the same artifact viewed from different angles. Closing a computation channel IS refining the type. The grade drops and the type becomes more honest in the same step, because both are consequences of replacing an uncommitted implementation with a committed one.

---

## 5. Implications for the Framework

### 5.1 Restated core

Ma is the residual between what an interface type promises and what the actor behind it actually does. The framework:
1. Measures the size of that residual (the grade lattice)
2. Decomposes it into three failure modes (infidelity, side effects, partiality)
3. Orders interface types by how much residual they leave (the enumerability preorder)
4. Provides tools for managing each component (specification, sandboxing, training, trust)
5. Describes a process for systematically reducing the residual over time (the two-stage ratchet)

### 5.2 Changes to existing posts

**Post 2 (The Space Between):** The core definition of ma should be restated: "ma is the residual between what an interface promises and what the actor actually does." The three failure modes should be introduced here as the decomposition of that residual.

**Post 5 (Predictability as Embeddability):** Major revision. The preorder should be restated as interface enumerability ordering. The monad morphism should be presented as a stronger property that connects to PL theory but isn't required for the framework's claims. The terms simulate/predict/characterize/model should be distinguished explicitly. The trust ordering (expected/reachable/total) should be introduced here.

**Post 7 (Computation Channels):** Add connection to effect systems literature. The taxonomy is a type system proposal. The phase transitions correspond to specific effect labels. Rice's theorem applies to the Exec effect, not IO in general.

**Post 8 (The Specified Band):** Add acknowledgment that the Inferencer has trained regulation of the Principal, and that this is the one case where trained judgment in a regulatory loop is unavoidable. Refine the specified band claim to apply to coordination (System 2), not to all regulation.

**The Configuration Ratchet (companion essay):** Add the two-stage framing (discovery vs crystallization). Emphasize that type honesty comes from tool replacement, not type annotation. The ratchet produces honest types by building implementations that back their commitments.

**Formal Companion:** Replace Def. 6.2 (monad morphism preorder) with the interface enumerability ordering as the primary definition. Keep the morphism as a stronger alternative in a remark. Add the three failure modes as formal definitions. Add type honesty as a formal concept. Revise the causal chain (Prop. 5.4) to use the new ordering.

### 5.3 Relationship to other revision documents

This document should be read alongside:
- **seed-coordination-is-not-control.md** — the Beer decomposition and System 3/3* gap
- **note-for-agents.md** — guidance for future instances
- **experiment-designs.md** — experimental program testing framework predictions (when available)

The Beer decomposition and these theoretical revisions are complementary:
- The Beer decomposition identifies missing *functions* (System 3, System 3*)
- These revisions refine the framework's *formal core* (preorder, trust, failure modes, type honesty)
- Together they constitute a substantial v2 of the framework

### 5.4 What hasn't been validated

The following claims in this document have not been tested against adversarial counterexamples beyond those documented:

- The three failure modes are exhaustive (tested against five counterexamples, all collapsed — but exhaustiveness is a strong claim that could fail against examples we haven't considered)
- The interface enumerability ordering produces the same architectural conclusions as the monad morphism preorder (checked for five major claims — but there may be claims in the formal companion that require the stronger property)
- The trust ordering is sufficient to replace the preorder for inter-actor reasoning (this is a substitution claim that needs verification across every use of the preorder in the formal companion)
- Type honesty is well-defined enough to formalize (the spectrum is informal — formalizing it requires connecting to effect systems literature, which is active research)

These should be verified during the revision process, not assumed.

---

## References (new)

- Leijen, D. (2014). Koka: Programming with row polymorphic effect types. *MSFP*.
- Leijen, D. (2017). Type directed compilation of row-typed algebraic effects. *POPL*.
- Wu, N., Schrijvers, T., & Hinze, R. (2014). Effect handlers in scope. *Haskell Symposium*.

(Add to existing reference list in formal companion)
