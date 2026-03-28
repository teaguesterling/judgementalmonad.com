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

The hook receives the full tool call on stdin as JSON, including `tool_name` and `tool_input` with file paths. For write tools (`Edit`, `Write`, `Bash`), it checks the path against the current mode's writable set.

**This works with Claude Code's built-in tools directly.** No reimplementation. The PreToolUse hook controls Edit, Write, Bash — the same tools the agent already uses. Exit code 0 with `permissionDecision: "deny"` blocks the call and sends the reason to the agent.

```python
#!/usr/bin/env python3
"""path_guard.py — Block writes to protected paths per mode.

Works with Claude Code's built-in tools (Edit, Write, Bash).
No tool reimplementation needed.

PreToolUse hook protocol:
  Input (stdin): {"tool_name": "Edit", "tool_input": {"file_path": "...", ...}, ...}
  Output (stdout): JSON with permissionDecision: "deny"|"allow"|"ask"
  Exit 0: output parsed. Exit 2: blocked with stderr as reason.
"""

import json
import sys
from pathlib import Path

def get_current_mode():
    state_file = Path(".jetsam/state.json")
    if state_file.exists():
        return json.loads(state_file.read_text()).get("mode", "implement")
    # Also check a simple mode file for systems without jetsam
    mode_file = Path(".kibitzer/mode")
    if mode_file.exists():
        return mode_file.read_text().strip()
    return "implement"

MODE_POLICIES = {
    "debug": {
        "writable": [],
        "message": "Debug mode: read-only. Use `jetsam mode implement` to start editing."
    },
    "implement": {
        "writable": ["src/"],
        "message": "Implementation mode: tests/ is protected. Use `jetsam mode test_dev` to edit tests."
    },
    "test_dev": {
        "writable": ["tests/"],
        "message": "Test development mode: src/ is protected. Use `jetsam mode implement` to edit source."
    },
    "review": {
        "writable": [],
        "message": "Review mode: read-only. Use `jetsam mode implement` to start editing."
    },
}

def extract_path(tool_name, tool_input):
    """Extract the target file path from a tool call."""
    if tool_name == "Edit":
        return tool_input.get("file_path", "")
    elif tool_name == "Write":
        return tool_input.get("file_path", "")
    elif tool_name == "Bash":
        # Can't reliably extract paths from bash commands
        # but we can check for obvious write patterns
        cmd = tool_input.get("command", "")
        # For bash, the sandbox spec (blq) is the right enforcement layer
        # Path guard only handles structured tools
        return ""
    # MCP tools
    return tool_input.get("path", tool_input.get("file_path", ""))

if __name__ == "__main__":
    hook_input = json.loads(sys.stdin.read())
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only check write tools
    write_tools = {"Edit", "Write"}
    if tool_name not in write_tools:
        sys.exit(0)  # allow non-write tools

    path = extract_path(tool_name, tool_input)
    if not path:
        sys.exit(0)  # no path to check

    mode = get_current_mode()
    policy = MODE_POLICIES.get(mode, {"writable": ["*"], "message": ""})

    # Check path against writable set
    allowed = False
    for writable_prefix in policy["writable"]:
        if path.startswith(writable_prefix):
            allowed = True
            break

    if not allowed and policy["writable"] != ["*"]:
        # Deny with reason — the agent sees this in its context
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"{policy['message']} (tried to write: {path})"
            }
        }))
    # else: exit 0 with no output = allow
```

**Key design: the denial reason tells the agent how to switch modes.** "Use `jetsam mode implement` to start editing." The agent can respond by requesting a mode switch rather than being silently blocked. This is the transparency principle from the Ma series — project constraints into the actor's scope.

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

## The extension: `kibitzer`

All four hooks package into a single extension:

```
kibitzer/
├── path_guard.py          # PreToolUse: path protection per mode
├── mode_controller.py     # PostToolUse: failure-driven transitions
├── coach.py               # PostToolUse (every N): efficiency suggestions
├── quartermaster.sh       # Session start: kit/mode/strategy selection
├── config.toml            # Mode policies, thresholds, coach frequency
└── install.sh             # Adds hooks to settings.json
```

### Configuration

```toml
# kibitzer/config.toml

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
kibitzer install

# This adds to .claude/settings.json:
# {
#   "hooks": {
#     "PreToolUse": ["python3 kibitzer/path_guard.py"],
#     "PostToolUse": [
#       "python3 kibitzer/mode_controller.py",
#       "python3 kibitzer/coach.py"
#     ],
#     "SessionStart": ["bash kibitzer/quartermaster.sh"]
#   }
# }
```

