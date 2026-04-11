# CSS Selectors for Code

*We gave a code analysis tool the ability to query itself. The tool that parses 27 programming languages now parses its own query language — using its CSS grammar. Then we gave it declaration blocks, because "find this code" and "show me this code" are the same query with different back-ends.*

> The full selector reference — every pseudo-class, every combinator, every attribute operator — lives in the [Sitting Duck docs](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/). This post is the design story and the shape of the language, not the exhaustive reference.

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
    '.func:has(.call#execute):not(:has(.try))');
```

The syntax maps directly:

| CSS | AST meaning |
|-----|-------------|
| `.func` | semantic type — cross-language (function_definition in Python, function_declaration in JS, func_declaration in Go, …) |
| `function` | bare keyword — tree-sitter prefix match (function_definition, function_expression, …) |
| `function_definition` | exact tree-sitter type |
| `#main` | node named "main" |
| `[name^=test_]` | attribute selector: name starts with `test_` |
| `A B` | B is a descendant of A |
| `A > B` | B is a direct child of A |
| `A + B` | B is the adjacent next sibling of A |
| `A ~ B` | B is a later sibling of A |
| `:has(X)` | contains X somewhere inside |
| `:not(:has(X))` | does NOT contain X |
| `::callers` | navigate — return functions that call this node |

Three tiers of type specificity matter enough to name. `.func` is the broadest, cross-language alias — it matches across all 27 languages via the semantic layer. `function` is a language-specific tree-sitter prefix. `function_definition` is exactly that one tree-sitter node type. Pick the tier that matches the question you're asking: cross-language audits use `.func`; debugging a single language uses bare keywords; forensics on one grammar uses exact types.

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
| `.func` (or `.fn`, `.function`, `.method`) | `function_definition` (Python), `function_declaration` (JS), `func_declaration` (Go) |
| `.class` (or `.cls`, `.struct`, `.trait`, `.interface`) | `class_definition` (Python), `class_declaration` (JS) |
| `.call` | `call` (Python), `call_expression` (JS) |
| `.loop` (or `.for`, `.while`) | `for_statement`, `while_statement`, `do_statement` (any language) |
| `.if` (or `.cond`, `.conditional`) | all conditionals: `if`, `elif`, `else`, `switch`, `case`, `match` |
| `.jump` (or `.return`, `.break`, `.continue`, `.yield`) | all unconditional control transfers |
| `.try` / `.catch` / `.throw` | error handling constructs |
| `.var` / `.const` | variable definitions |
| `.import` / `.export` | module-level bindings |

The semantic layer is about ~80 aliases organized into kinds (`.def`, `.flow`, `.error`) and super-types. Both `.func` and `.FUNC` work — case-insensitive. Full table: [Semantic Type Aliases](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/kinds-types-and-classes.html).

## The `#name` selector and `[attr]` operators

The `#` selector filters by the node's extracted name, like CSS ID selectors. Attribute selectors extend this to substring, prefix, and suffix matches on names and other metadata:

```sql
-- The function named "main"
SELECT * FROM ast_select('src/*.py', '.func#main');

-- Everything that looks like a test: name starts with test_
SELECT name FROM ast_select('src/**/*.py', '.func[name^=test_]');

-- Handlers: name ends with _handler
SELECT name FROM ast_select('src/**/*.py', '.func[name$=_handler]');

-- Anything auth-related
SELECT name FROM ast_select('src/**/*.py', '.func[name*=auth]');

-- Zero-parameter functions (metadata, not just name)
SELECT name FROM ast_select('src/**/*.py', '.func[params=0]');

-- Comments containing TODO (source text match)
SELECT peek FROM ast_select('src/**/*.py', 'comment[peek*=TODO]');

-- Async functions
SELECT name FROM ast_select('src/**/*.js', '.func[modifier=async]');
```

Shorthand pseudo-classes exist for the common modifiers: `:async`, `:static`, `:abstract`, `:const`, `:public`, `:private`, `:decorated`, `:typed`, `:void`, `:variadic`. They compose with everything else.

## Scope-aware queries: the pseudo-class that changed the shape of the answer

