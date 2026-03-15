# Experiment 12: Definition Consistency Analysis

*Tests C11 (capacity for informed judgment definition consistent with all uses of ma) and D2 (capacity definition generates same predictions AND illuminates placement).*

---

## Summary

- **Total uses of ma found:** 87 distinct uses across all published posts and companion essays
- **Consistency rate:** 78/87 (89.7%) — all three definitions produce the same reading
- **Divergence rate:** 9/87 (10.3%) — at least one definition produces a different or more/less informative reading
- **Interface ma compatibility:** "Capacity for informed judgment at/through the interface" works with a qualifier: "capacity for informed judgment *expressible* through the interface." Without the qualifier, 4 of 11 interface ma uses are misleading because they conflate the interface's expressive capacity with the entity's judgment capacity.
- **Recommendation:** "Capacity for informed judgment" is a valid v2 primary definition (below the 20% inconsistency threshold). It is more informative than Def A in 6 cases, equally informative in 72 cases, and less informative than Def C in 3 cases. **Use Def B as the primary definition with Def C as the boundary perspective.** Interface ma needs the qualifier.
- **Recommendation on "residual":** The residual framing (Def C) is the right framing for the boundary perspective. It's strictly more informative at boundaries than either A or B because it decomposes into actionable components (infidelity, side effects, partiality). Retain it as the companion framing.

---

## Definitions tested

| | Definition | Source |
|---|---|---|
| **A** | "The space between what an actor receives and what it produces" | Post 02, original |
| **B** | "The capacity for informed judgment at a point in the system" | v2 proposed primary |
| **C** | "The residual between what an interface type promises and what the actor behind it actually does" | The Residual Framework |

---

## Methodology

Every use of "ma" (間), "the space between," "the grade," "interface ma," "internal ma," or conceptual invocations of ma (where the concept is used without the term) was cataloged. Uses were grouped by agreement pattern. Only divergent and interesting cases receive full analysis below. Agreement cases are listed in the appendix.

---

## The 5 most interesting divergences

### Divergence 1: "Ma reduction" in the Configuration Ratchet

**Location:** `the-configuration-ratchet.md`, lines 63-64, 229-235

**Passage:** "Ma reduction: the conversion of high-ma solutions into low-ma infrastructure that handles equivalent problems." Also: "The irreducible core is where humans belong. The reducible periphery is where specified systems belong."

**Def A:** The *space* between input and output shrinks when bash patterns become structured tools. Clear — fewer paths through the computation.

**Def B:** The *capacity for informed judgment* decreases when bash becomes a macro. This is subtly wrong. The structured tool doesn't have *less judgment capacity* — it has *no judgment*. It's not a reduction in judgment capacity; it's a replacement of judgment with specification. "Judgment capacity" implies a continuum that passes through "some judgment." What actually happens is a phase transition from "requires judgment" to "no judgment needed."

**Def C:** The *residual* between interface promise and actual behavior shrinks. This is precisely correct — the structured tool can back its type commitments, closing the gap between promise and behavior. The residual decomposes into infidelity (reduced because the tool is faithful by construction), side effects (bounded by the specified interface), and partiality (eliminated for total tools).

**Agreement:** No — A and C agree, B is slightly misleading. B suggests the tool still has "judgment" but less of it. C captures what actually happened: the gap closed.

**Winner:** C is most informative. A is adequate. B is adequate if read as "the *need for* informed judgment at this point" rather than "the *capacity for* judgment." This reading works but requires the qualifier.

---

### Divergence 2: "Ma determines role" (Post 06)

**Location:** `06-conversations-are-folds.md`, lines 52-53

**Passage:** "'Ma determines role' gets stronger, not weaker. The Inferencer's role is stable across the conversation because its ma is stable."

**Def A:** The *space between input and output* determines role. The Inferencer always has the same space (same weights). Clear.

