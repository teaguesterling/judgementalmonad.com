# pluckit Grammar & Compilation Pipeline

*Reference spec for the [pluckit blog series](../blog/tools/pluckit/index). The tree-sitter grammar for pluckit chains and the pipeline from parse to execution.*

---

## Tree-Sitter Grammar

```js
// grammar.js — pluckit chain grammar
module.exports = grammar({
  name: 'pluckit',

  rules: {
    // A chain is one or more segments joined by newlines (or inline)
    chain: $ => seq(
      $.entry_point,
      repeat(seq(optional($._newline_indent), $.method_call))
    ),

    // Entry points: select(), source(), blq.event(), duck_hunt.event()
    entry_point: $ => choice(
      $.select_call,
      $.source_call,
      $.event_call,
    ),

    select_call: $ => seq(
      'select',
      '(',
      choice($.string, $.function_selector),
      ')'
    ),

    source_call: $ => seq(
      'source',
      '(',
      $.string,
      ')'
    ),

    event_call: $ => seq(
      choice('blq', 'duck_hunt'),
      '.',
      'event',
      '(',
      $.string,
      ')'
    ),

    // Method calls chain off the entry point or previous call
    method_call: $ => seq(
      '.',
      $.identifier,
      '(',
      optional($.arg_list),
      ')'
    ),

    arg_list: $ => seq(
      $.argument,
      repeat(seq(',', $.argument))
    ),

    argument: $ => choice(
      $.string,
      $.number,
      $.lambda_expr,
      $.function_selector,
      $.boolean,
    ),

    // Lambda for .filter(), .map() etc: fn: fn.callers().count() == 0
    lambda_expr: $ => seq(
      $.identifier,
      ':',
      $.expression
    ),

    // Function-form selector: fn().containing(call('print'))
    function_selector: $ => seq(
      $.selector_fn,
      repeat(seq('.', $.method_call))
    ),

    selector_fn: $ => seq(
      choice('fn', 'cls', 'call', 'ret', 'block'),
      '(',
      optional($.string),
      ')'
    ),

    expression: $ => choice(
      $.comparison,
      $.method_chain,
      $.identifier,
      $.number,
    ),

    comparison: $ => seq(
      $.expression,
      choice('==', '!=', '<', '>', '<=', '>='),
      $.expression
    ),

    method_chain: $ => seq(
      $.identifier,
      repeat1(seq('.', $.method_call))
    ),

    _newline_indent: $ => /\n\s+/,
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
    string: $ => choice(
      seq("'", /[^']*/, "'"),
      seq('"', /[^"]*/, '"'),
    ),
    number: $ => /[0-9]+(\.[0-9]+)?/,
    boolean: $ => choice('true', 'false', 'True', 'False'),
  }
});
```

---

## Operation Grades

Each operation in a pluckit chain carries a grade annotation from the Ma framework. Grades indicate the ratio of width (w, scope) to depth (d, detail) in what the operation returns or touches.

| Grade | w | d | Operations |
|-------|---|---|------------|
| Pure selection | high | low | `.find()`, `.filter()`, `select()`, `source()` |
| Narrow + deep | low | high | `.isolate()`, `.callers()`, `.callees()` |
| Transforming | varies | varies | `.replaceWith()`, `.addParam()`, `.rename()`, `.wrap()` |
| Terminal | 0 | 0 | `.save()`, `.text()`, `.show()` |
| Aggregating | 1 | high | `.similar()`, `.compare()` |
| Delegating | varies | varies | `.test()`, `.black()`, `.ruff_fix()` |

Grade annotations are used by Agent Riggs to classify traces and by the training pipeline to ensure dataset balance across operation categories.

---

## Compilation Pipeline

A pluckit chain goes through seven steps from source text to execution:

### Step 1: Tokenize

Split the source text into method name + argument tokens. Both JS and Python syntax accepted (identical for method chains).

```
Input:  "select('.fn:exported').addParam('timeout: int = 30').test().save('feat: add timeout')"
Tokens: [select('.fn:exported'), addParam('timeout: int = 30'), test(), save('feat: add timeout')]
```

### Step 2: Parse

Apply the tree-sitter grammar to produce a parse tree. Validates syntax — catches unclosed parens, malformed selectors, invalid lambda syntax.

### Step 3: Type flow validation

Walk the parse tree and verify that each operation's input type matches the output type of the previous operation. This is a static check — no execution needed.

```
select('.fn:exported')              → Selection
.addParam('timeout: int = 30')      → Selection  [requires Selection ✓]
.test()                             → TestResult  [requires Selection ✓]
.save('feat: add timeout')          → None        [requires TestResult ✓]
```

Reject chains where types don't flow: `.save()` after `.callers()` would fail here because `.callers()` → `Selection`, not `TestResult`.

### Step 4: Selector compilation

CSS selector strings are compiled to DuckDB SQL via sitting_duck. Keyword aliases are resolved first, then pseudo-selectors are mapped to SQL predicates.

```
'.fn:exported'
→ WHERE node_type = 'function_definition' AND NOT name LIKE '\_%%'
```

### Step 5: Segment splitting

Long chains are split at natural boundaries for incremental execution and progress reporting. Segment boundaries occur at:

- After any filtering operation (`.find()`, `.filter()`) — report selection size
- After any mutating operation (`.replaceWith()`, `.addParam()`) — report modified nodes
- Before any terminal operation (`.save()`, `.show()`) — confirm before proceeding

```
Segment 1: select('.fn:exported')
Segment 2: .addParam('timeout: int = 30')
Segment 3: .test()
Segment 4: .save('feat: add timeout')
```

### Step 6: Dispatch

Each method name maps to a Python implementation function:

| Chain method | Python dispatch |
|-------------|----------------|
| `select(s)` | `ops.select(selector=s)` |
| `.find(s)` | `ops.find(current, selector=s)` |
| `.filter(f)` | `ops.filter(current, predicate=f)` |
| `.replaceWith(o, n)` | `ops.replace_with(current, old=o, new=n)` |
| `.addParam(p)` | `ops.add_param(current, param_spec=p)` |
| `.ancestor(s)` | `ops.ancestor(current, selector=s)` |
| `.test(t)` | `ops.run_tests(current, target=t)` |
| `.save(m)` | `ops.git_commit(current, message=m)` |

### Step 7: Execute

Segments execute sequentially. Each segment receives the output of the previous segment. Failures halt execution and return a `ChainError` with the failing segment, the error, and the partial results so far.

---

## Segment Splitting Rules

Full ruleset for segment boundary decisions:

| Rule | Condition | Action |
|------|-----------|--------|
| Size gate | Selection > 500 nodes | Pause, report count, ask to continue |
| Mutation confirm | Any mutating op + no `.test()` follows | Warn: untested mutation |
| Cross-file scope | Selection spans > 10 files | Report scope before proceeding |
| Save gate | `.save()` without `.test()` in chain | Warn: uncommitted changes, no test |
| Error fingerprint | Known error pattern in selection | Suggest known fix chain |

These rules are enforced by the chain executor, not the parser. They are configurable per-project via `.pluckit.toml`.
