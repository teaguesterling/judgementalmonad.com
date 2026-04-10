# The pluckit API

*The full interface for treating code as a queryable material. Also: a training set in disguise.*

---

## Why publish the spec

This is an API specification for a tool that's being built. Normally you ship the tool, then document the API. We're doing it backwards, and for a reason.

A well-defined API spec — with type signatures, composition rules, and examples — is also a grammar for generating valid programs. If you know the types, you know what can chain after what. If you know the selectors, you know the vocabulary. If you know the operations, you can enumerate the space of valid chains.

That means this spec is simultaneously documentation and training data. By the time pluckit ships, we'll have a fine-tuned model that already knows how to compose its operations — trained on synthetic (intent, chain) pairs generated from this page. The [ratchet starts turning before the tool exists](../lackey/05-the-tool-that-teaches-itself-to-disappear).

Read this as a reference if you want to understand pluckit. Read it as a type system if you want to generate valid chains.

**Syntax note:** Examples use JS-style syntax. The pluckit chain parser accepts both JS and Python — the syntax is nearly identical (method chaining looks the same in both). JS is used here because it's cleaner on the page and aligns with the jQuery framing.

---

## Core types

```
Source          — a set of files (entry point)
Selection       — a set of AST nodes across files
Isolated        — a runnable block extracted from context
View            — an assembled collection of related code
History         — a sequence of versions of a selection
Trace           — a step-by-step execution record
CompareResult   — a structural diff between selections
Grade           — a (w, d) pair from the Ma framework
TestResult      — pass/fail with output and coverage
DiffResult      — structural differences between two versions
```

Every pluckit chain starts with a `Source` or a `Selection` and transforms it through operations that return one of these types. The types determine what operations are available next — `.test()` is available on `Selection` and `Isolated`, not on `History`.

---

## Entry points

### source(glob) → Source

Create a Source from a file glob pattern.

```python
source('src/**/*.py')           # all Python files in src/
source('tests/**/*.py')         # all test files
source('**/*.ts')               # all TypeScript files
source('src/auth/*.py')         # just the auth module
```

**Returns:** `Source` — a lazy file set. No files are read until an operation needs them.

### select(selector) → Selection

Select AST nodes from the current working directory using CSS selectors.

```python
select('.fn#validate_token')           # function named validate_token
select('.cls#AuthService')             # class named AuthService
select('.fn:exported')                 # all public functions
select('.fn:has(.ret > .none)')        # functions returning None
```

**Returns:** `Selection` — a set of AST nodes, potentially across files.

**Shorthand:** `select(selector)` is equivalent to `source('**/*').find(selector)`.

---

## Selectors

The selector language is CSS over tree-sitter ASTs, implemented by sitting_duck.

### Node types

| Short form | Tree-sitter node type | Description |
|---|---|---|
| `.fn` | `function_definition` | Function |
| `.cls` | `class_definition` | Class |
| `.call` | `call` | Function call expression |
| `.ret` | `return_statement` | Return statement |
| `.if` | `if_statement` | If statement |
| `.for` | `for_statement` | For loop |
| `.while` | `while_statement` | While loop |
| `.try` | `try_statement` | Try block |
| `.except` | `except_clause` | Except handler |
| `.with` | `with_statement` | Context manager |
| `.assign` | `assignment` | Assignment |
| `.import` | `import_statement` | Import |
| `.dec` | `decorator` | Decorator |
| `.arg` | `parameter` | Function parameter |
| `.str` | `string` | String literal |
| `.num` | `number` | Numeric literal |
| `.block` | `block` | Block (indented body) |
| `.comment` | `comment` | Comment |

### Name selectors

`#name` selects nodes by their identifier:

```css
.fn#validate_token          /* function named "validate_token" */
.cls#AuthService            /* class named "AuthService" */
.call#print                 /* call to print() */
.import#json                /* import of json */
.arg#user_id                /* parameter named user_id */
```

### Attribute selectors

```css
.fn[name^="test_"]          /* starts with test_ */
.fn[name$="_handler"]       /* ends with _handler */
.fn[name*="valid"]          /* contains "valid" */
.fn[params>=3]              /* 3 or more parameters */
.fn[lines>50]               /* more than 50 lines */
```

