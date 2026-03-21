# Ratchet Fuel Series Design Spec

*A practitioner series applying the Ma framework to tool building, data platforms, and organizations.*

---

## Overview

Ratchet Fuel is a 11-post series (0-10) for people who build with or work alongside AI agents. It translates the Ma of Multi-Agent Systems framework into practitioner guidance: code that ships, patterns that transfer, metrics that matter. Data platforms are a case study demonstrating generalization, not the primary audience.

The series lives alongside Ma on the same site, with a shared home page and independent entry points. No reading dependency — Ratchet Fuel is self-contained.

---

## Site Restructure

### Current structure
```
index.md              → Ma landing page ("Your Agent Is a Different System...")
series.md             → Ma series toctree
blog/                 → All posts, companions, everything flat
  00-intro.md
  01-the-four-actors.md
  ...
  the-configuration-ratchet.md
  where-the-space-lives.md
  coordination-is-not-control.md
  the-residual-framework.md
  formal-companion.md
  case-studies.md
  reference-tables.md
```

### Target structure
```
blog/
  index.md                    → NEW: Site home linking both series + more
  ma/
    index.md                  → Ma series toctree (moved from root series.md)
    00-intro.md               → Ma posts (moved from blog/)
    01-the-four-actors.md
    02-the-space-between.md
    03-conversations-are-closures.md
    04-raising-and-handling.md
    05-predictability-as-embeddability.md
    06-conversations-are-folds.md
    07-computation-channels.md
    08-the-specified-band.md
    09-building-with-ma.md
    formal-companion.md       → Stays with Ma
    the-residual-framework.md → Stays with Ma
    coordination-is-not-control.md → Stays with Ma (Fuel post 4 condenses it)
    case-studies.md           → Stays with Ma
    reference-tables.md       → Stays with Ma
  fuel/
    index.md                  → Fuel series toctree + summary
    00-ratchet-review.md      → Front door
    01-fuel.md                → Failure stream as product roadmap
    02-the-two-stage-turn.md  → MIGRATED from Ma: the-configuration-ratchet.md
    03-where-the-failures-live.md → MIGRATED from Ma: where-the-space-lives.md
    04-the-failure-driven-controller.md → Condensed from coordination essay
    05-closing-the-channel.md → NEW: build a tool
    06-the-segment-builder.md → NEW: data platform case study 1
    07-the-classification-engine.md → NEW: data platform case study 2
    08-teaching-without-theory.md → NEW: bootstrapping
    09-the-organizational-star.md → NEW: substrate independence
    10-ratchet-metrics.md     → NEW: what to measure
index.md                      → Root redirect or same as blog/index.md
conf.py                       → Updated for new structure
```

### Migration plan

1. Create `blog/ma/` and `blog/fuel/` directories
2. Move all Ma content from `blog/` to `blog/ma/`
3. Update all internal links within Ma posts (relative links stay relative — `02-the-space-between.md` still works within `ma/`)
4. Update cross-series links (Ma → Fuel companions, Fuel → Ma theory)
5. Create `blog/index.md` as site home
6. Move `series.md` content into `blog/ma/index.md`
7. Migrate `the-configuration-ratchet.md` and `where-the-space-lives.md` to `blog/fuel/` (with edits)
8. Update `conf.py` root doc and toctree
9. Update root `index.md` to redirect or serve as the new blog/index.md
10. Leave stubs or redirects at old paths if needed for external links

### Link update strategy

Ma posts reference each other with relative links like `[post 2](02-the-space-between.md)`. Since all Ma posts move together into `blog/ma/`, these links continue to work without changes.

Cross-references to companion essays need updating:
- Ma posts that reference `the-configuration-ratchet.md` or `where-the-space-lives.md` need to point to `../fuel/02-the-two-stage-turn.md` and `../fuel/03-where-the-failures-live.md` respectively
- Or: keep stubs in `blog/ma/` that redirect to the Fuel versions
- **Recommended:** Keep stubs. Less fragile than updating every reference.

---

## Essay Migration Details

### The Configuration Ratchet → Fuel Post 2: The Two-Stage Turn

**Current:** `blog/the-configuration-ratchet.md` — 248 lines, practitioner voice, tells the Fledgling origin story.

