# Ratchet Fuel

*A practitioner's guide to building systems that get smarter with use.*

---

## The series

The [Ma of Multi-Agent Systems](blog/00-intro.md) asked: how do you measure the space between agents? Nine posts of lattice theory later, it produced a structural vocabulary — the grade, the specified band, the computation channel taxonomy, the configuration ratchet.

*Ratchet Fuel* asks the follow-up question: **now what?**

This series is for people who build data platforms, agent systems, and AI-augmented tools. It assumes you either read the Ma or read the cheat sheet and got the gist. It doesn't re-derive the theory. It uses the theory to build things — and reports what happens honestly, including where the theory was wrong.

The central insight: **failures are the most valuable signal your system produces.** Every failed API call, every permission denial, every confused customer, every repeated query that should have been a tool — that's ratchet fuel. The system that captures its failures and crystallizes them into specified infrastructure gets more trustworthy with every interaction. The system that ignores them stays permanently static, regardless of how good the model is.

---

## 0. The Ratchet Review

*What the Ma series built, in one post, for people who weren't going to read nine posts of lattice theory.*

The accessible entry point. Seven takeaways: tools matter more than models, Bash is a portal not a tool, two simple agents aren't simple anymore, the boring orchestrator is the most important part, context management is your biggest lever, the orchestrator can get smarter without getting less predictable, and your system will teach itself to need less AI over time if you let it.

This is a lightly revised version of the existing index.md "Your Agent Is a Different System Than You Think It Is" — updated to incorporate the extensions from this conversation (world decoupling, failure-driven ratchet, snapshot-seal-funnel) and to set up the series arc.

*Previously: [The Ma of Multi-Agent Systems](blog/00-intro.md)*
*Next: Fuel →*

---

## 1. Fuel

*Every failed tool call is a frontier model's full weight manifold producing something a lookup table could have prevented. That's expensive. That's also data.*

Opens with the Fledgling origin story — querying Claude Code logs, discovering that the agent ran `grep -r` a thousand times through Bash. Each one was a computation channel call. Each one was an inference cycle spent on a specified operation. The waste was the signal.

Introduces the failure stream: permission denials, repeated patterns, timeouts, schema mismatches, empty results, support tickets. Each category maps to a specific ratchet action. The failure stream IS the product roadmap — it tells you exactly where the system's configuration doesn't match the task's requirements, categorized by the type of fix needed.

The key reframe: the trust gap (reachable minus expected) isn't only a risk to minimize. It's the learning surface. If reachable exactly equals expected, the system never discovers anything. You need instrumented gap — failures that are cheap, visible, and informative.

Three design variables: how much gap (sandbox configuration), where the gap lives (mode and projection filter), what happens when the gap produces a failure (monitoring and crystallization).

*Next: The Two-Stage Turn →*

---

## 2. The Two-Stage Turn

*You can't skip discovery. But you can make it cheap.*

The ratchet has two stages, and conflating them is the most common mistake.

**Stage 1: Discovery.** Use the computation channel. Observe empirically. The agent runs `Bash("date")` and it works. You observe: returns timestamps, no side effects, terminates. You characterize: this is really a time query. But you can't honestly narrow the type yet — the implementation hasn't changed. `Bash("date")` is still `IO String`. PATH can change, the binary can be replaced, an alias can shadow it.

**Stage 2: Crystallization.** Build a new tool whose implementation *backs* its type commitments. `CurrentTime() : Timestamp` is honest because the implementation calls the system clock directly. You replaced the tool, not the type annotation.

Stage 1 can't be skipped — you need to observe what agents actually do before you know what tools to build. Stage 2 can't be skipped — observing that something works doesn't make it safe. Only crystallization closes the gap.

The practical lesson: every system needs an exploration budget — time and resources where computation channel access is granted, failures are cheap, and the observation layer is running. And every system needs a promotion pipeline — a specified process for turning Stage 1 observations into Stage 2 tools.

Case studies: how UK Biobank went from notebooks to ukbrapR. How All of Us built the four-tier workspace hierarchy. How the Fledgling tool suite emerged from Claude Code logs. Same two-stage turn in each case.

*Next: Where the Failures Live →*

---

## 3. Where the Failures Live

*Read coupling and write coupling are independent controls. The interesting architectures live in the off-diagonal.*

The world decoupling insight. The published Ma framework treats world coupling as one scalar. This post shows it's at least two — and the decomposition enables the most important architectural patterns.

The snapshot-seal-funnel: broad read (capture state), zero persistent write (sealed copy), full computation inside (level 4, no consequences), structured output through the funnel (level 0 at the boundary). The agent gets maximum freedom where consequences are zero and maximum constraint where consequences are real.

The four edge types between sandboxes: access, knowledge, failure visibility, absence. The expensive state is knowledge-without-access — the agent probing boundaries that a specified rule could have prevented.

The debugging mode example: tests are read-only (ground truth), implementation is a sealed snapshot (experimental copy), output is a structured diagnosis (co-domain funnel). The agent can be maximally invasive because nothing persists. The mode boundary prevents the agent from editing tests during implementation (controller modification — level 8 disguised as a bug fix).

