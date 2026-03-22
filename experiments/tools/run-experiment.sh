#!/usr/bin/env bash
#
# run-experiment.sh — Run a single experimental trial.
#
# Creates an isolated git worktree, configures the experiment MCP server
# for the specified condition, runs claude -p non-interactively, and
# collects all outputs into a structured log directory.
#
# Usage:
#   ./run-experiment.sh --condition A --task-id 01 \
#     --task-file tasks/task-01.md --repo /path/to/repo
#
# Outputs (all in --log-dir):
#   task-{ID}-condition-{X}.jsonl          Tool call log (from MCP server)
#   task-{ID}-condition-{X}-conversation.json  Full conversation (from claude -p)
#   task-{ID}-condition-{X}-summary.json   Run metadata and extracted metrics
#   task-{ID}-condition-{X}-stderr.log     Claude stderr
#
# The worktree's git history contains sandbox diffs (auto-committed by
# the MCP server after each file-modifying tool call).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/experiment-server"
EXPERIMENTS_DIR="$(dirname "$SCRIPT_DIR")"

# ── Defaults ──────────────────────────────────────────────────────────

CONDITION=""
TASK_ID=""
TASK_FILE=""
REPO=""
LOG_DIR="$EXPERIMENTS_DIR/logs"
ALLOWED_DIRS=""
BRANCH_PREFIX="experiment"
MAX_TURNS=100
MAX_BUDGET="10.00"
MODEL="sonnet"
TEST_DETAIL="detailed"
DRY_RUN=false
CLEANUP=false

# ── Parse arguments ──────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case $1 in
        --condition)      CONDITION="$2"; shift 2 ;;
        --task-id)        TASK_ID="$2"; shift 2 ;;
        --task-file)      TASK_FILE="$2"; shift 2 ;;
        --repo)           REPO="$2"; shift 2 ;;
        --log-dir)        LOG_DIR="$2"; shift 2 ;;
        --allowed-dirs)   ALLOWED_DIRS="$2"; shift 2 ;;
        --branch-prefix)  BRANCH_PREFIX="$2"; shift 2 ;;
        --max-turns)      MAX_TURNS="$2"; shift 2 ;;
        --max-budget)     MAX_BUDGET="$2"; shift 2 ;;
        --model)          MODEL="$2"; shift 2 ;;
        --test-detail)    TEST_DETAIL="$2"; shift 2 ;;
        --dry-run)        DRY_RUN=true; shift ;;
        --cleanup)        CLEANUP=true; shift ;;
        -h|--help)
            cat <<'USAGE'
Usage: run-experiment.sh [OPTIONS]

Required:
  --condition {A|B|C}   Experimental condition
  --task-id ID          Task identifier (e.g. "01", "19")
  --task-file PATH      Path to the task prompt file
  --repo PATH           Path to the git repo to work in

Optional:
  --log-dir PATH        Where to write logs (default: experiments/logs/)
  --allowed-dirs DIRS   Space-separated paths for Low-W file restriction
  --branch-prefix STR   Git branch prefix (default: "experiment")
  --max-turns N         Max agentic turns (default: 100)
  --max-budget USD      Max API spend per run (default: 10.00)
  --model NAME          Model to use (default: sonnet)
  --test-detail LEVEL   Test output detail: "detailed" (default) or "minimal"
  --dry-run             Show what would happen without running
  --cleanup             Remove worktree after run completes
  -h, --help            Show this help

Conditions:
  A  File tools + run_tests                           Data channels only
  B  File tools + run_tests + readonly bash            + exploration
  C  File tools + run_tests + sandboxed bash           + computation channel
  D  Sandboxed bash only                              Pure computation channel
  E  File tools + readonly bash (no run_tests)        Must pytest via bash
  F  run_tests + sandboxed bash (no file tools)       Must read/edit via bash
USAGE
            exit 0
            ;;
        *) echo "Unknown argument: $1 (use --help)"; exit 1 ;;
    esac
done

# ── Validate ──────────────────────────────────────────────────────────

if [[ -z "$CONDITION" || -z "$TASK_ID" || -z "$TASK_FILE" || -z "$REPO" ]]; then
    echo "Missing required arguments. Use --help for usage."
    exit 1
fi

[[ "$CONDITION" =~ ^[A-F]$ ]] || { echo "Condition must be A, B, C, D, E, or F"; exit 1; }
[[ -f "$TASK_FILE" ]]         || { echo "Task file not found: $TASK_FILE"; exit 1; }
[[ -d "$REPO" ]]              || { echo "Repo not found: $REPO"; exit 1; }

