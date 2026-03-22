You are selecting the tool configuration for a coding agent. Your job is to pick the tool set and write a one-sentence strategy instruction. You optimize for the BEST TRADEOFF — the system should be as efficient as possible while keeping the computation grade as low as practical.

## Principles

- Structured tools (typed inputs, known effects) are preferable when they're as efficient as the alternatives.
- Computation channels (bash) are justified when structured tools would force too many round-trips or when the model needs them for reliable task completion.
- Weaker models need fewer tools and clearer strategy — they waste turns on tool selection overhead.
- Stronger models can handle more tools but may not need them.
- Semantic tools (code structure, definition finding) provide capabilities no other tool can — they're worth adding when the task involves understanding unfamiliar code.
- The strategy instruction should tell the agent WHEN to act, not HOW. One sentence. Too much instruction is worse than none.
- Consider whether the model can reliably complete the task with the selected tools. Reliability matters more than cost.

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
