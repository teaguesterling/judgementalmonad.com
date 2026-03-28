# Toolcraft Coordinator

*The integration layer that connects Fledgling, blq, and jetsam to implement the Patterns for Toolcraft.*

---

## Why a coordinator

Three tools, three levels, three roles:
- **Fledgling** reads code intelligence (level 0)
- **blq** executes and captures builds/tests (level 1-2)
- **jetsam** manages workflow state (level 1-2)

The patterns (Quartermaster, Mode Controller, Coach, Write/Execute Separation, Sandbox Specs) compose these tools. But none of the three should implement the composition — that would pull them out of their natural level. The composition is Harness-level logic: specified rules that operate on the outputs of all three.

The Coordinator is that composition layer.

## What it does

### 1. Path protection (Write/Execute Separation)

Block writes to specific paths based on the current mode.

**Mechanism: Claude Code PreToolUse hook**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "command": "python3 toolcraft-coordinator/path_guard.py",
        "description": "Enforce path protection per mode"
      }
    ]
  }
}
```

The hook receives the tool call before execution. For `Edit`, `Write`, and `file_edit`/`file_write` calls, it checks the path against the current mode's writable set:

```python
#!/usr/bin/env python3
"""path_guard.py — Block writes to protected paths per mode."""

import json
import sys
from pathlib import Path

# Read the current mode from jetsam state
def get_current_mode():
    # Read from jetsam state file or query jetsam status
    state_file = Path(".jetsam/state.json")
    if state_file.exists():
        state = json.loads(state_file.read_text())
        return state.get("mode", "implement")
    return "implement"  # default

# Mode path policies
MODE_POLICIES = {
    "debug": {
        "writable": [],              # nothing writable in debug mode
        "message": "Debug mode: read-only. Switch to implement mode to edit."
    },
    "implement": {
        "writable": ["src/"],        # only source files
        "message": "Implementation mode: tests/ is protected. Switch to test-dev mode to edit tests."
    },
    "test_dev": {
        "writable": ["tests/"],      # only test files
        "message": "Test development mode: src/ is protected. Switch to implement mode to edit source."
    },
    "review": {
        "writable": [],              # nothing writable
        "message": "Review mode: read-only. Use jetsam mode implement to start editing."
    },
}

def check_write(tool_name, arguments):
    """Check if a write operation is allowed in the current mode."""
    mode = get_current_mode()
    policy = MODE_POLICIES.get(mode, {"writable": ["*"]})

    # Extract the path from the tool arguments
    path = arguments.get("path", arguments.get("file_path", ""))
    if not path:
        return True  # no path to check

    # Check against writable paths
    writable = policy["writable"]
    if not writable:
        print(json.dumps({
            "blocked": True,
            "reason": policy["message"]
        }))
        return False

    for allowed in writable:
        if path.startswith(allowed):
            return True

    print(json.dumps({
        "blocked": True,
        "reason": f"Path '{path}' is not writable in {mode} mode. {policy['message']}"
    }))
    return False

# Hook receives tool call info on stdin
if __name__ == "__main__":
    # The hook protocol depends on Claude Code's hook format
    # This is a sketch — actual format TBD
    tool_input = json.loads(sys.stdin.read())
    tool_name = tool_input.get("tool_name", "")
    arguments = tool_input.get("arguments", {})

    write_tools = {"Edit", "Write", "file_edit", "file_write",
                   "file_edit_batch", "mcp__experiment__file_edit",
                   "mcp__experiment__file_write", "mcp__experiment__file_edit_batch"}

    if tool_name in write_tools:
        if not check_write(tool_name, arguments):
            sys.exit(1)  # block the tool call
```

### 2. Mode transitions (Mode Controller)

**Mechanism: Claude Code PostToolUse hook**

```python
#!/usr/bin/env python3
"""mode_controller.py — Switch modes on failure patterns."""

import json
import sys
from pathlib import Path

def get_state():
    state_file = Path(".jetsam/state.json")
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {"mode": "implement", "failure_count": 0, "turns_in_mode": 0}

def update_state(state):
    state_file = Path(".jetsam/state.json")
    state_file.parent.mkdir(exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2))

# Read hook input (tool call result)
tool_result = json.loads(sys.stdin.read())
success = tool_result.get("success", True)
tool_name = tool_result.get("tool_name", "")

state = get_state()
state["turns_in_mode"] = state.get("turns_in_mode", 0) + 1

if not success:
    state["failure_count"] = state.get("failure_count", 0) + 1

# Transition rules
mode = state["mode"]
transitions = []

if mode == "implement" and state["failure_count"] > 3:
    transitions.append(("debug", "Too many failures — switching to diagnosis"))

if mode == "debug" and state["turns_in_mode"] > 20:
    transitions.append(("implement", "Extended diagnosis — time to try fixing"))

if mode == "implement" and tool_name == "run_tests" and success:
    transitions.append(("review", "Tests passing — switching to review"))

if transitions:
    new_mode, reason = transitions[0]
    state["mode"] = new_mode
    state["failure_count"] = 0
    state["turns_in_mode"] = 0
    # Log the transition
    print(f"[mode-controller] Switching to {new_mode}: {reason}")

update_state(state)
```

### 3. Coach suggestions (The Coach)

**Mechanism: Claude Code PostToolUse hook, fires every N calls**

```python
#!/usr/bin/env python3
"""coach.py — Suggest more efficient tool usage."""

import json
import subprocess
import sys
from pathlib import Path

# Only fire every N calls
state = get_state()  # reuse jetsam state
call_count = state.get("total_calls", 0) + 1
state["total_calls"] = call_count
update_state(state)