**Changes for Fuel:**
- Rename to emphasize the two-stage mechanism (discovery → crystallization)
- Add the type honesty framing from the theoretical revisions (you replace the tool, not the type annotation)
- Add the failure-stream framing ("the ratchet is powered by friction")
- Remove/lighten footnotes that reference the formal companion (Fuel readers won't read it)
- Add cross-reference back to Ma for theory: "For the formal treatment, see [The Ma of Multi-Agent Systems](../ma/00-intro.md)"
- Keep the DuckDB SQL examples — they're the practitioner hook

**Estimated effort:** Light edit. 80% of the text stays.

### Where the Space Lives → Fuel Post 3: Where the Failures Live

**Current:** `blog/where-the-space-lives.md` — 297 lines, already practitioner voice, Taylor/Basho narrative.

**Changes for Fuel:**
- Retitle to emphasize failures/friction rather than abstract "space"
- Add the world decoupling concept from the coordination essay (read coupling vs write coupling as independent controls)
- Add a section connecting the placement principle to failure placement: "Where do you want the failures to happen? In planning (cheap, recoverable) or in execution (expensive, persistent)?"
- The Taylor/Basho narrative stays — it's the best writing in the project
- The kitchen renovation and corporate standards anecdotes stay — they ground the framework in non-technical contexts
- Remove the "suggested updates to existing posts" section (those updates are done)
- Add cross-reference back to Ma

**Estimated effort:** Moderate edit. 60% of the text stays, 40% is new or restructured.

---

## New Posts

### Post 0: The Ratchet Review

**Purpose:** Front door for Ratchet Fuel. Self-contained summary of the Ma framework's practical implications, without the theory.

**Source material:** Current `index.md` ("Your Agent Is a Different System Than You Think It Is") — reworked to point to Fuel instead of Ma, and to set up the ratchet as the organizing concept.

**Key content:**
- The 7 practical rules (already written, from the current landing page)
- "The ratchet" as the organizing concept: your system teaches itself to need less AI over time
- Series map: what each post covers
- Two paths: "Want to build? Keep reading. Want the theory? → [Ma series](../ma/00-intro.md)"

**Voice:** The same voice as the current landing page — direct, practical, slightly irreverent. "You are not going to read nine posts of lattice theory."

**Length:** ~1500 words (similar to current landing page)

### Post 1: Fuel

**Purpose:** Reframe friction as signal. Every failure is data about where your system's configuration doesn't match the task's requirements.

**Key content:**
- The failure stream: permission denials, timeouts, repeated patterns, scope exhaustion
- Each failure category maps to a specific configuration mismatch
- The expensive middle state: knowledge without access, repeated probing, wasted inference
- "Failures are the product roadmap" — each one tells you what to build next
- Concrete: show real Claude Code failure patterns from conversation logs

**Voice:** Direct. "Your agent is failing right now. Here's what the failures are telling you."

**Length:** ~2000 words

**Code ships:** DuckDB queries over Claude Code conversation logs that extract the failure stream

### Post 4: The Failure-Driven Controller

**Purpose:** System 3 for practitioners. How to build the thing that watches the failure stream and acts on it.

**Source material:** Condensed from `blog/ma/coordination-is-not-control.md` — the mode taxonomy, the failure categories, the trigger conditions. Strip the Beer theory, keep the engineering.

**Key content:**
- Four modes: debug, implementation, test development, review
- Mode transitions triggered by failure patterns (not by LLM judgment)
- The counters: repeated pattern count, timeout count, success rate, scope utilization
- When to escalate to the Principal vs when to handle automatically
- "The controller stays specified. If you need trained judgment to decide whether to switch modes, your modes are wrong."

**Voice:** Engineering. "Here's how to build it."

**Length:** ~2500 words

**Code ships:** A prototype mode controller (Python or Claude Code hook)

### Post 5: Closing the Channel

**Purpose:** The hinge post. The reader builds a tool and watches a computation channel close.

**Key content:**
- Pick a real bash pattern (from Fledgling's origin story or from the experiment MCP server)
- Stage 1: Discovery — show the bash pattern in conversation logs, measure frequency, characterize behavior
- Stage 2: Crystallization — build the structured replacement, verify type honesty
- Before/after: show the grade drop, show the trust gap shrink
- "You just turned a Level 4 system into a Level 1 system for this operation. The model didn't get smarter. The infrastructure got more honest."

**Voice:** Tutorial. Walk the reader through it.

**Length:** ~3000 words (longest post — it's a worked example)

**Code ships:** A complete structured tool that replaces a bash pattern. Could be a Fledgling macro, a DuckDB function, or an MCP tool.

### Post 6: The Segment Builder

**Purpose:** First data platform case study. The ratchet applied to data access.

**Key content:**
- A segment builder: users define population segments through structured queries
- The ratchet: common segment patterns get promoted to named, validated definitions
- Stage 1: analysts write SQL (computation channel)
- Stage 2: validated definitions become structured tools (data channel)
- The same two-stage turn, different substrate
- Access control as co-domain funnel: the analyst's full query power compressed through a validated segment interface

**Voice:** Case study. "Here's how this works in a data platform."

**Length:** ~2500 words

**Code ships:** DuckDB implementation of a segment builder with promotion mechanism

### Post 7: The Classification Engine

**Purpose:** Second data platform case study. Access control as architectural pattern.

**Key content:**
- Classification: sensitivity levels on data fields, access tiers on roles
- The ratchet: observed access patterns get crystallized into access policies
- Discovery: log who accesses what, how often, with what justification
- Crystallization: promote observed patterns into declared access rules
- The co-domain funnel: the analyst sees only the fields their role justifies
- "The same pattern that restricts an agent's tool set restricts an analyst's field access. Tool restriction IS access control, viewed from the Ma framework."

**Voice:** Case study with architectural depth.

**Length:** ~2500 words

**Code ships:** DuckDB access control layer with audit logging

### Post 8: Teaching Without Theory

**Purpose:** How to bootstrap agents and teams without explaining the framework.

**Key content:**
- You don't need to teach anyone about lattice theory to use the ratchet
- For agents: CLAUDE.md files, permission configurations, structured tool descriptions — all are ratchet artifacts
- For teams: onboarding docs, code review checklists, architectural decision records — all are ratchet artifacts
- The pattern: observe what works → crystallize it → make it the default
- "The best documentation is the documentation that makes itself unnecessary"

**Voice:** Reflective. "Here's what we've been doing all along."

**Length:** ~2000 words

### Post 9: The Organizational Star

**Purpose:** Substrate independence. The star topology works for people, teams, and companies.

**Source material:** Draws from the substrate independence section added to the coordination essay.

**Key content:**
- A person managing their own productivity (the internal Harness)
- A data team coordinating researchers and analysts (the organizational Harness)
- ADHD as unreliable internal Harness — externalize the extract step
- "The framework isn't about AI. It's about any system where actors with different capabilities coordinate through a mediating layer."

**Voice:** Personal and organizational. The most human post in the series.

**Length:** ~2000 words

### Post 10: Ratchet Metrics

**Purpose:** What to measure, what the numbers mean.

**Key content:**
- The ratchet rate: how fast are computation channels closing?
- The trust gap: measured as specified observer gap rate (from the experimental program)
- The failure stream composition: what proportion of failures are infidelity vs side effects vs partiality?
- The mode utilization: how much time in each mode? Is the system spending too long in debug?
- "The metrics tell you where the ratchet should turn next"
- Connection to the experimental program (link to experiments/)

**Voice:** Metrics-driven. Numbers and interpretation.

**Length:** ~2000 words

**Code ships:** DuckDB dashboard queries for all metrics

---

## Cross-Reference Strategy

### Ma → Fuel

Ma's supplementary materials section lists the migrated essays with a note:

> **[The Two-Stage Turn](../fuel/02-the-two-stage-turn.md)** (in the Ratchet Fuel series) — The practitioner treatment of the configuration ratchet. How to discover patterns and crystallize them into tools.
>
> **[Where the Failures Live](../fuel/03-where-the-failures-live.md)** (in the Ratchet Fuel series) — The placement principle applied to failures and friction.

Ma posts that reference theory developed in Fuel (modes, failure-driven controller) link forward with footnotes:

> "The companion series [Ratchet Fuel](../fuel/index.md) develops the practitioner treatment of these concepts."

### Fuel → Ma

Each Fuel post that has a theoretical foundation links back:

> "For the formal treatment, see [The Space Between](../ma/02-the-space-between.md) in the Ma series."

The Fuel landing page (post 0) offers the path explicitly:

> "Want the theory? [The Ma of Multi-Agent Systems](../ma/00-intro.md) develops the formal framework. Want to build? Keep reading."

---

## Voice

Ratchet Fuel is **not** Ma in simpler language. It's a different kind of writing:

- Ma is **measured, building-from-observation.** "Here's what we noticed. Here's what it means."
- Fuel is **direct, building-from-failure.** "Here's what broke. Here's what we built to fix it."

Ma explains why restriction helps. Fuel shows you which restriction to make next.

Ma cites Ashby and Beer. Fuel cites conversation logs and DuckDB queries.

Ma's unit of progress is the proposition. Fuel's unit of progress is the shipped tool.

Both are honest about limitations. Both value being precise enough to be wrong. The difference is where the precision lives: Ma's precision is formal. Fuel's precision is operational.

---

## Implementation Order

1. **Site restructure** — move files, update links, create new index pages. This is mechanical but high-risk (broken links). Do it first, verify everything builds.
2. **Migrate posts 2 and 3** — edit the configuration ratchet and placement essays for Fuel. Light-to-moderate effort.
3. **Write post 0** — the front door. Sets the tone for the series.
4. **Write post 1** — Fuel. The failure stream concept. Needs real conversation log data.
5. **Write post 4** — The controller. Condense the coordination essay.
6. **Write post 5** — Closing the Channel. The hinge. Needs a worked example with code.
7. **Write posts 6-7** — Data platform case studies. Need DuckDB implementations.
8. **Write posts 8-10** — Generalization posts. Can be written in any order.
9. **Update Ma cross-references** — point Ma's supplementary materials to Fuel.

---

## Success Criteria

- Both series are independently navigable (no reading dependency)
- The site home page clearly presents both paths
- Every Fuel post has code that ships (DuckDB queries, tools, or hooks)
- A reader who reads only Fuel can configure an agent system well
- A reader who reads only Ma can understand the theory completely
- Cross-references connect without creating dependency
- All existing external links to Ma posts continue to work (stubs or redirects)
