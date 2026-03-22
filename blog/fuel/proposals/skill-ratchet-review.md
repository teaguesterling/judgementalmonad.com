# Proposed Skill: ratchet-review

*A skill that runs the discovery phase of the ratchet against your own conversation logs — then proposes what to build next.*

---

## What this skill does

When invoked, the agent runs `ratchet-detect` against the current project's conversation logs, reads the report, and proposes specific actions: which bash patterns to promote, which tool adoption gaps to close, which failure categories to address. It's the weekly ratchet review from [Post 10](../10-ratchet-metrics.md) automated into a single command.

The skill is a **System 3 function** — it monitors the system's performance (the failure stream and tool usage patterns) and recommends interventions (promote a pattern, update CLAUDE.md, file an issue for a missing tool). It stays specified: SQL queries produce the data, the agent interprets and proposes, the human decides.

---

## The skill definition

The frontmatter identifies when the skill should be triggered. The `description` field is what Claude Code matches against when deciding whether to invoke the skill.

```yaml
---
name: ratchet-review
description: >
  Use after completing a significant feature, at the end of a work session,
  or when the user asks to review ratchet candidates. Analyzes conversation
  logs for repeated bash patterns, failure stream composition, and tool
  adoption gaps.
---
```

The trigger is deliberately broad — "after completing a significant feature" and "at the end of a work session" and "when the user asks." The ratchet review is most valuable as a habit, not a crisis response. Making it easy to invoke lowers the barrier to the weekly cadence that Post 10 recommends.

---

The overview establishes the core behavior: run the tool, read the output, propose actions.

```markdown
# Ratchet Review

## Overview

Run ratchet-detect against the current project's conversation logs.
Read the report. Propose specific, actionable changes based on
what the data shows.

**Announce at start:** "I'm running a ratchet review against your
conversation logs."

**Core principle:** The data tells you what to build next.
Don't propose changes that aren't grounded in the report.
```

The "don't propose changes that aren't grounded in the report" constraint is important. Without it, the agent will generate plausible-sounding recommendations from its training data rather than from the actual failure stream. The skill's value is that it's data-driven — specified queries over structured logs. The agent's role is interpretation and presentation, not invention.

---

The process section walks through the steps. Each step is concrete and has a clear output.

```markdown
## Process

### Step 1: Run the analysis

Execute ratchet-detect against the current project's conversation logs:

    python tools/ratchet-detect/ratchet_detect.py \
        --project {current_project_name} \
        --since 7 \
        --format json

If ratchet-detect is not available, inform the user and suggest
installing it:

    pip install duckdb
    git clone https://github.com/teaguesterling/judgementalmonad.com
    # tool is at tools/ratchet-detect/ratchet_detect.py

Use --since 7 for weekly reviews, --since 30 for monthly reviews.
```

The `--format json` flag is specified because the agent needs structured data to reason about, not a markdown report designed for human reading. The JSON format lets the agent extract specific numbers (call counts, success rates, adoption percentages) and reference them precisely in its recommendations.

---

```markdown
### Step 2: Analyze ratchet candidates

From the repeated_bash section of the report, identify the top 3
candidates by ratchet score (frequency * success_rate).

For each candidate, answer:

1. **What is the bash pattern?** (the command and its common arguments)
2. **How often does it appear?** (calls per week, across how many sessions)
3. **Does a structured alternative exist?** (check the tool_gaps section)
4. **If yes, why isn't it being adopted?** (missing from CLAUDE.md?
   tool not discoverable? tool doesn't cover the use case?)
5. **If no, what would the structured replacement look like?**
   (tool name, parameters, return type)
```

This step forces the agent to connect the quantitative data (the report) to qualitative analysis (why the pattern persists). The five questions mirror the characterization step from [Post 5: Closing the Channel](../05-closing-the-channel.md) — you can't build the replacement until you understand what the bash pattern actually depends on.

---

```markdown
### Step 3: Analyze the failure stream

From the failure_stream section, identify the dominant failure category.

Map it to the fix from Post 1:

| Category | Fix |
|----------|-----|
| permission_denied | Make constraints visible in CLAUDE.md or adjust sandbox |
| not_found | Check for stale references, update file paths |
| push_rejected | Use sync workflow before pushing |
| timeout | Add scoped alternatives for large operations |
| command_not_found | Fix environment or remove from scope |
| hook_blocked | Review hook configuration |

Propose ONE specific configuration change for the dominant category.
```

The "propose ONE" constraint prevents the agent from generating a laundry list. The ratchet turns one click at a time. One configuration change per review. Measure the shift next week.

---

```markdown
### Step 4: Check tool adoption

From the tool_gaps section, identify any category where:
- Status is "OPEN" (no structured alternative) — these are build candidates
- Status is "PARTIAL" (alternative exists, Bash dominates) — these are
  teaching/discoverability problems

For PARTIAL gaps:
- Check if CLAUDE.md mentions the structured tool
- Check if the tool name is guessable from the bash command
- Propose a CLAUDE.md update that routes the operation through
  the structured tool

For OPEN gaps:
- Assess whether the bash pattern is frequent enough to justify
  building a structured tool (threshold: 50+ calls per month)
- If yes, propose a tool spec (name, parameters, return type, effects)
- If no, note it as a watch candidate
```

The 50-call threshold is a pragmatic heuristic. Below that, the cost of building and maintaining a structured tool may exceed the inference savings. Above it, the math works — each call saved is inference budget freed. The threshold should be tunable per project.

---

```markdown
### Step 5: Propose actions

Present a prioritized list of 1-3 actions. For each:

1. **What to do** (specific, concrete — "add X to CLAUDE.md",
   "build search_definitions() tool", "file issue for jetsam pr review")
2. **Why** (which metric this addresses, with the number from the report)
3. **Expected impact** (which number should change, in which direction)

Format as a numbered list. The user decides which to act on.

Do NOT propose more than 3 actions. The ratchet turns one click at
a time.
```

The three-action limit is the skill's most important constraint. Without it, the agent will generate comprehensive improvement plans. The ratchet doesn't need comprehensive plans. It needs the next thing, informed by the data.

---

```markdown
### Step 6: Update tracking (optional)

If the user approves an action, track it:

- Note the current metric values (baseline)
- Describe the change made
- Set a reminder to re-run the ratchet review next week
  to measure the shift

This closes the loop: measure → change → measure again.
```

Step 6 is optional because not every review leads to immediate action. But when it does, the tracking makes the ratchet visible — you can see whether the change moved the metric. This is the verification step from [Post 10](../10-ratchet-metrics.md): "the failure stream composition should shift. If it doesn't, you changed the wrong thing."

---

## Why this skill matters

The existing superpowers (writing-plans, systematic-debugging, verification-before-completion) operate within a conversation. They improve the current session's work quality. The ratchet-review skill operates *across* conversations — it looks at the accumulated evidence from many sessions and proposes changes to the infrastructure that shapes future sessions.

This is System 3 behavior: monitoring performance across operational cycles and intervening to improve the configuration. The existing superpowers are System 2 behavior: coordinating within a cycle. Both are needed. The ratchet review is what makes the system learn between sessions, not just within them.

---

*From [Ratchet Fuel](../index) — see [Post 10: Ratchet Metrics](../10-ratchet-metrics.md) for the full metric framework and [ratchet-detect](../ratchet-detect) for the tool manual.*
