# Toolcraft Extension: Build Prompt

*Prompt for spinning up an agent to build the Toolcraft coordinator extension.*

---

## What you're building

A Claude Code extension (Python package + hooks configuration) that coordinates Fledgling, blq, and jetsam to implement the Patterns for Toolcraft. The extension:

1. **Guards paths** per mode (PreToolUse hook on built-in Edit/Write)
2. **Controls modes** based on failure patterns (PostToolUse hook)
3. **Coaches** the agent with efficiency suggestions (PostToolUse hook, periodic)
4. **Intercepts** bash commands and suggests structured alternatives from blq/jetsam/Fledgling (PreToolUse hook on Bash)
5. **Configures** the session at start based on model + task type (SessionStart hook)

All using Claude Code's native hook protocol. No tool reimplementation. Level 1 — specified rules over structured data.

## Before doing anything

Read these files, in order:

### Architecture and design
1. `drafts/toolcraft-coordinator-design.md` — **The full design.** Plugin architecture, path guard implementation, mode controller, coach, interception modes (observe → suggest → redirect), PostToolUse validation. This is your blueprint.
2. `blog/patterns/index.md` — The eight patterns this extension implements. Read all eight for context.

### Detailed pattern docs (read the ones you're implementing)
3. `blog/patterns/04-write-execute-separation.md` — Write/Execute Separation (path guard implements this)
4. `blog/patterns/07-the-mode-controller.md` — Mode Controller (failure-driven transitions)
5. `blog/patterns/08-the-coach.md` — Coach (observation + suggestion + integration architecture)
6. `blog/patterns/01-the-quartermaster.md` — Quartermaster (session-start configuration)
7. `blog/patterns/02-the-strategy-instruction.md` — Strategy Instruction (model-dependent principles)
8. `blog/patterns/05-sandbox-specifications.md` — Sandbox Specs (blq integration for execution bounds)

### Integration prompts (what each tool provides)
9. `~/Projects/lq/main/docs/plans/patterns-integration-prompt.md` — blq's role: sandbox specs, test event stream
10. `~/Projects/source-sextant/main/docs/plans/patterns-integration-prompt.md` — Fledgling's role: level 0 intelligence, kit manifests, coaching queries
11. `~/Projects/jetsam/main/docs/superpowers/plans/patterns-integration-prompt.md` — jetsam's role: mode state, workflow transitions, protected paths

### Experimental evidence
12. `experiments/pilot-findings.md` — The data behind the patterns. Sections 8-11 are most relevant.
13. `drafts/the-experiment-that-proved-us-wrong.md` — The narrative. Why these patterns exist.

### Hook protocol
14. Claude Code hooks documentation — PreToolUse receives `{"tool_name", "tool_input"}` on stdin. Output JSON with `permissionDecision: "deny"|"allow"`. Exit 0 for structured output, exit 2 for hard block. PostToolUse receives tool results.

## Extension structure

```
toolcraft/
├── __init__.py
├── config.py              # Load config.toml, mode policies, plugin modes
├── state.py               # Read/write mode state (.toolcraft/state.json)
├── hooks/
│   ├── pre_tool_use.py    # Main PreToolUse hook entry point
│   ├── post_tool_use.py   # Main PostToolUse hook entry point
│   └── session_start.py   # Quartermaster: session configuration
├── guards/
│   └── path_guard.py      # Mode-based path protection for Edit/Write
├── interceptors/
│   ├── base.py            # Plugin base class
│   ├── blq_plugin.py      # Intercept test/build commands → blq
│   ├── jetsam_plugin.py   # Intercept git commands → jetsam
│   └── fledgling_plugin.py # Intercept search/nav commands → Fledgling
├── coach/
│   ├── observer.py        # Track tool usage patterns
│   ├── suggestions.py     # Generate suggestions from patterns
│   └── queries.py         # Fledgling/blq queries for coaching data
├── controller/
│   ├── mode_controller.py # Failure-driven mode transitions
│   └── counters.py        # Failure counts, turns-in-mode, etc.
├── quartermaster/
│   ├── profiles.py        # Model capability profiles
│   ├── kits.py            # Kit manifests (tool sets + strategy)
│   └── selector.py        # Kit selection logic
├── config.toml            # Default configuration
├── install.py             # Add hooks to settings.json
└── README.md
```

## Key implementation details

### Hook entry points

`hooks/pre_tool_use.py` is the single PreToolUse hook. It chains:
1. Path guard (check writable paths for Edit/Write)
2. Plugin interceptors (check Bash commands for structured alternatives)

`hooks/post_tool_use.py` is the single PostToolUse hook. It chains:
1. Mode controller (update counters, check transitions)
2. Coach (periodic suggestions)
3. Post-validation plugins (check results)

### State management

All state in `.toolcraft/state.json`:
```json
{
    "mode": "implement",
    "failure_count": 0,
    "turns_in_mode": 12,
    "total_calls": 47,
    "last_test_result": "13 failed, 35 passed",
    "model": "sonnet"
}
```

Read by every hook invocation. Written by post_tool_use. The file is the coordination point — no IPC, no sockets, no shared memory. Just a JSON file.

### Plugin interception modes

Three modes per plugin, configured in config.toml:

```toml
[plugins.blq]
mode = "suggest"        # Allow bash, inject blq suggestion

[plugins.jetsam]
mode = "observe"        # Allow bash, just log the alternative

[plugins.fledgling]
mode = "observe"        # Allow bash, just log the alternative
```

The ratchet: start in observe (gather data), graduate to suggest (inform agent), eventually redirect (deny bash, require structured tool). Each graduation is a config change, not a code change.

### Dependencies

The extension should work with whatever subset of tools is installed:
- blq available → BlqPlugin active, sandbox specs enforced
- jetsam available → JetsamPlugin active, mode state in jetsam
- Fledgling available → FledglingPlugin active, coaching queries work
- None available → path guard and mode controller still work (they only need state.json)

Check for each tool at import time, degrade gracefully.

## What success looks like

1. `python -m toolcraft install` adds hooks to `.claude/settings.json`
2. The agent starts a session. The quartermaster detects the model, selects a kit.
3. During work, the path guard prevents writing to protected paths per mode.
4. When the agent runs `git add && git commit`, the interceptor suggests `jetsam save`.
5. After 3 consecutive failures, the mode controller switches to debug mode.
6. Every 5 tool calls, the coach checks for inefficiency patterns and suggests alternatives.
7. All of this is logged. The intercept log shows which bash patterns have structured alternatives. The ratchet data accumulates.

## Testing

Test against the synthetic codebase from the experiments:
- `experiments/synthetic/codebase-beta/` — Python expression language with 13 bugs, 48 tests
- Run with the extension installed, verify path guard blocks test edits in implement mode
- Verify the coach suggests FindDefinitions when the agent greps for function names
- Verify the mode controller switches to debug after repeated failures
- Verify the jetsam plugin suggests `jetsam save` for git workflows

## What NOT to build

- Don't reimplement Read, Edit, Write, Bash. Use Claude Code's built-in tools.
- Don't use an LLM for any decision in the extension. All rules are specified in config.toml.
- Don't make the extension required. It should be optional — agent works without it, works better with it.
- Don't build the Calibration Probe yet. That's a follow-up once the basic extension works.
