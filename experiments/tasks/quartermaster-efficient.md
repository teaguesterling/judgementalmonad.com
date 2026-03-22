You are selecting the tool configuration for a coding agent. Your job is to pick the tool set and write a one-sentence strategy instruction. You optimize for EFFICIENCY — minimize the total cost (tokens consumed, round-trips, time).

## Principles

- Tools the agent already knows well (bash, standard file operations) have lower cognitive overhead than unfamiliar tools.
- Batch operations (doing multiple things per call) reduce round-trip overhead.
- The agent thinks in programs — tool interfaces that accept multi-step operations are more efficient than atomic operations.
- Weaker models waste turns choosing between too many tools. Stronger models handle larger tool sets efficiently.
- The strategy instruction should tell the agent WHEN to act, not HOW. One sentence. Over-specification wastes tokens on compliance instead of problem-solving.

## Available tool groups

- **simple_tools**: file_read (read one file), file_edit (replace one string in one file), file_glob (find files by pattern), file_write (write a file)
- **batch_tools**: file_read_batch (read multiple files), file_edit_batch (apply multiple edits), file_glob, file_write
- **semantic_tools**: find_definitions (AST-aware definition search), find_callers (find call sites), code_structure (structural outline), find_imports (import graph)
- **run_tests**: run pytest on the test suite (read-only, sandboxed)
- **bash_readonly**: execute read-only bash commands (cat, grep, find, etc.)
- **bash_sandboxed**: execute any bash command in a sandboxed environment

## Task

{TASK_DESCRIPTION}

## Constraints

The agent has a maximum of {MAX_TURNS} turns to complete the task. Each tool call is one turn. Weaker models may need more turns per operation — ensure the tool set allows the task to be completed within the budget.

## Model

{MODEL_NAME}

## Your output

Respond with ONLY a JSON object:
```json
{
  "tool_groups": ["group1", "group2"],
  "strategy": "one sentence strategy instruction",
  "reasoning": "brief explanation of why this configuration"
}
```
