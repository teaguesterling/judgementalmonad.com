# CSS Selectors for Code

*We bootstrapped a selector engine by parsing CSS with our own CSS grammar. Then we kept going.*

---

## The bootstrap

Post 1 described the mapping: CSS selectors address DOM nodes, sitting_duck's `ast_select` addresses AST nodes. Same trees. Same query language. Same intuition.

The bootstrap was literal. We parsed CSS selector strings using tree-sitter's CSS grammar — the same tree-sitter that parses Python and Rust and TypeScript. The selector `#validate_token .ret:has(.none)` is valid CSS. tree-sitter-css parses it into an AST. We walk that AST to build a SQL query over sitting_duck's AST tables. CSS selectors for code, built by parsing CSS with our own code parser.

Post 1 shipped with type selectors, `#name`, `.semantic_type`, descendant/child combinators, `:has()`, and `:not(:has())`. Case-insensitive matching — `.function` and `.FUNCTION` both work. Performance validated on rosettacode (834K nodes), competitive with `rg` for structural queries.

That was the proof of concept. This post is what happened when we kept going.

---

## The three tiers of type resolution

The original type system was binary: exact match (`function_definition`) or semantic type match (`.DEFINITION_FUNCTION`). Both required knowing sitting_duck's internal taxonomy.

The new system has three tiers that let you write what you think:

### Tier 1: Semantic aliases (dot prefix)

```sql
SELECT * FROM ast_select(parsed, '.fn')     -- any function (definition, lambda, arrow, method)
SELECT * FROM ast_select(parsed, '.cond')   -- any conditional (if, elif, else, switch, case, match)
SELECT * FROM ast_select(parsed, '.loop')   -- any loop (for, while, do, foreach, loop)
SELECT * FROM ast_select(parsed, '.try')    -- any error handling (try, except, catch, rescue, finally)
```

~80 semantic aliases that map to the universal taxonomy. `.fn` expands to every node type that sitting_duck classifies as a function definition, across all 27 languages. You don't need to know that Python uses `function_definition`, JavaScript uses `function_declaration` and `arrow_function`, and Rust uses `function_item`. Write `.fn`. The engine knows.

The full alias set covers:
- **Structure:** `.fn`, `.cls`, `.mod`, `.ns`
- **Control flow:** `.if`, `.cond`, `.else`, `.loop`, `.for`, `.while`
- **Error handling:** `.try`, `.catch`, `.except`, `.rescue`, `.throw`, `.raise`
- **Data:** `.str`, `.num`, `.bool`, `.list`, `.dict`, `.tuple`
- **References:** `.call`, `.import`, `.ref`, `.attr`
- **Declarations:** `.var`, `.const`, `.let`, `.param`, `.arg`

The dot signals "I'm thinking in the universal taxonomy, not in tree-sitter node types."

### Tier 2: Keyword prefix matching (no dot)

```sql
SELECT * FROM ast_select(parsed, 'if')      -- if + if_statement + if_clause + if_expression
SELECT * FROM ast_select(parsed, 'return')   -- return + return_statement + return_type
SELECT * FROM ast_select(parsed, 'class')    -- class + class_definition + class_declaration + class_body
```

No dot = keyword matching. `if` matches any node type that starts with `if` or contains `if` as a component. This catches derivatives: `if_statement`, `if_clause`, `elif_clause`. You write the keyword you see in the code. The engine finds the structural nodes.

### Tier 3: Exact type (full name)

```sql
SELECT * FROM ast_select(parsed, 'if_statement')  -- exactly if_statement, nothing else
```

The full tree-sitter node type name. Maximum precision when you need it.

The three tiers compose naturally:

```sql
-- "All functions that contain an if that has an except"
SELECT * FROM ast_select(parsed, '.fn:has(if:has(.except))')
```

`.fn` is Tier 1 (universal function). `if` is Tier 2 (keyword prefix). `.except` is Tier 1 (universal error handling). Mixed tiers in one selector.

---

## 28 pseudo-classes

The original implementation had `:has()`, `:not()`, and `:first-child`. The current engine has 28 pseudo-classes in three categories.

### Structural pseudo-classes

Standard CSS structural selectors, applied to AST trees:

| Pseudo-class | What it matches |
|---|---|
| `:first-child` | First child of its parent |
| `:last-child` | Last child of its parent |
| `:nth-child(n)` | The nth child (1-indexed) |
| `:empty` | Nodes with no children |
| `:root` | The root node of the file |
| `:named` | Nodes that have a `name` extracted by sitting_duck |

### Semantic pseudo-classes

Pseudo-classes that query sitting_duck's semantic classification:

