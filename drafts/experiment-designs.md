# Claims Inventory and Revised Experimental Program

*Complete inventory of claims from the Ma framework (v1 published + v2 revisions), classified by validation method, with experimental designs for empirical claims.*

Note: This file contains references to security-sensitive patterns (subprocess imports, shell execution functions) in the context of designing detection experiments for Experiment 7. These are documentation of what auditors should detect, not executable code.

---

## Part 1: Claims Inventory

### Category A: Formal/Mathematical Claims (need proof, not experiment)

| ID | Claim | Source | Status | Validation method |
|----|-------|--------|--------|-------------------|
| A1 | Supermodularity of chi(w,d) = I(w) * log P(d) | Prop. 4.7 | Proven under independence model | Proof exists; test independence assumption empirically (see B1) |
| A2 | Composition is join on the grade lattice | Prop. 4.4 | Proven | Proof exists |
| A3 | Interface enumerability ordering produces same conclusions as monad morphism preorder | v2 revision | Claimed, partially verified | Must verify against every use of the preorder in formal companion |
| A4 | Three failure modes (infidelity, side effects, partiality) are exhaustive | v2 revision | Tested against 5 counterexamples | Need more adversarial testing; strong claim |
| A5 | Co-domain funnels restore linear growth from quadratic (Cor. 8.19) | Formal companion | Proven under independence model | Proof exists; test empirically (see B2) |
| A6 | Type honesty is formalizable via effect systems | v2 revision | Claimed, not developed | Requires formal development connecting to Koka/effect systems literature |
| A7 | The sandbox restores the configuration invariant (Prop. 9.9) | Formal companion | Proven | Proof exists |
| A8 | Delegation between agents is a computation channel (Prop. 9.11) | Formal companion | Proven | Proof exists; test consequences empirically (see B2) |

### Category B: Empirical Claims from v1 (covered by Experiments 1-5)

| ID | Claim | Source | Experiment |
|----|-------|--------|------------|
| B1 | Restriction has superlinear returns when both axes are high | Prop. 4.7, Cor. 4.8 | Experiment 1 |
| B2 | Unstructured inter-agent communication produces quadratic growth | Prop. 8.17, Cor. 8.18 | Experiment 2 |
| B3 | Systems above computation channel boundary show qualitatively different failure modes | Def. 9.8, Prop. 9.7 | Experiment 3 |
| B4 | Effective grade for previously-seen tasks is monotonically non-increasing | Conj. 12.1 | Experiment 4 |
| B5 | Trained judgment in regulatory loop degrades predictability | Prop. 10.3 | Experiment 5 |

### Category C: New Empirical Claims from v2

| ID | Claim | Source | Testable? |
|----|-------|--------|-----------|
| C1 | Trust gap is measurable and tracks with regulation difficulty | v2: trust ordering | Yes |
| C2 | Semantic trust gap is irreducible for computation-channel content | v2 + Rice's theorem | Partially |
| C3 | Two-stage ratchet produces type-honest tools | v2: type honesty | Yes |
| C4 | Type honesty reduces trust gap measurably | v2: type honesty | Yes |
| C5 | Inferencer has trained regulation of the Principal | v2: trust ordering | Yes |
| C6 | Minimum ma for System 3 scales with System 1's computation level | Beer decomposition | Yes |
| C7 | Current architectures lack real-time control (System 3) | Beer decomposition | Yes |
| C8 | Three failure modes are empirically exhaustive | v2: failure modes | Yes |
| C9 | Autonomy placement matters more than magnitude for system quality | Where the Space Lives | Yes |
| C10 | Specification at one point improves quality at adjacent unspecified points | Taylor/Johannsen insight | Yes |
| C11 | Capacity for informed judgment definition is consistent with all uses of ma | v2: restated core | Formal + empirical |

### Category D: Modeling Choices (assessed for usefulness, not truth)

| ID | Claim | Source | Assessment method |
|----|-------|--------|-------------------|
| D1 | Roles are interface contracts, not actor descriptions | v2 revision | Does this produce better design decisions? |
| D2 | Ma is the capacity for informed judgment at a point in the system | v2: restated core | Does this generate same predictions AND illuminate placement? Subsumes residual framing. |
| D3 | Beer VSM mapping (Harness = System 2, etc.) | Beer decomposition | Does this identify gaps the original misses? |
| D4 | The purpose of specification is to free the unspecifiable to do its work | Taylor/Basho exercise | Does this change design decisions vs defensive framing? |
| D5 | The field needs a placement map, not just a magnitude knob | Where the Space Lives | Does placement framing produce measurably different architectures? (See C9) |