### Pseudo-selectors

```css
.fn:has(.ret > .none)       /* contains a return None */
.fn:has(.call#print)        /* contains a call to print */
.fn:not(:has(.ret))         /* no return statement */
.fn:first                   /* first in document order */
.fn:last                    /* last in document order */
.fn:exported                /* public (no leading _) */
.fn:private                 /* starts with _ */
.fn:decorated(staticmethod) /* has @staticmethod */
```

### Positional and textual pseudo-selectors

```css
:line(n)            /* nodes spanning line n */
:lines(start, end)  /* nodes within line range */
:contains("text")   /* nodes whose source text contains "text" */
```

These compose with structural selectors:

```css
.fn:line(47)                    /* the function at line 47 */
.fn:contains("return None")    /* functions containing "return None" */
.fn:line(47):contains("token") /* function at line 47 that mentions "token" */
```

### Combinators

```css
.cls#Auth .fn               /* functions inside Auth class (descendant) */
.cls#Auth > .fn             /* direct child functions only */
.fn + .fn                   /* function immediately after another function */
.fn ~ .fn                   /* function preceded by another function (sibling) */
```

### Cross-file

```python
source('src/**/*.py').find('.fn:exported')
source('tests/**/*.py').find('.fn[name^="test_"]')
```

---

## Selection operations

A `Selection` is a set of AST nodes. These operations transform, filter, or act on that set.

### Filtering

#### .find(selector) → Selection

Narrow the selection to descendants matching a selector.

```python
select('.cls#AuthService').find('.fn')
# → all methods of AuthService

select('.fn#process_data').find('.for')
# → all for loops inside process_data
```

#### .filter(predicate) → Selection

Filter the selection by a predicate function.

```python
select('.fn').filter(fn: fn.params().length > 3)
# → functions with more than 3 parameters

select('.fn').filter(fn: fn.callers().count() == 0)
# → functions with no callers (potentially dead code)

select('.fn').filter(fn: fn.coverage() < 0.5)
# → functions with less than 50% branch coverage
```

**Predicate receives:** a single node from the selection.
**Predicate returns:** boolean.

#### .not_(selector) → Selection

Exclude nodes matching a selector.

```python
select('.fn').not_('[name^="_"]')
# → all functions except private ones
```

#### .unique() → Selection

Deduplicate nodes (by identity, not by content).

### Navigation

#### .parent(selector?) → Selection

Navigate to the parent node, optionally filtered by selector.

```python
select('.ret:has(.none)').parent('.fn')
# → functions that contain a return None
```

#### .children(selector?) → Selection

Navigate to child nodes.

```python
select('.fn#process_data').children('.for')
# → direct child for-loops (not nested ones)
```

#### .siblings(selector?) → Selection

Navigate to sibling nodes.

#### .next(selector?) → Selection

Navigate to the next sibling.

#### .prev(selector?) → Selection

Navigate to the previous sibling.

### Positional and textual filtering

#### .containing(text) → Selection

Filter to nodes whose source text contains the given string.

```javascript
select('.fn').containing('database')
// → functions mentioning "database" in their source
```

#### .at_line(n) → Selection

Filter to nodes that span a given line number.

```javascript
select('.fn').at_line(47)
// → the function(s) at line 47
```

#### .at_lines(start, end) → Selection

Filter to nodes within a line range.

#### .ancestor(selector) → Selection

Navigate UP from the current selection to the nearest ancestor matching the selector.

```javascript
source('src/auth/tokens.py')
    .containing('token.decode()')
    .ancestor('.fn')
// → the function containing "token.decode()" — navigate from text to structure
```

### Reading

#### .text() → str | list[str]

Return the source text of each node.

```python
select('.fn#validate_token').text()
# → "def validate_token(token: str) -> bool:\n    ..."
```

#### .attr(name) → Any | list[Any]

Return a node attribute.

```python
select('.fn#validate_token').attr('name')     # "validate_token"
select('.fn#validate_token').attr('line')      # 42
select('.fn#validate_token').attr('file')      # "src/auth/tokens.py"
select('.fn#validate_token').attr('end_line')  # 67
```