The test development / implementation / review mode taxonomy. Each mode is a named projection filter. Mode transitions are graph rewrites. The transition carries structured context — the co-domain funnel at the mode boundary.

*Next: System 3 →*

---

## 4. System 3

*The Harness coordinates. Something else has to control. The controller was hiding in the failure stream all along.*

The System 3 essay, condensed for the practitioner audience.

Beer's VSM has five systems. The Ma series mapped four. System 3 — operational control — was a declared gap. This post fills it with the failure-driven controller.

System 3's three functions: monitoring (the failure stream — free telemetry from the agent doing work), intervention (mode transitions triggered by specified thresholds), and resource bargaining (context budget allocation based on where the work is actually happening).

System 3 star: triggered audit. Not routine inspection (that's System 2 post-hooks). Fires on anomaly detection, sampling, or suspicious sequences. Uses the snapshot-and-compare pattern — capture world state, compare to what the agent thinks the state is, report discrepancies.

The critical property: System 3 stays in the specified band. Monitoring is counters and thresholds. Intervention is if/then rules. Audit is diff/comparison. No trained judgment in the control loop. The people using LLM-backed guardrails are putting System 4 where System 3 should be.

The System 3/4 tension: System 3 wants tighter modes and less waste (exploit). System 4 wants broader access and novel approaches (explore). System 5 (the human) mediates. Tightening is safe to automate. Loosening requires human authorization. The asymmetry is deliberate.

*Next: The Segment Builder →*

---

## 5. The Segment Builder

*Every data platform builds this first. Here's why, and here's what most get wrong.*

The first concrete tool post. `segment(criteria) → entity_set` is the universal pattern. UK Biobank's Cohort Builder, All of Us's Cohort Builder, every B2B analytics platform's audience segmentation — same structural pattern.

The key architectural decision that most implementations miss: the output is a *reference* (segment ID), not raw data. The segment builder is the single enforcement point for access control. Everything downstream accepts the reference. The co-domain funnel means downstream tools never need their own access control logic.

What most get wrong: the segment builder is a data channel (level 1, structured query), but the criteria specification is often freeform — natural language descriptions that an analyst translates to SQL. That's a computation channel at the specification boundary. The ratchet predicts: start with analyst-mediated queries, observe which criteria patterns recur, crystallize the recurrences into structured criteria builders (point-and-click, parameterized templates). Each crystallization drops the specification boundary from computation channel to data channel.

Implementation with DuckDB/MotherDuck. Schema design. Access control integration. Logging for System 3.

*Next: The Classification Engine →*

---

## 6. The Classification Engine

*The highest-value ratchet turn for most organizations is promoting the senior analyst's tribal knowledge to a named, versioned, parameterized definition.*

The second tool post. `classify(entity, signals, definition) → classification_table`. In genomics: phenotype ascertainment. In B2B: ICP scoring, churn prediction, fraud detection.

The insight: every data organization has classification knowledge that lives in someone's head or in an undocumented query. That knowledge is (evolved, broad) — trained judgment navigating complex signals. The classification definition, once specified, is (specified, scoped) — readable, auditable, parameterized. That grade drop is the biggest single improvement most organizations can make.

The validated definition library. The four-tier workspace pattern (tutorials → demonstrations → validated library → community gallery). The promotion pipeline from ad-hoc to validated. Versioning and deprecation.

Case study: All of Us phenotype library. Case study: PheKB (Phenotype Knowledge Base). The pattern generalizes to any domain where classification combines multiple signals.

*Next: Access Control in the Engine →*

---

## 7. Access Control in the Engine

*When access control is a separate review process, you have trained judgment in the regulatory loop. When it's in the engine, it's specified by construction.*

The third tool post, and the most architecturally consequential.

The Partners Biobank insight: consent enforcement at query time, not as a separate gate. The schema doesn't include non-consented data. The query literally can't return it. The access control decision is made once (when the schema is configured) and enforced every time (at query execution) with zero marginal cost.

The spectrum: manual review per request → LLM-based policy → rule engine around the query → access control in the schema. Each step is a ratchet turn. The destination is the bottom row, where the enforcement is specified, instant, auditable, and free.

Concrete implementations: row-level security, column masking, view-based access tiers, aggregation-only views, minimum entity thresholds with small-cell suppression. Each is a specified constraint that replaces a policy review.

SQL as a security boundary. Why SQL works (level 1, total function over schema, decidable) and why Python doesn't (level 4, Rice's theorem, undecidable). The computation channel boundary IS the security boundary. This isn't a convenience — it's a mathematical property.

*Next: Teaching Without Theory →*

---

## 8. Teaching Without Theory

*Don't teach the space. Shape it.*

How to bootstrap an AI agent, a new team member, or an entire organization with the framework's principles — without requiring anyone to read the theory.

The three-layer approach: constraints (always active, non-negotiable sandbox), design principles (applied during decisions), reference (loaded on demand). The constraints encode the theory's conclusions. The failure stream teaches the theory's intuitions. The reference documents are for the rare cases where understanding the "why" matters.

