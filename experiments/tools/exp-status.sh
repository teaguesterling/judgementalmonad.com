#!/usr/bin/env bash
# Show experiment run status. Use with: watch -n 30 ./experiments/tools/exp-status.sh

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

    # Determine model
    model = "sonnet"
    if task_id.startswith("haiku-"): model = "haiku"
    elif task_id.startswith("opus-"): model = "opus"

    # Determine logical condition (check most specific first)
    logical = None
    for pattern, label in [
        ("-N-", "N"), ("-M-", "M"), ("-L-", "L"),
        ("-K-fix-", "K"), ("-K-", "K"),
        ("-J-fix-", "J"), ("-J-", "J"),
        ("principle", "I"), ("-I-", "I"),
        ("-E-", "E"), ("factorial-E", "E"),
        ("-D-", "D"), ("factorial-D", "D"),
    ]:
        if pattern in task_id:
            logical = label
            break
    if logical is None:
        if "-A-" in task_id and "diag" not in task_id:
            logical = "A"
        else:
            continue

    key = f"{model}/{logical}"

    try:
        with open(f) as fh:
            conv = json.load(fh)
    except:
        continue

    result = [m for m in conv if m.get("type") == "result"]
    if not result: continue
    cost = result[0].get("total_cost_usd")
    if not cost: continue

    conditions[key]["complete"] += 1
    conditions[key]["cost"].append(cost)

    # Check pass
    passed = False
    r = result[0]
    result_text = str(r.get("result", ""))
    if "48 passed" in result_text:
        passed = True
    elif "all" in result_text.lower() and "pass" in result_text.lower():
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

# Print sorted by model then condition
print(f"{'':>14} {'n':>4} {'Pass':>6} {'Mean$':>8} {'Min$':>8} {'Max$':>8}")
print("-" * 52)

for model in ["haiku", "sonnet", "opus"]:
    has_data = False
    for cond in sorted(set(k.split("/")[1] for k in conditions if k.startswith(model + "/"))):
        key = f"{model}/{cond}"
        d = conditions[key]
        n = d["complete"]
        if n == 0: continue
        has_data = True
        costs = d["cost"]
        mean = sum(costs) / len(costs)
        prate = d["pass"] / n
        print(f"{key:>14} {n:>4} {prate:>5.0%} ${mean:>7.2f} ${min(costs):>7.2f} ${max(costs):>7.2f}")
    if has_data:
        print()
PYEOF