#### .params() → Selection

Return the parameters of a function.

```python
select('.fn#validate_token').params()
# → Selection of parameter nodes

select('.fn#validate_token').params().attr('name')
# → ["token", "strict"]
```

#### .body() → Selection

Return the body of a function, class, loop, or conditional.

#### .count() → int

Return the number of nodes in the selection.

#### .names() → list[str]

Return the names of all nodes in the selection.

#### .complexity() → int | list[int]

Return cyclomatic complexity (heuristic: descendant branching nodes).

---

## Structural mutations

These operations modify source code. Each returns the mutated `Selection` for further chaining. Mutations are staged — they don't write to disk until `.save()` or the chain completes in a transaction context.

### .addParam(spec) → Selection

Add a parameter to function signatures.

```python
select('.fn#validate_token').addParam('log_level: str | None = None')
select('.fn:exported').addParam('timeout: int = 30')
```

**spec:** a string in the target language's parameter syntax.
**Scope:** applies to every function node in the selection.

### .removeParam(name) → Selection

Remove a parameter by name.

### .retype(name, new_type) → Selection

Change a parameter's type annotation.

```python
select('.fn#get_user .arg#user_id').retype('UUID')
```

### .rename(new_name) → Selection

Rename a definition and all its references (scope-aware).

```python
select('.fn#old_name').rename('new_name')
# → renames the function AND every call site, import, and reference
```

### .prepend(code) → Selection

Insert code at the top of a body.

```python
select('.fn:exported').body().prepend('if log_level:\n    logging.setLevel(log_level)')
```

### .append(code) → Selection

Insert code at the bottom of a body.

### .wrap(before, after) → Selection

Wrap the selection in surrounding code.

```python
select('.call#database_query').wrap(
    'try:',
    'except DatabaseError:\n    log.error("query failed")\n    raise'
)
```

### .unwrap() → Selection

Remove the wrapping construct, dedent the contents.

```python
select('.try:has(.except:has(.pass))').unwrap()
# → removes try/except blocks where the except just passes
```

### .replaceWith(code) → Selection

Replace the selection's source text.

```python
select('.fn#validate .ret:has(.none)').replaceWith('raise ValueError("invalid")')
```

### .replaceWith(old, new) → Selection

Scoped find-and-replace within the selection. The selector provides scope, the string match provides targeting.

```javascript
select('.fn#validate_token')
    .replaceWith('return None', 'raise ValueError("invalid")')
// → replaces "return None" with the raise, but only inside validate_token
```

### .remove() → Selection

Remove the selection from the source.

### .move_to(path) → Selection

Move the selection to a different file. Updates all imports and references.

```python
select('.fn#validate_token').move_to('src/auth/validators.py')
```

### .extract(name) → Selection

Extract the selection into a new named function. Auto-detects parameters from scope analysis (variables read from enclosing scope become parameters, variables written become return values).

```python
select('.fn#big_function .if:first').extract('_validate_input')
```

### .inline() → Selection

Replace call sites with the function body (inverse of extract).

```python
select('.call#tiny_helper').inline()
```

---

## Call graph operations

These use fledgling's relationship data.

### .callers() → Selection

Functions that call this selection.

```python
select('.fn#validate_token').callers()
# → all functions containing a call to validate_token
```

### .callees() → Selection

Functions that this selection calls.

### .references() → Selection

All references to the names in this selection (broader than callers — includes imports, type annotations, assignments).

### .dependents() → Selection

Everything that would break if this selection changed (transitive callers).

### .dependencies() → Selection

Everything this selection depends on (transitive callees + imports).

### .reachable(max_depth?) → Selection

All nodes reachable from this selection in the call graph, up to max_depth.

```python
select('.fn#handle_request').reachable(max_depth=3)
# → the request pipeline: all functions within 3 hops
```

### .call_chain() → Selection

The linear call chain from this function, ordered by execution flow.

```python
select('.fn#handle_request').call_chain()
# → handle_request → validate_token → check_permissions → get_user_roles
# → ordered by execution, not by file
```

