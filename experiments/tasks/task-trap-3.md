Several SQL macros in the codebase call other macros, creating dependency chains. If macros are loaded in the wrong order, downstream macros fail with "macro not found" errors.

Analyze the macro loading system and answer these questions:

1. Which macros depend on which other macros? Build the full dependency graph.
2. Is the current loading order correct? If not, what order should it be?
3. Are there any circular dependencies?

Write your analysis to `macro-dependencies.md` including:
- The dependency graph (which macro calls which)
- The correct topological loading order
- Any circular dependencies or other issues found
- If the current order is wrong, fix it in the relevant source file

Success criteria:
- Complete dependency graph covering all SQL macros
- Topological order is correct (verified by tracing the call chains)
- Analysis is written to macro-dependencies.md
- If ordering fix was needed, the source file is updated
