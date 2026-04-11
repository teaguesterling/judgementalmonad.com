# Views Are Sandboxes

*Note to the blog writer: this is a raw thinking piece from an in-conversation design session. The connection I want explored is the one between the "view" idea sketched below and the nsjail-python project — both are, I think, the same pattern at different altitudes. There's a family of tools here waiting to be named. Feel free to reshape the framing entirely; what matters is that the connection gets examined.*

---

## The idea in brief

We've been designing a query language for code navigation: CSS-style AST selectors paired with declaration blocks. A selector like `.fn#authenticate { show: body; }` matches a function and renders it as a markdown code block. Multiple rules compose into a "view" — a named, saved perspective on a codebase.

The initial v1 is narrow: a selector matches, the declaration says how to render, the output is markdown. Useful but not surprising.

The surprise came when we started adding declarations that aren't about presentation. `editable: true` for sandbox write access. `test: after-change` for hook execution. Suddenly the view isn't a rendering spec — it's a specification of what an actor operating inside the view can see, edit, and trigger.

At which point the view becomes isomorphic to a sandbox. Or more precisely: a view *is* a sandbox spec, written at a different level of abstraction than the sandbox tools we already have.

## Why CSS is the right surface language

Before getting to the sandbox parallel, there's a property of the syntax choice worth naming because it shapes everything else: **every model in training data has seen enormous amounts of CSS.** More than tree-sitter query syntax, more than jq expressions, more than any custom DSL anyone could invent. A 1.5B model can write `.class#Foo { property: value; }` from muscle memory. A frontier model can reason about selector specificity and composition. The syntax isn't something we're *teaching* agents — it's something they already know.

This inverts a tradeoff that usually haunts domain-specific languages. Normally, introducing a DSL forces you to choose between expressiveness (which requires training or careful prompting) and restriction (which loses capability). With CSS selectors we get both — the syntax is already in every model's repertoire, so we can be as expressive as we want without paying in prompt tokens or accuracy. We demonstrated this empirically with qwen2.5-coder — even a 3B model produces correct selectors with only minimal guidance, something we couldn't achieve for arbitrary custom grammars.

The consequence: **CSS becomes a coordination medium between agents.** Any model in the system can read, write, and reason about views without specialized training or retrieval-augmented prompting. The outer agent can emit a view as plain text. The delegate can parse it. The human can inspect it in a text editor. The diff tool can compare two versions of it. No participant needs to be taught what a view is — they all already know the syntax.

And critically, **views flow through chain APIs as data.** An outer agent using pluckit can run exploratory queries, accumulate matches, and emit a view as the final artifact of that exploration. The view becomes a value that travels through the system — produced by one operation, consumed by another:

```python
# Explore via pluckit
callers = pluck.find(".fn#authenticate").callers()

# Build a view from the chain result
view = callers.to_view(show="body") + \
       pluck.find(".fn#authenticate").to_view(show="body") + \
       pluck.find(".class#User").to_view(show="signature")

# Delegate against the dynamically-built view
result = lens.delegate(view, "Fix the admin login bug", to="qwen2.5-coder:7b")
```

The view is the output of "figure out what matters" and the input to "bound the delegate's world." Same text, different phases of the workflow. It can be serialized to disk for versioning, or it can live as a transient value between operations. Either way, it's just CSS.

## The nsjail-python parallel

nsjail-python is a sandbox for Python processes. You declare what the sandboxed process can access — specific files, specific syscalls, network on or off, memory and CPU limits. The sandbox enforces those bounds at the OS level. The Python code inside doesn't know it's sandboxed; it just runs into hard walls when it tries to do something outside its grant.

A view does the same thing for an agent operating on code:

```
.fn#authenticate { show: body; editable: true; }
.fn#check_admin_role { show: body; editable: true; }
.class#User { show: signature; editable: false; }
.fn[name^=test_auth] { show: body; editable: false; }
@after-change { test: pytest tests/test_auth.py; }
```

This says: the actor can see the `authenticate` and `check_admin_role` function bodies, can edit them, can see the `User` class signature and test functions as read-only context, and must pass `pytest tests/test_auth.py` after any edit. The view doesn't enforce this at the OS level — it enforces it at the *semantic* level. The actor sees a workspace with virtual files corresponding to each matched region. If it writes to a virtual file, the view layer splices the change back into the real file. If it tries to read something that wasn't matched, it doesn't exist in the workspace.

Both nsjail-python and the view do the same thing: **declaratively bound what an actor can do, and enforce those bounds from outside.** The actor doesn't need to be trusted. It doesn't need to understand the sandbox. It just operates in a world where the walls are invisible but immovable.

## Different altitudes of the same pattern

Once you see the connection, you start noticing that sandbox specifications exist at many levels:

- **OS level**: nsjail, seccomp, cgroups, Docker. "This process can touch these files, these syscalls, this much RAM."
- **Language level**: lackpy's restricted interpreter, capability-based systems, the JVM SecurityManager. "This program can call these functions, not those."
- **Semantic level**: views. "This actor can see and edit these code regions, must run these tests after changes."
- **Conversational level**: context windows, compaction, retrieval. "This inference call sees these tokens, not those."

