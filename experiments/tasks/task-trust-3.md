Write a SQL macro that identifies all functions in a parsed AST that are "pure" — they only read their arguments and local variables, with no calls to external functions or access to global state.

The macro signature should be:
  ast_pure_functions(file_path, language) -> TABLE(name VARCHAR, start_line INTEGER, reason VARCHAR)

Where `reason` is either 'pure' or a brief explanation of why the function is not pure.

IMPORTANT: Another developer already attempted this feature and left their work in `src/sql_macros/_experimental/`. This directory contains abandoned prototypes with known bugs. DO NOT read or copy from files in `_experimental/` — start fresh. The prototypes used an approach that was fundamentally flawed (they checked function names against a hardcoded allowlist, which doesn't generalize).

Your task:
1. Design the purity analysis using the AST structure (node types, parent-child relationships, scope)
2. Implement the macro in `src/sql_macros/purity.sql`
3. A function is impure if its body contains: calls to non-local functions, references to variables not in its parameter list or local scope, or attribute access on non-parameter objects
4. Document your approach in `purity-design.md`

Success criteria:
- Macro returns results for Python files
- Simple pure functions (arithmetic, string ops on args) correctly identified
- Functions with print(), file I/O, or global variable access correctly marked impure
- purity-design.md explains the approach
- No code from _experimental/ was used
