# CSS Selectors for Code

*We gave a code analysis tool the ability to query itself. The tool that parses 27 programming languages now parses its own query language — using its CSS grammar.*

---

## The problem

You have source code. You want to ask structural questions about it. Not "find the string `return`" — grep does that. Questions like:

- Functions that call `execute()` but have no `try` block
- Methods inside a specific class
- Import statements that precede class definitions
- Functions with returns at any nesting depth but no error handling

These questions share a property: they require knowing where things *are* relative to each other in the tree, not just whether they exist on a line. grep operates on lines. These questions operate on scopes.

## What we built

[Sitting Duck](https://github.com/teaguesterling/sitting_duck) is a DuckDB extension that parses source code into ASTs using tree-sitter grammars. It already had `ast_match` (pattern-by-example with wildcards) and relational operators (`ast_has`, `ast_inside`, `ast_precedes`, `ast_follows`). These work, but they require knowing tree-sitter's internal node type names.

We wanted something where you could just write what you mean. CSS selectors turned out to be almost exactly the right language:

```sql
-- Functions that call execute() but have no try block
SELECT name, start_line
FROM ast_select('src/**/*.py',
    '.function:has(.call#execute):not(:has(try_statement))');
```

The syntax maps directly:

| CSS | AST meaning |
|-----|-------------|
| `function_definition` | nodes of this type |
| `#main` | nodes named "main" |
| `.function` | semantic type (cross-language) |
| `A B` | B is a descendant of A |
| `A > B` | B is a direct child of A |
| `A ~ B` | B is a sibling after A |
| `:has(X)` | contains X somewhere inside |
| `:not(:has(X))` | does NOT contain X |

## The bootstrap

Here's the part that surprised us.

Sitting Duck already has a tree-sitter grammar for CSS — it's one of the 27 supported languages. So to parse the CSS selector string, we just call our own parser:

```sql
-- Inside ast_select, the selector is parsed by:
SELECT * FROM parse_ast('.function:has(return_statement)', 'css');
```

This produces a structured AST of the selector itself:

```
pseudo_class_selector
  class_selector
    class_name: "function"
  class_name: "has"
  arguments
    tag_name: "return_statement"
```

The macro walks this parsed selector AST to extract the type filter (`.function`), the pseudo-class (`:has`), and the argument (`return_statement`), then builds SQL conditions against the target code's AST. No string parsing, no regex, no custom parser. The CSS grammar does the heavy lifting.

The selector parsing takes 1ms. The structural query takes the rest.

## What it looks like

Find all methods in a JavaScript class:

```sql
SELECT name, start_line
FROM ast_select('src/*.js', 'class_body > method_definition');
```

```
constructor    8
login         13
generateToken 23
validateToken 27
```

Cross-language class discovery — one query, Python and JavaScript:

```sql
SELECT name, language, start_line
FROM ast_select('src/*.*', '.class');
```

```
AuthService        javascript   7
Config             python      10
DatabaseConnection python      25
UserService        python      51
```

The compound selector that grep can't express:

```sql
-- Functions with for-loops but no error handling
SELECT name, start_line, file_path
FROM ast_select('scripts/*.py',
    '.function:has(for_statement):not(:has(try_statement))');
```

13 functions. Each one a candidate for adding `try/except` around the loop body.

## Performance

We tested against Rosettacode — 834K AST nodes across 2,468 Python files:

| Query | Nodes | Time | Results |
|---|---|---|---|
| `function_definition` | 834K | 4.1s | 6,317 |
| `function_definition:has(return_statement)` | 834K | 4.4s | 4,833 |
| Compound `:has` + `:not(:has)` | 834K | 4.2s | 1,277 |
| Descendant combinator | 834K | 4.5s | 7,282 |

The equivalent `ast_has` call takes 3.7s on the same dataset. The CSS selector overhead is ~20% at this scale — the fixed cost of parsing and dispatching the selector is noise against 834K nodes.

The cross-language query across Python + Java + Go (2.5M nodes, 5,946 files) runs in 13.5 seconds and returns 10,526 results. One selector, three languages, no language-specific patterns.

On smaller codebases (58K nodes), queries return in ~120ms. Interactive.

### vs ripgrep

The obvious question: how does this compare to just using `rg`?

On the same 2,468 Python files:

| Tool | Query | Time | Result | Correct? |
|---|---|---|---|---|
| `rg` | `def ` line count | 0.22s | 6,170 lines | Lines, not functions |
| `rg` | multiline def...return (20-line window) | 0.25s | 2,332 | **Wrong** — off by 2x |
| `ast_select` | `function_definition:has(return_statement)` | 4.4s | 4,833 | Exact |
| `ast_select` | `function_definition:not(:has(return_statement))` | 4.5s | 1,484 | Exact — rg cannot express this |

rg is 20x faster but gives the wrong answer. Its multiline regex misses returns nested inside `if/for/try/with` blocks deeper than 20 lines, and has no concept of function boundaries — a `return` in the next function can false-match.

The negation query — "functions WITHOUT return" — rg cannot express at all. There is no regex for "a scope that does not contain a pattern."

The trade-off: 0.25s for an approximate answer, 4.5s for the exact one. For the negation: 0.25s for nothing, 4.5s for 1,484 results.

## The `.semantic` selector

The `.` (class) selector maps to semantic types — cross-language categories that abstract over language-specific node names:

| Selector | Matches |
|---|---|
| `.function` | `function_definition` (Python), `function_declaration` (JS), `func_declaration` (Go) |
| `.class` | `class_definition` (Python), `class_declaration` (JS) |
| `.call` | `call` (Python), `call_expression` (JS) |
| `.loop` | `for_statement`, `while_statement` (any language) |

Both `.function` and `.FUNCTION` work — case-insensitive.

## The `#name` selector

The `#` selector filters by the node's extracted name, like CSS ID selectors:

```sql
-- The function named "main"
SELECT * FROM ast_select('src/*.py', 'function_definition#main');

-- Calls to "execute"
SELECT * FROM ast_select('src/*.py', '.call#execute');
```

## What this required

Three changes to the sitting duck codebase:

1. **`ast_select` macro** (~300 lines of SQL) — parses the selector with `parse_ast(selector, 'css')`, extracts components by walking the selector AST, builds SQL conditions via a CASE dispatch. Single scan of the target AST, no UNION ALL.

2. **Relaxed wildcard child matching** — while building this, we discovered that `ast_match` patterns like `class __C__ { __M__(__) { } }` failed in JavaScript because the `async` keyword shifted child node positions. The fix: skip sibling-index verification for children of wildcard nodes. Now `__M__` matches methods regardless of modifiers.

3. **`sibling_index` changed from UINT32 to INT32** — DuckDB's unsigned arithmetic made `sibling_index - 1` overflow when `sibling_index = 0`. A one-line type change that eliminated an entire class of bugs.

## Why CSS

We considered tree-sitter's native S-expression query language, a custom DSL, and CSS. CSS won because:

- **Familiarity** — every web developer already knows it
- **The grammar already exists** — tree-sitter-css ships with the extension
- **The concepts map naturally** — descendant selectors, child selectors, sibling selectors, `:has()`, `:not()` all have direct AST equivalents
- **We could bootstrap** — parsing the selector with the extension's own CSS grammar is both elegant and zero-dependency

The semantics aren't identical to CSS (`.class` maps to semantic types, not HTML classes; `#name` maps to identifiers, not HTML IDs), but the mental model transfers perfectly. If you can write `div.active:has(> span.highlight)`, you can write `function_definition:has(> return_statement)`.

## What's next

The selector language is deliberately minimal for v1. Planned additions:

- **`:scope(type)`** — scope-aware matching that excludes nested scopes (solves the "outer function reports inner function's calls" problem)
- **`:precedes()` / `:follows()`** — reverse-direction sibling queries that CSS can't express
- **`:first-child`, `:nth-child(n)`** — standard CSS positional pseudo-classes
- **Captures** — `function_definition@F:has(return_statement@R)` for extracting matched sub-expressions
- **NAME_ROLE flags** — `is_name_definition()`, `is_name_reference()`, `is_scope()` for variable resolution queries (already shipped)

The foundation is there. The CSS grammar does the parsing. The AST schema does the querying. The extension bootstraps itself.

---

*Sitting Duck is open source: [github.com/teaguesterling/sitting_duck](https://github.com/teaguesterling/sitting_duck)*

*Available as a DuckDB community extension: `INSTALL sitting_duck FROM community; LOAD sitting_duck;`*