## Plugin architecture: tool-aware interception

The coordinator isn't just hooks — it's a plugin system where each tool (blq, jetsam, Fledgling) registers what bash patterns it can handle and what it offers instead.

### How plugins work

Each plugin declares:
- **Triggers**: bash command patterns it recognizes
- **Intercept**: what it suggests or does instead
- **Mode**: observe (log only), suggest (inform agent), redirect (deny bash, offer alternative)

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class InterceptMode(Enum):
    OBSERVE = "observe"    # allow bash, log the suggestion (ratchet data)
    SUGGEST = "suggest"    # allow bash, inject suggestion into context
    REDIRECT = "redirect"  # deny bash, agent must use the alternative

@dataclass
class Suggestion:
    tool: str                          # the structured alternative
    reason: str                        # why it's better
    grade_before: Optional[str] = None # e.g. "level 4"
    grade_after: Optional[str] = None  # e.g. "level 1"

@dataclass
class Plugin:
    name: str
    triggers: list[str]                # bash patterns to match
    mode: InterceptMode = InterceptMode.SUGGEST

    def intercept(self, tool_name: str, tool_input: dict) -> Optional[Suggestion]:
        """Check if this plugin can handle the tool call. Return suggestion or None."""
        raise NotImplementedError
```

### The plugins

```python
class BlqPlugin(Plugin):
    """Intercepts build/test commands, offers blq structured capture."""

    name = "blq"
    triggers = ["pytest", "python -m pytest", "make", "npm test",
                "cargo test", "go test", "gradle test"]

    def intercept(self, tool_name, tool_input):
        if tool_name != "Bash":
            return None
        cmd = tool_input.get("command", "")

        for trigger in self.triggers:
            if trigger in cmd:
                return Suggestion(
                    tool=f"blq run test",
                    reason="Captures structured output — errors queryable via blq errors, "
                           "results persisted across sessions, diffable over time",
                    grade_before="level 4 (arbitrary bash)",
                    grade_after="level 1 (structured query over captured output)",
                )
        return None


class JetsamPlugin(Plugin):
    """Intercepts git commands, offers jetsam workflow operations."""

    name = "jetsam"
    triggers = ["git add", "git commit", "git push", "git stash",
                "git checkout", "git branch", "git diff", "git log"]

    def intercept(self, tool_name, tool_input):
        if tool_name != "Bash":
            return None
        cmd = tool_input.get("command", "")

        if "git add" in cmd and "git commit" in cmd:
            return Suggestion(
                tool="jetsam save 'description'",
                reason="Atomic save with plan tracking, confirmation step, "
                       "and automatic branch management",
                grade_before="level 4",
                grade_after="level 2 (structured workflow operation)",
            )
        if "git push" in cmd:
            return Suggestion(
                tool="jetsam sync",
                reason="Syncs with remote, handles rebasing, "
                       "requires confirmation before pushing",
            )
        if "git diff" in cmd:
            return Suggestion(
                tool="jetsam diff",
                reason="Structured diff with plan context",
            )
        if "git log" in cmd:
            return Suggestion(
                tool="jetsam log",
                reason="Commit history with plan annotations",
            )
        return None


class FledglingPlugin(Plugin):
    """Intercepts code search/navigation, offers semantic alternatives."""

    name = "fledgling"
    triggers = ["grep -r", "grep -rn", "find . -name", "find . -type f"]

    def intercept(self, tool_name, tool_input):
        if tool_name != "Bash":
            return None
        cmd = tool_input.get("command", "")

        # Detect searching for definitions
        if ("grep" in cmd and
            any(kw in cmd for kw in ["def ", "class ", "function ", "fn "])):
            return Suggestion(
                tool="FindDefinitions(name_pattern='...')",
                reason="AST-aware search — understands scope, type, and nesting. "
                       "Finds the definition, not just text matches",
                grade_before="level 4 (bash grep)",
                grade_after="level 0 (structured query over parsed AST)",
            )

        # Detect searching for file structure
        if "find" in cmd and ("-name" in cmd or "-type" in cmd):
            pattern = ""  # extract from cmd if possible
            return Suggestion(
                tool=f"CodeStructure(file_pattern='**/*.py')",
                reason="Shows classes, functions, and nesting — "
                       "not just file names but code organization",
                grade_before="level 4",
                grade_after="level 0",
            )

        # Detect reading files for understanding
        if "cat" in cmd and cmd.count("cat") >= 2:
            return Suggestion(
                tool="ReadLines with multiple files",
                reason="Structured multi-file read with line numbers "
                       "and context windowing",
            )

        return None
