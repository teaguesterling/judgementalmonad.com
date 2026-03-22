# Proposed Skill: git-workflow

*A skill that intercepts git and gh operations and routes them through JetSam — closing the largest open computation channel in most Claude Code installations.*

---

## What this skill does

When the agent is about to use `git` or `gh` through Bash, this skill intervenes: use JetSam's structured tools instead. JetSam provides plan-then-execute semantics — every mutating operation generates a preview plan that the user confirms before execution. The agent gets the same functionality with type-honest interfaces, and the user gets inspectable, confirmable plans instead of raw shell commands.

This is the ratchet turning on the single largest computation channel in the data. In the [ratchet-detect analysis](../ratchet-detect.md), `git` (3,408 calls) and `gh` (1,847 calls) dominate Bash usage while JetSam has <2% adoption. The structured alternative exists. It just isn't being used.

---

## The skill definition

```yaml
---
name: git-workflow
description: >
  Use INSTEAD OF raw git or gh bash commands. Route git operations through
  JetSam MCP tools for plan-then-execute semantics. Triggered proactively
  when the agent is about to use git or gh through Bash.
---
```

The key word is "INSTEAD OF" — this skill doesn't trigger after the fact. It intervenes at the decision point, before the Bash call is made. The description mentions "proactively" because the skill needs to be checked before the agent reaches for `Bash("git ...")`, not after it fails.

---

```markdown
# Git Workflow via JetSam

## Overview

NEVER use Bash for git or gh operations when JetSam tools are available.
JetSam provides structured, plan-then-execute alternatives for every
common git workflow.

**Core principle:** Git through Bash is a Level 4 computation channel.
Git through JetSam is a Level 1 data channel. Use the data channel.
```

The "NEVER" is strong language. It's justified by the numbers: 3,408 bash git calls with 96.6% success means the agent has thoroughly validated these patterns through Stage 1 (discovery). The structured replacement exists and covers the same operations. This isn't speculative promotion — it's adopting an already-built tool.

---

The mapping section is the core of the skill — it tells the agent which JetSam tool replaces which git/gh command. This is the translation table from computation channel to data channel.

```markdown
## Command Mapping

### Git operations

| Instead of | Use | Notes |
|-----------|-----|-------|
| `git status` | `mcp__jetsam__status()` | Returns structured repo state |
| `git diff` | `mcp__jetsam__diff()` | Structured diff output |
| `git log` | `mcp__jetsam__log()` | Structured commit history |
| `git add + git commit` | `mcp__jetsam__save(message=...)` | Returns a plan — confirm() to execute |
| `git add + commit + push` | `mcp__jetsam__ship(message=..., pr=false)` | Plan-then-execute, no PR |
| `git add + commit + push + PR` | `mcp__jetsam__ship(message=...)` | Full pipeline with PR creation |
| `git push` | `mcp__jetsam__sync()` | Handles fetch/merge/push safely |
| `git stash + pull + pop` | `mcp__jetsam__sync()` | Sync handles stash automatically |
| Any other git command | `mcp__jetsam__git(command=...)` | Passthrough for uncommon operations |
```

The `mcp__jetsam__git()` passthrough is the escape hatch — it's still a computation channel, but it signals that the operation is unusual. The common operations go through structured tools. The uncommon ones go through the passthrough. Over time, frequent passthrough patterns become candidates for new JetSam verbs (the ratchet turns again).

---

```markdown
### GitHub operations

| Instead of | Use | Notes |
|-----------|-----|-------|
| `gh pr view` | `mcp__jetsam__pr_view()` | Structured PR details |
| `gh pr list` | `mcp__jetsam__pr_list()` | Structured PR listing |
| `gh pr create` | `mcp__jetsam__ship(message=...)` | Part of the ship pipeline |
| `gh pr checks` | `mcp__jetsam__checks()` | CI status check |
| `gh issue list` | `mcp__jetsam__issues()` | Structured issue listing |
| `gh issue create` | Use Bash with `gh issue create` | Not yet in JetSam — file issue |
| `gh pr review` | Use Bash with `gh pr review` | Not yet in JetSam — file issue |
| `gh pr comment` | Use Bash with `gh pr comment` | Not yet in JetSam — file issue |
| `gh run view/list` | Consider `mcp__blq_mcp__*` tools | CI monitoring may be covered by blq |
```

The "Not yet in JetSam — file issue" entries are honest about gaps. They're also ratchet candidates — if these operations appear frequently in future ratchet-detect reports, they should become JetSam verbs. The skill acknowledges the gap rather than forcing a bad workaround.

---

```markdown
## Plan-then-execute pattern

JetSam's mutating operations (save, ship, sync, finish) return plans,
not results. The pattern is:

1. Call the tool (e.g., `mcp__jetsam__save(message="fix parser bug")`)
2. Read the plan — it shows exactly what will happen (stage, commit, push)
3. Call `mcp__jetsam__confirm(id=plan_id)` to execute
4. Or call `mcp__jetsam__cancel(id=plan_id)` to abort

NEVER skip the confirm step. The plan is the inspectable artifact.
It's what makes the operation a data channel — the user can see
exactly what will happen before it happens.

If a plan includes files you didn't intend, cancel and use the
`files` parameter to scope the staging.
```

The plan-then-execute pattern is type honesty applied to git operations. The plan is a structured artifact with typed fields (`plan_id`, `verb`, `steps`, `warnings`). The user can inspect it. The agent can read it. The confirmation is a binary decision — execute this exact plan, or don't. No ambiguity about what "git push" might do to which branch.

This is [Post 2's](../02-the-two-stage-turn.md) JetSam example in action: three layers of type commitments (planning, execution, recovery), each backed by implementation.

---

```markdown
## When to fall back to Bash

Use Bash for git only when:
- The operation isn't covered by JetSam (e.g., `git rebase -i`,
  `git bisect`)
- JetSam is not available as an MCP tool in this session
- The user explicitly requests raw git commands

When falling back, note it: "JetSam doesn't cover this operation,
using git directly." This makes the gap visible for future ratchet
reviews.
```

The fallback is specified, not silent. Noting the gap makes it show up in conversation logs, which makes it show up in future ratchet-detect reports, which makes it a candidate for a new JetSam verb. The skill feeds the ratchet even when it can't close the channel.

---

## Why this skill matters

The ratchet-detect data shows 3,408 git bash calls and 1,847 gh bash calls — over 5,000 computation channel operations in 30 days. Each one engages the full weight manifold to produce a string that a structured tool could handle.

The tools exist. The adoption doesn't. This skill is the teaching layer ([Post 8](../08-teaching-without-theory.md)) that bridges the gap: it tells the agent what to use instead of Bash for operations where the structured alternative is already built and validated.

This is the cheapest, highest-impact ratchet turn available: no new tools to build, no new infrastructure to deploy. Just a skill that says "use the tool you already have."

---

*From [Ratchet Fuel](../index) — see [Post 5: Closing the Channel](../05-closing-the-channel.md) for the mechanism and [ratchet-detect](../ratchet-detect) for the data.*