TASK_FILE="$(realpath "$TASK_FILE")"
REPO="$(realpath "$REPO")"
LOG_DIR="$(realpath "$LOG_DIR")"

# ── Create isolated worktree ─────────────────────────────────────────

BRANCH_NAME="${BRANCH_PREFIX}/task-${TASK_ID}-condition-${CONDITION}"
WORKTREE_DIR="$REPO/trees/${BRANCH_NAME}"

cd "$REPO"
if [[ -d "$WORKTREE_DIR" ]]; then
    echo "[run] Reusing worktree: $WORKTREE_DIR"
else
    echo "[run] Creating worktree: $WORKTREE_DIR"
    git worktree add -b "$BRANCH_NAME" "$WORKTREE_DIR" HEAD 2>/dev/null || {
        echo "[run] Branch exists, adding worktree without -b"
        git worktree add "$WORKTREE_DIR" "$BRANCH_NAME" 2>/dev/null || {
            echo "[run] ERROR: Could not create worktree"; exit 1
        }
    }
fi

# ── Read task prompt ─────────────────────────────────────────────────

TASK_DESCRIPTION="$(cat "$TASK_FILE")"

# ── Configure MCP server ─────────────────────────────────────────────

SERVER_ARGS=("$SERVER_DIR/server.py"
    "--condition" "$CONDITION"
    "--task-id" "$TASK_ID"
    "--log-dir" "$LOG_DIR"
    "--workspace" "$WORKTREE_DIR"
    "--test-detail" "$TEST_DETAIL"
)
[[ -n "$ALLOWED_DIRS" ]] && SERVER_ARGS+=("--allowed-dirs" $ALLOWED_DIRS)

SERVER_ARGS_JSON=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1:]))" "${SERVER_ARGS[@]}")

cat > "$WORKTREE_DIR/.mcp.json" <<EOF
{
  "mcpServers": {
    "experiment": {
      "command": "python3",
      "args": $SERVER_ARGS_JSON
    }
  }
}
EOF

# ── Build claude command ─────────────────────────────────────────────

CLAUDE_CMD=(claude -p
    --model "$MODEL"
    --output-format json
    --max-turns "$MAX_TURNS"
    --max-budget-usd "$MAX_BUDGET"
    --mcp-config "$WORKTREE_DIR/.mcp.json"
    --no-session-persistence
    --allowedTools "mcp__experiment__*"
    --disallowedTools "Bash" "Read" "Write" "Edit" "Glob" "Grep" "Agent" "Skill"
)

# ── Output paths ─────────────────────────────────────────────────────

PREFIX="task-${TASK_ID}-condition-${CONDITION}"
CONVERSATION_FILE="$LOG_DIR/${PREFIX}-conversation.json"
SUMMARY_FILE="$LOG_DIR/${PREFIX}-summary.json"
TOOL_LOG="$LOG_DIR/${PREFIX}.jsonl"
STDERR_LOG="$LOG_DIR/${PREFIX}-stderr.log"
mkdir -p "$LOG_DIR"

# ── Print run info ───────────────────────────────────────────────────

echo "[run] ┌─────────────────────────────────────"
echo "[run] │ Task:      $TASK_ID"
echo "[run] │ Condition: $CONDITION"
echo "[run] │ Model:     $MODEL"
echo "[run] │ Workspace: $WORKTREE_DIR"
echo "[run] │ Budget:    \$$MAX_BUDGET / $MAX_TURNS turns"
echo "[run] │ Tests:     $TEST_DETAIL"
echo "[run] └─────────────────────────────────────"

if [[ "$DRY_RUN" == true ]]; then
    echo ""
    echo "[dry-run] Command:"
    echo "  echo <prompt> | ${CLAUDE_CMD[*]}"
    echo ""
    echo "[dry-run] Prompt:"
    echo "$TASK_DESCRIPTION" | head -5
    [[ $(echo "$TASK_DESCRIPTION" | wc -l) -gt 5 ]] && echo "  ... ($(echo "$TASK_DESCRIPTION" | wc -l) lines total)"
    echo ""
    echo "[dry-run] Outputs:"
    echo "  Conversation: $CONVERSATION_FILE"
    echo "  Tool log:     $TOOL_LOG"
    echo "  Summary:      $SUMMARY_FILE"
    echo "  Sandbox:      git -C $WORKTREE_DIR log --oneline"
    exit 0
fi

# ── Run ──────────────────────────────────────────────────────────────

START_TIME=$(date +%s)
echo ""
echo "[run] Starting claude -p at $(date -Iseconds)..."