The teaching ratchet: the student works on real tasks with constraints active. Failures against constraints are logged. Patterns emerge. The patterns become additions to constraints or principles. The teaching material improves with use.

Why this works: it's the same structure the framework describes. Specified constraints, observed failures, crystallized into better configuration. The framework is taught through the mechanism it describes.

Practical example: onboarding a Claude Code instance for a new project. The CLAUDE.md layers. The slash commands for reference. The failure stream that refines the CLAUDE.md over time.

Practical example: onboarding a new analyst to a data platform. The access tiers (constraints). The template library (design principles made concrete). The community gallery (reference, loaded by exploring what others did). The support ticket stream that tells you where the onboarding is failing.

*Next: The Organizational Star →*

---

## 9. The Organizational Star

*The framework isn't about AI agents. It's about any system where actors with different capabilities coordinate through a mediating layer.*

The substrate independence post. Applies the full framework — star topology, VSM mapping, ratchet, failure stream — to organizations rather than software.

The data business division as a multi-actor system. Researchers as Principals (they bring the questions). Analysts/bioinformaticians as Inferencers (they translate questions into approaches). The data platform as Executor (query in, result out). The governance and coordination layer as Harness.

The team captain as System 3. Monitoring whether the configuration serves the mission. Intervening when it doesn't. The failure stream at organizational scale: requests that take too long, reviews that are rubber-stamps, collaborations that don't produce reusable artifacts.

The organizational ratchet: every time a bespoke analyst-researcher collaboration produces a reusable tool, the organizational computation channel level drops. The interaction that was natural-language delegation (computation channel) becomes a structured tool selection (data channel). The chi of the collaboration drops from quadratic to linear.

Structured handoff schemas as co-domain funnels at organizational boundaries. Why freeform email between teams is a computation channel. Why structured request templates restore linear coordination cost.

*Next: Ratchet Metrics →*

---

## 10. Ratchet Metrics

*If you can't measure the ratchet, you can't manage it. Here's what to track.*

The final post. Concrete metrics for whether the ratchet is turning, how fast, and whether it's producing value.

**Ratchet velocity:** how many Stage 2 promotions per quarter? Each promotion is a pattern that moved from ad-hoc to specified. Count them.

**Failure stream composition:** what fraction of failures are in each category? A healthy system has most failures in the "repeated pattern" category (ratchet candidates) and few in "permission denial" (misconfigured boundaries). A sick system has many "support ticket" failures (missing tools) and "timeout" failures (wrong architecture).

**Self-service ratio:** what fraction of data access goes through crystallized tools versus ad-hoc queries? This should increase monotonically. If it plateaus, the ratchet has stalled — you're not promoting fast enough or you're not observing the right patterns.

**Trust surface area:** the gap between what the sandbox allows and what agents/users actually do. Should shrink over time as the ratchet tightens boundaries and crystallizes patterns. If it grows, the system is accumulating capability faster than it's accumulating constraints.

**Computation channel fraction:** what fraction of system interactions go through computation channels (level 4+) versus data channels (level 0-2)? The ratchet should push this toward data channels. If it drifts toward computation channels, you're gaining capability without gaining structure.

**Specified band coverage:** what fraction of regulatory decisions are made by specified rules versus trained judgment (human or ML)? Should be near 100% for coordination (System 2), high for control (System 3), and lower for intelligence (System 4). If trained judgment is creeping into coordination, the Harness is leaving the specified band.

Each metric connects to a specific framework concept. Each can be computed from the failure stream log. Each tells you something actionable about whether the system is improving.

---

## Supplementary

**[Coordination Is Not Control](coordination-is-not-control.md)** — The full theoretical treatment of System 3, world decoupling, modes, and the snapshot-seal-funnel pattern. For readers who want the formal argument.

**[Extensions to the Ma Framework](extensions-to-the-ma-framework.md)** — Five refinements to the published Ma series. For readers who want to see where the original framework was extended and why.

---

## Voice and approach

Ratchet Fuel is not the Ma series. Different audience, different register, different goals.

- **Practitioner-first.** Every post starts with a concrete problem and ends with something you can build. Theory is introduced to explain the solution, not for its own sake.
- **Honest about what's tested.** The Ma series is a theoretical framework. Ratchet Fuel is an applied program. When a claim is theoretical, say so. When it's been tested, show the data. When it's speculative, flag it.
- **Show the failures.** The series is about learning from failures. It should model that by reporting what went wrong — tools that didn't work, metrics that were misleading, ratchet turns that produced worse tools than the ad-hoc patterns they replaced.
- **Concrete examples from real systems.** UK Biobank, All of Us, Partners Biobank, Claude Code logs, DuckDB/MotherDuck, Fledgling. Named systems, named tools, reproducible patterns. Not hypotheticals.
- **Each post is self-contained.** A reader should be able to enter at any post and get value. Cross-references earn their place by deepening understanding, not by creating dependencies.
- **Code ships.** Posts that propose tools should include working implementations. The segment builder post should have a DuckDB schema. The classification engine post should have a SQL macro. The access control post should have a row-level security configuration. The reader should be able to run the code after reading the post.
