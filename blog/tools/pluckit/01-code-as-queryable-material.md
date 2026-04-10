# Code as a Queryable Material

*What if your codebase were a database you could query, filter, mutate, and test — in one chain?*

---

## The hour you've lost a hundred times

You've been asked to add an optional `log_level` parameter to every public function in the module. You know exactly what needs to happen:

- Edit 47 function signatures
- Add a conditional block to 47 function bodies
- Find 89 call sites across the codebase
- Update each one to pass `log_level` through where the caller already has it
- Run tests
- Fix the three you missed

This takes an hour. The PR is 40 files. The reviewer looks at it and says "looks mechanical, LGTM" — because it IS mechanical. Your job was to be a slow, error-prone search-and-replace engine.

Every developer has done this. Renamed a parameter across a codebase. Added error handling to every database call. Converted print statements to logging. Wrapped API calls in retry logic. Each time: find the pattern, apply the transformation, repeat N times, pray you didn't miss one.

The IDE helps with some cases. "Rename symbol" works. "Extract method" works for a single function. But "add an optional parameter to all public functions, with call-site propagation where the caller already has it" — no IDE on earth does that in one operation.

This is the gap. Not between bad tools and good tools. Between describing a pattern and performing each instance of it manually. Between saying what you want and doing it forty-seven times.

---

## But also: the bug you're fixing right now

The mass refactoring is the dramatic case. Here's the everyday one.

A traceback gives you a file, a function, a line number, and an error message. That's four pieces of information. You open the file. You scroll to the line. You read the function. You figure out the fix. You make the edit. You switch to the terminal. You run the tests. You switch back. You commit.

Five context switches. One fix.

```javascript
source('src/auth/tokens.py')
    .find('.fn#validate_token')
    .at_line(47)
    .replaceWith('return None', 'raise ValueError("invalid")')
    .test('tests/test_auth.py')
    .save('fix: validate_token raises instead of returning None')
```

One chain. The traceback's information IS the selector. grep + editor + terminal + pytest + git = five context switches. pluckit = one chain that compresses the workflow, not just the edit.

---

## When to use what

Be honest about when pluckit is overkill:

- **One function, you know which file:** Use your editor. You're already there.
- **Rename a symbol:** Use your IDE's rename. It's built for this.
- **A pattern across 10+ files:** pluckit. One selector, N applications.
- **A structural condition grep can't express:** pluckit. "Functions that return None inside a try block" isn't a regex.
- **Edit + test + commit as one atomic operation:** pluckit. The chain either succeeds completely or rolls back.
- **A cross-dimensional query** (structure × history × behavior × relationships): pluckit. No alternative exists.

---

## Code is a tree. You already know this.

Every programmer knows it in the abstract. Source code parses to an AST. Compilers work on trees. Tree-sitter parses 27 languages into trees.

And there's already a battle-tested API for querying and manipulating trees: jQuery.

The DOM is a tree. CSS selectors address nodes. jQuery provides chainable operations on selections. Before jQuery, manipulating the DOM meant `document.getElementById()` and manual traversal. After jQuery, it meant `$('#sidebar a').css('color', 'red')`. The API didn't change what was possible — it changed what was *easy*.

```javascript
// DOM: find all links in the sidebar, change their color
$('#sidebar a').css('color', 'red')
```

```javascript
// Source: find all return-None statements in validate, replace them
select('.fn#validate .ret:has(.none)').replaceWith('raise ValueError("invalid")')
```

The mapping is direct:

| CSS (HTML) | pluckit (source code) |
|---|---|
| Element types | Node types: `.fn`, `.cls`, `.call`, `.ret`, `.if`, `.for` |
| `#id` | `#name`: `.fn#validate_token`, `.cls#AuthService` |
| `[attr^="prefix"]` | `[name^="test_"]`, `[name$="_handler"]` |
| `:has()`, `:not()` | `.fn:has(.ret > .none)`, `.fn:not(:has(.ret))` |
| Descendant selector | `.cls#Auth .fn` — functions inside the Auth class |
| Cross-document | `source('src/**/*.py').find('.fn:exported')` |

