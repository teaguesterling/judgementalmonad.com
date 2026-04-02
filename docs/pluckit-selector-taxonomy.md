# pluckit Selector Language — Universal Taxonomy & Keyword Selectors

*Reference spec for the [pluckit blog series](../blog/tools/pluckit/index). Defines the three selector vocabularies.*

---

## Three Addressing Levels

The pluckit selector language operates at three levels of granularity, each further subdividing the node space:

| Level | Count | Examples |
|-------|-------|---------|
| Super Kind | 4 classes | statement, expression, literal, structural |
| Kind | 16 classes | function, class, call, flow, assignment, ... |
| Super Type | 64 classes | `.fn`, `.cls`, `.call`, `.ret`, `.if`, `.for`, ... |

All three levels are addressable in selectors. Coarser levels select broader sets.

---

## Super Kind (4 classes)

| Super Kind | Covers |
|------------|--------|
| `statement` | Control flow, assignments, imports, return — things that execute |
| `expression` | Calls, names, operators — things that evaluate to values |
| `literal` | Strings, numbers, booleans — leaf values |
| `structural` | Functions, classes, blocks — containers that hold other nodes |

---

## Kind (16 classes)

| Kind | Super Kind | Includes |
|------|------------|---------|
| `function` | structural | `.fn`, `.lambda` |
| `class` | structural | `.cls` |
| `block` | structural | `.block` |
| `call` | expression | `.call` |
| `name` | expression | identifiers |
| `operator` | expression | binary/unary ops |
| `flow` | statement | `.if`, `.for`, `.while`, `.with`, `.try` |
| `assignment` | statement | `.assign` |
| `return` | statement | `.ret` |
| `import` | statement | `.import` |
| `decorator` | structural | `.dec` |
| `parameter` | structural | `.arg` |
| `handler` | structural | `.except` |
| `string` | literal | `.str` |
| `number` | literal | `.num` |
| `comment` | structural | `.comment` |

---

## Super Type (64 classes) — Core Selectors

The short-form CSS selectors that appear in pluckit chains map to tree-sitter node types:

| Short form | Tree-sitter node type | Kind |
|------------|----------------------|------|
| `.fn` | `function_definition` | function |
| `.cls` | `class_definition` | class |
| `.call` | `call` | call |
| `.ret` | `return_statement` | return |
| `.if` | `if_statement` | flow |
| `.for` | `for_statement` | flow |
| `.while` | `while_statement` | flow |
| `.try` | `try_statement` | flow |
| `.except` | `except_clause` | handler |
| `.with` | `with_statement` | flow |
| `.assign` | `assignment` | assignment |
| `.import` | `import_statement` | import |
| `.dec` | `decorator` | decorator |
| `.arg` | `parameter` | parameter |
| `.str` | `string` | string |
| `.num` | `number` | number |
| `.block` | `block` | block |
| `.comment` | `comment` | comment |

The full 64-class taxonomy extends this to cover language-specific constructs (comprehensions, async/await, type annotations, f-strings, etc.) as individual Super Types.

---

## Keyword Selectors

Keyword selectors are natural language aliases that resolve to CSS selectors. They exist so that common developer concepts map to pluckit without requiring knowledge of the taxonomy.

### Definition keywords

| Keyword | Resolves to | Description |
|---------|-------------|-------------|
| `def` | `.fn` | Any function definition |
| `func` | `.fn` | Same as `def` |
| `fn` | `.fn` | Same as `def` (also the short form) |
| `function` | `.fn` | Same |
| `method` | `.cls > .fn` | Function inside a class |
| `class` | `.cls` | Class definition |
| `definition` | `.fn, .cls` | Any named definition |

### Modifier keywords

Modifier keywords resolve to selector + pseudo-selector combinations:

| Keyword | Resolves to |
|---------|-------------|
| `public` | `:exported` (no leading `_`) |
| `private` | `:private` (leading `_`) |
| `exported` | `:exported` |
| `async` | `[async=true]` |
| `decorated` | `:has(.dec)` |

### Compound keyword examples

```
"public functions" → .fn:exported
"private methods"  → .cls > .fn:private
"async functions"  → .fn[async=true]
"test functions"   → .fn[name^="test_"]
"database calls"   → .call[name*="query"], .call[name*="execute"]
```

---

## Three Vocabularies, One SQL

All three selector vocabularies resolve to the same DuckDB query against the sitting_duck AST database:

```
Keyword selector:    "public functions"
CSS selector:        .fn:exported
Taxonomy selector:   kind=function, modifier=exported

All resolve to:
    SELECT * FROM nodes
    WHERE node_type = 'function_definition'
      AND NOT name LIKE '\_%'
```

The chain DSL parser handles the resolution. Users can mix vocabularies within a chain — the parser normalizes before constructing the SQL.

---

## Selector Composition

Selectors compose through standard CSS combinators and pluckit pseudo-selectors:

```css
/* Descendant */
.cls#AuthService .fn          /* methods of AuthService */

/* Direct child */
.cls#AuthService > .fn        /* direct methods only (no nested classes) */

/* Pseudo-selectors */
.fn:has(.call#query)          /* functions that call query() */
.fn:not(:has(.ret))           /* functions with no return statement */
.fn:has(.ret > .none)         /* functions that return None */

/* Attribute filters */
.fn[lines>50]                 /* long functions */
.fn[params>=3]                /* functions with 3+ parameters */
.fn[name*="valid"]            /* functions with "valid" in name */
```

Keyword aliases work in these positions too:

```js
select('public functions that call query()')
// → .fn:exported:has(.call#query)
```
