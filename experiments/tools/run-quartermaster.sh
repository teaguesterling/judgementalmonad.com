#!/usr/bin/env bash
#
# Run the quartermaster: select a tool configuration for a task + model.
#
# Usage:
#   ./run-quartermaster.sh --mode secure --model haiku --task-file tasks/task-synth-1.md
#   ./run-quartermaster.sh --mode efficient --model sonnet --task-file tasks/task-synth-1.md
#   ./run-quartermaster.sh --mode balanced --model opus --task-file tasks/task-synth-1.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPERIMENTS_DIR="$(dirname "$SCRIPT_DIR")"

MODE="balanced"
MODEL="sonnet"
TASK_FILE=""
QM_MODEL="haiku"  # quartermaster always uses haiku (fast, cheap)
MAX_TURNS=50

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)       MODE="$2"; shift 2 ;;
        --model)      MODEL="$2"; shift 2 ;;
        --task-file)  TASK_FILE="$2"; shift 2 ;;
        --qm-model)   QM_MODEL="$2"; shift 2 ;;
        --max-turns)  MAX_TURNS="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [[ -z "$TASK_FILE" ]]; then
    echo "Usage: $0 --mode {secure|efficient|balanced} --model {haiku|sonnet|opus} --task-file PATH"
    exit 1
fi

TASK_FILE="$(realpath "$TASK_FILE")"
QM_PROMPT_FILE="$(realpath "$EXPERIMENTS_DIR/tasks/quartermaster-${MODE}.md")"

if [[ ! -f "$QM_PROMPT_FILE" ]]; then
    echo "Quartermaster prompt not found: $QM_PROMPT_FILE"
    exit 1
fi

TASK_DESCRIPTION="$(cat "$TASK_FILE")"
QM_PROMPT="$(cat "$QM_PROMPT_FILE")"
QM_CONTEXT="$(cat "$EXPERIMENTS_DIR/tasks/quartermaster-context.md")"

# Inject shared context (model profiles + tool descriptions with rationales)
# Replace the generic tool group list with the detailed version from context
QM_PROMPT="${QM_PROMPT//"## Available tool groups"*"## Task"/"$QM_CONTEXT

## Task"}"

# If that didn't work (pattern matching is fragile), just append context
if [[ "$QM_PROMPT" != *"Model profiles"* ]]; then
    QM_PROMPT="$QM_PROMPT

$QM_CONTEXT"
fi

# Substitute task, model, and turns
QM_PROMPT="${QM_PROMPT//\{TASK_DESCRIPTION\}/$TASK_DESCRIPTION}"
QM_PROMPT="${QM_PROMPT//\{MODEL_NAME\}/$MODEL}"
QM_PROMPT="${QM_PROMPT//\{MAX_TURNS\}/$MAX_TURNS}"

echo "[quartermaster] Mode: $MODE"
echo "[quartermaster] Target model: $MODEL"
echo "[quartermaster] QM model: $QM_MODEL"
echo "[quartermaster] Task: $(head -1 "$TASK_FILE")"
echo ""

# Run the quartermaster as a single claude -p call
RESULT=$(echo "$QM_PROMPT" | claude -p --model "$QM_MODEL" --max-turns 1 --no-session-persistence 2>/dev/null)

echo "[quartermaster] Selection:"
echo "$RESULT"
