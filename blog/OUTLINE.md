# The Ma of Multi-Agent Systems — Series Outline v2

## The arc

Observe → Name → Formalize → Dynamize → Regulate

Each post carries enough formalism to be self-contained. The formal companion
provides rigor for readers who want proofs.

---

## 0. The Ma of Multi-Agent Systems (intro)

**File:** `00-intro.md`
**Rewrite of:** `blog/blog-series-intro.md`

The harness moment. Industry context (Fowler, OpenAI, LangChain benchmark).
The gap: practice exists, composition algebra exists (Zhang & Wang MCE),
design theory doesn't. This series proposes one. The observation (four actors,
one axis). Series map.

**Key claims:**
- The harness is the architecture; the model is not the bottleneck
- The field lacks a theory for WHY certain designs work
- Ma (co-domain characterizability) is the single axis that explains actor roles

---

## 1. The Four Actors

**File:** `01-the-four-actors.md`
**Draws from:** `blog/actor-taxonomy.md`, `blog/turn-anatomy.md`,
`blog/the-harness.md`, `blog/formal-framework.md` §16 (worked example)

The concrete, ground-level post. What a conversation actually looks like.
Who participates. What each sees. The star topology. No heavy formalism —
just observation grounded in how systems like Claude Code work.

**Content:**
- The four actors: Principal, Inferencer, Executor, Harness
- What each sees (different projections of the same state)
- The star topology (Harness mediates every message)
- The turn cycle: extract → infer → propose → gate → execute → inject
- Worked example: a file read in Claude Code (trace through all four actors)
- The naming: why "Harness" (connects capability to direction)
- The punchline: the Harness is the most powerful and least understood participant

**Does NOT include:** Ma (that's post 2), formalism (that's the companion),
algebraic effects (that's post 4)

---

## 2. The Space Between

**File:** `02-the-space-between.md`
**Rewrite merging:** `blog/the-space-between.md` + `blog/the-grade-lattice.md`
**Absorbs:** `blog/ma-critique.md` (the evolution from opacity to co-domain)

Ma as a concept → the grade lattice as its formalization. The post that
names and measures the core idea.

**Content:**
- Ma (間): the space between inputs and outputs
- Not unpredictability (SHA), not hidden state (lookup table), not variability (die)
- Three determinants: world coupling, decision surface, interface restriction
- The grade lattice: (w, d) ∈ W × D, two orthogonal axes
- Decision surface formalized: log of distinguishable execution paths
  (Ashby's variety, VC dimension, Montufar linear regions)
- Composition is join: ma(A using B) = (w_A ∨ w_B, d_A ∨ d_B)
- Supermodularity of characterization difficulty → restriction is load-bearing
- The four actors on the grade lattice
- Three formal objects for ma (unified): grade (measure), K-complexity
  (interface projection), monad morphism preorder (comparison)
- The cybernetics connection: Ashby's variety, Good Regulator Theorem

---

## 3. Conversations Are Closures

**File:** `03-conversations-are-closures.md`
**Mostly as-is from:** `blog/conversations-as-closures.md`

The structural correspondence to PL closures. Light editing to align
terminology with the new series order (reader has seen actors + ma).

**Content:**
- Closures: code + environment
- Agent closures: behavior + scope + log
- Static capture (PL) vs monotonically growing capture (agents)
- Scope extrusion (pi-calculus correspondence)
- The conversation as shared heap
- Handoffs as Kleisli composition
- Where the correspondence breaks → motivation for the handler framing

---

## 4. Raising and Handling

**File:** `04-raising-and-handling.md`
**Mostly as-is from:** `blog/raising-and-handling.md`

The algebraic effects reframing. Focused on the handler structure.

**Content:**
- The "two-level structure" problem (object vs meta level fiction)
- The reframing: raising effects vs handling effects
- The mapping to algebraic effects (Plotkin & Pretnar 2009)
- Every "porous boundary" case dissolves
- Refined effect signatures (implementation vs interface types)
- Store comonad extend: what it actually captures (handler's design space)
- The punchline: regulation ≠ prediction (setup for post 5)
- The Conant-Ashby connection: the handler doesn't predict, it handles

---

## 5. Predictability as Embeddability

**File:** `05-predictability-as-embeddability.md`
**Condensed from:** `blog/predictability-as-embeddability.md` (594→~250 lines)

The monad morphism preorder as the formal tool for comparing actors.
What it means for one actor to be "more predictable" than another.

**Content:**
- The monad morphism preorder: M ≤ N iff N can embed M's effects
- Trust flows down the preorder; opacity flows up
- Three conditions for prediction: embeddability + accessibility + tractability
- The open-weights Inferencer: has 1+2, fails 3 (simulation = replication)
- Interface ma vs internal ma: independent levers
- Co-domain funnels: high internal ma → low interface ma (quartermaster,
  auditor, sub-agent boundary)
- The configuration lattice → grade → interface ma causal chain
- Design principles: restrict tools not models; funnels need high-internal
  low-interface

---

## 6. Conversations Are Folds

**File:** `06-conversations-are-folds.md`
**Mostly as-is from:** `blog/conversations-are-folds.md`

The dynamical turn. Static structure (posts 2-5) meets temporal evolution.

**Content:**
- Every inference call is stateless
- The conversation is foldl step initial_state turns
- Context is input, not decision surface (d_reachable vs d_total)
- The composite entity (StateT Conv_State IO)
- Grade as a coupled recurrence: g(n+1) = F(g(n), config(n))
- The Harness as dynamical system controller
- The one-shot join was always the right composition

---

## 7. Computation Channels

**File:** `07-computation-channels.md`
**Mostly as-is from:** `blog/computation-channels.md`

**Content:**
- Data channels vs computation channels
- The 9-level taxonomy (0-8)
- Three phase transitions: mutation, amplification, escape from fold
- The computation level is the derivative of the grade trajectory
- The star topology is an aspiration (breaks at level 6+)
- The sandbox becomes the load-bearing boundary

---

## 8. The Specified Band

**File:** `08-the-specified-band.md`
**Mostly as-is from:** `blog/the-specified-band.md`

**Content:**
- The wrong worry (monitoring erodes characterizability)
- The OS existence proof: (open, specified) is viable
- The specified band across the full world coupling axis
- Layered regulation: constraint, observation, policy
- Capability publishing keeps the Harness specified
- The SELinux coda: constraints must be projected into actor scope
- The Ashby resolution: variety reduction, not variety matching

---

## Formal Companion

**File:** `formal-companion.md`
**Rewrite of:** `blog/formal-framework.md` (1354→~600 lines)

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
