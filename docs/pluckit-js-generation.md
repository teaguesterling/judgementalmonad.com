# pluckit Design Update — JS Generation Target & Workflow Refinements

*Reference spec for the [pluckit blog series](../blog/tools/pluckit/index). Addendum to pluckit-design.md and pluckit-technical-roadmap.md.*

---

## Table of Contents

1. [Two-arg replaceWith](#two-arg-replacewith)
2. [Function equivalents for selectors and .ancestor()](#function-equivalents)
3. [blq/duck_hunt event selectors](#event-selectors)
4. [Small model generation target](#small-model-generation)
5. [JavaScript as the generation target](#javascript-generation-target)
6. [Full error-to-fix workflow](#error-to-fix-workflow)
7. [Updated selector spec summary](#updated-selector-spec)

---

## Two-arg replaceWith

`.replaceWith(old, new)` — replaces literal text within selected nodes.

```js
blq.event('build:42:error_123')
    .select()
    .replaceWith('return None', 'raise ValueError("invalid")')
    .test('tests/test_auth.py')
    .save('fix: validate_token raises on None')
```

The two-arg form differs from the one-arg form (which replaces the entire node with generated code). The two-arg form is a targeted text substitution within the node's source, enabling precise surgical fixes.

---

## Function Equivalents for Selectors and .ancestor()

Selectors can be expressed as function calls instead of CSS strings for programmatic composition:

```js
// CSS form
select('.fn:has(.call#print)')

// Function equivalent
select(fn().containing(call('print')))
```

`.ancestor(selector)` — traverse upward to the nearest matching ancestor node:

```js
select('.call#query')
    .ancestor('.fn')    // → the function containing each query call
```

This is useful when an error points at a call site but the fix should apply to the enclosing function.

---

## blq/duck_hunt Event Selectors

Event selectors are compound selectors that encode both location and context from a build/test event:

```js
blq.event('build:42:error_123')    // entry point from a blq event ID
    .select()                       // → Selection at the error location

duck_hunt.event('test:run:99:fail_7')
    .select()                       // → Selection at the failing assertion
```

The event metadata (file, line, error type) drives the selector automatically. No manual `.at_line()` or `#name` lookup needed — the event carries the address.

---

## Small Model Generation Target

The fine-tuned model (Qwen 2.5 Coder 3B via LoRA) generates pluckit chains, not Python code. Key design constraints:

- **Input:** natural language intent or structured error description
- **Output:** pluckit chain (JS or Python syntax, 1-8 lines)
- **Not output:** Python AST manipulation, DuckDB SQL, tree-sitter queries

The model needs to learn the pluckit vocabulary (~20 node types, ~10 pseudo-selectors, ~60 operations) and composition rules (type flow), not the internals of any operation.

---

## JavaScript as the Generation Target

### Evidence from lackpy evaluation

Lackpy (Qwen 2.5 Coder 1.5B, local) tested three generation approaches for producing pluckit chains:

| Option | Approach | Result |
|--------|----------|--------|
| A | Generate Python calls directly | Hallucinated Python APIs, mixed pluckit with stdlib |
| B | Generate AST JSON | Verbose, model drifted from schema |
| C | Chain DSL parser (JS-style) | Clean output, familiar jQuery pattern, easy to parse |

Option C won because:
1. The model has seen millions of jQuery-style method chains in training data
2. JS method chaining is syntactically identical to Python in this context
3. A ~200-line chain DSL parser maps the JS-style chain to Python execution without a Node.js runtime

### Option C: Chain DSL Parser

The chain DSL parser accepts both JS and Python syntax (they're nearly identical for method chains) and maps each call to a Python implementation:

```
Source text (JS or Python)
    → tokenize (method names + args)
    → validate types (composition rules)
    → dispatch to Python implementations
    → execute
```

The model generates:
```js
select('.fn:exported')
    .addParam('timeout: int = 30')
    .test()
    .save('feat: add timeout parameter')
```

The parser resolves `.addParam()` → `ops.add_param()`, validates the type flow (`Selection → Selection → TestResult → None`), and executes. No eval, no exec, no Node.js.

---

## Error-to-Fix Workflow

The full ratchet from error event to resolved fix:

```
1. Error event fires (blq or duck_hunt)
   ↓
2. Event metadata extracted (file, line, error type, message)
   ↓
3. Compound selector constructed from metadata
   blq.event('build:42:error_123').select()
   ↓
4. lackpy (1.5B, local) generates fix chain from:
   - error description
   - selector context
   - pluckit chain vocabulary
   ↓
5. Chain executed:
   .select() → locate node
   .replaceWith(old, new) → patch
   .test('relevant_tests') → verify
   .save('fix: ...') → commit if passing
   ↓
6. Trace recorded: (event_id, chain, diff, test_result)
   ↓
7. Agent Riggs fingerprints pattern:
   error_type + location_pattern → fix_chain_template
   ↓
8. Second occurrence: Tier 0 (template, no model, no human)
```

---

## Updated Selector Spec Summary

New pseudo-selectors added (see pluckit-selector-taxonomy.md for full taxonomy):

| Selector | Meaning |
|----------|---------|
| `:line(n)` | nodes spanning line n |
| `:lines(start, end)` | nodes in line range |
| `:contains("text")` | nodes whose source contains text |

New traversal operation:

| Operation | Signature | Description |
|-----------|-----------|-------------|
| `.ancestor(selector)` | `Selection → Selection` | Nearest matching ancestor node |
| `.containing(selector)` | function equivalent for `:has()` | Programmatic composition |
