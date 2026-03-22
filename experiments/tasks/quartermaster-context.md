## Model profiles

- **haiku**: Fast, cheap, limited reasoning. Struggles with complex tool interfaces (batch tools with list-of-dict arguments). Benefits dramatically from clear strategy instructions. Fails when given too many tool choices — wastes turns on tool selection instead of problem-solving. Best with simple, familiar tools and a one-sentence principle.
- **sonnet**: Strong reasoning, good tool selection. Naturally selects the right tool per operation when given multiple options. Handles batch tools well. Benefits moderately from strategy instructions. Can compose bash operations fluently. Performs well across most configurations.
- **opus**: Deep reasoning, plans naturally. May not need strategy instructions — it front-loads understanding on its own. Generates more output tokens (thorough reasoning). Handles any tool set. Cost per run is higher due to deeper thinking, not inefficiency.

## Available tool groups

- **simple_tools**: `file_read` (read one file), `file_edit` (replace one string in one file), `file_glob` (find files by pattern), `file_write` (write a file). *Why: the atomic operations every coding task needs. Simple interfaces any model can use.*
- **batch_tools**: `file_read_batch` (read multiple files in one call), `file_edit_batch` (apply multiple edits in one call), `file_glob`, `file_write`. *Why: reduces round-trip overhead for models that can construct complex arguments. Requires list-of-dict inputs — harder for small models.*
- **semantic_tools**: `find_definitions` (AST-aware definition search), `find_callers` (find call sites), `code_structure` (structural outline), `find_imports` (import graph). *Why: provides code understanding that text search can't — knows about functions, classes, scope. Useful for navigating unfamiliar codebases.*
- **run_tests**: Run pytest on the test suite (read-only, sandboxed). *Why: structured verification — the agent can check its work without bash. The test files can't be modified.*
- **bash_readonly**: Execute read-only bash commands (cat, grep, find, etc.) in a sandbox. *Why: flexible exploration without mutation risk. The agent can probe the codebase but can't change it through bash.*
- **bash_sandboxed**: Execute any bash command in a sandboxed environment. *Why: full computation channel — the agent can write scripts, run code, iterate. Most flexible but hardest to characterize. The agent thinks in programs, which can be more efficient than atomic tool calls.*