`:has` gets you most of the way there, but it can't tell the difference between "this function calls `execute`" and "this function contains a nested function that calls `execute`." Both nodes satisfy the descendant relation. For large codebases that distinction is the difference between a useful answer and a noisy one.

`:scope(type)` fixes it. The selector matches within the nearest ancestor of the given type, **excluding subtrees of nested ancestors of the same type**:

```sql
-- Return statements inside their DIRECT enclosing function
-- (skips returns that live in nested inner functions)
SELECT peek FROM ast_select('src/**/*.py', 'return_statement:scope(function)');

-- Calls inside the nearest class, not the one three levels down
SELECT name FROM ast_select('src/**/*.py', '.call:scope(class)');
```

The same machinery powers a set of call-graph pseudo-classes that are more ergonomic than writing the scope logic by hand:

```sql
-- Functions that call execute (direct scope only, no nested-function noise)
SELECT name FROM ast_select('src/**/*.py', '.func:calls(execute)');

-- All calls made by main()
SELECT name FROM ast_select('src/**/*.py', '.call:called-by(main)');

-- Unused functions: defined but never called
SELECT name FROM ast_select('src/**/*.py', '.func:not(:is-called)');

-- Dead exports: public API that nothing references
SELECT name FROM ast_select('src/**/*.py', ':exported:not(:is-referenced)');
```

These answers were possible before — you could JOIN `ast_callees` against `ast_exports` and get there — but they required knowing the schema. The pseudo-class makes the common question a one-liner. The uncommon question still has the macros underneath.

## Navigation: pseudo-elements that return different nodes

Pseudo-classes filter the matched set. Pseudo-elements *move* from it — they navigate from matched nodes to related ones.

```sql
-- Who calls validate?
SELECT name FROM ast_select('src/**/*.py', '.func#validate::callers');

-- What does main() call?
SELECT name FROM ast_select('src/**/*.py', '.func#main::callees');

-- The class containing this method
SELECT name FROM ast_select('src/**/*.py', '.func#login::parent-definition');

-- The function a return_statement belongs to (walk up to the nearest definition)
SELECT peek FROM ast_select('src/**/*.py', 'return_statement::parent-definition');
```

Pseudo-elements available: `::parent`, `::scope`, `::parent-definition`, `::next-sibling`, `::prev-sibling`, `::callers`, `::callees`. Full reference: [Pseudo-Classes and Pseudo-Elements](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/pseudo-classes.html).

## Declaration blocks: "find this" becomes "show me this"

The original selector language answered *which nodes match?* It returned rows. The follow-up question, asked over and over, was: *okay, show me the code.* Agents don't want rows — they want source text with enough context to reason about.

So we added the other half of CSS. A selector can now be paired with a **declaration block** that controls how the match is rendered:

```
.fn#main                              -- bare selector: default rendering
.fn#main { show: body; }              -- full function body
.class#Config { show: outline; }      -- class signature + method signatures
.func[name^=test_] { show: signature; }  -- just the def line for every test
.call#execute:not(:has(.try)) { show: enclosing; }  -- unsafe call, rendered with its scope
```

The output is markdown code blocks with location headers, not AST rows:

````markdown
# src/my_module.py:12-18
```python
def main(argv):
    """Entry point."""
    config = parse_args(argv)
    return run(config)
```
````

The `show` property picks which slice of the matched node appears:

| Value | Behavior |
|---|---|
| `body` | The full matched node — default for functions, calls, statements. |
| `signature` | Declaration line(s) only — `def foo(x, y):` with no body, `class Foo(Bar):` with no methods. |
| `outline` | Signature plus child signatures with no bodies — default for classes and modules. |
| `enclosing` | Walks up to the nearest function/class and renders that with `show: body`. Useful when the bare match (a call site, a return) lacks context. |

Defaults are type-specific: `.fn`/`.call`/`.return` default to `body`; `.class`/`:root` default to `outline`. The whole language parses as `selector (declaration_block)?`, so a bare selector is equivalent to `{ show: body }`.