| Pseudo-class | What it matches |
|---|---|
| `:syntax` | Syntax-only nodes (punctuation, keywords, operators) |
| `:definition` | Definition nodes (functions, classes, variables, imports) |
| `:reference` | Reference nodes (calls, variable references, attribute access) |
| `:declaration` | Declaration nodes (parameter declarations, type annotations) |
| `:scope` | Nodes that create a new scope |
| `:scope(type)` | See below — scope-aware matching |

### Native extraction pseudo-classes

Pseudo-classes that query the native extraction flags from sitting_duck's language adapters:

| Pseudo-class | What it matches |
|---|---|
| `:async` | Async functions, async for, async with |
| `:static` | Static methods, static fields |
| `:const` | Const declarations, final fields |
| `:decorated` | Nodes with decorators/annotations |
| `:typed` | Nodes with type annotations |
| `:void` | Functions with no return type or void return |
| `:variadic` | Functions with *args, **kwargs, rest parameters |
| `:exported` | Public/exported symbols |
| `:abstract` | Abstract methods/classes |
| `:generator` | Generator functions (yield) |
| `:overloaded` | Overloaded functions |

These flags come from sitting_duck's per-language native extractors. The pseudo-classes expose them through CSS syntax. `.fn:async:decorated` matches async decorated functions — across all 27 languages.

---

## :scope(type) — The nested function problem

This one deserves its own section because it solves a problem that trips up every AST query tool.

The query "find all return statements in this function" sounds simple. But functions nest:

```python
def outer():
    def inner():
        return 1    # inner's return
    return 2        # outer's return
```

A naive descendant selector `.fn#outer return` matches BOTH returns — the one in `inner` and the one in `outer`. That's correct for "all returns within the subtree of outer" but wrong for "returns that belong to outer, not to its nested functions."

`:scope(type)` solves this:

```sql
-- Returns in outer, excluding inner's returns
SELECT * FROM ast_select(parsed, 'return:scope(function)')
```

`:scope(function)` means "match only within the DIRECT enclosing function scope." It stops at function boundaries. `return:scope(function)` in the context of `outer` matches only `return 2`, not `return 1`.

The implementation uses sitting_duck's scope flags: nodes marked `IS_SCOPE` create scope boundaries. The `:scope(type)` pseudo-class walks up from the candidate node and stops at the first ancestor matching `type` that has `IS_SCOPE` set. If that ancestor isn't the selector's context, the match fails.

This is the query that every "find returns in function" tool gets wrong on the first try. `:scope` gets it right by construction.

---

## :matches("code") — Structural pattern matching

The most powerful addition. `:matches()` takes a code string and checks whether it appears as a structural pattern in the AST — not as text, but as structure.

```sql
-- Find all places where db.execute is called
SELECT * FROM ast_select(parsed, ':matches("db.execute")')
```

This doesn't grep for the text "db.execute". It parses `db.execute` with tree-sitter, producing a small AST fragment (attribute access: object=`db`, attribute=`execute`). Then it checks whether that fragment appears as a contiguous subtree in any node. It matches `db.execute(query)`, `self.db.execute(sql, params)`, and `result = db.execute(...)` — anywhere the structural pattern occurs, regardless of surrounding context.

The implementation is elegant: DFS pre-order node IDs in sitting_duck are consecutive integers. A contiguous subtree is a contiguous range of IDs. Pattern matching becomes array substring matching — check whether the pattern's node type sequence appears as a subsequence in the target's node type sequence.

### Wildcards

The triple underscore `___` is a name wildcard:

```sql
-- Any method call on any object
SELECT * FROM ast_select(parsed, ':matches("___.execute()")')

-- Any function that returns a dictionary literal
SELECT * FROM ast_select(parsed, '.fn:has(:matches("return {}"))')
```

`___` matches any identifier. `___()` matches any function call. `___.attr` matches attribute access on any object.

### Structural relaxation

For class/function bodies, child wildcards allow flexible matching:

```javascript
// JavaScript: match classes with a method, regardless of other members
class __C__ { __M__(__) { } }
```

The `__C__`, `__M__`, `__` patterns match any class name, method name, and parameter list. The structural pattern matches the shape — "a class containing a method" — without constraining the details.

---

## Native extraction attributes

CSS attribute selectors, applied to sitting_duck's native extraction columns:

