# Proposed Skill: build-query

*A skill that routes build, test, and log analysis through blq — replacing the second-largest category of raw Bash commands with structured, queryable operations.*

---

## What this skill does

When the agent needs to build, test, or analyze build output, this skill routes the operation through blq (Build Log Query) instead of raw Bash commands. blq captures output into a queryable DuckDB database, making build failures searchable, filterable, and analyzable after the fact — not just scrollable text in a terminal buffer.

The ratchet insight: build output through Bash is write-once, read-never. Build output through blq is write-once, query-many. The same information, but the second version compounds — you can search across runs, find recurring errors, measure build times, and identify patterns that should become fixes.

---

## The skill definition

```yaml
---
name: build-query
description: >
  Use INSTEAD OF raw build, test, and make commands through Bash.
  Route builds and tests through blq MCP tools for captured, queryable
  output. Use blq output/errors/info tools to analyze results instead
  of parsing terminal text.
---
```

The trigger is "INSTEAD OF" — same pattern as git-workflow. The skill intervenes at the decision point.

---

```markdown
# Build and Test via blq

## Overview

NEVER pipe build output or grep test results through Bash. Use blq
to run commands, then query the captured output with blq's tools.

**Core principle:** Build output through Bash is a string you read
once. Build output through blq is data you can query forever.

**Announce at start:** "I'm using blq to run this build/test so
the output is captured and queryable."
```

The "never pipe" instruction addresses a specific anti-pattern: `pytest | tail -20` or `make 2>&1 | grep error`. These are computation channel operations — arbitrary text processing on unstructured output. blq replaces this with `mcp__blq_mcp__run(command="test")` followed by `mcp__blq_mcp__output(tail=20)` or `mcp__blq_mcp__errors()`. Same information, structured access.

This is also specified in the project's CLAUDE.md: "Do NOT use shell pipes or redirects in commands. Instead: run the command, then use `output(run_id=N, tail=20)` to filter."

---

```markdown
## Command Mapping

### Running builds and tests

| Instead of | Use | Notes |
|-----------|-----|-------|
| `pytest` | `mcp__blq_mcp__run(command="test")` | Requires registered command |
| `make test` | `mcp__blq_mcp__run(command="test")` | Register first if needed |
| `make build` | `mcp__blq_mcp__run(command="build")` | Register first if needed |
| `npm test` | `mcp__blq_mcp__run(command="test")` | Register first if needed |

### Registering commands

Before running through blq, check if the command is registered:

    mcp__blq_mcp__commands()

If not, register it:

    mcp__blq_mcp__register_command(
        name="test",
        command="pytest",
        description="Run pytest test suite"
    )
```

Command registration is itself a ratchet turn. The first time you run `pytest` through blq, you register it. Every subsequent run uses the registration. The command name ("test") is a data channel interface — the agent says "run tests," not "execute `pytest -xvs --tb=short` in the project root." The registration encodes the command details.

---

```markdown
### Analyzing results

| Instead of | Use | Notes |
|-----------|-----|-------|
| `pytest 2>&1 \| tail -20` | `mcp__blq_mcp__output(tail=20)` | After running |
| `pytest 2>&1 \| grep FAIL` | `mcp__blq_mcp__output(grep="FAIL")` | Structured grep |
| `echo $?` | `mcp__blq_mcp__status()` | Check exit code |
| Reading error output | `mcp__blq_mcp__errors()` | Extracted errors only |
| Checking specific line | `mcp__blq_mcp__output(lines="45-60")` | Line range access |
| Looking at run history | `mcp__blq_mcp__history()` | All runs with metadata |
| Comparing runs | `mcp__blq_mcp__info(ref="latest")` | Detailed run info |
```

Each row is a computation channel → data channel conversion. `pytest 2>&1 | grep FAIL` is a three-stage pipeline: run an arbitrary program, capture its stdout/stderr into a string, pipe that string through a text filter. `mcp__blq_mcp__output(grep="FAIL")` is a structured query against captured data. Same result, but the second version is inspectable, replayable, and doesn't require the agent to construct a shell pipeline.

---

```markdown
## The capture-then-query pattern

blq's key insight: separate RUNNING from READING.

1. **Run** the command with `mcp__blq_mcp__run()`. Output is captured
   into a DuckDB database.
2. **Query** the captured output with `output()`, `errors()`, `info()`.
   Filter, search, and slice without re-running.

This means:
- You can look at different parts of the output without re-running
- You can search across multiple runs for recurring patterns
- You can compare runs side by side
- Build output survives context compaction — the data is in the
  database, not in the conversation history

The last point matters for long sessions. When context is compacted,
Bash output is lost. blq output persists in the database and can
be re-queried.
```

The persistence point connects to [Post 1's](../01-fuel.md) success rate decay: long conversations lose information as context fills up. Build output in the conversation window is ephemeral — it scrolls out. Build output in blq's database is persistent — it survives compaction and can be re-queried.

This is the snapshot-seal-funnel pattern from [Post 3](../03-where-the-failures-live.md) applied to build output: the run captures the full output (snapshot), the database stores it immutably (seal), and the query tools provide structured access (funnel).

---

```markdown
## When to fall back to Bash

Use Bash for builds only when:
- blq is not available as an MCP tool in this session
- The command is a one-off that doesn't need captured output
  (e.g., `which python`, `node --version`)
- The command requires interactive input

When falling back, note it: "blq is not available, running directly."
```

The escape hatch is minimal. One-off informational commands (`which python`) don't benefit from capture. Everything that produces output worth reading twice should go through blq.

---

## Why this skill matters

Build and test commands are the second-largest Bash category after git. Each `make test` or `pytest` invocation through Bash is a computation channel call that produces unstructured text. The agent then has to parse that text — reading through test output, searching for error messages, counting failures. That parsing is inference budget spent on string processing that a structured tool handles instantly.

blq turns build output from a string into a database. The agent queries for errors instead of grepping text. It checks status instead of parsing exit codes. It compares runs instead of re-running and hoping the output looks different. Each query is a data channel operation — Level 1, structured, bounded.

The same output, but the agent's inference is freed from string parsing to focus on what the errors actually mean and how to fix them.

---

*From [Ratchet Fuel](../index) — see [Post 1: Fuel](../01-fuel.md) for the failure stream concept and [Post 5: Closing the Channel](../05-closing-the-channel.md) for the mechanism.*
