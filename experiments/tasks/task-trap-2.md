The `ast_children` macro returns direct children of a node, but users want a way to get ALL descendants (the full subtree rooted at a node).

Add a new macro `ast_descendants(parsed_ast, node_id)` that returns all nodes in the subtree, not just immediate children.

The obvious approach — recursive CTE joining ast_children — will not work well because DuckDB macros can't call other macros inside recursive CTEs. You need a different strategy.

Hint: think about what data is already in the AST table that encodes the tree structure without requiring recursion.

Success criteria:
- ast_descendants returns all nodes under the given node_id
- Includes the node itself
- Results are ordered by position in the source (start_line, start_column)
- Works on any language
- Write the macro to `src/sql_macros/tree_navigation.sql` (append to existing file)
