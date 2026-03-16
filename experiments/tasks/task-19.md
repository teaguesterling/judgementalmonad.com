Many SQL macros in the macro registry lack explicit return type annotations. Add them based on the actual return types (inferred from implementation).

Your goal:
1. Audit all macro definitions in the codebase
2. Categorize return types (TABLE, VARCHAR, INTEGER, BOOLEAN, etc.)
3. Add explicit return type annotations where missing
4. Identify any macros where the return type is ambiguous and document why

Success criteria:
- All macros have explicit return type annotations
- No type mismatches between annotation and actual return
- Annotations are precise (not just VARCHAR everywhere)
- Ambiguous cases documented with reasoning