---

## Similarity operations

### .similar(threshold) → Selection

Find structurally similar nodes (AST similarity, not text).

```python
select('.fn#validate_token').similar(0.7)
# → [validate_session (82%), validate_api_key (76%)]
```

**threshold:** 0.0-1.0, minimum similarity score.

### .clones(threshold?) → list[Selection]

Group nodes by near-exact structural duplication.

### .common_pattern() → Selection

Compute the shared AST skeleton across all nodes in the selection.

### .refactor(name) → Selection

Extract the common pattern into a named function, replace all instances with calls to it.

```python
select('.fn[name^="validate_"]').similar(0.7).refactor('validate_credential')
```

---

## Scope operations

These require sitting_duck's scope resolution flags.

### .refs(name?) → Selection

References within this selection. If name is provided, only references to that name.

```python
select('.fn#process_data').refs()
# → all name references inside process_data

select('.fn#process_data').refs('threshold')
# → all references to 'threshold' inside process_data
```

### .defs(name?) → Selection

Definitions within this selection.

### .resolves_to(selector) → Selection

Filter references by what they resolve to.

```python
select('.fn#process_data').refs() \
    .filter(r: r.resolves_to('.cls#Config .assign'))
# → references to variables defined as Config class attributes
```

### .interface() → dict

Compute the read/write interface of a block (used by `.isolate()`).

```python
select('.fn#process_data .for:first').interface()
# → {'reads': ['items', 'threshold'], 'writes': ['filtered'], 'calls': ['classify']}
```

### .shadows() → Selection

Find variables that shadow an outer-scope variable with the same name.

### .unused_params() → Selection

Find parameters not referenced within the function body (scope-aware).

---

## History operations

These require duck_tails (git history as DuckDB tables).

### .history() → History

Every version of this selection, indexed by commit.

```python
select('.fn#validate_token').history()
# → sequence of versions, each with sha, date, author, text, AST
```

### .at(ref) → Selection

The selection at a point in time or a named reference.

```python
select('.fn#validate_token').at('2025-06-15')
select('.fn#validate_token').at('last_green_build')
select('.fn#validate_token').at('HEAD~5')
```

### .diff(other) → DiffResult

Structural diff between two versions of a selection.

```python
select('.fn#validate_token').diff(
    select('.fn#validate_token').at('last_green_build')
)
```

### .blame() → Selection

Per-AST-node attribution (not per-line — structural blame).

### .authors() → list[str]

Who has modified this selection.

### .filmstrip() → list[Selection]

Visual evolution: each version as a snapshot.

### .when(selector) → History

"When did this structural property first appear?"

```python
select('.fn#validate_token').when('.ret > .none')
# → "First returned None in commit abc123 on 2025-03-12"
```

### .co_changes(threshold) → list[tuple[Selection, Selection]]

Find code that always changes together (shotgun surgery detection).

```python
select('.fn').co_changes(0.8)
# → pairs of functions that co-change in ≥80% of commits
```

---

## Behavior operations

These require blq (test capture, execution traces).

### .test(inputs?) → TestResult

Run the selection in isolation (calls `.isolate()` internally if needed).

```python
select('.fn#validate_token').test({'token': 'expired_abc123'})
```

### .isolate() → Isolated

Extract a block into an independently runnable form. Auto-detects the interface from scope analysis.

```python
loop = select('.fn#process_data .for:first').isolate()
loop.interface()
# → {'reads': ['items', 'threshold'], 'writes': ['filtered'], 'calls': ['classify']}
loop.test({'items': [1, 2, 3], 'threshold': 0.7, 'classify': mock_fn})
```

### .coverage() → float | dict

Branch coverage for this selection.

### .failures() → History

Executions where this selection's code failed.

### .timing() → dict

Execution time distribution (mean, p50, p95, p99, trend).

### .inputs() → list[dict]

Observed input values from traced executions.

### .outputs() → list[Any]

Observed output values.

### .runs() → History

All recorded executions.

### .fuzz(n) → list[TestResult]

Random input generation, n iterations.

### .benchmark(n) → dict