This is the layer that makes sitting duck usable as an **AST viewer**, not just a query engine. The same CSS string that filters nodes also tells the viewer how to present them. One grammar, two back-ends — a relational one that returns rows, and a rendering one that returns formatted source. And because declarations are parsed as forward-compatible key-value pairs, future additions (`trace: callers; depth: 2`, `expand: .fn#__init__`, `show: call-site`) can land without breaking existing queries.

For agents this matters more than it sounds. An agent that asks "show me the main function" wants *the function* — formatted, language-tagged, with a path header it can cite. Not a tuple of `(start_line, end_line, node_id)` that it has to re-query to read. The declaration block closes the loop.

## Scope resolution and call graphs as macros

Underneath the pseudo-classes there's a small family of macros that expose the raw scope and call-graph relations, for when you need a JOIN instead of a one-liner:

```sql
-- Module-level public API
SELECT name, type FROM ast_exports('src/**/*.py');

-- Reference → definition resolution via scope walk
SELECT ref_name, ref_line, def_line, def_type, scope_hops
FROM ast_resolve('src/main.py');

-- Call graph: every (caller, callee) pair
SELECT caller, callee, COUNT(*) AS n
FROM ast_callees('src/**/*.py')
GROUP BY caller, callee ORDER BY n DESC;

-- Cross-file call graph via import resolution
SELECT c.caller, c.callee, c.file_path AS caller_file, ex.file_path AS callee_file
FROM ast_callees('src/**/*.py') c
JOIN ast_exports('src/**/*.py') ex ON ex.name = c.callee
WHERE c.file_path != ex.file_path;
```

Every node in `read_ast()` output has a `scope_id` (the nearest enclosing scope boundary) and scope-creating nodes carry a `scope_stack` (the full chain from root). `:scope(type)`, `:calls()`, `:called-by()`, `ast_resolve`, `ast_callees`, and `ast_callers` all build on those two columns. The CSS layer is the ergonomic front. The macros are the escape hatch.

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

## Where it's at now

The "planned for v1" list from the original version of this post has mostly shipped. `:scope(type)` is the most-used pseudo-class in the codebase. `:precedes()` / `:follows()` give you the reverse-direction sibling queries CSS can't express. `:first-child` / `:last-child` / `:nth-child(n)` / `:empty` / `:root` work as you'd expect. NAME_ROLE flags are exposed as `:definition` / `:reference` / `:declaration`. The full pseudo-class vocabulary is over thirty filters across containment, positional, structural, scope, call-graph, ordering, modifier, and annotation categories.

A few newer additions worth calling out:

