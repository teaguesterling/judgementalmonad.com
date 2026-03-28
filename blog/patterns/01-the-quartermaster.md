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

## The anti-pattern: universal configuration

A single CLAUDE.md with strategy instructions for all models. Works for the model it was tuned for, hurts the others. Our strategy instruction helped Haiku (+60% reliability) and Sonnet (-16% cost) but hurt Opus (-15% reliability, +45% cost). Universal instructions are the throat harness — they constrain everything the same way regardless of what's pulling.

## Connection to Skills

The Quartermaster is a meta-skill. Each kit it selects IS a Skill — a named configuration with tools, strategy, and constraints. The Skills system in Claude Code already loads tools on demand. The Quartermaster adds model-aware selection: which skill to invoke depends on the model, not just the task.

## What's next

The Quartermaster needs the Calibration Probe (pattern 3) for unknown models and the Mode Controller (pattern 7) for mid-task reconfiguration. Together they form a three-layer system: configure before (Quartermaster), monitor during (Controller), probe when uncertain (Calibration).
