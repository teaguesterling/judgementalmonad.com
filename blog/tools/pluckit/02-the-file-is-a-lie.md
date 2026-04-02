# The File Is a Lie

*Your code is organized by files. Your problems aren't.*

---

## The wrong axis

You're debugging a request that fails intermittently. The request enters at `handle_request` in `src/api/routes.py`. It calls `validate_token` in `src/auth/tokens.py`. That calls `check_permissions` in `src/auth/permissions.py`. That queries the database through `get_user_roles` in `src/db/queries.py`.

The bug is somewhere in this pipeline. You know the four functions. You need to see them together — their signatures, their bodies, their data flow. But they're in four different files. So you open four tabs. You scroll to the right function in each. You arrange them on screen. You lose one. You scroll again.

Your problem is a pipeline: a chain of functions that data flows through. Your tools present it as four files. Files are the storage axis. The pipeline is the semantic axis. They're orthogonal — and your tools only show you one.

This isn't a tooling limitation you can fix with a better editor layout. It's a conceptual one. The file is the unit of organization, the unit of display, the unit of editing, the unit of version control. But it's almost never the unit of understanding.

You understand code in: pipelines, feature slices, call graphs, data flows, modules-in-the-logical-sense. None of these align with files.

---

## Views

What if you could assemble a view of exactly the code you need, regardless of where it lives?

```python
# The request pipeline, in execution order
select('.fn#handle_request').call_chain()
```

That returns four functions from four files, ordered by execution flow. Not file order. Not alphabetical. The order data actually moves through them. Display them together. Read them together. Edit them together.

```python
# Everything that touches the database
source('src/**/*.py') \
    .find('.call[name*="query"], .call[name*="execute"], .call[name*="fetch"]') \
    .parent('.fn') \
    .unique()
```

Every function that makes a database call, across the entire codebase. Not grep — structural. This finds `self.db.query(...)` and `cursor.execute(...)` and `session.fetch_one(...)` but not `# TODO: add query caching` in a comment.

```python
# The authentication feature, traced from entry points
auth_roots = select('.fn#login, .fn#logout, .fn#refresh_token')
auth_roots.reachable()
# → every function reachable from these three entry points
# → the "auth feature" as a subgraph of the codebase
# → 23 functions across 8 files, none of which are named "auth" except the roots
```

A **view** is a selection of code assembled by a query. It has no physical location. It's a projection of the codebase along whatever axis you care about right now.

---

## isolate()

Point at any block of code and make it independently runnable.

```python
loop = select('.fn#process_data .for:first')
cell = loop.isolate()
```

What just happened? The scope resolution flags in sitting_duck's AST tables tell us that this `for` loop:
- **reads** `items` and `threshold` from the enclosing function's scope
- **writes** to `filtered` (a list that accumulates results)
- **calls** `classify(item)` — a function imported at module level

`isolate()` generates a wrapper: a function with `items`, `threshold`, and `classify` as parameters, the loop as the body, and `filtered` as the return value. The wrapper is a Jupyter-cell-shaped thing — runnable, testable, independently of the 200-line function it lives inside.

```python
cell.test({'items': [1, 2, 3], 'threshold': 0.7, 'classify': mock_classify})
# → runs the loop in isolation
# → returns: [{'score': 0.9}]
```

You didn't define the interface. You pointed at code and the tool figured it out from scope analysis. The variables the block reads from outside become parameters. The variables it writes become return values. The function calls it makes become injectable dependencies.

This is the shift from "code runs as programs" to "code is a material you can grab pieces of and experiment with."

### isolate() for debugging

You have a function that's 150 lines and failing on one branch. You don't need to run the whole function. You need to run lines 47-63 — the branch that handles expired tokens.

```python
branch = select('.fn#validate_token .if:has(.str="expired"):first')
cell = branch.isolate()

# What does this branch need?
cell.interface()
# → reads: token (str), config (dict), logger (Logger)
# → writes: nothing (raises or returns)
# → calls: parse_expiry(), config.get()

# Run it with the failing input
cell.test({'token': 'expired_abc123', 'config': prod_config, 'logger': mock_logger})
# → TokenExpiredError: token expired 3 days ago

# Run the old version with the same input
branch.at('last_green_build').isolate() \
    .test({'token': 'expired_abc123', 'config': prod_config, 'logger': mock_logger})
# → None (the old version didn't raise on this input)

# Structural diff between old and new
branch.diff(branch.at('last_green_build'))
# → added: comparison against config["grace_period_days"]
# → the bug: grace period check was added but config doesn't have that key
```

Three operations. Found the bug. The old version didn't check grace period. The new version does, but the config doesn't define it. You didn't read the whole function. You didn't set up a test harness. You pointed at a branch and ran it.

### isolate() for learning

You're new to the codebase. You're reading `process_data` and you don't understand what the inner loop does. You don't want to run the whole function — it takes real database connections and 30 seconds of setup.

