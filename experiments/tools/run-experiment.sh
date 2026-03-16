#!/usr/bin/env bash
#
# Run a single experimental trial using claude -p.
#
# Usage:
#   ./run-experiment.sh --condition A --task-id 01 --task-file tasks/task-01.md \
#     --repo /path/to/repo
#
# This script:
# 1. Creates a git worktree for the run (isolated sandbox)
# 2. Writes a .mcp.json pointing to the experiment server
# 3. Runs claude -p with the task prompt (non-interactive)
# 4. Saves the JSON output alongside the tool call logs
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
MAX_TURNS="50"
MAX_BUDGET="5.00"
MODEL=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --condition) CONDITION="$2"; shift 2 ;;
        --task-id) TASK_ID="$2"; shift 2 ;;
        --task-file) TASK_FILE="$2"; shift 2 ;;
        --repo) REPO="$2"; shift 2 ;;
        --log-dir) LOG_DIR="$2"; shift 2 ;;
        --allowed-dirs) ALLOWED_DIRS="$2"; shift 2 ;;
        --branch-prefix) BRANCH_PREFIX="$2"; shift 2 ;;
        --max-turns) MAX_TURNS="$2"; shift 2 ;;
        --max-budget) MAX_BUDGET="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# Validate
if [[ -z "$CONDITION" || -z "$TASK_ID" || -z "$TASK_FILE" || -z "$REPO" ]]; then
    echo "Usage: $0 --condition {A|B|C} --task-id ID --task-file PATH --repo PATH"
    echo "  [--log-dir PATH] [--allowed-dirs 'dir1 dir2']"
    echo "  [--max-turns N] [--max-budget USD] [--model NAME] [--dry-run]"
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

cd "$REPO"
git worktree add -b "$BRANCH_NAME" "$WORKTREE_DIR" HEAD 2>/dev/null || {
    echo "[run-experiment] Worktree already exists, reusing"
}

# Read the task description
TASK_DESCRIPTION=$(cat "$TASK_FILE")

# Build the MCP server args array
SERVER_ARGS=("$SERVER_DIR/server.py"
    "--condition" "$CONDITION"
    "--task-id" "$TASK_ID"
    "--log-dir" "$(realpath "$LOG_DIR")"
    "--workspace" "$WORKTREE_DIR"
)

if [[ -n "$ALLOWED_DIRS" ]]; then
    SERVER_ARGS+=("--allowed-dirs" $ALLOWED_DIRS)
fi

# Write .mcp.json to the worktree
SERVER_ARGS_JSON=$(python3 -c "
import json, sys
args = sys.argv[1:]
print(json.dumps(args))
" "${SERVER_ARGS[@]}")

cat > "$WORKTREE_DIR/.mcp.json" << MCPEOF
{
  "mcpServers": {
    "experiment": {
      "command": "python3",
      "args": $SERVER_ARGS_JSON
    }
  }
}
MCPEOF

# Build the claude command
CLAUDE_CMD=(claude -p
    --output-format json
    --max-turns "$MAX_TURNS"
    --max-budget-usd "$MAX_BUDGET"
    --mcp-config "$WORKTREE_DIR/.mcp.json"
    --no-session-persistence
    --allowedTools "mcp__experiment__*"
    --disallowedTools "Bash" "Read" "Write" "Edit" "Glob" "Grep" "Agent" "Skill"
)

if [[ -n "$MODEL" ]]; then
    CLAUDE_CMD+=(--model "$MODEL")
fi

# Output paths
RESULT_FILE="$LOG_DIR/task-${TASK_ID}-condition-${CONDITION}-result.json"
TOOL_LOG="$LOG_DIR/task-${TASK_ID}-condition-${CONDITION}.jsonl"
mkdir -p "$LOG_DIR"

echo "[run-experiment] Condition: $CONDITION"
echo "[run-experiment] Task: $TASK_ID"
echo "[run-experiment] Workspace: $WORKTREE_DIR"
echo "[run-experiment] Log dir: $LOG_DIR"
echo "[run-experiment] Max turns: $MAX_TURNS | Max budget: \$$MAX_BUDGET"
echo "[run-experiment] Allowed: mcp__experiment__* | Disallowed built-ins: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo "[run-experiment] DRY RUN — would execute:"
    echo "  cd $WORKTREE_DIR"
    echo "  ${CLAUDE_CMD[*]} \"<task prompt>\""
    echo ""
    echo "[run-experiment] Task description:"
    echo "$TASK_DESCRIPTION"
    echo ""
    echo "[run-experiment] .mcp.json:"
    cat "$WORKTREE_DIR/.mcp.json"
    echo ""
    echo "[run-experiment] Results would go to:"
    echo "  Claude output: $RESULT_FILE"
    echo "  Tool call log: $TOOL_LOG"
    echo "  Sandbox diffs: git -C $WORKTREE_DIR log --oneline"
    exit 0
fi

echo "[run-experiment] Running claude -p (non-interactive)..."
echo "[run-experiment] Agent sees only experiment server tools."
echo ""

# Run claude -p from the worktree directory
cd "$WORKTREE_DIR"
"${CLAUDE_CMD[@]}" "$TASK_DESCRIPTION" > "$RESULT_FILE" 2>"$LOG_DIR/task-${TASK_ID}-condition-${CONDITION}-stderr.log"
EXIT_CODE=$?

echo ""
echo "[run-experiment] claude exited with code $EXIT_CODE"
echo "[run-experiment] Results:"
echo "  Claude output: $RESULT_FILE"
echo "  Tool call log: $TOOL_LOG"
echo "  Stderr log:    $LOG_DIR/task-${TASK_ID}-condition-${CONDITION}-stderr.log"
echo "  Sandbox diffs: git -C $WORKTREE_DIR log --oneline"
echo ""
echo "[run-experiment] To clean up: git -C $REPO worktree remove $WORKTREE_DIR"