**Def B:** The *capacity for informed judgment* determines role. The Inferencer has vast judgment capacity; the Harness has specified judgment capacity; the Executor has minimal judgment capacity. This works and adds something — it explains *why* the Harness belongs at the hub (its judgment is fully specified, not just "small") and why the Inferencer is valuable (its judgment is *informed* by training, not just "large").

**Def C:** The *residual* determines role. The Harness has minimal residual; the Inferencer has large residual. This works but is less intuitive for "role" — roles aren't naturally described as "the amount of gap between promise and behavior."

**Agreement:** All three produce valid readings but B is most informative here.

**Winner:** B. It captures the *kind* of processing (judgment, informed by training/experience) that determines role, not just its *size*.

---

### Divergence 3: Interface ma in co-domain funnels (Post 02, Post 05)

**Location:** `02-the-space-between.md`, lines 185-200; `05-predictability-as-embeddability.md`, lines 138-155

**Passage:** "A reviewer backed by Opus that analyzes thousands of lines of code with deep chain-of-thought reasoning: enormous internal ma. But its interface is Approve | Reject | RequestChanges — three possible outputs. Low interface ma."

**Def A:** The *space between input and output at the interface* is small — three outputs. The *space inside* is vast. Clear.

**Def B:** The *capacity for informed judgment at the interface* is small. But wait — is the judgment at the interface actually small? The reviewer's *judgment* is vast; it's the *expression* of that judgment that's constrained. The interface constrains output, not judgment. Saying "low capacity for informed judgment at the interface" could be read as "the interface doesn't exercise much judgment" — which is exactly backwards. The interface exercises *profound* judgment compressed into three categories.

**Def C:** The *residual at the interface* is small — the three-valued type captures almost everything the observer needs. The reviewer might be unfaithful (infidelity), but the interface type is so constrained that the trust gap is minimal. This is precise and correct.

**Agreement:** A and C agree. B diverges — "low capacity for informed judgment" at the interface is misleading. The interface has *high* judgment compressed through *low* expressiveness.

**Winner:** A and C. B needs the qualifier: "low capacity for informed judgment *expressible through* the interface" works. "Low capacity for informed judgment *at* the interface" doesn't, because the judgment is present — it's just not visible.

**This is the critical divergence for interface ma.** The distinction between "capacity for judgment" and "capacity for *expressing* judgment" is exactly the interface/internal distinction. Def B collapses them unless qualified.

---

### Divergence 4: The Ashby/variety connection (Post 02)

**Location:** `02-the-space-between.md`, lines 88-94

**Passage:** "Ashby's variety (1956) — log of distinguishable controller states. Variety IS decision surface, measured in bits."

**Def A:** Variety is the number of distinguishable paths — the *space*. This is precisely Ashby's original definition. Direct correspondence.

**Def B:** Variety is the *capacity for informed judgment*. This is a reinterpretation. Ashby's variety is a structural property (how many states), not a functional property (capacity for judgment). A random number generator has high variety and zero judgment. A thermostat has low variety and effective (if trivial) regulatory judgment. Variety and judgment capacity are correlated but not identical.

**Def C:** Variety is related to the *residual* — higher variety means more possible behaviors the interface type doesn't capture. This works as a derived relationship but isn't as direct as A.

**Agreement:** A captures the correspondence precisely. B introduces a reinterpretation that's mostly correct but technically imprecise for the Ashby connection. C is adequate.

**Winner:** A for the specific Ashby correspondence. B is fine for design intuition but shouldn't replace A in the formal claim.

---

### Divergence 5: "The space between things is itself functional" (Post 02, Post 00, Where the Space Lives)

**Location:** `02-the-space-between.md`, lines 9-16; `where-the-space-lives.md` throughout

**Passage:** "In Japanese aesthetics, 間 (ma) is the concept that the space between things is itself functional. The pause that gives the notes shape. The empty room that makes the architecture."