And for developers who think in the keywords they see in their code, not in AST node types:

```javascript
// Instead of remembering tree-sitter node types...
select('.function_definition:has(.try_statement:not(:has(.finally_clause)))')

// ...write what you see:
select('def:has(try:not(:has(finally)))')
```

`def`, `try`, `finally` — the keywords resolve to the right AST node types per language. A full selector taxonomy covers all 27 supported languages.

This isn't a metaphor. It's an implementation. [sitting_duck](https://github.com/teague/sitting-duck) already implements CSS selectors over tree-sitter ASTs, backed by DuckDB. The selector engine exists. The AST tables exist. The query performance is there — DFS ordering over node tables means containment queries are range scans, not tree walks.

---

## First taste

Start small. Select and read:

```javascript
select('.fn#validate_token').text()
```

Select and replace:

```javascript
select('.fn#validate .ret:has(.none)').replaceWith('raise ValueError("invalid")')
```

Select and wrap:

```javascript
select('.call#database_query').wrap(
    'try:',
    'except DatabaseError:\n    log.error("query failed")\n    raise'
)
```

These feel like jQuery because they are. Selector → selection → operation. One line per intent.

Now chain:

```javascript
source('src/**/*.py')
    .find('.fn:exported')
    .filter(fn => fn.params().length > 3)
    .addParam('log_level: str | None = None')
    .body().prepend('if log_level:\n    logging.setLevel(log_level)')
```

Read it aloud: across all Python files in src, find all exported functions with more than 3 parameters, add a `log_level` parameter to each, and prepend a conditional logging block to each body.

### Three ways in

Developers find code differently depending on context. pluckit meets you where you are:

| How you found the code | Selector | Method |
|---|---|---|
| A traceback gave a line number | `:line(47)` | `.at_line(47)` |
| grep found the text | `:contains("return None")` | `.containing("return None")` |
| You know the structure | `.fn#validate_token .ret:has(.none)` | `.find()` |
| An error event has an ID | `blq.event('build:42:error_123').select()` | — |

All four flow into the same chain. The selector provides scope. The operation provides intent.

### Select broadly, replace precisely

The two-argument `.replaceWith()` is the on-ramp for grep users:

```javascript
// You don't need to navigate to the exact AST node.
// Select the function, then do a text replace inside it.
select('.fn#validate_token')
    .replaceWith('return None', 'raise ValueError("invalid")')
```

The selector is imprecise on purpose — selecting the whole function is easy. The string match is precise — targeting exactly what to change. Together they're as precise as a structural selector, but neither alone requires deep AST knowledge.

One chain. No loops. No file-by-file iteration. The chain builds a query lazily — it doesn't execute three separate passes over the codebase. It builds a plan and executes once, the same way a SQL query planner does.

---

## Beyond jQuery

HTML elements don't have call sites. Functions do. This is where source code as a queryable material goes past what any tree-manipulation API has done.

### Call-site propagation

When you add a parameter to `validate_token`, every function that calls it and already has `log_level` should pass it through:

```javascript
fn = select('.fn#validate_token')
fn.addParam('log_level: str | None = None')

fn.callers()
    .filter(caller => caller.parent('.fn').has('.arg#log_level'))
    .update(call => call.addArg('log_level=log_level'))
```

This requires the call graph (who calls what) combined with structural queries (does the caller have this parameter) combined with mutation (add the argument). Three capabilities — relationships, structure, and mutation — composed in one chain.

### .isolate() — the Jupyter cell for any block

Point at ANY block of code — not a function, just a `for` loop — and make it runnable:

```javascript
loop = select('.fn#process_data .for:first')
cell = loop.isolate()
// Detects: reads [items, threshold] from enclosing scope
//          writes [filtered]
// Generates: runnable wrapper with those as parameters

cell.test({'items': [1, 2, 3], 'threshold': 0.7})
```

You didn't define an interface. You pointed at code and the tool figured out what it reads from enclosing scope, what it writes, and generated a runnable wrapper. Any block. Any file. On demand.

The scope detection comes from sitting_duck's flag system — a single byte per AST node encodes whether it's a definition, a reference, or a scope boundary. "What variables does this block need from outside?" is a range query: find all references within the block's byte range that don't have a matching definition within the same range. That's SQL over the AST tables. The query is fast because it's a range scan over DFS-ordered nodes.

### .guard() — context-aware error handling

```javascript
select('.call#database_query').guard('DatabaseError', 'log and reraise')
```

`.guard()` is smarter than `.wrap()`. Is this call already inside a try block? Add to the existing except clause. Are there adjacent similar calls? Wrap them together. What exceptions does this function actually throw? Suggest types. Error handling with structural awareness, not blind wrapping.

### .similar() — the clone detector that fixes itself

```javascript
select('.fn#validate_token').similar(0.8)
// → [validate_session (82%), validate_api_key (76%)]

select('.fn#validate_token').similar(0.8).refactor('validate_credential')
// → generates parameterized function
// → generates call-site replacements
// → tests behavioral equivalence against original test suites
```

Structural similarity, not text similarity. Two functions with different variable names but identical control flow register as clones. The refactoring extracts the common pattern, parameterizes what varies, replaces all instances, and verifies the result.

---

## The four dimensions

Here's the shift.

A source code block isn't just its current text. It's four things:

| Dimension | What it is | Where it lives |
|---|---|---|
| **Structure** | The AST shape right now | sitting_duck |
| **History** | Every version this block has ever been | duck_tails (git as queryable tables) |
| **Behavior** | What happens when it runs | blq (test capture, execution traces) |
| **Relationships** | What calls it, what it calls, what it looks like | fledgling (code intelligence) |

No existing tool queries across all four simultaneously. pluckit does:

```javascript
// "Which function is most likely to cause the next production incident?"
select('.fn')
    .filter(fn => fn.complexity() > 10)
    .filter(fn => fn.coverage() < 0.5)
    .filter(fn => fn.history().last_month().count() > 3)
    .filter(fn => fn.failures().count() > 0)
    .sort(fn => fn.dependents().count())
```

That query combines cyclomatic complexity (structure), code coverage (behavior), change frequency (history), failure rate (behavior), and dependency count (relationships). Five data sources. One chain. Currently, answering this question requires a human analyst combining five different tools and synthesizing the results mentally.

### Time travel

```javascript
// What changed that broke the tests?
select('.fn#validate_token').diff(
    select('.fn#validate_token').at('last_green_build')
)
```

Structural diff against the last version where CI passed. Not a text diff — an AST diff. Formatting changes don't show up. Only semantic changes.

```javascript
// When did this function get complicated?
select('.fn#validate_token').history()
    .map(v => {'sha': v.sha, 'complexity': v.complexity()})
```

Complexity over time. See exactly which commit introduced the complexity.

```javascript
// Find dead code that USED to be called
select('.fn:exported')
    .filter(fn => fn.callers().count() == 0)
    .filter(fn => fn.callers().at('6_months_ago').count() > 0)
```

Nobody calls this function now. But six months ago, someone did. That's dead code you can safely remove — with the git history to prove it.

---

## What exists today

Pull back from the vision.

**sitting_duck** is shipped. CSS selectors over tree-sitter ASTs in DuckDB. 27 languages. The selector engine, the DFS-ordered node tables, the byte ranges for every node — all queryable. The flags byte is being extended with scope resolution bits driven by tree-sitter's `locals.scm` patterns.

**fledgling** is working. Code intelligence — `find_definitions`, `find_callers`, cross-file resolution, structural similarity — as MCP tools over sitting_duck's SQL layer.

**duck_tails** is working. Git history as queryable DuckDB tables. Per-file, per-commit.

**blq** is working. Sandbox presets, test capture, build log query.

**The fluent API** is the new layer. Selection class, mutation primitives, the `.isolate()` / `.guard()` / `.similar()` operations. This is what's being designed.

The architecture has three layers, and the fluent API hides the dispatch between them:

**Queries go through DuckDB.** `.find()`, `.filter()`, `.callers()`, `.history()`, `.coverage()` — these are SQL over sitting_duck's AST tables, joined with fledgling's call graph, duck_tails' git history, and blq's test capture. The fluent API builds query plans lazily and executes them once, the way an ORM builds SQL.

**Structural mutations are byte-range splices.** `.addParam()`, `.prepend()`, `.wrap()`, `.rename()` — these *use* a query for context (where does the parameter list end?) but do their work at the API level. A language-specific renderer produces the bytes ("a Python parameter looks like `name: type = default`"), and a generic splice inserts them at the right position. Unchanged regions keep their original text — formatting, comments, whitespace all preserved. Only the mutated region is regenerated.

**Delegated operations hand off to external tools.** `.black()` sends selected text to black and splices the result back. `.test()` isolates the block and sends it to blq's sandbox. `.refactor()` sends the selection to lackpy or a frontier model and integrates the rewritten block. `.ruff_fix()`, `.isort()`, `clang-format` — any formatter or linter that can operate on a text fragment. These operations don't need DuckDB or renderers. They need a subprocess, a text boundary, and a splice.

A single chain can cross all three layers:

```javascript
select('.fn:exported')                  // query: DuckDB selector
    .filter(fn => fn.coverage() < 0.5) // query: join with blq data
    .addParam('timeout: int = 30')      // mutate: renderer + splice
    .black()                            // delegate: external formatter
    .test()                             // delegate: blq sandbox
    .save('feat: add timeout param')    // delegate: jetsam
```

The user doesn't care which layer handles each link. The chain works.

The language-specific renderer is the only part that needs per-language work, and it's small. The query layer, the selector engine, the splice mechanism, the delegation protocol, and the fluent API are all language-agnostic. A Python implementation and a TypeScript implementation would share the SQL and differ only in the fluent syntax and the renderers — which means pluckit can live in both ecosystems, integrated with Node.js tooling as naturally as with the Python Rigged suite.

---

## The ratchet underneath

There's a feedback loop here that connects to everything else.

A developer figures out a refactoring by chaining pluckit operations interactively. They add `log_level` to 47 functions, propagate call sites, run tests, save. That interactive session is a trace — a sequence of operations that achieved a goal.

[Agent Riggs](https://github.com/teague/agent-riggs) sees the trace. It identifies the pattern: "add optional parameter with call-site propagation." It crystallizes the pattern into a named refactoring. Next time, [lackpy](https://github.com/teague/lackpy) serves it from a template — the micro-inferencer translates "add dry_run parameter to all public functions" into a pluckit chain without touching a frontier model.

```
Interactive session
    → named refactoring
    → template
    → lackpy dispatch
    → automatic
```

The developer's exploration became everyone's tool. The exploration cost was human time. The reuse cost is zero.

That's the architecture the [suite](../index) has been building toward. Each tool provides one dimension. pluckit is the surface where they all meet. See the [full catalog](../index) for what each tool does and how they connect.

---

*This is the first post in the pluckit series. Next: the selector language — how CSS selectors map to AST queries, and why DuckDB makes it fast.*

```{seealso}
- [CSS Selectors for Code](../../sitting-duck-css-selectors) — How sitting_duck implements CSS selectors over ASTs
- [Closing the Channel](../../fuel/05-closing-the-channel) — Where structured tools come from
- [The Round-Trip Tax](../lackey/01-the-round-trip-tax) — Why composition matters
- [The Lackpy Gambit](../lackey/02-the-lackpy-gambit) — The micro-inferencer that generates pluckit chains
- [The Tool That Teaches Itself to Disappear](../lackey/05-the-tool-that-teaches-itself-to-disappear) — Template crystallization from traces
```