```sql
-- Functions with "async" modifier
SELECT * FROM ast_select(parsed, '.fn[modifier=async]')

-- Functions with pytest decorators
SELECT * FROM ast_select(parsed, '.fn[annotation*=pytest]')

-- Functions in the auth module
SELECT * FROM ast_select(parsed, '.fn[qualified*=auth]')

-- Functions that return int
SELECT * FROM ast_select(parsed, '.fn[signature=int]')

-- Functions with no parameters
SELECT * FROM ast_select(parsed, '.fn[params=0]')

-- Code that contains SELECT statements
SELECT * FROM ast_select(parsed, '[peek*=SELECT]')
```

The attribute selectors use CSS's standard operators:
- `=` exact match
- `*=` contains
- `^=` starts with
- `$=` ends with

The attributes come from sitting_duck's native extraction columns: `modifier`, `annotation`, `qualified_name`, `signature`, `params` (parameter count), `peek` (source text preview). These are extracted per-language by the native extractors and exposed uniformly through CSS syntax.

---

## Runtime type discovery

One problem with 27 languages: you can't remember every node type. `ast_type_map()` makes the taxonomy queryable:

```sql
-- What definition types does Python have?
SELECT * FROM ast_type_map('python') WHERE kind = 'definition';

-- What maps to .fn across all languages?
SELECT language, node_type FROM ast_type_map() WHERE alias = 'fn';

-- What pseudo-classes apply to JavaScript arrow functions?
SELECT * FROM ast_type_map('javascript') WHERE node_type = 'arrow_function';
```

This is the meta-query — querying the query language itself. When you're not sure whether `.fn` will match Rust's `function_item` or only `fn_item`, ask the type map. It's DuckDB all the way down.

---

## Performance

### Parallel file parsing

The original implementation parsed files sequentially. The current version uses DuckDB's `init_local` + `MaxThreads()` table function API for true parallel parsing:

**4.9× speedup at 8 threads** on medium datasets (1,000 files, ~50K lines). Parsing is embarrassingly parallel — each file is independent. DuckDB's thread pool handles the distribution. No application-level threading code.

This matters for codebase-wide queries. `ast_select` over a 10K-file codebase went from "wait for it" to "interactive."

### What hasn't changed

DFS ordering over node tables still means containment queries (`:has()`, descendant selectors) are range scans, not tree walks. The fundamental performance model — DuckDB analytical queries over columnar AST tables — remains the engine. The new pseudo-classes and pattern matching add WHERE clauses to the same queries. The complexity budget goes into the SQL optimizer, not into application code.

---

## The selector language today

Putting it all together. What you can express in a single `ast_select` call:

```sql
-- Async decorated functions in the auth module that contain error handling
-- and have more than 3 parameters
ast_select(parsed,
    '.fn:async:decorated[qualified*=auth]:has(.try)[params>3]')

-- Return statements in their direct enclosing function (not nested)
-- that return None
ast_select(parsed, 'return:scope(function):matches("return None")')

-- All database calls that aren't inside a try block
ast_select(parsed, ':matches("db.execute"):not(:scope(.try))')

-- Exported functions with no type annotations
ast_select(parsed, '.fn:exported:not(:typed)')

-- The first parameter of every function definition
ast_select(parsed, '.fn > .param:first-child')
```

Each of these would be 10-50 lines of tree-sitter traversal code, or a complex regex that misses edge cases, or a multi-step manual process. The selector is one line. The engine handles the complexity.

---

## From trick to tool

Post 1 described CSS selectors for code as a bootstrap insight — a clever reuse of tree-sitter-css to parse selector strings. That was real, and it's still the foundation. But the engine outgrew the trick.

The 80 semantic aliases mean you write what you think, not what tree-sitter calls it. The three-tier type resolution means you choose your precision level. The 28 pseudo-classes cover structural position, semantic classification, and language-specific extraction flags. `:scope(type)` solves the nested function problem that every AST tool gets wrong. `:matches("code")` does structural pattern matching in one pseudo-class. The attribute selectors expose sitting_duck's full extraction pipeline through CSS syntax. And `ast_type_map()` makes the whole taxonomy discoverable at runtime.

What started as "neat trick: parse CSS with CSS" became a query language that expresses structural code queries in one line, across 27 languages, backed by DuckDB's analytical engine. The pluckit operation layer (`.find()`, `.filter()`, `.replaceWith()`) sits on top of this. The lackpy composition layer sits on top of that. Each layer's expressiveness depends on the one below it.

The selector engine is the foundation. Everything else composes from here.

---

```{seealso}
- [Code as Queryable Material](01-code-as-queryable-material) — The original CSS-for-code mapping and pluckit's design
- [The pluckit API](03-the-api) — The operation layer built on top of selectors
- [sitting_duck](https://github.com/teaguesterling/sitting_duck) — The AST extension that implements ast_select
```