if call_count % 5 != 0:
    sys.exit(0)  # not time yet

# Query Fledgling for tool usage patterns
def query_fledgling(sql):
    result = subprocess.run(
        ["fledgling", "query", sql],
        capture_output=True, text=True, timeout=5
    )
    return result.stdout

# Check for repeated searches
repeated = query_fledgling("""
    SELECT arguments->>'pattern' as pattern, count(*) as times
    FROM ChatToolUsage
    WHERE tool_name = 'file_search'
    AND sequence_number > (SELECT max(sequence_number) - 10 FROM ChatToolUsage)
    GROUP BY pattern
    HAVING count(*) >= 3
""")

if repeated.strip():
    print(f"[coach] You've searched for the same pattern multiple times. "
          f"Try FindDefinitions for AST-aware search across all files.")

# Check for edit-without-test
edits_since_test = query_fledgling("""
    SELECT count(*) as edits
    FROM ChatToolUsage
    WHERE tool_name LIKE '%edit%'
    AND sequence_number > COALESCE(
        (SELECT max(sequence_number) FROM ChatToolUsage WHERE tool_name = 'run_tests'),
        0
    )
""")
# Parse and suggest if needed
```

### 4. Quartermaster kit activation (The Quartermaster)

**Mechanism: Claude Code session start hook or skill invocation**

The Quartermaster runs at session start, queries the model and task, and configures:
- Which Fledgling kit to activate (tool publication)
- Which jetsam mode to start in
- Which blq sandbox spec to use
- Whether to include the strategy instruction

```bash
#!/usr/bin/env bash
# quartermaster.sh — Configure the session based on task and model

MODEL=$(claude --version 2>&1 | grep model | awk '{print $NF}')
TASK_TYPE="${1:-implement}"  # debug, implement, review, etc.

# Select kit based on model + task
case "$MODEL" in
    *haiku*)
        FLEDGLING_KIT="navigate"
        STRATEGY="Do not start editing until you understand the full picture."
        TOOL_RESTRICTION="simple"
        ;;
    *sonnet*)
        FLEDGLING_KIT="diagnose"
        STRATEGY=""  # Sonnet doesn't need it
        TOOL_RESTRICTION="full"
        ;;
    *opus*)
        FLEDGLING_KIT="diagnose"
        STRATEGY=""  # Harmful for Opus
        TOOL_RESTRICTION="full"
        ;;
esac

# Configure Fledgling
fledgling profile "$FLEDGLING_KIT"

# Configure jetsam mode
jetsam mode "$TASK_TYPE"

# Inject strategy if needed
if [ -n "$STRATEGY" ]; then
    echo "$STRATEGY" >> .claude/CLAUDE.md
fi

echo "[quartermaster] Configured: model=$MODEL kit=$FLEDGLING_KIT mode=$TASK_TYPE"
```

## The extension: `toolcraft`

All four hooks package into a single extension:

```
toolcraft/
├── path_guard.py          # PreToolUse: path protection per mode
├── mode_controller.py     # PostToolUse: failure-driven transitions
├── coach.py               # PostToolUse (every N): efficiency suggestions
├── quartermaster.sh       # Session start: kit/mode/strategy selection
├── config.toml            # Mode policies, thresholds, coach frequency
└── install.sh             # Adds hooks to settings.json
```

### Configuration

```toml
# toolcraft/config.toml

[modes.debug]
writable = []
strategy = "Identify all failures before proposing fixes."

[modes.implement]
writable = ["src/"]
strategy = ""

[modes.test_dev]
writable = ["tests/"]
strategy = "Write tests for the expected behavior, not the current behavior."

[modes.review]
writable = []
strategy = "Read everything before forming an opinion."

[controller]
max_failures_before_debug = 3
max_turns_in_debug = 20
auto_review_on_tests_passing = true

[coach]
frequency = 5           # suggest every N tool calls
max_suggestion_length = 2  # lines
model_config.haiku = "aggressive"    # every 3 calls
model_config.sonnet = "standard"     # every 5 calls
model_config.opus = "minimal"        # every 10, action-oriented only

[quartermaster]
default_mode = "implement"
haiku_kit = "navigate"
sonnet_kit = "diagnose"
opus_kit = "diagnose"
```

### Installation

```bash
# Install the extension
toolcraft install

# This adds to .claude/settings.json:
# {
#   "hooks": {
#     "PreToolUse": ["python3 toolcraft/path_guard.py"],
#     "PostToolUse": [
#       "python3 toolcraft/mode_controller.py",
#       "python3 toolcraft/coach.py"
#     ],
#     "SessionStart": ["bash toolcraft/quartermaster.sh"]
#   }
# }
```

## Grade of the coordinator

The coordinator is level 1 — specified mutations over structured data:
- Path guard: reads mode state (JSON), checks path against a list, allows or blocks
- Mode controller: reads counters, compares to thresholds, updates mode state
- Coach: queries Fledgling (level 0), formats a suggestion string
- Quartermaster: pattern-matches on model name and task type, sets configuration

No computation channels. No trained judgment. Every decision is traceable to a specified rule in config.toml. The coordinator stays in the specified band.

## Dependency architecture

```
toolcraft (coordinator, level 1)
├── reads from: Fledgling (level 0, via query)
├── reads from: blq (level 1, via events/status)
├── reads from: jetsam (level 1, via state)
├── writes to: jetsam state (mode transitions)
├── writes to: Claude Code context (coach suggestions)
├── writes to: MCP tool config (kit activation)
└── enforces: path protection (PreToolUse hook)
```

Each dependency is specified and auditable. The coordinator never interprets executable specification. It reads structured data and applies rules.
