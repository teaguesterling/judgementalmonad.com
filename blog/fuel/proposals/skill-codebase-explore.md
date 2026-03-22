# Proposed Skill: codebase-explore

*A skill that routes code navigation and conversation analysis through Fledgling — replacing grep, find, and cat through Bash with SQL-native structured queries over indexed codebases and conversation history.*

---

## What this skill does

When the agent needs to search code, find definitions, read file sections, or analyze its own conversation history, this skill routes the operation through Fledgling's MCP tools instead of Bash. Fledgling provides DuckDB-backed code navigation (indexed, queryable, structured output) and conversation analysis (tool usage patterns, session history, content search across conversations).

The ratchet has already partially turned here — Claude Code's built-in Grep, Glob, and Read tools handle most file operations. But two gaps remain:

1. **Structural code navigation** — finding definitions, tracing references, understanding code structure. The agent still uses `grep -r "class MyClass"` through Bash when Fledgling's `FindDefinitions` and `CodeStructure` tools provide indexed, structured results.
2. **Conversation analysis** — searching past conversations, understanding tool usage patterns, finding what was discussed in previous sessions. There's no built-in tool for this. The agent either doesn't have this capability or uses raw JSONL parsing through Bash.

---

## The skill definition

```yaml
---
name: codebase-explore
description: >
  Use for code navigation beyond simple text search, and for analyzing
  conversation history. Route structural code queries through Fledgling
  MCP tools instead of grep/find through Bash. Use conversation analysis
  tools to search past sessions and understand tool usage patterns.
---
```

The trigger is narrower than git-workflow or build-query. It targets operations where grep/find are insufficient — structural queries that need indexing. Simple text search is already well-served by Claude Code's built-in Grep tool.

---

```markdown
# Codebase Exploration via Fledgling

## Overview

For code navigation that needs more than text search — finding
definitions, understanding structure, analyzing conversation
history — use Fledgling's MCP tools.

**Core principle:** grep finds strings. Fledgling finds structure.
Use the right tool for the level of query.

Claude Code's built-in Grep, Glob, and Read tools are the right
choice for simple text search and file reading. Fledgling adds
value when you need structural understanding or conversation analysis.
```

The explicit deference to built-in tools is important. The skill shouldn't route ALL code queries through Fledgling — that would be over-promoting. Grep is already a data channel (Level 1). The skill targets the cases where grep isn't enough: structural queries and conversation analysis.

---

```markdown
## When to use Fledgling vs built-in tools

| Need | Use | Why |
|------|-----|-----|
| Find text in files | `Grep` (built-in) | Already Level 1, no shell |
| Find files by name | `Glob` (built-in) | Already Level 1, no shell |
| Read a file | `Read` (built-in) | Already Level 1, no shell |
| Find function/class definitions | `mcp__fledgling__FindDefinitions` | Structural, not text |
| Understand code structure | `mcp__fledgling__CodeStructure` | Indexed analysis |
| Read specific line ranges | `mcp__fledgling__ReadLines` | Precise extraction |
| Search past conversations | `mcp__fledgling__ChatSearch` | Cross-session search |
| View session tool usage | `mcp__fledgling__ChatToolUsage` | Ratchet data |
| Inspect a session in detail | `mcp__fledgling__ChatDetail` | Deep session analysis |
| Run custom SQL over codebase | `mcp__fledgling__query` | Full DuckDB access |
```

This table is the decision framework. Notice the pattern: built-in tools handle Level 1 operations (text search, file read). Fledgling handles Level 2 operations (structural traversal, indexed lookup) and cross-session analysis (conversation history). The skill matches the tool to the computation level of the query.

---

```markdown
## Code navigation

### Finding definitions

Instead of:
    Bash("grep -rn 'def my_function\|class MyClass' ./src")

Use:
    mcp__fledgling__FindDefinitions(name="my_function")
    mcp__fledgling__FindDefinitions(name="MyClass")

FindDefinitions uses sitting_duck's AST-based indexing. It finds
definitions by parsing code structure, not by matching text patterns.
This means:
- It won't match comments or string literals that mention the name
- It knows the difference between a definition and a reference
- It returns structured results (file, line, type of definition)
```