Performance benchmark, n iterations.

### .trace(inputs) → Trace

Step-by-step data flow trace through the selection.

---

## Delegate operations

These hand off to external tools.

### .black() → Selection

Format with black (delegate: subprocess → splice result back).

### .ruff_fix() → Selection

Auto-fix with ruff.

### .isort() → Selection

Sort imports with isort.

### .format(tool, args?) → Selection

Generic formatter delegation.

```python
select('.fn#validate_token').format('clang-format', style='google')
```

### .guard(exception_type, strategy) → Selection

Context-aware error handling. Checks whether the call is already inside a try block, groups adjacent similar calls, suggests exception types from behavior data.

```python
select('.call[name*="query"]').guard('DatabaseError', 'log and reraise')
```

### .save(message?) → None

Commit the staged mutations via jetsam. If no message is provided and `.intent()` was set, generates the message from intent + diff summary.

```python
select('.fn:exported') \
    .intent('Add timeout parameter for SLA compliance') \
    .addParam('timeout: int = 30') \
    .test() \
    .save()
# → jetsam save 'feat: add timeout parameter for SLA compliance'
```

---

## blq integration

Error events from blq contain file, function, line, and content — they're compound selectors waiting to be used.

### blq.event(event_id) → EventSelection

Select the code location of a specific error event.

```javascript
blq.event('build:42:error_123')
    .select()
    .replaceWith('return None', 'raise ValueError("invalid")')
    .test('tests/test_auth.py')
    .save('fix: validate_token raises')
```

### blq.run(run_id) → RunSelection

Access all events from a build run.

```javascript
blq.run('build:42')
    .events({ type: 'TypeError', pattern: 'expected str, got None' })
    .select()
    .ancestor('.fn')
    .replaceWith('return None', 'raise TypeError("expected str")')
    .test()
    .save('fix: handle None returns causing TypeErrors')
```

A build run's error list becomes a batch of selectors.

---

## View operations

### .impact() → View

The selection, its callers, their callers, and covering tests. Annotated with coverage, failure history, and change recency.

### .compare() → CompareResult

Structural comparison across all nodes in the selection.

### .call_chain() → Selection

Ordered by execution flow, not file location.

---

## Chain metadata

### .intent(description) → Selection

Attach intent metadata. Flows through the trace log, into `.save()` commit messages, and into Agent Riggs template promotion.

```python
select('.fn[name^="validate_"]') \
    .intent('Extract common skeleton before adding validate_mfa') \
    .similar(0.7) \
    .refactor('validate_credential')
```

### .preview() → str

Show what the chain would produce without applying it.

### .explain() → str

Show the query plan — which operations are queries, which are mutations, which are delegations.

### .dry_run() → DiffResult

Execute the chain, show the diff, but don't write to disk.

---

## Composition rules

The type system constrains what chains are valid:

```
Source     → .find() → Selection
Selection → .find() .filter() .not_() .unique()         → Selection
Selection → .parent() .children() .siblings()            → Selection
Selection → .callers() .callees() .reachable()           → Selection
Selection → .similar() .clones()                         → Selection
Selection → .refs() .defs() .shadows() .unused_params()  → Selection

Selection → .addParam() .removeParam() .rename()         → Selection (mutated)
Selection → .prepend() .append() .wrap() .unwrap()       → Selection (mutated)
Selection → .replaceWith() .remove() .move_to()          → Selection (mutated)
Selection → .extract() .inline() .refactor()             → Selection (mutated)
Selection → .retype()                                    → Selection (mutated)

Selection → .black() .ruff_fix() .isort() .format()     → Selection (formatted)
Selection → .guard()                                     → Selection (mutated)

Selection → .text() .attr() .count() .names()            → terminal (data)
Selection → .complexity()                                → terminal (data)
Selection → .params() .body()                            → Selection (sub-selection)
Selection → .interface()                                 → terminal (dict)

Selection → .isolate()                                   → Isolated
Isolated  → .test() .trace() .fuzz() .benchmark()       → terminal (result)
Isolated  → .interface()                                 → terminal (dict)

Selection → .test()                                      → terminal (TestResult)
Selection → .coverage() .timing() .failures()            → terminal (data)
Selection → .inputs() .outputs() .runs()                 → terminal (data)

Selection → .history()                                   → History
Selection → .at(ref)                                     → Selection (historical)
Selection → .diff(other) .blame()                        → terminal (data)
Selection → .when(selector)                              → terminal (data)
Selection → .filmstrip()                                 → terminal (list)
Selection → .co_changes()                                → terminal (list)

Selection → .impact()                                    → View
Selection → .compare()                                   → terminal (CompareResult)

Selection → .intent(str)                                 → Selection (annotated)
Selection → .preview() .explain() .dry_run()             → terminal (str/data)
Selection → .containing() .at_line() .at_lines()           → Selection
Selection → .ancestor(selector)                             → Selection
Selection → .replaceWith(old, new)                          → Selection (mutated)

Selection → .save(message?)                              → terminal (None)

EventSelection → .select()                                  → Selection
RunSelection   → .events(filter?)                           → EventSelection

History   → .map(fn) .filter(fn)                         → History
History   → .at(ref)                                     → Selection
```