```

### The interception hook

The PreToolUse hook runs all plugins against every Bash call:

```python
#!/usr/bin/env python3
"""plugin_interceptor.py — Route bash commands to structured alternatives."""

import json
import sys
from pathlib import Path

# Load plugins (in practice, imported from the extension package)
plugins = [BlqPlugin(), JetsamPlugin(), FledglingPlugin()]

# Load interception mode from config
config_file = Path(".kibitzer/config.toml")
default_mode = InterceptMode.SUGGEST  # start with suggest, graduate to redirect

def run():
    hook_input = json.loads(sys.stdin.read())
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept Bash calls
    if tool_name != "Bash":
        return

    # Check each plugin
    suggestions = []
    for plugin in plugins:
        suggestion = plugin.intercept(tool_name, tool_input)
        if suggestion:
            suggestions.append((plugin, suggestion))

    if not suggestions:
        return  # no plugin matches, allow the bash call

    # Use the first matching suggestion (could rank by grade_reduction)
    plugin, suggestion = suggestions[0]

    mode = plugin.mode  # or override from config

    if mode == InterceptMode.OBSERVE:
        # Log the suggestion but allow bash
        log_entry = {
            "bash_command": tool_input.get("command", "")[:200],
            "suggested_tool": suggestion.tool,
            "reason": suggestion.reason,
            "plugin": plugin.name,
        }
        log_file = Path(".kibitzer/intercept.log")
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        return  # allow

    elif mode == InterceptMode.SUGGEST:
        # Allow bash but inject the suggestion into context
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": (
                    f"[toolcraft] {plugin.name} suggests: {suggestion.tool}\n"
                    f"Reason: {suggestion.reason}"
                    + (f"\nGrade: {suggestion.grade_before} → {suggestion.grade_after}"
                       if suggestion.grade_before else "")
                ),
            }
        }))
        return  # allow, but with suggestion in context

    elif mode == InterceptMode.REDIRECT:
        # Deny bash, provide the alternative
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"A structured alternative is available: {suggestion.tool}\n"
                    f"{suggestion.reason}"
                    + (f"\nThis reduces the grade from {suggestion.grade_before} to {suggestion.grade_after}."
                       if suggestion.grade_before else "")
                ),
            }
        }))
        return

if __name__ == "__main__":
    run()
```

### The three modes: the ratchet applied to interception

```
OBSERVE → SUGGEST → REDIRECT
```

Start in **observe**: log every bash command that has a structured alternative. This builds the ratchet data — which commands are candidates for promotion.

After reviewing the logs and confirming the alternatives work, graduate to **suggest**: the agent sees "jetsam save is available" in its context alongside the bash call. It can choose either.

After confirming the agent follows suggestions reliably, graduate to **redirect**: bash calls with structured alternatives are denied. The agent must use the structured tool.

Each graduation is a ratchet turn. The mode can be set per-plugin:

```toml
[plugins.blq]
mode = "redirect"          # tests must go through blq (mature)

[plugins.jetsam]
mode = "suggest"           # git workflow suggestions (learning)

[plugins.fledgling]
mode = "observe"           # code navigation alternatives (new, gathering data)
```

### PostToolUse validation plugins

The same plugin architecture works for PostToolUse — validating results:

```python
class BlqPostPlugin(Plugin):
    """After blq run test, check for new failures."""

    def validate(self, tool_name, tool_input, tool_result):
        if tool_name == "blq_run" or "pytest" in str(tool_input):
            # Parse test results, update failure counter
            failures = parse_test_failures(tool_result)
            if failures > previous_failures:
                return PostAction(
                    type="warn",
                    message=f"New failures introduced: {failures - previous_failures}. "
                            f"Consider reverting the last edit.",
                )
            if failures == 0 and previous_failures > 0:
                return PostAction(
                    type="celebrate",
                    message=f"All tests passing! {previous_failures} failures fixed.",
                )

class FledglingPostPlugin(Plugin):
    """After file_edit, check if the agent should read related files."""

    def validate(self, tool_name, tool_input, tool_result):
        if tool_name in ("Edit", "file_edit"):
            edited_file = tool_input.get("file_path", "")
            # Query Fledgling for files that import from the edited file
            related = query_fledgling(
                f"SELECT file FROM imports WHERE imported_module LIKE '%{edited_file}%'"
            )
            if related:
                return PostAction(
                    type="suggest",
                    message=f"You edited {edited_file}. These files import from it: "
                            f"{', '.join(related)}. Consider checking they still work.",
                )
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
