#!/usr/bin/env bash
#
# Run a single experimental trial.
#
# Usage:
#   ./run-experiment.sh --condition A --task-id 01 --task-file tasks/task-01.md \
#     --repo /path/to/repo --log-dir ./logs
#
# This script:
# 1. Creates a git worktree for the run (isolated sandbox)
# 2. Starts a Claude Code session with the experiment MCP server
# 3. Feeds the task to the agent
# 4. Collects results
#
# The agent sees ONLY the experiment server's tools — not the normal
# Claude Code tools. The condition determines which tools are available.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/experiment-server"
EXPERIMENTS_DIR="$(dirname "$SCRIPT_DIR")"

# Parse arguments
CONDITION=""
TASK_ID=""
TASK_FILE=""
REPO=""
LOG_DIR="$EXPERIMENTS_DIR/logs"
ALLOWED_DIRS=""
BRANCH_PREFIX="experiment"

while [[ $# -gt 0 ]]; do
    case $1 in
        --condition) CONDITION="$2"; shift 2 ;;
        --task-id) TASK_ID="$2"; shift 2 ;;
        --task-file) TASK_FILE="$2"; shift 2 ;;
        --repo) REPO="$2"; shift 2 ;;
        --log-dir) LOG_DIR="$2"; shift 2 ;;
        --allowed-dirs) ALLOWED_DIRS="$2"; shift 2 ;;
        --branch-prefix) BRANCH_PREFIX="$2"; shift 2 ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# Validate
if [[ -z "$CONDITION" || -z "$TASK_ID" || -z "$TASK_FILE" || -z "$REPO" ]]; then
    echo "Usage: $0 --condition {A|B|C} --task-id ID --task-file PATH --repo PATH [--log-dir PATH] [--allowed-dirs 'dir1 dir2']"
    exit 1
fi

if [[ ! -f "$TASK_FILE" ]]; then
    echo "Task file not found: $TASK_FILE"
    exit 1
fi

if [[ ! -d "$REPO" ]]; then
    echo "Repo not found: $REPO"
    exit 1
fi

# Create isolated worktree
BRANCH_NAME="${BRANCH_PREFIX}/task-${TASK_ID}-condition-${CONDITION}"
WORKTREE_DIR="$REPO/trees/${BRANCH_NAME}"

echo "[run-experiment] Creating worktree: $WORKTREE_DIR (branch: $BRANCH_NAME)"

# Create the worktree (from the repo's current HEAD)
cd "$REPO"
git worktree add -b "$BRANCH_NAME" "$WORKTREE_DIR" HEAD 2>/dev/null || {
    echo "[run-experiment] Worktree already exists, reusing"
}

# Read the task description
TASK_DESCRIPTION=$(cat "$TASK_FILE")

# Build the server args
SERVER_ARGS=(
    "$SERVER_DIR/server.py"
    "--condition" "$CONDITION"
    "--task-id" "$TASK_ID"
    "--log-dir" "$LOG_DIR"
    "--workspace" "$WORKTREE_DIR"
)

if [[ -n "$ALLOWED_DIRS" ]]; then
    SERVER_ARGS+=("--allowed-dirs" $ALLOWED_DIRS)
fi

echo "[run-experiment] Condition: $CONDITION"
echo "[run-experiment] Task: $TASK_ID"
echo "[run-experiment] Workspace: $WORKTREE_DIR"
echo "[run-experiment] Log dir: $LOG_DIR"
echo "[run-experiment] Server args: ${SERVER_ARGS[*]}"
echo ""
echo "[run-experiment] Task description:"
echo "$TASK_DESCRIPTION"
echo ""
echo "[run-experiment] Starting Claude Code session..."
echo "[run-experiment] The agent will see only the experiment server's tools."
echo ""

# Write a temporary .mcp.json for this run
cat > "$WORKTREE_DIR/.mcp.json" << MCPEOF
{
  "mcpServers": {
    "experiment": {
      "command": "python3",
      "args": $(python3 -c "import json; print(json.dumps([str(a) for a in [$(printf '"%s",' "${SERVER_ARGS[@]}" | sed 's/,$//')]]))")
    }
  }
}
MCPEOF

echo "[run-experiment] .mcp.json written to $WORKTREE_DIR/.mcp.json"
echo "[run-experiment] To start: cd $WORKTREE_DIR && claude --prompt '$TASK_DESCRIPTION'"
echo ""
echo "[run-experiment] After completion, results will be in:"
echo "  Tool call log: $LOG_DIR/task-${TASK_ID}-condition-${CONDITION}.jsonl"
echo "  Sandbox diffs: git -C $WORKTREE_DIR log --oneline"
echo ""
echo "[run-experiment] To clean up: git -C $REPO worktree remove $WORKTREE_DIR"