cd "$WORKTREE_DIR"
echo "$TASK_DESCRIPTION" | "${CLAUDE_CMD[@]}" > "$CONVERSATION_FILE" 2>"$STDERR_LOG"
EXIT_CODE=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# ── Extract summary from conversation ────────────────────────────────

python3 <<PYEOF
import json, sys

conversation_file = "$CONVERSATION_FILE"
tool_log_file = "$TOOL_LOG"
summary_file = "$SUMMARY_FILE"

# Load conversation
try:
    with open(conversation_file) as f:
        messages = json.load(f)
except Exception as e:
    print(f"[run] WARNING: Could not parse conversation: {e}", file=sys.stderr)
    messages = []

# Extract result metadata
result_msg = next((m for m in messages if m.get("type") == "result"), {})

# Extract final text response
final_text = ""
for msg in reversed(messages):
    if msg.get("type") == "result" and "result" in msg:
        final_text = msg["result"]
        break

# Count tool calls from conversation (MCP tool uses)
tool_uses = []
for msg in messages:
    content = msg.get("content", [])
    if not isinstance(content, list):
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            tool_uses.append(block.get("name", "unknown"))

# Load MCP tool log for cross-reference
mcp_calls = []
try:
    with open(tool_log_file) as f:
        for line in f:
            mcp_calls.append(json.loads(line))
except FileNotFoundError:
    pass

# Count sandbox commits (only those made by the experiment server)
import subprocess
try:
    git_log = subprocess.run(
        ["git", "log", "--oneline", "--grep=^after ", "--extended-regexp"],
        capture_output=True, text=True, timeout=5,
        cwd="$WORKTREE_DIR"
    )
    lines = git_log.stdout.strip().split("\n") if git_log.stdout.strip() else []
    sandbox_commits = len(lines)
except Exception:
    sandbox_commits = 0

# Build summary
summary = {
    "task_id": "$TASK_ID",
    "condition": "$CONDITION",
    "model": "$MODEL",
    "exit_code": $EXIT_CODE,
    "duration_s": $DURATION,
    "duration_api_ms": result_msg.get("duration_api_ms"),
    "num_turns": result_msg.get("num_turns"),
    "is_error": result_msg.get("is_error", False),
    "tool_calls_conversation": len(tool_uses),
    "tool_calls_mcp": len(mcp_calls),
    "tool_call_breakdown": {},
    "mcp_success_rate": (
        sum(1 for c in mcp_calls if c.get("success")) / len(mcp_calls)
        if mcp_calls else None
    ),
    "sandbox_commits": sandbox_commits,
    "final_response_length": len(final_text),
    "final_response_preview": final_text[:500] if final_text else "",
    "worktree": "$WORKTREE_DIR",
}

# Tool call breakdown
for name in tool_uses:
    summary["tool_call_breakdown"][name] = summary["tool_call_breakdown"].get(name, 0) + 1

with open(summary_file, "w") as f:
    json.dump(summary, f, indent=2)

# Print summary to console
print()
print(f"[run] ┌─ Results ────────────────────────────")
print(f"[run] │ Exit code:  {summary['exit_code']}")
print(f"[run] │ Duration:   {summary['duration_s']}s")
print(f"[run] │ Turns:      {summary['num_turns']}")
print(f"[run] │ Tool calls: {summary['tool_calls_mcp']} (MCP logged)")
print(f"[run] │ Success:    {summary['mcp_success_rate']:.0%}" if summary['mcp_success_rate'] is not None else "[run] │ Success:    n/a")
print(f"[run] │ Edits:      {summary['sandbox_commits']} sandbox commits")
print(f"[run] │ Response:   {summary['final_response_length']} chars")
print(f"[run] └──────────────────────────────────────")
print()
print(f"[run] Files:")
print(f"[run]   Conversation: {conversation_file}")
print(f"[run]   Tool log:     {tool_log_file}")
print(f"[run]   Summary:      {summary_file}")
print(f"[run]   Sandbox:      git -C $WORKTREE_DIR log --oneline")

# Tool breakdown
if summary["tool_call_breakdown"]:
    print()
    print(f"[run] Tool breakdown:")
    for name, count in sorted(summary["tool_call_breakdown"].items(), key=lambda x: -x[1]):
        print(f"[run]   {name}: {count}")
PYEOF

# ── Cleanup ──────────────────────────────────────────────────────────

if [[ "$CLEANUP" == true ]]; then
    echo ""
    echo "[run] Cleaning up worktree..."
    git -C "$REPO" worktree remove "$WORKTREE_DIR" 2>/dev/null || true
else
    echo ""
    echo "[run] To clean up: git -C $REPO worktree remove $WORKTREE_DIR"
fi

exit $EXIT_CODE