The AST-based indexing is the type honesty argument from [Post 2](../02-the-two-stage-turn.md). `grep -rn "def my_function"` is honestly `IO String` — it finds text patterns that look like definitions but might be comments, docstrings, or variable names. `FindDefinitions` is honestly `Definition[]` — it returns actual definitions because the implementation parses the AST. The type narrowing is backed by the implementation.

---

```markdown
### Understanding code structure

Instead of a sequence of grep/cat/head calls to understand a module:

    Bash("grep -rn 'class ' ./src/mymodule/")
    Bash("grep -rn 'def ' ./src/mymodule/core.py")
    Bash("head -50 ./src/mymodule/__init__.py")

Use:
    mcp__fledgling__CodeStructure(path="src/mymodule")

CodeStructure returns an indexed summary: classes, functions,
imports, and their relationships. One call replaces the
grep-then-read-then-grep exploration loop.
```

The exploration loop — grep to find candidates, cat to read them, grep again to refine — is a computation channel pattern that compounds. Each step requires the agent to interpret text output and decide the next query. `CodeStructure` collapses the loop into a single structured query. The decision surface shifts from "what to grep next" to "what in this structure matters for my task."

---

```markdown
## Conversation analysis

### Searching past sessions

    mcp__fledgling__ChatSearch(query="ratchet detection")

Searches across all conversation sessions for messages containing
the query. Useful for:
- Finding where a decision was made
- Locating previous work on the same topic
- Understanding what was tried before

### Understanding tool usage

    mcp__fledgling__ChatToolUsage(days="7")

Shows which tools were used, how often, across how many sessions.
This IS the ratchet-detect data — the same information that
ratchet-detect analyzes, available directly in conversation.

### Session details

    mcp__fledgling__ChatDetail(session_id="...")

Deep view of a single session: metadata, token costs, per-tool
breakdown. Useful for understanding why a session was expensive
or what went wrong.
```

The conversation analysis tools are unique — no other tool in the agent's standard kit provides cross-session memory. The agent normally has no visibility into what previous instances did. Fledgling's conversation tools break that barrier, providing a specified read-only view of the conversation history. This is the observation layer that the ratchet needs: you can't promote patterns you can't see.

---

```markdown
## Custom SQL for deeper analysis

For anything not covered by the named tools:

    mcp__fledgling__query(sql="
        SELECT tool_name, count(*) as calls
        FROM tool_calls()
        WHERE bash_command LIKE 'git %'
        GROUP BY tool_name
        ORDER BY calls DESC
    ")

This exposes the full DuckDB query layer. The same macros
(tool_calls, tool_results, bash_commands, sessions) that
ratchet-detect uses are available for ad-hoc analysis.

Use this for:
- Custom ratchet-detect queries tailored to your project
- Analyzing specific failure patterns
- Building evidence for tool promotion decisions
```

The custom SQL escape hatch is itself a computation channel — the agent writes arbitrary SQL. But it's a *bounded* computation channel: SQL is Level 1 (total function over known schema), not Level 4 (arbitrary program). The schema is known. The effects are read-only. The output is structured. This is the "SQL as security boundary" argument from [Post 7](../07-the-classification-engine.md) applied to conversation analysis.

---

```markdown
## When to fall back to Bash

Use Bash for code navigation only when:
- Fledgling is not available as an MCP tool in this session
- The query is a simple text search better handled by Grep (built-in)
- The codebase uses a language sitting_duck doesn't index

When falling back, note it: "Fledgling is not available, using
grep directly."
```

---

## Why this skill matters

The code navigation gap is smaller than the git gap — Claude Code's built-in Grep, Glob, and Read tools already handle most file operations at Level 1. But structural navigation and conversation analysis are genuinely unserved by built-in tools. The agent uses multi-step grep-then-read loops (computation channel, Level 4) for something that indexed lookup handles in one call (data channel, Level 2).

The conversation analysis capability is unique and directly feeds the ratchet. An agent that can see its own history — what tools it used, what failed, what patterns recur — can participate in its own ratchet review. It can notice "I've searched for this class definition three times this session using grep" and suggest "should we index this codebase with Fledgling?" The observation layer becomes self-aware.

---

*From [Ratchet Fuel](../index) — see [Post 2: The Two-Stage Turn](../02-the-two-stage-turn.md) for type honesty and [Post 10: Ratchet Metrics](../10-ratchet-metrics.md) for the observation layer.*
