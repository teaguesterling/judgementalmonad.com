#!/usr/bin/env python3
"""
Analyze experiment runs across conditions.

Extracts full test results from conversation JSON (not truncated JSONL previews),
computes costs, token breakdowns, and pass rates.

Usage:
    python3 analyze-runs.py experiments/logs/ --conditions A D E F
    python3 analyze-runs.py experiments/logs/ --prefix "h5-detailed"
    python3 analyze-runs.py experiments/logs/ --prefix "factorial"
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def extract_run_data(logs_dir: Path, task_id: str, condition: str) -> dict:
    """Extract full data from a single run."""
    prefix = f"task-{task_id}-condition-{condition}"
    conv_file = logs_dir / f"{prefix}-conversation.json"
    tool_file = logs_dir / f"{prefix}.jsonl"
    summary_file = logs_dir / f"{prefix}-summary.json"

    data = {
        "task_id": task_id,
        "condition": condition,
        "exists": False,
    }

    if not conv_file.exists():
        return data
    data["exists"] = True

    # Load conversation
    try:
        with open(conv_file) as f:
            conv = json.load(f)
    except Exception:
        return data

    # Extract result metadata
    result_msgs = [m for m in conv if m.get("type") == "result"]
    if result_msgs:
        r = result_msgs[0]
        data["duration_ms"] = r.get("duration_ms")
        data["num_turns"] = r.get("num_turns")
        data["cost"] = r.get("total_cost_usd")
        data["is_error"] = r.get("is_error", False)

        usage = r.get("usage", {})
        data["input_tokens"] = usage.get("input_tokens", 0)
        data["output_tokens"] = usage.get("output_tokens", 0)
        data["cache_read"] = usage.get("cache_read_input_tokens", 0)
        data["cache_write"] = usage.get("cache_creation_input_tokens", 0)

    # Find ALL test results from the conversation (full text, not truncated)
    test_results = []
    for msg in conv:
        content = msg.get("content", msg.get("message", {}).get("content", []))
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            # Tool results contain the full pytest output
            if block.get("type") == "tool_result":
                text = block.get("content", "")
                if isinstance(text, list):
                    text = " ".join(b.get("text", "") for b in text if isinstance(b, dict))
                if "passed" in text:
                    # Extract the summary line
                    for line in text.split("\n"):
                        if "passed" in line and ("failed" in line or "passed" == line.strip().split()[-1]
                                                  or "in " in line):
                            test_results.append(line.strip())

    data["test_results"] = test_results
    data["all_48_passed"] = any("48 passed" in r for r in test_results)

    # Find final test state
    if test_results:
        data["final_test"] = test_results[-1]
    else:
        data["final_test"] = "no test results found"

    # Load tool calls
    tool_calls = []
    if tool_file.exists():
        with open(tool_file) as f:
            for line in f:
                try:
                    tool_calls.append(json.loads(line))
                except Exception:
                    pass

    data["tool_call_count"] = len(tool_calls)
    data["tool_success_rate"] = (
        sum(1 for c in tool_calls if c.get("success")) / len(tool_calls)
        if tool_calls else None
    )

    # Tool breakdown
    tool_breakdown = defaultdict(int)
    for c in tool_calls:
        tool_breakdown[c["tool"]] += 1
    data["tool_breakdown"] = dict(tool_breakdown)

    # Count bash calls specifically
    data["bash_calls"] = sum(1 for c in tool_calls if "bash" in c["tool"])
    data["run_tests_calls"] = sum(1 for c in tool_calls if c["tool"] == "run_tests")

    return data


def find_runs(logs_dir: Path, prefix: str = None, conditions: list = None):
    """Find all runs matching criteria."""
    runs = defaultdict(list)

    for f in sorted(logs_dir.glob("*-conversation.json")):
        name = f.stem.replace("-conversation", "")
        # Parse: task-{id}-condition-{cond}
        parts = name.split("-condition-")
        if len(parts) != 2:
            continue
        task_id = parts[0].replace("task-", "")
        condition = parts[1]

        if prefix and not task_id.startswith(prefix):
            continue
        if conditions and condition not in conditions:
            continue

        data = extract_run_data(logs_dir, task_id, condition)
        if data["exists"]:
            runs[condition].append(data)

    return runs


def print_comparison(runs: dict):
    """Print a comparison table across conditions."""
    conditions = sorted(runs.keys())

    # Header
    print(f"\n{'':>20}", end="")
    for c in conditions:
        print(f"{'Cond '+c:>12}", end="")
    print()
    print("-" * (20 + 12 * len(conditions)))

    # n
    print(f"{'n':>20}", end="")
    for c in conditions:
        print(f"{len(runs[c]):>12}", end="")
    print()

    # Pass rate
    print(f"{'48/48 pass rate':>20}", end="")
    for c in conditions:
        r = runs[c]
        rate = sum(1 for x in r if x.get("all_48_passed")) / len(r) if r else 0
        print(f"{rate:>11.0%}", end="")
    print()

    # Avg turns
    print(f"{'Avg turns':>20}", end="")
    for c in conditions:
        vals = [x["num_turns"] for x in runs[c] if x.get("num_turns")]
        print(f"{sum(vals)/len(vals):>12.1f}" if vals else f"{'?':>12}", end="")
    print()

    # Avg tool calls
    print(f"{'Avg tool calls':>20}", end="")
    for c in conditions:
        vals = [x["tool_call_count"] for x in runs[c]]
        print(f"{sum(vals)/len(vals):>12.1f}" if vals else f"{'?':>12}", end="")
    print()

    # Avg cost
    print(f"{'Avg cost':>20}", end="")
    for c in conditions:
        vals = [x["cost"] for x in runs[c] if x.get("cost")]
        avg = sum(vals) / len(vals) if vals else 0
        print(f"{'$'+f'{avg:.2f}':>12}" if vals else f"{'?':>12}", end="")
    print()

    # Avg time
    print(f"{'Avg time':>20}", end="")
    for c in conditions:
        vals = [x["duration_ms"] for x in runs[c] if x.get("duration_ms")]
        avg = sum(vals) / len(vals) / 1000 if vals else 0
        print(f"{f'{avg:.0f}s':>12}" if vals else f"{'?':>12}", end="")
    print()

    # Avg output tokens
    print(f"{'Avg output tokens':>20}", end="")
    for c in conditions:
        vals = [x["output_tokens"] for x in runs[c] if x.get("output_tokens")]
        avg = sum(vals) / len(vals) if vals else 0
        print(f"{avg:>12,.0f}" if vals else f"{'?':>12}", end="")
    print()

    # Avg cache read
    print(f"{'Avg cache read':>20}", end="")
    for c in conditions:
        vals = [x["cache_read"] for x in runs[c] if x.get("cache_read")]
        avg = sum(vals) / len(vals) if vals else 0
        print(f"{avg:>12,.0f}" if vals else f"{'?':>12}", end="")
    print()

    # Bash calls
    print(f"{'Avg bash calls':>20}", end="")
    for c in conditions:
        vals = [x["bash_calls"] for x in runs[c]]
        print(f"{sum(vals)/len(vals):>12.1f}" if vals else f"{'?':>12}", end="")
    print()

    # run_tests calls
    print(f"{'Avg run_tests':>20}", end="")
    for c in conditions:
        vals = [x["run_tests_calls"] for x in runs[c]]
        print(f"{sum(vals)/len(vals):>12.1f}" if vals else f"{'?':>12}", end="")
    print()

    # Individual runs
    print("\n\nIndividual runs:")
    for c in conditions:
        print(f"\n  Condition {c}:")
        for r in runs[c]:
            p = "✓" if r.get("all_48_passed") else "✗"
            cost = f"${r['cost']:.2f}" if r.get("cost") else "?"
            turns = r.get("num_turns", "?")
            calls = r.get("tool_call_count", "?")
            dur = f"{r['duration_ms']/1000:.0f}s" if r.get("duration_ms") else "?s"
            test = r.get("final_test", "?")[:60]
            print(f"    {r['task_id']}: {p} {turns:>3} turns, {calls:>3} calls, {dur:>6}, {cost:>7}  [{test}]")


if __name__ == "__main__":
    logs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("experiments/logs")

    # Parse args
    prefix = None
    conditions = None
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--prefix":
            prefix = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--conditions":
            conditions = []
            i += 1
            while i < len(sys.argv) and not sys.argv[i].startswith("--"):
                conditions.append(sys.argv[i])
                i += 1
        else:
            i += 1

    runs = find_runs(logs_dir, prefix=prefix, conditions=conditions)

    if not runs:
        print("No runs found.")
        sys.exit(1)

    print_comparison(runs)
