# The Ma of Multi-Agent Systems — Series Outline v3

## The arc

Observe → Name → Formalize → Dynamize → Regulate

Each post carries enough formalism to be self-contained. The formal companion
provides rigor for readers who want proofs.

## Voice and approach (established across posts 1-5)

- **Measured, building-from-observation** — not breathless "you already know this!"
- **Honest about limitations** — the formalism marks its own boundaries (IO confession, where correspondences break)
- **Concrete examples ground abstractions** — every formal concept gets a Claude Code / real-system example
- **Cross-references earn their place** — tie back to earlier posts when the callback deepens understanding, not for decoration
- **Interface ≠ implementation** is the recurring thesis — the whole framework is built on this separation
- **Terms of art from the series** — use "permission configuration" not "session type", "permission gates" not "handler pattern matching". PL terms are introduced when the correspondence is being drawn, then translated back to series vocabulary.
- **Bare vs agentic Inferencer** — post 5 established this distinction. A bare Inferencer is (sealed, trained), 3-actor system. An agentic Inferencer has tools, full 4-actor system, grade shifts to (sealed–broad, trained). Use this distinction going forward.
- **IO is under-refined** — acknowledged in post 5. Three things collapsed: what enters (world coupling axis, done), what it can do to the world (observe→modify→generate, post 7), what exits as output (funnels, partially done).

---

## 0. The Ma of Multi-Agent Systems (intro) ✅

**File:** `00-intro.md`
**Rewrite of:** `blog/blog-series-intro.md`
**Status:** Written

Compressed tl;dr of the full framework in ~4 paragraphs. Industry context
(Fowler, OpenAI, LangChain benchmark). Series map linking all 10 posts.
Complements post 1 — post 1 is observation-driven opening, post 0 is
the summary for readers who want the punchline first.

---

## 1. The Four Actors ✅

**File:** `01-the-four-actors.md`
**Status:** Written, reviewed, revised

Observation-driven. Multi-agent scenario → four actors → what nobody sees →
star topology → turn cycle → concrete trace → the measurement question.

**Key decisions made:**
- Opening broadened from "harness engineering" to "what makes a good interaction"
- `Conv_State` introduced by name in Harness definition
- Harness naming absorbed into Harness section (no standalone section)
- Bridge added before trace connecting multi-agent opening to single-agent example
- Closing points at the path-space measurement question, not applied design

---

## 2. The Space Between ✅

**File:** `02-the-space-between.md`
**Status:** Written, reviewed, revised

Names and measures ma. Two axes, composition, supermodularity, predictions.

**Key decisions made:**
- Merged `the-space-between.md` + `the-grade-lattice.md`
- Executor grade: `(sealed–broad, literal–specified)` with "world coupling is whatever the Harness grants" — no "borrowed w" notation
- Temp-0 LLM counterexample: connects to distinguishable paths / exponential depth, not counterfactuals
- "Three formal objects" section → "What the grade captures" — deferred K-complexity and monad morphism preorder to posts where they're earned
- Cybernetics section cleaned: only references grade + interface/internal (no unearned forward refs)
- "At first glance" not "the original formulation" for the one-axis-to-two-axes transition

---

## 3. Conversations Are Closures ✅

**File:** `03-conversations-are-closures.md`
**Status:** Written, reviewed, revised

The PL closure correspondence. Where it's exact, where it breaks, the monadic spectrum.

**Key decisions made:**
- Quartermaster section removed (already in post 2 as funnel example)
- Ma introduction removed (reader has it from post 2)
- Grade vocabulary callback added: "capture list = world coupling, internal logic = decision surface"
- "The handler" → "The Harness" in stuck-agent section, with harness engineering callback
- Monadic spectrum: "context" language throughout, Moggi named only where it matters
- Store comonad introduced as closer model than simple closure (living structure with focus)

---

## 4. Raising and Handling ✅

**File:** `04-raising-and-handling.md`
**Status:** Written, reviewed, revised

Algebraic effects reframing. Handler structure. Regulation ≠ prediction.

**Key decisions made:**
- Entry from post 3's closing ("these are effects — who handles them?")
- Stripped all formal-framework section references
- Continuation claim fixed: Inferencer isn't suspended, Harness simulates continuation through context reconstruction — turns a technical inaccuracy into an interesting observation about how the handler maintains the illusion of continuity
- "Interface IS implementation" claim removed — contradicts the post's own thesis
- "Session type" → "permission configuration" — series vocabulary
- "Connection to existing framework" section cut (formal companion material)
- Effect signatures table references four actors and grade vocabulary, not propositions

---

## 5. Predictability as Embeddability ✅

**File:** `05-predictability-as-embeddability.md`
**Status:** Written, reviewed, revised

The monad morphism preorder. Three conditions. Ocap parallel. Why formalize.

**Key decisions made:**
- Opens with "Why formalize" — addresses the question head-on at the point of maximum formality
- IO confession: honest that IO at top "characterizes by declining to characterize"
- IO refinement: three things collapsed (what enters, what it can do to world, what exits) — teases post 7
- Bare vs agentic Inferencer distinction in both tables
- Ocap parallel (Miller) kept — too good for companion; validates from security theory
- Co-domain funnels deepened from post 2's mention into design principle
- Configuration → Grade → Interface ma causal chain made explicit
- Closing teases the dynamic problem: coupled recurrence, grade can grow over time

---

## 6. Conversations Are Folds ✅

**File:** `06-conversations-are-folds.md`
**Source:** `blog/conversations-are-folds.md`
**Status:** Written, reviewed, revised