- **`:matches("code")`** — structural substring match. Parses the argument as real code and checks whether that structure appears as a contiguous subtree within the matched node. `.func:matches("db.execute()")` finds functions containing a specific structural pattern, not a regex. Uses `___` as a wildcard for "any name." Cheap because DFS pre-order contiguity lets structural matching reduce to array substring matching. *(The name and semantics of this pseudo-class are about to change — see the open design question below.)*
- **Call-graph pseudo-classes** — `:calls(name)`, `:called-by(name)`, `:is-called`, `:is-referenced`, `:exported`. Scope-aware by construction.
- **Navigation pseudo-elements** — `::callers`, `::callees`, `::parent-definition`, `::scope`. Return different nodes rather than filtering.
- **Attribute operators** — `=`, `*=`, `^=`, `$=` across `[name]`, `[type]`, `[language]`, `[semantic]`, `[modifier]`, `[annotation]`, `[qualified]`, `[signature]`, `[params]`, `[peek]`.
- **Declaration blocks** — the viewer layer described above. Ships alongside an [AST CSS viewer](https://sitting-duck.readthedocs.io/) that returns rendered source regions instead of rows.

The foundation held up. The CSS grammar does the parsing. The AST schema does the querying. The declaration block does the rendering. The extension still bootstraps itself.

## Open design question: `:matches` drifted from CSS

Here's a place where the current shipped behavior and the CSS mental model have quietly diverged, and we're planning to fix it. Calling it out here because the rename is going to break existing queries, and we'd rather you see it coming.

In CSS, `:matches()` (and its modern alias `:is()`) **matches the current element**, not its descendants. `div:matches(.active)` means "this `div` is also `.active`." It doesn't mean "this `div` contains something that's `.active`" — that's what `:has()` is for.

Our current `:matches("code")` drifted. The implementation walks the matched node's subtree and checks whether the argument's parsed structure appears as a contiguous subtree anywhere inside. So `function_definition:matches("db.execute()")` finds any function whose body contains a `db.execute()` call anywhere. That's useful — it's the common case — but it's really a compound of "has a descendant that matches the pattern," which CSS would spell as `:has(:matches(...))`.

The proposal is:

1. **Rename `:matches(...)` → `:match(...)`** and change its semantics to *match the current node directly*. `call:match("db.execute()")` succeeds only if the matched node is itself a call that structurally equals the pattern.
2. **Add `:contains("...")`** as syntactic sugar for `:has(:match("..."))` — the current behavior, spelled more honestly.
3. **Keep `:matches` as a deprecated alias for `:contains`** for one release so existing queries don't silently break. After that, remove it.

This unlocks queries that don't currently compose:

```sql
-- Comments that are NOT TODOs
SELECT peek FROM ast_select('src/**/*.py', 'comment:not(:match("TODO"))');

-- Calls that exactly match print(anything)
SELECT peek FROM ast_select('src/**/*.py', '.call:match("print(___)")');

-- Functions that contain db.execute() with no string literal argument
SELECT name FROM ast_select('src/**/*.py',
    '.func:contains("db.execute(___)"):not(:contains("db.execute(\"___\")"))');
```

There's also an implementation win. The current `:matches` iterates descendants within every matched subtree. `:match` is just a node-id equality check — no iteration, a much faster path for the common exact-node case. And the compound `:has(:match(...))` can still use the optimized contiguous-subtree trick internally, so `:contains` doesn't pay an extra cost.

One open sub-question: should `:match` require the target node type to equal the pattern's root type, or should it be a prefix match? If the pattern is `db.execute()` (which parses as a `call`), does `:match` only succeed when the target is itself a `call`, or also when the target is an `expression_statement` wrapping that call? Current intuition is strict — target type must equal pattern root type — and users who want looser matching reach for `:has(:match(...))` / `:contains(...)`.

For readers who have queries using the current `:matches("...")`: the mechanical migration is to replace it with `:contains("...")`. Same semantics, new name. The deprecation alias will keep old queries working during the transition.

## Why this matters beyond sitting duck

This post has been about one tool, but the move generalizes.

When we wrote [The Specialization Lives in the Language](tools/lackey/03-the-specialization-lives-in-the-language), the argument was that small language models don't need fine-tuning to hit a target reliably — they need a target language whose *shape* they already know. CSS is the archetypal example. Every code-trained model has seen millions of CSS selectors during training. The grammar is encoded in the weights. When you hand a 3B model a prompt that says "produce an AST query using this selector syntax," the model isn't learning a new DSL; it's being cued to re-use a pattern that's already there.

That's what makes `ast_select` viable as a *tool* for LLM agents, not just a query language for humans. An agent reaches for CSS because its attention routes to CSS easily. The syntax it produces is syntactically valid on the first try because the weights already know `:has()` and `:not()` and `[name^=test_]`. The semantics get validated by the grammar and the schema, not by the model.

The declaration block extension is the same move applied twice. An agent that knows CSS also knows `{ property: value; }` blocks. We didn't invent a new framing language for rendering; we borrowed the one the model already understood. Both halves of the selector-plus-block string land in familiar territory.

This is dialect design as a design discipline: pick a grammar the model has seen, borrow its shape, and let the validator do the work the fine-tune would have done.

---

*Sitting Duck is open source: [github.com/teaguesterling/sitting_duck](https://github.com/teaguesterling/sitting_duck)*

*Full selector reference and guides: [sitting-duck.readthedocs.io](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/) — [Node Types](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/node-types.html), [Pseudo-Classes](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/pseudo-classes.html), [Attributes](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/attributes.html), [Semantic Aliases](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/kinds-types-and-classes.html), [Tutorial](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/tutorial.html), [Cookbook](https://sitting-duck.readthedocs.io/en/latest/guide/selectors/examples.html)*

*Available as a DuckDB community extension: `INSTALL sitting_duck FROM community; LOAD sitting_duck;`*