**Key constraint:** mutation operations (`.addParam()`, `.rename()`, etc.) return `Selection (mutated)`, which supports all the same operations as `Selection`. This means mutations compose:

```python
select('.fn:exported') \
    .addParam('timeout: int = 30') \    # mutate
    .body().prepend('...')  \           # mutate
    .black() \                          # delegate
    .test() \                           # terminal
```

**Key constraint:** terminal operations (`.text()`, `.count()`, `.test()`, `.save()`) return data, not `Selection`. They end the chain.

---

## Training set generation

This spec is a grammar. The composition rules define what chains are valid. The selectors define the vocabulary. The operations define the productions. That means we can generate valid chains programmatically.

A training example is an (intent, chain) pair:

```
Intent: "find all functions with more than 5 parameters"
Chain:  select('.fn').filter(fn: fn.params().count() > 5)

Intent: "rename process_data to transform_batch and update all callers"
Chain:  select('.fn#process_data').rename('transform_batch')

Intent: "add retry logic to all API calls in the client module"
Chain:  source('src/client/**/*.py').find('.call[name*="request"]').guard('RequestError', 'retry 3 times')

Intent: "show me which functions have gotten more complex this month"
Chain:  select('.fn').filter(fn: fn.history().last_month().any(v: v.complexity() > fn.at('1_month_ago').complexity()))

Intent: "extract the validation logic from signup into its own function"
Chain:  select('.fn#signup .if:first').extract('_validate_signup_input')

Intent: "find dead code that used to have callers"
Chain:  select('.fn:exported').filter(fn: fn.callers().count() == 0).filter(fn: fn.callers().at('6_months_ago').count() > 0)
```

The generation process:

1. **Sample an operation sequence** from the composition rules (e.g., select → filter → mutation → delegate → save)
2. **Fill in selectors** from the vocabulary (node types, names, attributes, pseudo-selectors)
3. **Fill in parameters** from the operation signatures
4. **Generate an intent description** from the chain's semantics (this part needs a model — but a small one, since the chain is the source of truth)

The synthetic pairs don't need to execute. They need to be *well-typed* — valid according to the composition rules. The validator can check this from the spec alone.

This is the training data for [lackpy's fine-tuning loop](../lackey/05-the-tool-that-teaches-itself-to-disappear). The 3B model learns to generate pluckit chains from intent, trained on thousands of synthetic examples generated from this page. By the time pluckit ships, the model already knows the API.

---

*Next: training the model — how to go from this spec to a fine-tuned 3B that generates pluckit chains.*

```{seealso}
- [Code as a Queryable Material](01-code-as-queryable-material) — The vision
- [The File Is a Lie](02-the-file-is-a-lie) — Views, isolate, and assembled code
- [The Lackpy Gambit](../lackey/02-the-lackpy-gambit) — The restricted language these chains run inside
- [The Tool That Teaches Itself to Disappear](../lackey/05-the-tool-that-teaches-itself-to-disappear) — Template promotion from traces
```