The dynamical turn. Static structure (posts 2-5) meets temporal evolution.

**Key decisions made:**
- d_reachable vs d_total distinction: d_total (weights) is constant grade
  component, d_reachable = f(d_total, |context|) grows with context length
- Closure callback: "each step creates a fresh closure over the updated Conv_State"
- StateT Conv_State IO: the composite's type IS the Harness's type (backwards
  from expectation — brain is step function, plumbing is identity)
- IO at bottom is the same under-refined IO from post 5 (honest, not a flaw)
- Coupled recurrence uses d_reachable(n) throughout, not plain d(n)
- Context management identified as single most leveraged Harness operation
  (controls both world coupling AND effective decision surface simultaneously)

---

## 7. Computation Channels ✅

**File:** `07-computation-channels.md`
**Source:** `blog/computation-channels.md`
**Status:** Written, reviewed, revised

The IO refinement that post 5 teased. What the computation can do TO the world.

**Key decisions made:**
- Body covers levels 0-4 inline; full 9-level taxonomy in appendix
- Level 4 expanded with halting-problem discussion and compounding across calls
- "Bounded transducer or universal machine" given plain-language translation
- Finer line within agentic case (not bare vs agentic — both are agentic)
- observe → modify → generate mapped to the taxonomy levels
- Sandbox as dynamics controller (determines which phase transitions reachable)
- Closing reframed from "overwhelmed" to regulatory cost approaching undecidability

---

## 8. The Specified Band ✅

**File:** `08-the-specified-band.md`
**Source:** `blog/the-specified-band.md`
**Status:** Written, reviewed, revised

The resolution. How can the Harness stay characterizable while mediating
actors that can change the world?

**Key decisions made:**
- Removed per-layer grades (sandbox isn't an actor with a grade)
- Grounded "useful ma" as "portion of decision surface spent on proposals
  that could actually succeed"
- Audit vs characterize distinction: auditability is quantitative (how much),
  characterizability is qualitative (is it specified at all?)
- "The loop closes" closing section traces full series arc (posts 1-8)
- SELinux coda: opaque constraints are a tax on system performance
- Ashby resolution: variety reduction + specified observation + capability
  publishing + sandbox backstop

---

## 9. Building With Ma ✅

**File:** `09-building-with-ma.md`
**Status:** Written

The practical "so what." Design rules, multi-agent systems, decision checklist.

**Key decisions made:**
- Six design rules derived from the framework (restrict tools not models,
  computation channel level, sandbox > model config, stay specified, project
  constraints, co-domain funnels)
- Multi-agent section: multiple Inferencers with different tool sets/trajectories,
  sub-agent boundaries as co-domain funnels, agent-to-agent communication routed
  through Harness (capability-based security parallel)
- Decision checklist: computation level → sandbox → tools → scope → interface → specified band
- "What the formalism buys": diagnosis, prediction, transfer
- Closing acknowledges formal companion is forthcoming

---

## Formal Companion

**File:** `formal-companion.md`
**Rewrite of:** `blog/formal-framework.md` (1354→~600 lines)
**Status:** Not yet written

Not a blog post. Pure formal development: definitions, propositions, proofs,
open problems. No narrative. No worked examples (those live in post 1).
No design principles (those live in the posts).

**Structure:**
1. Conversation log, scopes, scope lattice (from §§1-3, tightened)
2. The conversation monad and scoped computation (from §§4-5, 7, rewritten
   over Conv_State from the start — no Writer→State substrate shift)
3. The Store comonad and monad-comonad duality (from §12.1-12.6, focused)
4. The Harness type and configuration lattice (from §12.7-12.8)
5. The grade lattice (from §12.9, with fixes: soften Prop 12.14, note
   Prop 12.15/computation-channel tension)
6. Interface monad ordering and co-domain characterizability (from §11)
7. Interface ma vs internal ma, co-domain funnels (from §13)
8. Session types for permission protocol (from §15.1-15.2)
9. Parallel execution in π-calculus (from §15.3-15.4)
10. Promises and backgrounded tasks (from §15.5-15.6)
11. Unified statement: three formal objects for ma, one causal chain
12. Open problems (from §18 "further work", re-prioritized)
13. References

**Key changes from formal-framework.md:**
- Start from Conv_State, not M* (no substrate shift)
- Soften Prop 10.7 (Harness performs quartermaster's structural function)
- Fix Prop 12.14 (either define f or weaken to a bound)
- Note Prop 12.15 / computation channel tension explicitly
- Unified ma definition connecting all three formal objects
- Drop §§8-9 (quartermaster, continuations — absorbed into posts 3-4)
- Drop §14 (fractal architecture — a remark, not a section)
- Drop §16 (worked example — lives in post 1)
- Drop §17 (design principles — distributed across posts)
- Re-prioritize open problems (coupled recurrence and computation channels
  first, distributive law and mechanical verification later)

---

## Supporting material (linked, not in series)

- `primer.md` — Mathematical Primer (from `blog/primer-kleisli-graded-pi.md`)
- `self-critique.md` — Honest Accounting (from `blog/self-critique-formalisms.md`,
  updated for v2)

## Dropped

- `conversation-dynamics.md` — superseded by posts 6-7
- `scope-transitions.md` — absorbed into formal companion §2
- `the-harness.md` — absorbed into post 1
- `actor-taxonomy.md` — absorbed into post 1
- `turn-anatomy.md` — absorbed into post 1
- `ma-critique.md` — absorbed into post 2