```python
inner = select('.fn#process_data .for:first .for:first')
cell = inner.isolate()

cell.interface()
# → reads: batch (list[dict]), transform (callable)
# → writes: results (list)

# Experiment with small data
cell.test({
    'batch': [{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}],
    'transform': lambda x: {**x, 'value': x['value'] * 10}
})
# → [{'name': 'a', 'value': 10}, {'name': 'b', 'value': 20}]
```

Now you understand what the loop does. You didn't need to understand the rest of the function. You didn't need a database. You isolated the piece you cared about and ran it.

---

## Assembled views

Views get interesting when you assemble code from multiple locations and operate on the assembly.

### The impact view

You're about to change `validate_token`. What's the blast radius?

```python
fn = select('.fn#validate_token')
view = fn.impact()
# → fn itself
# → 12 direct callers (relationships)
# → 3 indirect callers (callers of callers)
# → 8 tests that cover fn (behavior)
# → 2 tests that cover the callers but not fn directly
```

One query. The view contains everything that might break. You can filter it:

```python
# Just the parts with low test coverage
view.filter(fn: fn.coverage() < 0.5)
# → 4 callers with less than 50% branch coverage
# → these are the ones that will bite you

# Just the parts that changed recently
view.filter(fn: fn.history().last_week().count() > 0)
# → 2 callers were modified this week
# → these might already be unstable
```

### The comparison view

Two functions that look similar. Show them side by side with their differences highlighted:

```python
select('.fn#validate_token, .fn#validate_session').compare()
# → structural alignment: which parts are identical, which differ
# → parameter diff: token takes a string, session takes a dict
# → body diff: token checks expiry, session checks IP binding
# → shared pattern: both call check_permissions() with the same logic
```

This is AST diff, not text diff. Renamed variables don't show as differences. Reformatted code doesn't show. Only semantic changes.

```python
# Find ALL functions similar to this one
select('.fn#validate_token').similar(0.7)
# → validate_session (82% similar)
# → validate_api_key (76%)
# → validate_refresh_token (91%)

# Compare all of them
select('.fn#validate_token').similar(0.7).compare()
# → common pattern: parse credential → check expiry → check permissions → return
# → variations: how the credential is parsed, what "expiry" means, extra checks
```

Four validation functions in three files. You've never seen them together before. Laid out side by side, the shared pattern is obvious. The refactoring is obvious too — extract the common skeleton, parameterize the variations.

### The feature slice

"Everything related to authentication" isn't a file. It's a subgraph.

```python
auth = select('.fn#login, .fn#logout, .fn#refresh_token, .fn#validate_token')
feature = auth.reachable(max_depth=3)
# → 23 functions across 8 files

feature.external_interface()
# → 5 functions are called from OUTSIDE the feature subgraph
# → these are the feature's API surface

feature.internal_coupling()
# → 3 functions are called by EVERY other function in the feature
# → these are the feature's core (probably the database layer)

feature.boundary()
# → 7 functions call things OUTSIDE the feature subgraph
# → these are the feature's dependencies (database, config, logging)
```

The "auth feature" isn't `src/auth/`. It's a graph query. Some of it is in `src/auth/`. Some is in `src/db/`. Some is in `src/middleware/`. Files didn't tell you the shape. The call graph did.

### The time-lapse

Watch a function evolve:

```python
select('.fn#validate_token').filmstrip()
# → v1 (2024-03): 8 lines. Checks signature only.
# → v2 (2024-06): 15 lines. Added expiry check.
# → v3 (2024-09): 28 lines. Added permissions, IP binding.
# → v4 (2025-01): 42 lines. Added rate limiting, audit logging.
# → v5 (2025-08): 67 lines. Added grace period, token refresh.
```

Five versions. The function grew from 8 lines to 67. Complexity went from 2 to 14. But the growth wasn't gradual — v3 to v4 was the big jump (permissions + audit logging added in one commit). That's where the code review should have suggested extraction.

```python
# Which version was most stable?
select('.fn#validate_token').history() \
    .map(v: {'sha': v.sha, 'failures_next_30d': v.failures().next(days=30).count()})
# → v2 had zero failures for 90 days
# → v4 had 12 failures in the first week
# → the permissions change broke things
```

---

## The Jupyter precedent

None of this is philosophically new. Jupyter notebooks already treat code as a material you can grab pieces of and experiment with. A notebook cell is `isolate()` made manual — you paste code into a cell, define the inputs, run it, see the output.

The difference is that Jupyter requires you to do the isolation by hand. You copy the code. You figure out what variables it needs. You define them in earlier cells. You manage the dependencies.

pluckit automates the isolation. Scope resolution handles the interface detection. The tool figures out what the block reads and writes. You just point and run.

And unlike Jupyter, pluckit operations compose. `isolate()` returns something you can `.test()`, `.diff()`, `.compare()`, `.trace()`. The isolation feeds into other operations. It's not a stopping point — it's a link in a chain.

---

## "Refactor the validation functions"

Here's the full stack in action. An agent — or a human — says:

```
"The four validate_* functions are structurally similar.
 Extract the common pattern into a generic validate_credential function."
```

