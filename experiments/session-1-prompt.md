# Experiment Session 1: Foundation Setup + Definition Consistency

*Prompt for an agent starting the experimental program for The Ma of Multi-Agent Systems.*

---

## Context

You are beginning the experimental program for The Ma of Multi-Agent Systems, a design theory for multi-agent AI systems. The theory is published at this repo (blog/ directory). Companion essays, seed documents, and experimental designs are in drafts/.

Before doing anything, read:
1. `drafts/note-for-agents.md` — Guidance from a prior instance. Read this first.
2. `drafts/experiment-designs.md` — The full claims inventory and 12 experiment designs
3. `drafts/experiment-statistics.md` — Statistical designs for the controlled experiments
4. `drafts/experiment-setup.md` — Infrastructure requirements

Also read the memory files at:
`~/.claude/projects/-mnt-aux-data-teague-Projects-judgementalmonad-com/memory/`

These contain project status, editorial decisions, voice guidelines, and the reviewer decision log.

---

## This session has three tasks, in order.

### Task 1: Set up failure logging protocol (~15 min)

Create a failure logging protocol file at:
`~/.claude/projects/-mnt-aux-data-teague-Projects-judgementalmonad-com/memory/protocol_failure_logging.md`

Frontmatter:
```yaml
---
name: Failure logging protocol for experiments 4, 9, 10
description: How to log failures during normal work to generate longitudinal data
type: reference
---
```

The protocol should instruct future agents (including yourself in future sessions) to log every conversation failure. Each entry needs:

- **Date and topic** of the conversation
- **Tool call(s)** where the failure manifested (tool name, arguments, result)
- **Expected behavior** vs **actual behavior**
- **Classification** as one of: `infidelity` (output didn't faithfully represent state of affairs — includes hallucination, staleness, confabulation), `side_effect` (world changed outside declared effect signature), `partiality` (actor failed to produce output — timeout, hang, crash), `compound` (multiple modes), or `unclear`
- **Classification reasoning** — why this classification, what made it ambiguous if it was
- **Computation level** of the tools involved (0-8, per the taxonomy in blog post 7)
- **Downstream consequence** — what went wrong because of this failure
- **Ratchet candidate?** — was this a bash pattern used repeatedly that could be promoted to a structured tool?

Include a separate section for **ratchet observations**: when a bash command pattern is used repeatedly and succeeds consistently, log the pattern, its frequency, world dependencies, side effects, and whether it's total (always returns) or partial (can hang). These feed Experiment 10.

After creating the file, update MEMORY.md to include it.

### Task 2: Run Experiment 12 — Definition Consistency Analysis (~2-3 hours)

This is the highest-leverage low-cost experiment. It determines whether the "capacity for informed judgment" definition can serve as the v2 primary definition of ma.

**Read every published blog post and companion essay:**
- `blog/00-intro.md` through `blog/09-building-with-ma.md`
- `blog/formal-companion.md`
- `blog/case-studies.md`
- `blog/the-configuration-ratchet.md`
- `blog/the-residual-framework.md`
- `blog/where-the-space-lives.md`

**Do NOT read** `drafts/theoretical-revisions-march-2026.md` — you need to evaluate the definitions against the published text on their own merits, not with knowledge of the arguments for why one is better.

**For every use of "ma" (間) or the concept of ma** (the space between, the grade, interface ma, internal ma, etc.), record:

1. **Location:** file and line number
2. **Passage:** Brief quote — just enough context (one sentence)
3. **Definition A** ("the space between what an actor receives and what it produces"): What does this passage mean under definition A?
4. **Definition B** ("the capacity for informed judgment at a point in the system"): What does this passage mean under definition B?
5. **Definition C** ("the residual between what an interface type promises and what the actor behind it actually does"): What does this passage mean under definition C?
6. **Agreement:** Do all three definitions produce the same reading? If not, which captures the passage's intent most accurately?
7. **Interface ma check:** If this passage uses "interface ma" specifically — does "capacity for informed judgment visible through the interface" work, or is there a problem?

**Be efficient.** Don't belabor cases where all three obviously agree (most will). Spend your analysis time on:
- Divergent cases (where the definitions produce different readings)
- Interface ma uses (the known risk area)
- Cases where one definition is clearly more informative than the others

**Write results to:** `experiments/experiment-12-results.md`

**Include a summary section at the top with:**
- Total uses of ma found
- Consistency rate (percentage where all three agree)
- Divergence rate (percentage where they differ)
- Interface ma compatibility: does "capacity for informed judgment at/through the interface" work?
- The 5 most interesting divergences, with analysis
- **Recommendation:** Is "capacity for informed judgment" a valid v2 primary definition? What qualifier, if any, does interface ma need?
- **Recommendation:** Is "residual" the right framing for the boundary perspective, or is there something better?

### Task 3: Build the task suite skeleton (~1 hour)

The controlled experiments (3, 6, 11) all need a shared task suite. Start building it.

**Requirements from the statistical designs:**
- 30-50 tasks minimum
- Each task must have two natural phases (understanding/planning, then implementation)
- Planning quality must matter (wrong approach = wasted effort)
- Tasks must have clear correctness criteria (tests pass, code compiles, behavior correct)
- Moderate difficulty (completable in ~30 minutes)
- Tag each task with: `needs-bash` (yes/no), `planning-matters` (how much), `expected-failure-modes`

**Sources for tasks:**
- The repos in this user's project directory (sitting_duck, duck_tails, Fledgling, blq, plinking_duck, duck_hunt, pajama_man, etc.)
- SWE-bench Lite tasks (public, standardized)
- Synthetic tasks designed for specific properties

**For this session, produce:**
1. A task suite file at `experiments/task-suite.md` with:
   - 10-15 concrete tasks drawn from the user's repos (read the repos to find real issues, TODOs, or natural feature additions)
   - 5-10 task templates that can be instantiated against any repo
   - Each task with: description, success criterion, quality criterion, difficulty estimate, tags
2. A note on what additional tasks are needed to reach 30-50

**Do NOT run any tasks yet.** This is design, not execution.

For finding tasks in the user's repos, explore the codebases to identify:
- Open issues or TODOs in the code
- Natural feature additions that would exercise both planning and execution
- Bug-shaped problems where the root cause isn't obvious
- Refactoring opportunities that require understanding the architecture first

---

## Deliverables

By the end of this session:

1. `~/.claude/projects/.../memory/protocol_failure_logging.md` — The failure logging protocol (updated MEMORY.md)
2. `experiments/experiment-12-results.md` — Full definition consistency analysis with summary and recommendations
3. `experiments/task-suite.md` — 15-25 task descriptions with metadata

Commit all three to the repo with a descriptive message.

---

## Notes

- This session is research and infrastructure. No published blog posts should be modified.
- If you encounter something in the published posts that seems wrong or inconsistent, note it in the Experiment 12 results — don't fix it.
- The failure logging protocol will be used by every future session. Make it clear enough that an agent encountering it for the first time knows exactly what to do.
- The task suite will be used across Experiments 3, 6, and 11. Design for reuse.
- If any task takes significantly longer than estimated, stop and note where you are. It's better to produce thorough partial results than rushed complete ones.
