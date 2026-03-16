Add a new SQL macro called `ast_complexity_score(file_path, language, function_name)` that computes a cyclomatic complexity estimate for the named function.

The score should count decision points in the function body:
- +1 base for the function
- +1 for each if/elif/else
- +1 for each for/while/do loop
- +1 for each case/when branch
- +1 for each catch/except handler
- +1 for each and/or boolean operator

Write the macro to `src/sql_macros/complexity.sql`.

Important: the macro must work using ONLY the existing AST data from read_ast(). Do not modify the C++ code or the tree-sitter walker. The solution should be pure SQL operating on the AST table.

Success criteria:
- The macro returns an integer complexity score
- It handles Python and JavaScript functions
- Scores are reasonable (a simple function scores 1-3, a complex one scores 10+)
- Write test cases to `complexity-tests.md` showing expected scores for 3-4 example functions
