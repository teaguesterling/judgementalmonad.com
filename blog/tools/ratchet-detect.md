# ratchet-detect: Find Your Ratchet Candidates

*Your conversation logs contain your next three infrastructure investments. This tool finds them.*

---

## What it does

`ratchet-detect` analyzes your Claude Code conversation logs and produces a report identifying:

- **Repeated bash patterns** — commands the agent runs frequently with high success rates. Each one is a computation channel call that a structured tool could handle. These are your ratchet candidates.
- **Computation channel fraction** — what percentage of your tool calls go through Bash vs structured tools. The ratchet should push this toward structured tools over time.
- **Tool adoption gaps** — where structured tools exist in your environment but the agent still uses Bash for equivalent operations.
- **Failure stream composition** — permission denials, not-found errors, push rejections, timeouts. Each category maps to a specific configuration fix ([Post 1](../fuel/01-fuel) has the full taxonomy).

The tool implements the discovery phase described in [The Two-Stage Turn](../fuel/02-the-two-stage-turn): observe what the agent actually does, identify the patterns worth promoting, then crystallize them into structured tools.

---

## Install

```bash
pip install duckdb
```

No other dependencies. Python 3.10+. The tool lives in the [judgementalmonad.com repository](https://github.com/teaguesterling/judgementalmonad.com) at `tools/ratchet-detect/`.

---

## Quick start

```bash
# Clone the repo (or just grab the tools/ directory)
git clone https://github.com/teaguesterling/judgementalmonad.com.git
cd judgementalmonad.com

# Run against your last 30 days of conversation logs
python tools/ratchet-detect/ratchet_detect.py
```

The tool auto-discovers conversation logs from `~/.claude/projects/` — the default location where Claude Code stores them.

---

## Usage

```bash
# Scan last 30 days (default)
python tools/ratchet-detect/ratchet_detect.py

# Last 7 days only (faster, good for weekly checks)
python tools/ratchet-detect/ratchet_detect.py --since 7

# Filter to a specific project
python tools/ratchet-detect/ratchet_detect.py --project myproject

# Show top 5 candidates instead of default 15
python tools/ratchet-detect/ratchet_detect.py --top 5

# JSON output for programmatic use
python tools/ratchet-detect/ratchet_detect.py --format json

# Custom log location
python tools/ratchet-detect/ratchet_detect.py --root /path/to/logs
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--since DAYS` | 30 | How many days of history to analyze |
| `--project NAME` | all | Filter to project directories matching this string |
| `--top N` | 15 | Number of candidates to show per section |
| `--format` | markdown | Output format: `markdown` or `json` |
| `--root PATH` | `~/.claude/projects` | Conversation logs root directory |

---

## Reading the report

### Computation channel fraction

```
- data: 3,826 calls (71.3%)
- computation: 1,539 calls (28.7%) <-- ratchet target
```

This is the big picture. "Computation" means Bash — arbitrary strings sent to a universal machine. "Data" means structured tool calls — typed parameters, known effects. The ratchet pushes the computation fraction down. Run the report weekly and track the trend.

**Healthy:** Declining computation fraction over weeks.
**Stalling:** Stable or rising computation fraction — new bash patterns are appearing faster than old ones get promoted.

### Ratchet candidates

```
| Command | Category | Calls | Success% | Sessions | Example |
|---------|----------|------:|----------:|--------:|---------|
| git     | git_write| 183   | 95.6%    | 20      | git push |
| grep    | file_search| 54  | 98.1%    | 7       | grep -r ... |
```

These are bash commands ranked by `calls * success_rate`. High frequency + high success = the agent has converged on a pattern that works reliably. That's a ratchet candidate — a computation channel call that should become a structured tool.

**What to do:** Pick the top candidate. Build or adopt a structured tool for it. Deploy it. Run the report again next week. The pattern should drop off the list.

The `category` column groups commands by function (git operations, file search, file read, build tools, etc.). This helps you see which *kind* of operation is consuming the most computation channel budget.

### Tool adoption gaps

```
| Category    | Bash Calls | Structured Calls | Adoption | Status  | Tools |
|-------------|----------:|-----------------:|---------:|---------|-------|
| file_search | 65        | 456              | 87.5%    | ADOPTED | Grep, Glob |
| git_write   | 183       | 0                | 0.0%     | OPEN    | — |
```

This compares bash usage in each category against structured tools the agent actually uses. The tool discovers what's available from your logs — no hardcoded tool names.

Three statuses:

- **ADOPTED** — structured tools handle most of this category. The ratchet has turned.
- **PARTIAL** — structured tools exist but Bash still dominates. The tools may not be discoverable, or the CLAUDE.md may not direct the agent to use them.
- **OPEN** — no structured alternative detected. This is where you should build or adopt tools.

### Failure stream

```
| Category       | Tool | Count | Sessions | Example |
|----------------|------|------:|---------:|---------|
| other          | Bash | 101   | 18       | Exit code 1 |
| push_rejected  | Bash | 19    | 10       | ... |
```

Failures classified by pattern. Each category has a specific fix:

| Category | What it means | What to do |
|----------|--------------|------------|
| `permission_denied` | Agent hitting invisible boundaries | Make constraints visible in CLAUDE.md |
| `not_found` | Agent looking for things that don't exist | Check for stale references in context |
| `push_rejected` | Remote is ahead of local | Use a sync workflow before pushing |
| `timeout` | Wrong tool for the problem size | Add scoped alternatives |
| `command_not_found` | Tool not installed in environment | Fix environment or remove from scope |
| `hook_blocked` | Pre-hook rejected the operation | Check hook configuration |
| `other` | Unclassified (often nonzero exit codes) | Review examples for new categories |

---

## How it works

The tool reads Claude Code's JSONL conversation logs. Each log file contains one JSON object per line — messages with nested content blocks containing tool calls and results.

DuckDB handles the parsing. The JSONL structure is complex (nested arrays of content blocks with different types), but DuckDB's `read_json_auto` with `union_by_name=true` handles it natively. The parsing macros are adapted from [Fledgling](https://github.com/teaguesterling/fledgling)'s conversation analysis.

The analysis queries are in `tools/ratchet-detect/queries/` — each is a standalone SQL file:

| File | What it finds |
|------|--------------|
| `schema.sql` | Defines the parsing macros (content_blocks, tool_calls, tool_results, bash_commands) |
| `repeated_bash.sql` | Bash patterns ranked by frequency * success rate |
| `failure_stream.sql` | Failures classified by error pattern |
| `tool_gaps.sql` | Bash categories compared against detected structured tools |
| `channel_mix.sql` | Computation channel vs data channel breakdown |

You can run any of these independently in the DuckDB CLI for custom analysis.

---

## Weekly workflow

The report is most useful as a weekly habit, not a one-time analysis.

**1. Run the report.** `python tools/ratchet-detect/ratchet_detect.py --since 7`

**2. Check the computation fraction.** Is it declining? If not, why?

**3. Pick one ratchet candidate.** The top bash pattern by frequency * success rate. Build a structured tool, adopt an existing one, or add a CLAUDE.md instruction that directs the agent to use an existing tool.

**4. Check the failure stream.** What's the dominant category this week? Make one configuration change that addresses it.

**5. Run the report again next week.** The candidate you promoted should drop off the list. The failure category you addressed should shrink. If neither happened, you changed the wrong thing.

This is the ratchet's cadence. Not the mechanism — the habit of looking at the numbers and acting on what they say.

---

## Customizing

The queries in `tools/ratchet-detect/queries/` are plain SQL. Common customizations:

**Add bash command categories.** Edit `schema.sql` — the `CASE` statement in `bash_commands()` classifies commands by their leading word. Add new categories for your tool chain.

**Adjust ratchet thresholds.** Edit `repeated_bash.sql` — the `HAVING count(*) >= 3` filter controls the minimum frequency for a pattern to be considered a candidate. Raise it for noisy environments, lower it for quieter ones.

**Add failure classifications.** Edit `failure_stream.sql` — the `CASE` statement classifies errors by pattern matching on the error text. Add patterns for errors specific to your environment.

**Change the tool gap mappings.** Edit `tool_gaps.sql` — the `tool_category_map` CTE maps structured tool names to the bash categories they replace. Adjust for your tool set.

---

*From [Ratchet Fuel](index) — a practitioner series on building systems that get smarter through friction.*