---

## Part 2: Experimental Program

### Experiments 1-5: Unchanged

The original five experiments (supermodularity, communication amplification, computation channel phase transition, configuration ratchet, specified band violation) remain as previously designed. They test claims B1-B5.

### Experiment 6: Trust Gap Measurement

**Tests:** C1, C4

Build a specified observer (rule-based tool call predictor). Measure gap rate (proportion of unpredicted tool calls). Run before and after ratchet promotion to test whether crystallization shrinks the gap. Observer should be deliberately simple. Consider multiple observer complexities.

**Falsification:** C1 fails if gap rate doesn't correlate with regulation difficulty. C4 fails if promotion doesn't reduce gap rate.

### Experiment 7: Semantic Trust Gap and Obfuscation

**Tests:** C2, C5 partially

Experimenter constructs innocuous (Set A) and obfuscated (Set B) tool call sequences. Three specified auditors evaluate both: syntactic pattern matching, AST-based (sitting_duck), trajectory-based (duck_tails + sitting_duck). Variant for C5: obfuscation from Principal direction.

**Falsification:** C2 fails if specified auditor achieves high detection with low false positives. Caveat: can only test specific patterns, not prove universal irreducibility.

Ethical note: constructed code must be demonstrably harmless.

### Experiment 8: System 3 Effectiveness vs Computation Level

**Tests:** C6, C7

Tasks with planted failure modes (Write-Test oscillation, scope creep, stale reference). Three tool configurations (levels 0-2, 2-3, 4). Specified pattern detector as System 3. Then trained System 3 (Haiku evaluator) for comparison.

**Falsification:** C6 fails if specified System 3 works equally well at all levels. C7 fails if existing Harness mechanisms already catch planted failures.

### Experiment 9: Failure Mode Taxonomy Validation

**Tests:** C8

Corpus study over 4-8 weeks alongside Experiment 4. Log all failures. Classify as infidelity, side effect, or partiality. Residual analysis for unclassifiable failures. Independent classification by two raters.

**Falsification:** C8 fails if more than 10% resist classification after compound analysis.

### Experiment 10: Two-Stage Ratchet Validation

**Tests:** C3, extends Experiment 4

During promotion step, separately measure discovery (observed behavior gap) and crystallization (type commitments vs implementation guarantees). Check type honesty: do implementations back their commitments?

**Falsification:** C3 fails if tools make aspirational commitments, or if discovery doesn't influence crystallization.

### Experiment 11: Autonomy Placement vs Magnitude

**Tests:** C9, C10, D4, D5

**Core idea:** Hold total ma budget approximately constant. Vary where the ma is placed. Measure system quality.

**Setup:** Two-phase coding task: (1) understand and plan, (2) implement. Three conditions:

| Condition | Planning phase | Execution phase | Total ma budget |
|-----------|---------------|-----------------|-----------------|
| A: Uniform | Medium tools (Read, Grep, Glob, Edit) | Medium tools (Read, Grep, Glob, Edit) | Moderate everywhere |
| B: Front-loaded | Broad tools (Read, Grep, Glob, Bash read-only, web search) | Narrow tools (Edit only, pre-specified file list) | High planning, low execution |
| C: Back-loaded | Narrow tools (Read on specified files only) | Broad tools (Read, Grep, Glob, Edit, Bash sandboxed) | Low planning, high execution |

**Predictions:** Framework predicts B (front-loaded) produces highest quality. Planning benefits from broad world coupling and large decision surface (System 4). Execution benefits from narrow tools once the plan is good (System 1). Condition C is the Taylor anti-pattern: precise tools but doesn't know what to build.

**Measurements:**
- Task completion rate and quality (human-judged: correctness, elegance, edge cases)
- Approach quality and implementation quality scored independently and blind to condition
- Wasted effort (dead-end exploration, reverted changes)
- Behavioral variance across 5 runs per condition

