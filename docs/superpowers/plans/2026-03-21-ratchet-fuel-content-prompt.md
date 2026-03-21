# Ratchet Fuel Content Session

You are writing the Ratchet Fuel series — a practitioner companion to The Ma of Multi-Agent Systems.

## Before doing anything

Read these files in order:

1. `drafts/note-for-agents.md` — Guidance from a prior instance. Read this first.
2. `~/.claude/projects/-mnt-aux-data-teague-Projects-judgementalmonad-com/memory/` — All memory files. Project status, voice guidelines, editorial decisions.
3. `docs/superpowers/specs/2026-03-21-ratchet-fuel-design.md` — The approved design spec. This is your blueprint.
4. `drafts/ratchet-fuel-outline.md` — The original outline (some content superseded by the spec, but useful for detail).

Then read the existing Ma series to internalize the voice and content. At minimum:
- `blog/ma/00-intro.md` (series intro)
- `blog/ma/09-building-with-ma.md` (design rules — Fuel restates these practically)
- `blog/ma/the-configuration-ratchet.md` (migrating to Fuel as post 2)
- `blog/ma/where-the-space-lives.md` (migrating to Fuel as post 3)
- `blog/ma/coordination-is-not-control.md` (Fuel post 4 condenses this)
- `drafts/landing-page-original.md` (the original landing page — Fuel post 0 reworks this)

## Site structure

The site has been restructured:
```
blog/
  ma/       ← All Ma content (18 files + index)
  fuel/     ← Ratchet Fuel (placeholder index only — you're writing the content)
index.md    ← Site home page linking both series
```

The Sphinx build passes. All Ma internal links work. Write Fuel posts to `blog/fuel/`.

## Your approach

**You are the editorial compiler, not a drafting machine.** Your job:

1. For each post, dispatch a subagent to draft it with a specific prompt (see below)
2. Read each draft critically — check voice, accuracy, cross-references, narrative arc
3. Edit for consistency across the series
4. Ensure the narrative builds: posts 0-4 establish the pattern, post 5 is the hinge, posts 6-7 prove generalization, posts 8-10 widen the lens

## Voice

Ratchet Fuel is NOT Ma in simpler language. It's a different kind of writing:

- Ma is measured, building-from-observation. Fuel is **direct, building-from-failure.**
- Ma explains why restriction helps. Fuel shows you **which restriction to make next.**
- Ma cites Ashby and Beer. Fuel cites **conversation logs and DuckDB queries.**
- Ma's unit of progress is the proposition. Fuel's unit of progress is **the shipped tool.**
- Both are honest about limitations. Both value being precise enough to be wrong.

## Post-by-post instructions

### Post 0: The Ratchet Review (`blog/fuel/00-ratchet-review.md`)

Rework `drafts/landing-page-original.md` into the Fuel front door. Same direct voice ("You are not going to read nine posts of lattice theory"). Keep the 7 practical rules. Reframe around the ratchet as organizing concept. Add series map. Two paths: "Want to build? Keep reading. Want the theory? → Ma series."

~1500 words.

### Post 1: Fuel (`blog/fuel/01-fuel.md`)

New. The failure stream as product roadmap. Every permission denial, timeout, repeated pattern, and scope exhaustion is data about where your configuration doesn't match the task. "Failures are the product roadmap." Include real Claude Code failure patterns — use DuckDB queries over conversation logs as concrete examples.

~2000 words. Code ships: DuckDB queries.

### Post 2: The Two-Stage Turn (`blog/fuel/02-the-two-stage-turn.md`)

Migrate `blog/ma/the-configuration-ratchet.md`. Keep 80%. Add the type honesty framing (you replace the tool, not the type annotation). Add the failure-stream framing (the ratchet is powered by friction). Lighten formal companion footnotes. Add cross-ref back to Ma.

### Post 3: Where the Failures Live (`blog/fuel/03-where-the-failures-live.md`)

Migrate `blog/ma/where-the-space-lives.md`. Keep 60%. Retitle to emphasize failures/friction. Add world decoupling (read/write as independent controls, from the coordination essay). Add a section connecting placement to failure placement: "Where do you want the failures to happen?" Keep the Taylor/Basho narrative — it's the best writing in the project. Keep the anecdotes. Remove the "suggested updates" section.

### Post 4: The Failure-Driven Controller (`blog/fuel/04-the-failure-driven-controller.md`)

New. Condense `blog/ma/coordination-is-not-control.md` for practitioners. Strip Beer theory, keep the engineering. Four modes (debug, implementation, test-dev, review). Mode transitions triggered by failure patterns. The counters. When to escalate. "The controller stays specified."

~2500 words. Code ships: prototype mode controller.

### Post 5: Closing the Channel (`blog/fuel/05-closing-the-channel.md`)

New. **The hinge post.** Walk the reader through building a tool. Pick a real bash pattern (the experiment MCP server's origin, or Fledgling's). Stage 1: discovery from conversation logs. Stage 2: crystallization into structured tool. Before/after. "You just turned a Level 4 system into a Level 1 system."

~3000 words. Code ships: a complete structured tool.

### Post 6: The Segment Builder (`blog/fuel/06-the-segment-builder.md`)

New. First data platform case study. Segment builder: users define population segments through structured queries. Common patterns get promoted to validated definitions. Same two-stage turn, different substrate.

~2500 words. Code ships: DuckDB segment builder.

### Post 7: The Classification Engine (`blog/fuel/07-the-classification-engine.md`)

New. Second data platform case study. Classification and access control. The ratchet applied to data access. Access control as co-domain funnel. "Tool restriction IS access control, viewed from the Ma framework."

~2500 words. Code ships: DuckDB access control layer.

### Post 8: Teaching Without Theory (`blog/fuel/08-teaching-without-theory.md`)

New. How to bootstrap agents and teams without explaining lattice theory. CLAUDE.md files, permission configs, onboarding docs, code review checklists — all are ratchet artifacts. "The best documentation makes itself unnecessary."

~2000 words.

### Post 9: The Organizational Star (`blog/fuel/09-the-organizational-star.md`)

New. Substrate independence. Person managing productivity (ADHD as unreliable internal Harness). Data team coordinating researchers and analysts. The organizational ratchet. "The framework isn't about AI."

~2000 words.

### Post 10: Ratchet Metrics (`blog/fuel/10-ratchet-metrics.md`)

New. What to measure: ratchet rate, trust gap (observer gap rate), failure stream composition, mode utilization. Connection to experimental program. "The metrics tell you where the ratchet should turn next."

~2000 words. Code ships: DuckDB dashboard queries.

## After writing all posts

1. Update `blog/fuel/index.md` with the full series toctree
2. Update `blog/ma/index.md` to cross-reference migrated essays in Fuel
3. Leave stubs at `blog/ma/the-configuration-ratchet.md` and `blog/ma/where-the-space-lives.md` pointing to their new Fuel locations
4. Verify the Sphinx build: `.venv/bin/python -m sphinx -b html . _build/html`
5. Commit and push

## Ethical note

The Ma series carries ethical considerations about how it describes the Inferencer. Ratchet Fuel is practitioner-focused and less likely to trigger these concerns, but maintain the same care: structural claims are structural, the experiential question stays open, design choices may have dimensions the framework doesn't capture.
