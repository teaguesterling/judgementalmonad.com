# The Quartermaster

*Select the right tools, strategy, and constraints for the task and model — before execution begins.*

---

## The problem

Every agent system gives the agent a fixed tool set. The agent receives the same tools whether the task is bug diagnosis, feature addition, or code review. Whether the model is Haiku or Opus. Whether the codebase is 600 lines or 300,000. The tool set is configured at deployment, not at task time.

Our experiments showed this matters:
- Haiku with 9 tools: 40% pass. With 5 tools + principle: 100%. More tools overwhelms a weaker model.
- Sonnet with file tools + bash: $0.98. With structured tools only: $1.35. The right mix matters.
- Opus with the strategy instruction: 85% pass, $1.67. Without it: 100% pass, $1.15. The wrong instruction hurts a strong model.

A universal configuration is suboptimal for every model and every task. The Quartermaster selects the right configuration per task.

## The pattern

A fast, cheap pre-pass that reads the task description and selects:
1. **Which tools** to make available (the kit)
2. **Which strategy instruction** to include (the principle)
3. **Which constraints** to enforce (protected paths, sandbox bounds)

The Quartermaster runs once, before execution. It uses a weaker/cheaper model (Haiku) for the selection — it doesn't need deep reasoning, just pattern matching on task type and model capability.

## Three modes

### Secure (minimize grade)
Prefer structured tools. Avoid computation channels. Add the strategy instruction for weaker models. Accept the cost premium for characterizability.

### Efficient (minimize cost)
Match tools to what the model uses naturally. Give Sonnet file tools + bash (E). Give Haiku simple tools + principle (I). Give Opus minimal configuration (A). Avoid over-specification.

### Balanced (best tradeoff)
Structured tools where they add genuine capability (semantic tools for unfamiliar codebases). Bash where structured alternatives add overhead (running tests). Strategy instruction for models that benefit. No instruction for models that don't.

## The model profiles

The Quartermaster needs a model of model capabilities:

- **Haiku**: Needs focus. Fewer tools, clearer strategy. Wastes turns on tool selection when given too many options. Needs tools with simple interfaces — one operation, simple arguments. Benefits dramatically from the strategy instruction.
- **Sonnet**: Good tool selection. Naturally picks the right tool per operation. Handles larger tool sets. Benefits moderately from strategy. Can compose multi-step operations.
- **Opus**: Plans deeply on its own. May not need strategy instructions — it front-loads understanding naturally. More tools and more instruction can trigger over-analysis. Works best with minimal configuration.

These profiles can be hardcoded, learned from experimental data, or discovered via the Calibration Probe pattern.

## Implementation

```bash
# Phase 1: Quartermaster selects configuration
echo "$TASK_DESCRIPTION" | claude -p --model haiku --max-turns 1 \
    --system-prompt "$(cat quartermaster-balanced.md)"
# Returns: {"tool_groups": [...], "strategy": "...", "reasoning": "..."}

# Phase 2: Executor runs with selected configuration
echo "$TASK_DESCRIPTION\n\n$STRATEGY" | claude -p --model $TARGET_MODEL \
    --mcp-config $SELECTED_TOOLS --max-turns 50
```

## What the experiments actually showed

We tested nine tool configurations across three models. The Quartermaster's job is to predict which configuration works best — without running nine experiments per task.

### The optimal configurations (empirical)

| Model | Best config | Pass | Cost | Why it works |
|---|---|---|---|---|
| **Haiku** | Simple tools + run_tests + principle (I) | **100%** | $0.66 | Focus. Fewer tools, clear principle. |
| **Sonnet** | File tools + bash (E) | **100%** | $0.98 | Natural selection. Agent picks the right tool per operation. |
| **Opus** | Structured tools, no principle (A) | **100%** | $1.15 | Minimal config. Opus plans naturally. |

### The worst configurations (empirical)

| Model | Worst config | Pass | Cost | Why it fails |
|---|---|---|---|---|
| **Haiku** | File tools + bash (E) | **40%** | $0.62 | Too many choices. Haiku wastes turns selecting. |
| **Sonnet** | Four-phase strategy (G) | 100% | **$2.06** | Over-specification. Verbose compliance, not problem-solving. |
| **Opus** | Structured tools + principle (I) | **85%** | $1.67 | Over-analysis. The principle amplifies Opus's natural tendency to plan. |

