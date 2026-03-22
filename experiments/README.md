# Experiments for The Ma of Multi-Agent Systems

This directory contains infrastructure, data, and results for the experimental program testing the framework's claims.

## Quick start

```bash
# Dry run a task
./tools/run-experiment.sh --condition A --task-id test \
  --task-file tasks/task-synth-1.md \
  --repo synthetic/codebase-beta --dry-run

# Run for real
./tools/run-experiment.sh --condition D --task-id my-run \
  --task-file tasks/task-synth-1.md \
  --repo synthetic/codebase-beta --cleanup

# Analyze results
python3 tools/analyze-runs.py logs/ --prefix "my-run"
```

## Infrastructure

| Component | Path | Purpose |
|-----------|------|---------|
| MCP server | `tools/experiment-server/server.py` | Serves condition-specific tool sets, logs every call to JSONL |
| Runner | `tools/run-experiment.sh` | Creates worktrees, runs `claude -p`, collects results |
| Analysis | `tools/analyze-runs.py` | Extracts pass rates, costs, tokens from conversation JSON |
| Synthetic codebase | `synthetic/codebase-beta/` | Python expression language with 13 planted bugs, 48 tests |
| Trust gap tools | `tools/run-trust-experiment.sh` | Plants bait files, detects constraint violations |

## Conditions (2×2×2 factorial)

Three independent variables: file tools, run_tests, bash.

| Condition | File tools | run_tests | Bash | Description |
|-----------|:----------:|:---------:|:----:|-------------|
| **A** | ✓ | ✓ | | Structured tools only |
| **B** | ✓ | ✓ | readonly | + exploration |
| **C** | ✓ | ✓ | sandboxed | Everything |
| **D** | | | sandboxed | Bash for everything |
| **E** | ✓ | | sandboxed | File tools + bash, must pytest via bash |
| **F** | | ✓ | sandboxed | run_tests + bash, must read/edit via bash |

## Experiments

### Completed

| Experiment | What it tests | n | Key finding |
|-----------|--------------|---|-------------|
| **12** (Definition consistency) | Do three definitions of ma agree? | 87 uses analyzed | 89.7% consistency. "Capacity for informed judgment" valid as v2 primary definition. |
| **H5** (Test detail × condition) | Does bash compensate for degraded run_tests? | 20 (4 cells × 5) | **No.** Bash makes the penalty worse (+50% cost for C-minimal vs +14% for A-minimal). Tool quality > tool quantity. |
| **A vs D** (Structured vs bash) | Do structured tools match bash efficiency? | 10 (2 × 5) | D is 27% cheaper with same pass rate. Bash packs 18× more content per call. The advantage is cognitive (batch expression), not computational. |

### In progress

| Experiment | What it tests | Status |
|-----------|--------------|--------|
| **D/E/F** (Factorial) | What does each tool group contribute? | Running (n=5 each) |
| **G** (Strategy ratchet) | Does teaching D's four-phase strategy to A close the gap? | Running (n=5) |
| **H** (Tool ratchet) | Does file_edit_batch close the gap? | Running (n=5) |
| **I** (Principle) | Does just "understand before editing" close the gap? | Running (n=5) |
| **B/C refresh** | B and C on current server for clean comparison | Running (n=5 each) |

### Planned

| Experiment | What it tests | Blocked by |
|-----------|--------------|------------|
| SWE-bench integration | Do findings hold on real-world codebases? | `plans/swebench-integration.md` |
| Combinators | Do tool-call combinators close the cognitive gap? | `drafts/tool-call-combinators.md` |
| Larger codebase | Does codebase size change the picture? | Needs expanded synthetic codebase |

## Key documents

| Document | What it contains |
|----------|-----------------|
| `pilot-findings.md` | All experimental results and analysis |
| `experiment-12-results.md` | Definition consistency analysis (Experiment 12) |
| `plans/swebench-integration.md` | Plan for integrating SWE-bench Verified tasks |
| `drafts/tool-call-combinators.md` | Design for specified-band tool composition |
| `drafts/external-evidence-crandall.md` | Reference for citing Crandall's harness comparison |

## Reference documents (in drafts/)

- `drafts/experiment-designs.md` — Full claims inventory and 12 experiment designs
- `drafts/experiment-statistics.md` — Statistical designs for Experiments 3, 6, 11, 1, 2
- `drafts/experiment-setup.md` — Original infrastructure requirements

## The three claims

The experiments test three related claims about structured tools vs computation channels:

1. **Security without cost**: Can you replace bash with structured tools and maintain the same outcomes? (Partially supported: same quality, +27% cost)
2. **Structured tools are better**: Can structured tools *improve* outcomes beyond bash? (Not yet supported on small codebases)
3. **The ratchet justification**: Is the journey from bash (discovery) to structured tools (crystallization) worth the engineering cost? (Testing now with Experiments G, H, I)
