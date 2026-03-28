#!/usr/bin/env bash
# Show experiment run status. Use with: watch -n 30 ./experiments/tools/exp-status.sh

LOGS="/mnt/aux-data/teague/Projects/judgementalmonad.com/experiments/logs"

python3 << 'PYEOF'
import json
from pathlib import Path
from collections import defaultdict

logs = Path("/mnt/aux-data/teague/Projects/judgementalmonad.com/experiments/logs")

conditions = defaultdict(lambda: {"complete": 0, "cost": [], "pass": 0})

for f in sorted(logs.glob("*-conversation.json")):
    name = f.stem.replace("-conversation", "")
    parts = name.split("-condition-")
    if len(parts) != 2: continue
    task_id = parts[0].replace("task-", "")
    cond = parts[1]

    # Determine model
    model = "sonnet"
    if task_id.startswith("haiku-"): model = "haiku"
    elif task_id.startswith("opus-"): model = "opus"

    # Determine logical condition
    if "-N-" in task_id:
        logical = "N"
    elif "-M-" in task_id:
        logical = "M"
    elif "-L-" in task_id:
        logical = "L"
    elif "-K-" in task_id:
        logical = "K"
    elif "-J-" in task_id:
        logical = "J"
    elif "principle" in task_id or "-I-" in task_id:
        logical = "I"
    elif "-E-" in task_id or "factorial-E" in task_id:
        logical = "E"
    elif "-D-" in task_id or "factorial-D" in task_id:
        logical = "D"
    elif "-A-" in task_id and "diag" not in task_id:
        logical = "A"
    else:
        continue  # skip others for clarity

    key = f"{model}/{logical}"

    try:
        with open(f) as fh:
            conv = json.load(fh)
        result = [m for m in conv if m.get("type") == "result"]
        if not result: continue
        cost = result[0].get("total_cost_usd")
        if not cost: continue
        conditions[key]["complete"] += 1
        conditions[key]["cost"].append(cost)
        # Check pass — look in result text AND tool_result blocks
        passed = False
        r = result[0]
        if "48 passed" in str(r.get("result", "")) or "all" in str(r.get("result", "")).lower() and "pass" in str(r.get("result", "")).lower():
            passed = True
        if not passed:
            for m in conv:
                content = m.get("content", m.get("message", {}).get("content", []))
                if not isinstance(content, list): continue
                for block in content:
                    if isinstance(block, dict):
                        text = str(block.get("text", "") or block.get("content", ""))
                        if "48 passed" in text:
                            passed = True
                            break
                if passed: break
        if passed:
            conditions[key]["pass"] += 1
    except:
        pass

# Print
print(f"{'':>14} {'n':>4} {'Pass':>6} {'Mean$':>8} {'Min$':>8} {'Max$':>8}")
print("-" * 52)
for model in ["haiku", "sonnet", "opus"]:
    for cond in ["A", "D", "E", "I"]:
        key = f"{model}/{cond}"
        d = conditions[key]
        n = d["complete"]
        if n == 0:
            print(f"{key:>14} {0:>4}")
            continue
        costs = d["cost"]
        mean = sum(costs)/len(costs)
        prate = d["pass"]/n
        print(f"{key:>14} {n:>4} {prate:>5.0%} ${mean:>7.2f} ${min(costs):>7.2f} ${max(costs):>7.2f}")
    print()

# Active runs
import glob
active = sorted(Path("/tmp").glob("claude-1000/*/tasks/*.output"))
for a in active[-5:]:
    try:
        lines = a.read_text().strip().split("\n")
        last = [l for l in lines if "Starting claude" in l or "Exit code" in l]
        if last:
            print(f"  {last[-1].strip()}")
    except:
        pass
PYEOF
