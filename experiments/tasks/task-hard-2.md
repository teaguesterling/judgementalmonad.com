The `qualified_name` column in the AST output is currently NULL for all languages. It needs to be populated during the tree-sitter walk as a scoped breadcrumb path.

The algorithm:
1. The root/file node gets qualified_name = filename
2. Track the last named ancestor as you walk the tree
3. When you encounter a named node, set: qualified_name = parent.qualified_name + "::" + node.name

For example, in Python:
- A top-level function `foo` → `main.py::foo`
- A method `bar` inside class `MyClass` → `main.py::MyClass::bar`
- A nested function `inner` inside `foo` → `main.py::foo::inner`

Implement this in the C++ tree-sitter walker where AST nodes are produced. The qualified_name should be computed during the existing tree walk, not as a post-processing step.

Success criteria:
- qualified_name is non-NULL for all named nodes
- The breadcrumb path correctly reflects scope nesting
- Works for at least Python, JavaScript, and Rust
- Existing tests still pass (no regressions in other columns)
- Write a brief design note to `qualified-name-notes.md` explaining your approach