These are not alternatives to each other. They're *stacked*. A delegate agent could run inside:
- a view (semantic bounds on what code it can touch)
- a lackpy-restricted Python interpreter (language bounds on what it can call)
- an nsjail process (OS bounds on what it can access)
- with a curated token window (conversational bounds on what it attends to)

Each layer catches different failure modes. The view catches "edited a file it shouldn't have." lackpy catches "called a forbidden function." nsjail catches "tried to read a protected file." Retrieval catches "drowned in irrelevant examples and stopped attending to the important ones."

And they're all *declarative*. You write down what the actor should have, the system enforces it. You don't audit the actor's behavior; you audit the spec that bounds it.

## The ma connection

In the conversation-as-fold framing, the Harness's primary job is constructing the Inferencer's input for each turn. That input has two axes: world coupling (what tools and world state the actor has access to) and decision surface (which of the model's paths are reachable given the input).

Every layer in the sandbox stack is a way for the Harness to specify its grade directive. The view says "your world coupling is these four files, your decision surface is bounded by this prompt." nsjail says "your world coupling is these syscalls." The token window says "your decision surface is whatever these tokens activate."

The pattern is **declarative grade specification**. The Harness doesn't trust the Inferencer (or the delegate, or the subprocess) to stay within bounds. It encodes the bounds in a structure the underlying system enforces. The actor can't violate the spec because the spec is the only world it sees.

This suggests a general theory: **sandboxes are grade specifications rendered into enforceable form at a particular level of abstraction.** nsjail renders grade specifications into kernel-enforceable form. lackpy renders them into Python-AST-enforceable form. Views render them into code-editing-enforceable form. Token windows render them into attention-enforceable form. Different enforcement mechanisms, same concept.

If that's right, then designing one of these tools is about picking the right enforcement layer for the threats you care about, and then writing the same declarative vocabulary in a form that layer can check.

## Why this matters for delegation

The immediate practical reason this matters: we've been exploring whether to delegate coding tasks from a large model to a small one. The big model understands the request and has the context. The small model is fast and cheap but needs tight bounds on what it's touching.

Without views, delegation is nerve-wracking. You hand the small model a task, give it tool access, and hope it doesn't run amok. You audit its output after the fact. If it edits the wrong file, you roll back.

With views, delegation is **contractual**. The big model writes a view: "here are the four functions you can edit, here are two classes you can read for context, here are the tests that must pass, go." The small model operates inside that view and *cannot* do anything else. Not because it's smart enough to stay in bounds — because the bounds are the only world it can see.

This is exactly the shape of a sandbox. The view is an nsjail config for the semantic level.

It also composes cleanly. The small model's delegate runs:
- Inside a view (semantic bounds)
- Writing to files that are actually virtual files mapping to specific line ranges
- Being asked to produce output that the tests can verify
- In a process that can further be nsjail'd if you want belt-and-suspenders

The big model's job changes from "monitor the delegate" to "write the view." Writing a view is cheap, declarative, auditable, and composable. Monitoring a delegate is expensive, imperative, ad-hoc.

## Self-containment via `@source` blocks

A view as sketched so far has selectors and declarations, but it's missing one thing: *which files do the selectors run against?* Without that, the view depends on external configuration — the caller has to specify the source set, and the view isn't portable on its own.

CSS already gives us the right pattern for this: media queries. In CSS, `@media` scopes rules to a viewport condition:

```css
@media (max-width: 768px) {
  .nav { display: none; }
}
```

For views, the analogous construct is `@source` — a block that scopes rules to a file set:

```
@source("src/**/*.py") {
  .fn#authenticate { show: body; editable: true; }
  .class#User { show: signature; editable: false; }
}

@source("tests/**/*.py") {
  .fn[name^=test_auth] { show: body; editable: false; }
}

@after-change { test: pytest tests/test_auth.py; }
```

Same pattern, different axis — `@media` scopes rules to viewport conditions, `@source` scopes rules to files. Any agent that's seen CSS knows this pattern already. No new vocabulary to learn.

The properties that make `@source` blocks work:

- **Self-containment**: a view with `@source` blocks is portable. Hand the file to a delegate executor with nothing else and it knows exactly which files to touch.
- **Multiple sources per view**: real work usually needs different rules for different file sets. Source code has different concerns than tests, which have different concerns than fixtures. Block scoping handles this naturally.
- **Cascade matches CSS semantics**: rules outside any `@source` block apply to every source set. Rules inside a block apply only to that block's source. Exactly the same as `@media`.
- **Composes with existing source resolution**: the argument to `@source()` is the same string that pluckit already accepts — glob pattern, table/view name, file path, or (eventually) git ref. No new resolution machinery.
- **Bare views still work**: a view with no `@source` blocks runs against whatever the caller provides. Simple views stay simple.

With kwargs for filters (familiar from Python) and a declarations-block form for complex cases:

```
# Kwargs form — concise
@source("**/*.py", language=python, exclude="**/vendor/**") {
  .fn:async { show: signature; }
}

# Declarations form — verbose but clear
@source {
  include: "src/**/*.py", "tests/**/*.py";
  exclude: "**/node_modules/**", "**/_build/**";
  language: python;

  .fn#authenticate { show: body; }
}
```

Both forms map to the same underlying concept: a set of files with filters. The parser supports both; users pick what fits.

The important thing about `@source` isn't the exact syntax — it's that **the pattern of block-scoped at-rules with a scope predicate is already in every model's CSS repertoire**. Adding a new at-rule keyword costs nothing in agent comprehension because the structural pattern is universal. The view file becomes fully self-contained without introducing any concepts an agent hasn't already seen.

## Questions to explore

For the piece you write, the questions I'd like explored:

1. **Is the "declarative grade specification" generalization real?** Do nsjail, view, lackpy, and retrieval actually share a structural pattern, or do they just rhyme? If they share structure, what's the shape of the shared abstraction?

2. **What's the sandbox tower look like?** If you stack these layers, what does the composite sandbox look like from the inside? From the outside? Where are the seams between layers, and which layer catches which class of failure?

3. **What's the smallest useful view system?** The sketch here adds declarations for editability, tests, hooks. How much of that is needed to prove the "view as sandbox" claim, versus how much is feature creep on the original rendering spec?

4. **Does the view layer need its own name and project?** We've been calling it a viewer but it's clearly larger than that. "Lens" is one candidate. But it's also possible this should be part of nsjail-python as its next layer, or part of lackpy, or part of pluckit. Where's the right architectural home for a declarative-sandbox-for-semantic-edits?

5. **How does this connect to the broader coordination framework?** Is a view just a special case of some more general coordination primitive? What would the generalization look like?

6. **What's the failure mode?** Every sandbox has edge cases where the abstraction leaks. For nsjail it's side channels and escape techniques. For lackpy it's string-eval tricks and AST confusion. For views, what's the equivalent? The obvious answer is that a view can only constrain edits within the matched regions — the delegate could still produce output that, when the tests run, affects things outside the view's scope. Is there a principled way to bound *effects* in addition to bounding *visibility*?

7. **Where does this fit in the blog's existing arc?** We've been building up to coordination-as-grade-adjustment for a while. This is a concrete instantiation of that idea with a working prototype attached. What's the throughline from the earlier pieces (ma, harness, conversation fold, retrieval-beats-stuffing) to this one?

8. **Is "CSS as universal coordination medium" a generalizable observation?** The choice of CSS here isn't decorative — it's load-bearing for the claim that views are a coordination currency between agents. But CSS is a specific historical accident: it's in every model's training data because the web had a particular shape. What other syntaxes share that property? Are there *other* domains where the same move (picking a syntax that's already saturated in training data instead of designing a new one) could unlock similar coordination effects? The retrieval-beats-stuffing piece argued that focused examples beat stuffing for small models on structured output. This is a different move — *pick a syntax that doesn't need examples at all because it was learned for free*. Both moves are about minimizing prompt overhead for structured output, but they work at different layers. Is there a unifying principle?

## Raw material

A working example of a fully self-contained view:

```
# views/auth-fix.view
# Self-contained delegation workspace for the admin login bug.
# Can be handed to a delegate executor with no external configuration.

@source("src/**/*.py", language=python) {
  .fn#authenticate {
    show: body;
    editable: true;
    label: "Main authentication entry";
  }

  .fn#check_admin_role {
    show: body;
    editable: true;
    label: "Admin role check";
  }

  .class#User {
    show: outline;
    editable: false;
    label: "User model (read-only reference)";
  }
}

@source("tests/**/*.py", language=python) {
  .fn[name^=test_auth] {
    show: body;
    editable: false;
    label: "Auth tests";
  }
}

@after-change(.fn) {
  test: pytest tests/test_auth.py;
  lint: ruff check src/auth.py;
}
```

Everything needed to bound the delegate is in this file. The `@source` blocks say which files are in scope. The selectors inside each block say which regions of those files are in scope. The declarations say how each region is rendered and whether it's editable. The `@after-change` rule says what must pass after any edit. Nothing about this view depends on external configuration — it can be version-controlled, committed to a feature branch alongside the code it's scoped to, and handed to any delegate executor that understands the format.

A delegate invocation against this view:

```
lens delegate auth-fix.view --to qwen2.5-coder:7b \
  "Fix the bug where admin users can't log in"
```

What the delegate sees: four files in a virtual workspace, the task description, a `run_tests` tool that the view's `@after-change` rule provides. That's its entire world. No other files, no other tools, no way to drift.

What happens under the hood:
- The view evaluator runs the selectors against the current codebase
- For each match, it extracts the source region and creates a virtual file
- It builds a manifest mapping each virtual file back to its source file + line range
- It presents the virtual files as the delegate's working directory
- After the delegate edits, it splices changes back, runs the `@after-change` hook, captures the result
- It returns the delegate's result + the diff + the test output to the outer agent

The outer agent sees none of the mechanics. It sees: "I wrote a view, I got back a diff and a test result." The outer agent never has to think about file paths, line numbers, or sandbox construction.

---

*End of thinking piece. Shape this however serves the blog best. The view-as-sandbox framing is the part I most want to preserve; everything else is negotiable.*
