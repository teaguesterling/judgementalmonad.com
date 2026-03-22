# ratchet-detect

Find ratchet candidates in your Claude Code conversation logs.

Analyzes your conversation history to identify bash patterns worth promoting to structured tools — the discovery phase of the [Ratchet Fuel](https://judgementalmonad.com/blog/fuel/) series.

## Install

```bash
pip install duckdb
```

No other dependencies. Python 3.10+.

## Usage

```bash
# Scan last 30 days of conversation logs
python tools/ratchet-detect/ratchet_detect.py

# Last 7 days only
python tools/ratchet-detect/ratchet_detect.py --since 7

# Filter to a specific project
python tools/ratchet-detect/ratchet_detect.py --project myproject

# JSON output for programmatic use
python tools/ratchet-detect/ratchet_detect.py --format json

# Show top 5 candidates
python tools/ratchet-detect/ratchet_detect.py --top 5
```

## What it reports

**Computation channel fraction** — what percentage of your tool calls go through Bash (computation channel) vs structured tools (data channel). The ratchet should push this toward structured tools.

**Ratchet candidates** — bash commands that appear frequently with high success rates. These are the patterns to promote. Each one is a computation channel call that a structured tool could handle.

**Tool adoption gaps** — where structured alternatives exist but the agent still uses Bash. The tool discovers what's available from your logs — no hardcoded tool names. A gap means the ratchet has turned (the tool exists) but the agent hasn't adopted it yet.

**Failure stream** — error categories across all tools. Permission denials, not-found errors, push rejections, hook blocks. Each category maps to a specific configuration fix (see [Post 1: Fuel](https://judgementalmonad.com/blog/fuel/01-fuel)).

## How it works

The tool reads Claude Code's JSONL conversation logs from `~/.claude/projects/`. It uses DuckDB to parse the nested message structure and extract tool calls, results, and errors. The analysis queries are in `queries/` — each is a standalone SQL file you can run independently in `duckdb`.

The JSONL parsing is adapted from [Fledgling](https://github.com/teaguesterling/fledgling)'s conversation analysis macros.

## Customizing

The queries in `queries/` are plain SQL. Edit them to:
- Add new bash command categories
- Change the `replaceable_by` mappings for your tool set
- Adjust thresholds for what counts as a ratchet candidate
- Add new failure classification patterns

## From the series

This tool implements the discovery phase described in:
- [Post 1: Fuel](https://judgementalmonad.com/blog/fuel/01-fuel) — the failure stream taxonomy
- [Post 2: The Two-Stage Turn](https://judgementalmonad.com/blog/fuel/02-the-two-stage-turn) — discovery → crystallization
- [Post 10: Ratchet Metrics](https://judgementalmonad.com/blog/fuel/10-ratchet-metrics) — what to measure
