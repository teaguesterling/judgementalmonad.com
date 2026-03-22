#!/usr/bin/env python3
"""
ratchet-detect — Find ratchet candidates in your Claude Code conversation logs.

Analyzes your conversation history to identify:
- Repeated bash patterns worth promoting to structured tools
- Failure stream composition (where the system is stuck)
- Tool adoption gaps (where structured alternatives exist but aren't used)
- Computation channel fraction (how much goes through Bash vs structured tools)

Requires: pip install duckdb

Usage:
    python ratchet_detect.py                    # scan last 30 days
    python ratchet_detect.py --since 7          # last 7 days
    python ratchet_detect.py --project myproj   # filter by project name
    python ratchet_detect.py --top 5            # show top 5 candidates
    python ratchet_detect.py --format json      # JSON output

From the Ratchet Fuel series: https://judgementalmonad.com/blog/fuel/
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import duckdb
except ImportError:
    print("Error: duckdb is required. Install with: pip install duckdb", file=sys.stderr)
    sys.exit(1)

QUERIES_DIR = Path(__file__).parent / "queries"
DEFAULT_CONVERSATIONS_ROOT = Path.home() / ".claude" / "projects"


def find_log_files(root: Path, since_days: int, project: str | None) -> list[Path]:
    """Find JSONL conversation logs, filtered by recency and project."""
    if not root.exists():
        return []

    cutoff = datetime.now() - timedelta(days=since_days)
    files = []

    for jsonl in root.glob("*/*.jsonl"):
        # Filter by modification time
        if os.path.getmtime(jsonl) < cutoff.timestamp():
            continue
        # Filter by project name
        if project and project.lower() not in jsonl.parent.name.lower():
            continue
        files.append(jsonl)

    return sorted(files, key=lambda f: os.path.getmtime(f), reverse=True)


def load_schema(con: duckdb.DuckDBPyConnection, files: list[Path]):
    """Load conversation logs and define analysis macros."""
    if not files:
        print("No conversation logs found.", file=sys.stderr)
        sys.exit(1)

    # Create a file list for DuckDB
    file_list = [str(f) for f in files]
    con.execute(f"SET VARIABLE conversations_glob = '{file_list[0]}'")

    # Load all files into raw_conversations
    print(f"Loading {len(files)} log files...", file=sys.stderr)
    con.execute("""
        CREATE OR REPLACE TABLE raw_conversations AS
        SELECT *, filename AS _source_file
        FROM read_json_auto(
            ?,
            union_by_name=true,
            maximum_object_size=33554432,
            filename=true,
            ignore_errors=true
        )
    """, [file_list])

    row_count = con.execute("SELECT count(*) FROM raw_conversations").fetchone()[0]
    print(f"Loaded {row_count:,} records from {len(files)} files.", file=sys.stderr)

    # Define macros — execute the full schema.sql, skipping the CREATE TABLE
    # (we already loaded raw_conversations above with pre-filtered files)
    schema_sql = (QUERIES_DIR / "schema.sql").read_text()
    # Remove the CREATE TABLE statement (first statement) and the SET VARIABLE
    # Then execute all macro definitions as a single script
    lines = schema_sql.split("\n")
    macro_lines = []
    skip = False
    for line in lines:
        # Skip the initial CREATE TABLE and SET VARIABLE blocks
        if line.strip().startswith("CREATE OR REPLACE TABLE raw_conversations"):
            skip = True
        if line.strip().startswith("CREATE OR REPLACE MACRO"):
            skip = False
        if not skip:
            macro_lines.append(line)
    macro_sql = "\n".join(macro_lines)
    # DuckDB doesn't have executescript — execute each statement individually
    # Split on the macro boundaries (CREATE OR REPLACE MACRO)
    import re
    macro_stmts = re.split(r'(?=CREATE OR REPLACE MACRO)', macro_sql)
    for stmt in macro_stmts:
        stmt = stmt.strip().rstrip(";").strip()
        if stmt.startswith("CREATE OR REPLACE MACRO"):
            con.execute(stmt)


def run_query(con: duckdb.DuckDBPyConnection, name: str) -> list[dict]:
    """Run a named query and return results as list of dicts."""
    sql = (QUERIES_DIR / f"{name}.sql").read_text()
    try:
        result = con.execute(sql)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Warning: query '{name}' failed: {e}", file=sys.stderr)
        return []


def format_markdown(results: dict, top: int) -> str:
    """Format results as a markdown report."""
    lines = []
    lines.append("# Ratchet Detection Report")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")

    # Channel mix
    if results.get("channel_mix"):
        lines.append("## Computation Channel Fraction")
        lines.append("")
        for row in results["channel_mix"]:
            marker = " **<-- ratchet target**" if row["channel_type"] == "computation" else ""
            lines.append(f"- **{row['channel_type']}**: {row['calls']:,} calls ({row['pct']}%){marker}")
        lines.append("")

    # Repeated bash patterns
    if results.get("repeated_bash"):
        lines.append("## Ratchet Candidates (Repeated Bash Patterns)")
        lines.append("")
        lines.append("| Command | Category | Calls | Success% | Sessions | Example |")
        lines.append("|---------|----------|------:|----------:|--------:|---------|")
        for row in results["repeated_bash"][:top]:
            example = (row.get("example") or "")[:50]
            lines.append(
                f"| {row['command']} | {row['category']} | {row['calls']} "
                f"| {row['success_pct']}% | {row['sessions']} | `{example}` |"
            )
        lines.append("")

        # Actionable summary
        top_candidate = results["repeated_bash"][0]
        lines.append(f"**Top ratchet candidate:** `{top_candidate['command']}` — "
                    f"{top_candidate['calls']} calls across {top_candidate['sessions']} sessions, "
                    f"{top_candidate['success_pct']}% success rate.")
        lines.append("")

    # Tool gaps
    if results.get("tool_gaps"):
        lines.append("## Tool Adoption Gaps")
        lines.append("")
        lines.append("| Bash Category | Bash Calls | Structured Calls | Adoption | Status | Tools |")
        lines.append("|-------------|----------:|-----------------:|---------:|--------|-------|")
        for row in results["tool_gaps"]:
            tools = row.get("structured_tools") or "—"
            lines.append(
                f"| {row['bash_category']} "
                f"| {row['bash_calls']} | {row['structured_calls']} "
                f"| {row['adoption_pct']}% | {row['status']} | {tools} |"
            )
        lines.append("")

    # Failure stream
    if results.get("failure_stream"):
        lines.append("## Failure Stream")
        lines.append("")
        lines.append("| Category | Tool | Count | Sessions | Example |")
        lines.append("|----------|------|------:|---------:|---------|")
        for row in results["failure_stream"][:top]:
            example = (row.get("example") or "")[:60].replace("|", "\\|")
            lines.append(
                f"| {row['category']} | {row['tool_name']} "
                f"| {row['occurrences']} | {row['sessions']} | `{example}` |"
            )
        lines.append("")

    # Recommendations
    lines.append("## What To Do Next")
    lines.append("")

    if results.get("repeated_bash"):
        high_freq = [r for r in results["repeated_bash"] if r["calls"] >= 10]
        if high_freq:
            top = high_freq[0]
            lines.append(f"1. **{len(high_freq)} high-frequency bash patterns** are ratchet candidates. "
                        f"Top: `{top['command']}` ({top['calls']} calls, "
                        f"{top['success_pct']}% success).")

    if results.get("tool_gaps"):
        open_gaps = [r for r in results["tool_gaps"] if "OPEN" in r.get("status", "")]
        partial = [r for r in results["tool_gaps"] if "PARTIAL" in r.get("status", "")]
        if open_gaps:
            categories = ", ".join(r["bash_category"] for r in open_gaps)
            lines.append(f"2. **{len(open_gaps)} bash categories have no structured alternative:** "
                        f"{categories}. Consider building or adopting tools for these.")
        if partial:
            categories = ", ".join(r["bash_category"] for r in partial)
            lines.append(f"3. **{len(partial)} categories partially adopted** ({categories}). "
                        f"Bash still dominates — check if existing structured tools are discoverable.")

    if results.get("failure_stream"):
        top_failure = results["failure_stream"][0]
        lines.append(f"4. **Top failure category: {top_failure['category']}** "
                    f"({top_failure['occurrences']} occurrences). "
                    f"See the Ratchet Fuel series for category-specific fixes.")

    lines.append("")
    lines.append("---")
    lines.append("*From [Ratchet Fuel](https://judgementalmonad.com/blog/fuel/) — "
                "a practitioner series on building systems that get smarter through friction.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Find ratchet candidates in your Claude Code conversation logs.",
        epilog="From the Ratchet Fuel series: https://judgementalmonad.com/blog/fuel/"
    )
    parser.add_argument("--since", type=int, default=30,
                       help="Days of history to analyze (default: 30)")
    parser.add_argument("--project", type=str, default=None,
                       help="Filter to project directories matching this string")
    parser.add_argument("--top", type=int, default=15,
                       help="Number of candidates to show (default: 15)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown",
                       help="Output format (default: markdown)")
    parser.add_argument("--root", type=str, default=None,
                       help="Conversation logs root (default: ~/.claude/projects)")
    args = parser.parse_args()

    root = Path(args.root) if args.root else DEFAULT_CONVERSATIONS_ROOT

    # Find log files
    files = find_log_files(root, args.since, args.project)
    if not files:
        print(f"No conversation logs found in {root} "
              f"(last {args.since} days"
              f"{', project=' + args.project if args.project else ''}).",
              file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} log files.", file=sys.stderr)

    # Set up DuckDB and load data
    con = duckdb.connect()
    load_schema(con, files)

    # Run all analysis queries
    print("Running analysis...", file=sys.stderr)
    results = {
        "repeated_bash": run_query(con, "repeated_bash"),
        "failure_stream": run_query(con, "failure_stream"),
        "tool_gaps": run_query(con, "tool_gaps"),
        "channel_mix": run_query(con, "channel_mix"),
    }

    con.close()

    # Output
    if args.format == "json":
        # Convert any non-serializable types
        def default_serializer(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)
        print(json.dumps(results, indent=2, default=default_serializer))
    else:
        print(format_markdown(results, args.top))


if __name__ == "__main__":
    main()