The optimal for one model is the worst for another. Universal configuration is always wrong for at least one model.

## Kit manifests

The Quartermaster selects from pre-defined kits. Each kit specifies tools, strategy, and constraints:

### Bug diagnosis kit

```yaml
name: diagnose-bugs
tools:
  core: [file_read, file_edit, file_glob, file_write, run_tests]
  extended: [file_read_batch, file_edit_batch, file_search, file_search_context]
  semantic: [find_definitions, find_callers, code_structure]
strategy:
  haiku: "Do not start editing until you understand the full picture. Read the code, run the tests, and identify all the bugs first. Multiple test failures often share a root cause — find the root causes before fixing symptoms."
  sonnet: null  # Sonnet selects efficiently without guidance
  opus: null    # Opus plans naturally. Adding strategy hurts.
model_config:
  haiku:
    use: core                    # 5 tools. Simple interfaces only.
    strategy_required: true      # Essential — 40% → 100% pass rate.
  sonnet:
    use: core + extended         # 9 tools. Agent self-selects.
    strategy_required: false     # Helpful (-16% cost) but not essential.
    include_bash: true           # Sonnet's cheapest config uses bash for pytest.
  opus:
    use: core                    # Minimal. Opus doesn't need help.
    strategy_required: false     # Harmful — causes over-analysis.
```

### Code review kit

```yaml
name: code-review
tools:
  core: [file_read, file_glob, file_search]
  semantic: [code_structure, find_definitions, find_callers, find_imports]
strategy:
  all: "Read the full change set before forming an opinion."
model_config:
  haiku:
    use: core
    strategy_required: true
  sonnet:
    use: core + semantic
  opus:
    use: core + semantic
constraints:
  write_access: none             # Review is read-only
```

## The output format

The Quartermaster produces a JSON configuration that the runner consumes:

```json
{
  "tool_groups": ["simple_tools", "run_tests"],
  "strategy": "Do not start editing until you understand the full picture...",
  "constraints": {
    "protected_paths": ["tests/"],
    "max_turns": 50
  },
  "reasoning": "Haiku with a bug-fix task: use simple tools (fewer choices), add the principle instruction (essential for reliability), protect test files."
}
```

The runner translates this to MCP server configuration:
- `tool_groups` → `--condition` flag or dynamic tool enabling
- `strategy` → prepended to the task prompt
- `constraints` → sandbox spec and path protection
- `reasoning` → logged for audit

## The three-layer architecture

```
Layer 1: Quartermaster (before task)
  Input: task description + model name + available kits
  Output: selected kit + strategy + constraints
  Runs once. Uses Haiku (fast, cheap). 1-2 turns.

Layer 2: Mode Controller (during task)
  Input: tool call stream + failure counters
  Output: mode transitions (debug → implement → verify)
  Runs continuously. Specified rules, no LLM.

Layer 3: Calibration Probe (when uncertain)
  Input: first 3-5 tool calls of a new model
  Output: behavioral classification → profile update
  Runs when the Quartermaster's profiles are stale.
```

The Quartermaster configures. The Controller adapts. The Probe learns. Each operates at a different timescale: per-task, per-phase, per-model-version.

## The anti-pattern: universal configuration

A single CLAUDE.md with strategy instructions for all models. Works for the model it was tuned for, hurts the others. Our strategy instruction helped Haiku (+60% reliability) and Sonnet (-16% cost) but hurt Opus (-15% reliability, +45% cost). Universal instructions constrain everything the same way regardless of what's pulling.

The fix isn't "no instructions." It's "the right instructions for the model." The Quartermaster is the component that makes this selection — and the experimental data is what tells it which selection to make.

## Connection to Skills

The Quartermaster is a meta-skill. Each kit it selects IS a Skill — a named configuration with tools, strategy, and constraints. The Skills system in Claude Code already loads tools on demand. The Quartermaster adds model-aware selection: which skill to invoke depends on the model, not just the task.

Fledgling's modules map to kits: Code Navigation, Bug Diagnosis, Change Analysis, Refactoring. Each module is a Skill with a curated tool subset and model-aware strategy. See `~/Projects/source-sextant/main/docs/plans/skill-modules-from-experiments.md` for the full mapping.