That's a [lackpy](../lackey/02-the-lackpy-gambit) intent. The micro-inferencer generates a pluckit program:

```python
# Generated by lackpy (Qwen 2.5 Coder 1.5B, Tier 2)
fns = select('.fn[name^="validate_"]').similar(0.7)
common = fns.common_pattern()
extracted = common.extract('validate_credential')
fns.replace_with_calls(extracted)
run_tests()
```

Five lines. The 1.5B model generated them from the intent and the pluckit kit namespace. It didn't need to understand the codebase — it needed to compose the right operations in the right order. The validation pipeline checked the AST. The executor ran it.

What actually happened inside:

1. `.similar(0.7)` found 4 functions across 3 files with ≥70% structural similarity (query: DuckDB over fledgling's similarity index)
2. `.common_pattern()` computed the shared AST skeleton — the control flow that all four share — and identified what varies (how the credential is parsed, what "expiry" means, extra checks)
3. `.extract('validate_credential')` generated a parameterized function with the common skeleton and the variations as strategy parameters (mutate: language renderer + splice)
4. `.replace_with_calls(extracted)` replaced each original function with a call to the new one, passing the appropriate strategy (mutate: call-site rewriting with scope-aware argument binding)
5. `run_tests()` ran the existing test suite to verify behavioral equivalence (delegate: blq sandbox)

The result: a 40-file PR that a human couldn't produce in under an hour. Reviewable because each step is traceable. Reversible because the chain is atomic. And the pattern is now a template — next time someone says "extract the common pattern from these similar functions," lackpy serves it from Tier 0.

---

## Intent

There's a subtlety worth making explicit. That refactoring chain works — but if you read it six months from now in a trace log, you know *what* happened and not *why*. Why did someone extract the validation functions? Was it a performance concern? A readability cleanup? Preparation for adding a fifth validator?

Chains can carry intent:

```python
select('.fn[name^="validate_"]') \
    .similar(0.7) \
    .intent("Extract common validation pattern — "
            "we're adding validate_mfa next week and want a consistent skeleton") \
    .common_pattern() \
    .extract('validate_credential') \
    .save('refactor: extract common validation skeleton')
```

`.intent()` doesn't change what the chain does. It attaches metadata — a string that travels with the operation through the trace log. When Agent Riggs analyzes the trace, it sees not just "extracted a common pattern" but *why*. When the commit lands, the intent can flow into the commit message or PR description.

This matters for template promotion. Without intent, Riggs sees "extract common pattern from similar functions" and promotes that mechanical pattern. With intent, Riggs can distinguish "extract for readability" from "extract to prepare for extension" — different intents might produce different refactoring strategies.

It also matters for agents. When an outer agent (Opus, Sonnet) delegates a pluckit chain through lackpy, the intent is the agent's reasoning — the bridge between "what the model was thinking" and "what the tool did." The chain becomes an audit trail with both the *what* and the *why*. The Harness stores both. The intent is data, not code — it doesn't execute, it just travels alongside the execution.

The [annotate combinator](../../drafts/tool-call-combinators) from the Ma framework predicts this: every operation should optionally carry intent, hypothesis, and observations. pluckit's `.intent()` is the minimal version — just the why. Richer annotations (hypothesis, confidence, alternatives considered) are possible but might be overkill for most chains. Start with intent. Expand if the trace data shows it's useful.

---

## What changes

The shift isn't about better tools for existing workflows. It's about workflows that don't exist yet.

**Code review changes.** Instead of reading a diff file by file, you assemble a view: the changed functions, their callers, their tests, the impact radius. The diff is structural, not textual. You see what semantically changed, not what lines moved.

**Debugging changes.** Instead of reproducing the bug through the whole program, you isolate the failing block, run it with the failing input, compare it to the last-known-good version. Three operations instead of "add print statements and re-run."

**Onboarding changes.** Instead of reading files top to bottom, a new developer asks "show me the request pipeline" and gets a view: four functions, in execution order, with their data flow annotated. They understand the architecture without reading 20 files.

**Refactoring changes.** Instead of "I think these functions are similar," you query for structural similarity and get a list. Instead of manually extracting common code, you tell the tool to parameterize the shared pattern. Instead of praying you updated every call site, the tool does it from the call graph.

**Architecture changes.** "Is auth well-encapsulated?" becomes a query. "What would break if we moved the validation module?" becomes a query. "Where are the hidden dependencies?" becomes a query. The answers come from the code itself, not from someone's mental model of the code.

The file was never the right unit. It was just the only one we had.

---

*Next in the series: the selector language — how CSS selectors map to AST queries, and why DFS ordering in DuckDB makes structural queries fast.*

```{seealso}
- [Code as a Queryable Material](01-code-as-queryable-material) — The vision and the architecture
- [CSS Selectors for Code](../../sitting-duck-css-selectors) — The selector engine underneath
- [Closing the Channel](../../fuel/05-closing-the-channel) — Replacing bash patterns with structured tools
- [The Lackpy Gambit](../lackey/02-the-lackpy-gambit) — Generating pluckit chains from natural language
```