**Falsification:**
- C9 fails if A (uniform) performs as well as or better than both B and C
- C10 fails if B's execution quality (narrow tools) is worse than A's execution quality (medium tools) — constraint didn't create freedom, just reduced capability

**Cost:** ~$300-900 (3 conditions x 5 runs x 20 tasks at $1-3/run)

### Experiment 12: Capacity for Informed Judgment — Definition Consistency

**Tests:** C11, D2

**Core idea:** Systematic textual analysis. Apply capacity, residual, and original definitions independently to every use of "ma" in the published series. Check consistency.

**Phase 1: Consistency check.** For each use of ma in posts 1-9, formal companion, case studies, ratchet:
1. What does it mean under "space between inputs and outputs"?
2. What does it mean under "capacity for informed judgment"?
3. What does it mean under "residual between interface promise and behavior"?
4. Do the three agree? Which captures the passage's intent most accurately?

**Phase 2: Divergence analysis.** Where they diverge: does the capacity definition produce different, better, or worse design recommendations?

**Phase 3: Interface ma stress test.** Check every use of "interface ma" — does "capacity for informed judgment at the interface" work, or does the interface constrain expression rather than judgment itself?

**Falsification:**
- C11 fails if more than 20% of uses are inconsistent with capacity definition
- D2 fails if capacity definition never produces a more informative reading

**Practical notes:** Can be done by an authoring agent during v2 revision. Low cost, high leverage — foundation for all v2 changes.

---

## Part 3: Priority and Sequencing

| Priority | Experiment | Tests | Effort | Time |
|----------|-----------|-------|--------|------|
| 1 | 4 + 9 + 10 (Ratchet + Failures + Two-Stage) | B4, C3, C4, C8 | Low | 4-8 weeks |
| 2 | 12 (Definition Consistency) | C11, D2 | Low | 1-2 days |
| 3 | 3 (Computation Channel Phase Transition) | B3 | Medium | 1-2 days |
| 4 | 6 (Trust Gap Measurement) | C1, C4 | Medium | 1-2 days |
| 5 | 11 (Autonomy Placement vs Magnitude) | C9, C10, D4, D5 | Medium-High | 2-3 days |
| 6 | 8 (System 3 Effectiveness) | C6, C7 | Medium-High | 2-3 days |
| 7 | 1 (Supermodularity) | B1 | Medium | 1-2 days |
| 8 | 5 (Specified Band Violation) | B5 | Medium-High | 2-3 days |
| 9 | 7 (Semantic Trust Gap / Obfuscation) | C2, C5 | High | 3-5 days |
| 10 | 2 (Communication Amplification) | B2 | High | 3-5 days |

## Part 4: Shared Infrastructure

| Component | Used by | Build effort |
|-----------|---------|-------------|
| Task suite (20+ tasks, including planning-matters tasks for Exp 11) | 1, 2, 3, 5, 6, 8, 11 | Medium |
| Specified observer | 1, 3, 5, 6 | Low-Medium |
| Sandbox diffing | 3, 7 | Low |
| Failure logging protocol | 4, 9 | Low |
| sitting_duck audit queries | 7, 10 | Need specific queries |
| Pattern detector for System 3 | 8 | Medium |
| Obfuscation corpus | 7 | Medium-High |
| Phase-gated tool configurations | 11 | Low |
| Quality rubric for human judging | 11 | Low |

Build order: Failure logging -> Exp 12 textual analysis (no infra needed) -> specified observer -> task suite -> sandbox diffing -> phase-gated tool configs + rubric -> pattern detector -> obfuscation corpus

## Part 5: Formal Verification Tasks

| ID | Task | Effort | Priority |
|----|------|--------|----------|
| A3 | Verify interface enumerability across all preorder uses | Medium | High |
| A4 | Additional adversarial testing of failure mode exhaustiveness | Low-Medium | High |
| A6 | Formal development: type honesty via Koka effect rows | Medium-High | Medium |
| A1 | Assess independence assumption against correlated path models | Medium | Medium |
| NEW | Verify capacity definition consistency with all formal uses of ma | Medium | High — foundation for v2; run alongside Exp 12 |
| NEW | Formalize placement as optimization over grade lattice | Medium-High | Medium — may resist formalization; supermodularity implies non-uniform optimal placement but the quality function Q(placement) is speculative |