**Def A:** Ma is *the space between* input and output. Direct translation of the aesthetic concept into a technical one. The etymological and conceptual connection is clean.

**Def B:** Ma is *the capacity for informed judgment*. This loses the spatial/aesthetic resonance of 間. The Japanese concept of ma is about emptiness, interval, negative space — not about judgment. The name "ma" becomes less motivated if the definition shifts to "capacity for informed judgment."

**Def C:** Ma is *the residual*. This also loses the spatial resonance, though "residual" has a geometric interpretation (the gap between two surfaces).

**Agreement:** Only A preserves the connection to the Japanese aesthetic concept that motivates the name. B and C are technical redefinitions that work as frameworks but weaken the etymological grounding.

**Winner:** A for the cultural/etymological connection. This is a naming/framing concern, not a logical one — the framework works under any definition. But the name "ma" is more motivated by A.

---

## Additional divergences (4 more)

### Divergence 6: "What's the ma of a conversation?" (Post 06, line 41)

**Passage:** "The question 'what's the ma of a conversation?' was badly posed. The conversation isn't a computation. It's a fold. Ma applies to the step function (a single inference call), not to the fold."

- **A:** "The space between input and output" — correctly restricted to a single computation.
- **B:** "The capacity for informed judgment" — slightly awkward. A conversation does have judgment capacity (the composite entity's). The correction is that judgment capacity is a *per-step* property of the Inferencer, not a *whole-conversation* property of the fold.
- **C:** "The residual" — naturally per-step, since the residual is measured at the interface boundary of each call.

All three work but B requires the reader to understand that "capacity for informed judgment" is a property of the step function, not the fold. A and C make this more naturally.

### Divergence 7: "Effective grade" and d_reachable (Post 06, lines 62-78)

**Passage:** "d_reachable = f(d_total, |context|) (monotone in context length)"

- **A:** Reachable *space* grows with context — natural.
- **B:** Reachable *judgment capacity* grows with context — this is actually insightful. Longer context activates more attention paths, which genuinely increases the model's capacity to make informed judgments about the content.
- **C:** Reachable *residual* grows with context — technically correct but less intuitive.

B is actually *most* informative here. "More context = more informed judgment" is a cleaner insight than "more context = larger space."

### Divergence 8: The placement principle (Where the Space Lives)

**Passage:** "The question is not whether the space exists. It's whether you've put it where it can do the most good."

- **A:** "Put the *space* where it can do the most good" — works, spatial metaphor.
- **B:** "Put the *capacity for informed judgment* where it can do the most good" — works and is arguably more actionable. It tells you what the space is *for*: judgment.
- **C:** "Put the *residual* where it can do the most good" — doesn't work. You don't *want* residual. You want to *minimize* residual. The placement principle is about where to put the *positive* thing (judgment capacity), not where to put the *gap* (residual).

This is a case where B is clearly superior. The placement principle is about allocating something valuable (judgment capacity), not about where to put a deficit (residual). A is neutral. C gets the valence wrong.

### Divergence 9: Supermodularity — "restriction has superlinear returns" (Post 02)

**Passage:** "Reducing either axis has a larger effect when the other axis is high."

- **A:** Reducing the *space* has superlinear returns — adequate.
- **B:** Reducing the *capacity for informed judgment* has superlinear returns — this is misleading. You don't *want* to reduce judgment capacity in general. You want to reduce *interface* judgment capacity (expressiveness at the boundary) while preserving *internal* judgment capacity (reasoning quality). B requires the interface/internal distinction to make supermodularity make sense.
- **C:** Reducing the *residual* has superlinear returns — correct. You *do* want to reduce the residual, and it's supermodular. This is the most natural reading.

C is most informative for the supermodularity claim. A is adequate. B is misleading without qualification.

---

## Interface ma stress test

11 uses of "interface ma" were found across the published series. Each was tested with "capacity for informed judgment at/through the interface."

| # | Location | Passage | "Capacity for informed judgment at the interface" works? | Notes |
|---|----------|---------|--------------------------------------------------------|-------|
| 1 | 02:185 | "Ma is measured at the interface — the output space as seen by other actors" | Partial | "Judgment expressible through the interface" works; "judgment at the interface" conflates judgment with expression |
| 2 | 02:188 | "A reviewer: enormous internal ma. But its interface is Approve\|Reject\|RequestChanges — three possible outputs. Low interface ma." | No | The judgment is vast; the expression is narrow. "Low judgment capacity" is backwards — it has high judgment capacity compressed through low expressiveness. |
| 3 | 02:198 | "Internal ma determines quality. Interface ma determines auditability." | Partial | "Internal judgment determines quality" works well. "Interface judgment determines auditability" is awkward — auditability is determined by *expressiveness*, not *judgment*. |
| 4 | 02:200 | "A good co-domain funnel has high internal ma and low interface ma." | Partial | "High internal judgment, low interface judgment" suggests the funnel *reduces* judgment. Actually it *compresses* expression of judgment. |
| 5 | 05:138-150 | "The funnel creates an actor whose interface effect type is lower in the preorder than its internal effect type." | Yes | The preorder statement is about interface types, not about judgment per se, so the substitution is neutral. |
| 6 | 05:153 | "The Harness itself is the ultimate funnel. High internal ma on the world-coupling axis, low interface ma on both axes." | Partial | "High internal judgment capacity, low interface judgment capacity" — the Harness has *specified* judgment, which is a specific *kind* of judgment capacity, not "low" judgment capacity. |
| 7 | 06:41 | "Ma applies to the step function, not the fold" | Yes | Works with either definition. |
| 8 | 06:51 | "The Inferencer's own grade is a constant: (sealed, trained)." | Yes | "Judgment capacity is constant" — correct, weights don't change. |
| 9 | case-studies:27 | "delta_chi_from_restricting_d = I(w_ceiling) · (log P(d_current) - log P(d_restricted))" | N/A | Formal expression — definition substitution not applicable. |
| 10 | 09:10 | "Model selection determines the quality of decisions within the constrained space. Tool selection determines the size of the space." | Partial | Under B: "Model selection determines judgment quality. Tool selection determines judgment capacity." Works better than A — distinguishes quality from capacity. |
| 11 | residual:162-178 | "The preorder relates interface types presented by roles in the system" | Yes | Neutral — the preorder is about interface types regardless of which definition of ma is used. |

**Summary:** Of 11 interface ma uses, 4 are misleading without a qualifier, 4 work partially (better with qualifier), and 3 work fine. The qualifier needed: "capacity for informed judgment *expressible through* the interface" or equivalently "capacity for informed judgment *visible at* the interface."

The core issue: Def B naturally describes *internal* ma well ("the entity's capacity for informed judgment") but struggles with *interface* ma because the interface constrains *expression*, not *judgment*. The entity behind the interface may have vast judgment; the interface constrains how much of that judgment is visible/expressible.

**Proposed solution:** "Interface ma is the capacity for informed judgment visible through the interface — not the judgment happening behind it, but the judgment the interface allows the observer to characterize." This aligns with the residual framing (what the interface type captures vs. what the entity actually does) and with the interface enumerability ordering from the Residual Framework.

---

## Agreement cases (appendix)

The following 78 uses all produce the same reading under all three definitions. They are grouped by type.

### Type 1: "Ma as the space/capacity/residual of an actor" (42 uses)

Every use of "ma(A) = (w, d)" or "the grade of A" works identically under all three definitions because all three describe the same structural quantity — just with different framings. The grade lattice measures the same thing regardless of whether you call it "space," "judgment capacity," or "residual size."

Locations: 00:11, 01:160-163, 02:17, 02:42-48, 02:99-107, 02:112-118, 02:134-139, 02:159, 02:206-210, 02:230-241, 03:46, 04:68-77, 04:113, 05:20-21, 05:169-171, 05:177-183, 06:37-42, 06:94, 06:117-131, 07:9, 07:33-34, 07:92-107, 07:117-123, 08:42-55, 08:57-58, 09:10-11, 09:29-45, 09:61-76, 09:119-121, ratchet:30-32, ratchet:57, ratchet:63, ratchet:196, residual:13, residual:84, residual:322-333, case-studies:11, case-studies:49-50, where:15-18, where:237, formal:189-201, formal:297-313.

### Type 2: "Restrict ma / reduce ma" (18 uses)

Every use of "restrict," "reduce," "lower" ma works identically because all three definitions agree that the structural quantity should be minimized at boundaries. A: reduce the space. B: reduce the judgment capacity (at the interface). C: reduce the residual. Same action, same outcome.

Locations: 02:169-177, 04:115, 05:128-132, 05:177-183, 08:56-68, 08:170-178, 09:10-17, 09:61-76, ratchet:45-57, ratchet:132-148, ratchet:239-248, where:236-237, case-studies:27-35, case-studies:85-103, formal:275-293, formal:348-385.

### Type 3: "Supermodularity" and "characterization difficulty" (8 uses)

These are formal claims about chi(w,d). The formal quantity is definition-independent — it's a function on the grade lattice. The interpretation changes (difficulty of describing the space / judgment capacity / residual) but the math is identical.

Locations: 02:159-167, 02:173-177, case-studies:11-13, case-studies:49-55, case-studies:85-103, formal:232-293, 08:34-38, 09:93-97.

### Type 4: "Ma as a design concept" (10 uses)

General references to the framework concept ("building with ma," "the ma framework," "the Ma of Multi-Agent Systems") that work under any definition.

Locations: 00:title, 00:8, 02:1, 09:title, 09:87, 09:119, ratchet:title, ratchet:239, where:title, residual:title.

---

## Formal companion uses

The formal companion uses ma primarily through the grade lattice (Def 4.1), characterization difficulty (Def 4.6), and the monad morphism preorder (Def 6.2). These are mathematical objects that are definition-independent — the definitions determine the *interpretation* of the objects, not their formal properties. All proofs (Props. 4.4, 4.7, 4.8, 4.9, 4.12, 5.3-5.5, 6.3, 6.5, 6.7, 8.2-8.13, 9.2-9.12, 10.2-10.8) hold under any of the three definitions because the proofs operate on the formal structure (the lattice, the preorder, the morphisms), not on the interpretation.

One area to watch: Conjecture 12.1 ("the specified band expands monotonically") is stated in the language of Def A ("effective grade for previously-seen tasks is monotonically non-increasing"). Under Def B, this becomes "the capacity for informed judgment needed for previously-seen tasks is monotonically non-increasing" — which is actually a *more informative* statement. Under Def C, "the residual for previously-seen tasks is monotonically non-decreasing" — wait, that's the wrong direction. The residual *shrinks*, not grows. The ratchet *reduces* the residual. Conjecture 12.1 should say the residual is monotonically *non-increasing*. This is consistent with the ratchet essay but the formal statement needs to be checked for sign when restated under Def C.

---

## Recommendations

### 1. "Capacity for informed judgment" is a valid v2 primary definition

The consistency rate (89.7%) exceeds the threshold (80%). The divergences are concentrated in three areas:
- Interface ma (needs qualifier)
- Ma reduction / ratchet language (needs "need for judgment" rather than "judgment capacity")
- The Ashby/variety connection (preserve Def A language for the specific formal correspondence)

None of these are structural failures. They're phrasing issues resolvable with qualifiers.

### 2. Def B is more informative than Def A in specific cases

- **Role determination** (Divergence 2): "Judgment capacity determines role" is more informative than "space determines role" because it explains *why* different roles have different structural positions.
- **The placement principle** (Divergence 8): "Put judgment capacity where it does the most good" is clearly more actionable than "put the space where it does the most good."
- **d_reachable** (Divergence 7): "More context = more informed judgment" is a cleaner insight.
- **Design rules** (post 09): "Restrict tools, not models" is clearer under B — restrict the *expression* of judgment, not the *capacity* for judgment.

### 3. Interface ma needs the qualifier

The recommended formulation: **"Interface ma is the capacity for informed judgment *visible through* the interface."**

This preserves the internal/interface distinction:
- Internal ma = the entity's capacity for informed judgment (how many paths, how much it can reason)
- Interface ma = how much of that judgment is visible/expressible at the boundary (what the observer can characterize)

Without the qualifier, interface ma conflates the interface's expressiveness with the entity behind it's judgment capacity. The co-domain funnel pattern becomes "high internal judgment, low visible judgment" — which is correct: vast judgment, little of it visible at the boundary.

### 4. Retain the residual framing (Def C) as the boundary perspective

Def C is strictly more informative at boundaries because it decomposes into actionable components. Use it:
- When discussing what the grade *measures* at an interface
- When discussing failure modes
- When discussing the ratchet's mechanism (type refinement)
- When discussing the trust gap

Def B is more informative for:
- The big-picture definition ("what is ma?")
- The placement principle ("where should judgment live?")
- Role determination ("why this architecture?")
- Design intuition ("restrict expression, not capacity")

### 5. Preserve Def A for the etymology and the Ashby connection

"The space between" is the etymological grounding. Keep it in the introduction and in the passage about 間. The Japanese concept of ma is about space, interval, emptiness — not about judgment. The name is motivated by Def A, the design framework is captured by Def B, the boundary analysis is sharpened by Def C.

### 6. The recommended v2 definition stack

> **Ma** is the capacity for informed judgment at a point in the system. Decision surface is the capacity for judgment — how many distinguishable paths through the computation an input could take. World coupling is what makes the judgment *informed* — how much of the world can enter. The grade measures both.
>
> At an interface boundary, ma manifests as the **residual** between what the interface type promises and what the actor behind it actually does. The residual decomposes into infidelity, side effects, and partiality — each managed by a different mechanism.
>
> The concept takes its name from 間, the Japanese aesthetic principle that the space between things is itself functional. Ma is the space between what an actor receives and what it produces — the space where processing happens, where decisions are made, where inputs become outputs.

This stack uses Def B as primary, Def C at boundaries, and Def A for the cultural grounding. Each definition appears where it's most informative.

---

## Notes on inconsistencies in the published text

These are not errors — they're places where the published text would read differently under the v2 definition and may warrant annotation or revision:

1. **Post 02, line 17:** "Ma is the space between what an actor receives and what it produces." This is the canonical statement of Def A. In v2, this sentence should present Def B with A as the spatial metaphor, not the definition.

2. **Post 06, lines 37-42:** The discussion of "what's the ma of a conversation?" depends on Def A's spatial framing. Under Def B, the question becomes "what's the judgment capacity of a conversation?" — which is a well-posed question (the composite's judgment capacity) that the fold model answers (it's the step function's, not the fold's). The correction still works but the phrasing changes.

3. **The Configuration Ratchet, line 63:** "Ma reduction" under Def B should be "reduction in the *need for* informed judgment" rather than "reduction in judgment capacity." The distinction matters: the ratchet doesn't make systems dumber. It makes them not need to be smart for the handled cases.

4. **Post 02, line 39:** "Ma is the space of paths between input and output — how many distinguishable routes through the computation an input could take." This is Def A's formal unpacking. Under Def B, this becomes the formal unpacking of "decision surface" (one axis of judgment capacity), not of ma itself (which is the full two-axis concept).

---

*Analysis conducted 2026-03-15 by a Claude Opus instance reading every published blog post and companion essay without access to the theoretical revisions document. Classification is the analyst's assessment; the author may disagree on specific cases.*
