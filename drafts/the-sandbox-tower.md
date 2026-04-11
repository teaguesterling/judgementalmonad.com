# The Sandbox Tower

*Views became sandboxes the moment we added `editable: true`. That wasn't an extension of the viewer — it was the moment we noticed nsjail, lackpy, views, and retrieval are all the same pattern at different altitudes, and you can stack them. Once you stack them, delegation stops being nerve-wracking and starts being contractual.*

---

## The moment the frame clicked

We'd been designing [a CSS-style query language for code](../blog/sitting-duck-css-selectors). Selectors match AST nodes; declaration blocks say how to render them. `.fn#authenticate { show: body; }` finds the function, returns it as a fenced markdown code block with a location header. Composed together, a file of rules becomes a *view* — a named, curated perspective on a codebase. The v1 was narrow: selectors in, markdown out. Useful, not surprising.

The surprise came the first time someone wanted to write a declaration that wasn't about presentation. `editable: true` on a matched region. `@after-change { test: pytest tests/test_auth.py; }` as a hook that fires when any matched node is modified. `editable: false` on a class definition that should be *visible* to the actor but read-only.

As soon as those declarations existed, the view stopped being a rendering spec and became something else. It was a *declarative specification of what an actor operating inside it can see, read, edit, and trigger*. Which is the same sentence you'd write about an nsjail config, a lackpy interpreter, a capability-bounded process — just spelled in a different vocabulary.

The view isn't *like* a sandbox. The view *is* a sandbox, with enforcement happening at a level of abstraction we didn't have a tool for before.

## Why CSS is the right surface for this

Before the tower generalization, there's a property of the syntax choice that does real work and has to be named first, because everything downstream depends on it: **every language model in training data has seen enormous amounts of CSS.** More than tree-sitter query syntax, more than jq expressions, more than any custom DSL anyone would design from scratch. A 1.5B model can write `.class#Foo { property: value; }` from muscle memory. A frontier model can reason about selector specificity, composition, and the interaction between combinators. The syntax isn't something we're *teaching* agents — it's something they already know.

This inverts a tradeoff that usually haunts domain-specific languages. Normally, a DSL forces you to choose between expressiveness (which costs training or careful prompting) and restriction (which costs capability). With CSS selectors we get both. The grammar is already in every model's repertoire, so expressiveness is free. We saw this empirically in [Retrieval Beats Stuffing](retrieval-beats-stuffing): even a 3B coder model produces valid selectors with minimal guidance, something we couldn't reliably achieve for arbitrary custom grammars. The [dialect-design argument from the lackey series](../blog/tools/lackey/03-the-specialization-lives-in-the-language) applies here verbatim — borrow a grammar the model already knows and let the validator do the work the fine-tune would have done — but applied to the coordination-language role, not the query-language role.

The consequence is bigger than it sounds: **CSS becomes a coordination medium between agents.** Any model in the system can read, write, and reason about views without specialized training or retrieval-augmented prompting. The outer agent can emit a view as plain text. The delegate can parse it. The human can inspect it in a text editor. The diff tool can compare two versions of it. No participant has to be taught what a view is — they all already know the syntax at both halves: the selector and the declaration block.

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

The view is the output of "figure out what matters" and the input to "bound the delegate's world." Same text, different phases of the workflow. It can be serialized to disk for versioning, or it can live as a transient value between operations. Either way, it's just CSS — readable by every participant, diffable, version-controllable, compositional.

This is also what makes the view layer the *unified context* across tools, not just a feature of a viewer. The view is the artifact that threads the stack: pluckit produces it, the delegate consumes it, the test hook validates against it, the audit store records it, the next iteration's outer agent reads the recorded one to decide what to change. The sandbox tower has a theoretical spine (grade specifications rendered at different altitudes) *and* a concrete data format (CSS text) that every layer can read. The two together are what make it more than rhyme.

And because the same borrow-what-the-model-already-knows logic keeps working, the pattern generalizes beyond the selector and the declaration block. When the view needs to say *which files these rules apply to* — something a pure selector doesn't answer — CSS already has the right construct: `@media`, the block-scoped at-rule pattern where rules apply under a scope predicate. The view layer uses the same shape with a different axis:

```
@source("src/**/*.py") {
  .fn#authenticate { show: body; editable: true; }
  .class#User { show: outline; editable: false; }
}

@source("tests/**/*.py") {
  .fn[name^=test_auth] { show: body; editable: false; }
}

@after-change { test: pytest tests/test_auth.py; }
```

`@source` is to file sets what `@media` is to viewports. Different axis, same structural pattern — block-scoped at-rule with a scope predicate, rules outside any block cascade to every source, rules inside apply only to that block's source. No participant has to learn it. Every model has seen `@media` thousands of times and the structural shape transfers verbatim.

This is the move worth naming: every time the view layer needs to express something new — rendering, editability, hooks, source scoping, and whatever comes next — there's already a CSS construct for the same shape, and we use it instead of inventing a new one. Dialect design isn't just "pick a grammar the model knows." It's "pick a grammar and then stay inside its existing conventions as the language grows." The view stays a coordination medium between agents as long as every extension lands on territory every participant already understands.

And the practical payoff: `@source` blocks make a view *self-contained*. A view file with source blocks is portable. Hand it to a delegate executor with nothing else and the executor knows exactly which files to match against. The view isn't a fragment that needs a caller to supply context — it's a complete specification. That matters for the integration layer: if views are the unified context threading between tools, they have to be standalone artifacts, not references into the caller's implicit state.

## The tower

Once you see the connection, you start noticing that sandbox specifications exist at every level of the stack, and they're mostly not in conversation with each other:

| Altitude | Example tools | What it bounds |
|---|---|---|
| **OS** | nsjail, seccomp, cgroups, Docker | Files, syscalls, network, memory, CPU |
| **Language** | [lackpy](../blog/tools/lackey/02-the-lackpy-gambit), JVM SecurityManager, capability systems | Which functions, operators, imports are reachable |
| **Semantic** | Views, scoped editors | Which code regions the actor can see and modify, what must run after changes |
| **Conversational** | Context windows, retrieval, prompt curation | Which tokens an inference call attends to |

These aren't alternatives. They're stacked. A delegate agent could run inside all four at once:

- A *view* that exposes only four files as virtual workspace entries — everything else in the codebase doesn't exist from the delegate's perspective.
- A *lackpy-restricted interpreter* that can only call pre-loaded namespace functions — no `eval`, no arbitrary imports, no runtime reflection.
- An *nsjail* process that can't touch files outside the sandbox directory or open network sockets.
- With a *retrieval-curated prompt* that shows the delegate only the examples relevant to its task, not the full library that would dilute attention. (See [Retrieval Beats Stuffing](retrieval-beats-stuffing) — the post where we found that a 3B model went from 2/8 to 7/8 by reducing example count from twenty to six.)

Each layer catches a different class of failure:

| Layer | Catches |
|---|---|
| View | "Edited the wrong file" / "saw code it shouldn't have" |
| lackpy | "Called a forbidden function" / "wrote Turing-complete code we can't analyze" |
| nsjail | "Tried to read a protected path" / "opened a socket" |
| Retrieval | "Drowned in irrelevant examples and stopped attending to the important ones" |

None of these substitutes for another. A perfect nsjail config doesn't stop the delegate from editing a file *it was allowed to edit* in the wrong way. A perfect view doesn't stop the delegate from shelling out inside the code it's writing. A perfect lackpy interpreter doesn't stop the delegate from filling its output with code that passes every local check and still does the wrong thing because it was prompted with the wrong examples.

The layers compose because the failure modes don't overlap.

## The pattern underneath: declarative grade specifications

In the [ma framework](../blog/ma/00-intro), every turn has a *grade*: two axes that together determine the shape of the computation the actor is being asked to perform. **World coupling** is what the actor can see and affect — tools, files, state, external systems. **Decision surface** is which of the model's paths are reachable given its input — what patterns the prompt activates, what behaviors the context primes.

The Harness's job is to *specify the grade* for each turn. It does this by constructing the actor's input: choosing which tools are visible, which files are loaded, which examples are retrieved, which constraints the output must satisfy. The actor receives a world; the Harness decided what that world is.

Every layer in the sandbox tower is a way for the Harness to specify its grade directive *declaratively*, at a particular altitude:

- **nsjail** renders world-coupling bounds into kernel-enforceable form. The actor can't open the file because the kernel returns an access error.
- **lackpy** renders world-coupling bounds into Python-AST-enforceable form. The actor can't call a forbidden primitive because the AST validator rejects the program before it runs.
- **Views** render world-coupling bounds into code-editing-enforceable form. The actor can't modify `User` because `User` appears in its workspace as a read-only file.
- **Retrieval** renders decision-surface bounds into attention-enforceable form. The actor can't over-attend to the twenty irrelevant examples because only six are in its context.

The abstract specification is the same: *what is this actor's grade?* The enforcement mechanism differs because each layer catches violations the others can't see. But the thing you *write* at each layer is a declaration, not an audit — a statement about what should be true, backed by a mechanism that makes violating it impossible rather than merely discoverable after the fact.

**Sandboxes are grade specifications rendered into enforceable form at a particular level of abstraction.** That's the claim.

If it's right, then designing a sandbox tool is a very particular kind of work: you pick the threats you care about, identify which altitude can actually catch them, and then write the same declarative vocabulary in a form that altitude's enforcement mechanism can check. The vocabulary is the same across the tower. Only the compiler changes.

## Why this matters: delegation becomes contractual

The immediate reason any of this matters: delegation.

Without the tower, delegating a coding task from a large model to a small one is nerve-wracking in a specific way. The big model understands the request and has the context. The small model is fast and cheap and has none of that context. You hand it a task, give it tool access, and *hope*. You audit its output after the fact. If it edits the wrong file or imports the wrong library or runs an unsafe command, you notice during review (or worse, you don't). Your only defense is imperative — you watch, you intervene, you roll back.

With the tower, delegation is contractual. The big model writes a spec:

```
@source("src/**/*.py") {
  .fn#authenticate      { show: body;    editable: true;  }
  .fn#check_admin_role  { show: body;    editable: true;  }
  .class#User           { show: outline; editable: false; }
}

@source("tests/**/*.py") {
  .fn[name^=test_auth]  { show: body; editable: false; }
}

@after-change(.fn) {
  test: pytest tests/test_auth.py;
  lint: ruff check src/auth.py;
}
```

This example uses the sandbox consumer's at-rule sugar (`@source`, `@after-change`). The canonical entity-selector form is shorter on the page for complex views and generalizes to any registered taxon: `world file[path^="src/"] node[kind="function"][name="authenticate"] { show: body; editable: true; }` is the same rule as the nested selector above. Both parse to the same AST. See [Umwelt: The Layer We Found](umwelt-the-layer-we-found) for the full framing and the vision docs in `~/Projects/umwelt/docs/vision/` for the grammar reference.

That's a view file — self-contained because the `@source` blocks name their own file sets. The delegate executor needs nothing else to turn this into a workspace. Written by the big model (often built up programmatically from pluckit exploration rather than hand-authored), rendered by the Harness into:

- A virtual workspace containing four files (the bodies of the two editable functions, the outline of `User`, the bodies of the test functions).
- A write-back layer that splices any edits the delegate makes back into the real source files.
- A hook that runs the tests and the linter after every change.
- Nothing else. No other files exist in the delegate's world. No other tools. No other hooks.

And then — if you want belt-and-suspenders — the whole delegate invocation runs inside a lackpy interpreter (so any code the delegate executes during its session is from a restricted namespace), inside an nsjail process (so even if lackpy leaks, the OS catches it), with a retrieval layer providing only the six most relevant auth-fix examples from the example bank (so attention stays concentrated).

The delegate's entire universe is the spec. It can't edit the wrong file because the wrong file doesn't exist in its workspace. It can't call the wrong function because the function isn't in its namespace. It can't read the wrong path because the path isn't in its filesystem view. It can't attend to the wrong examples because the wrong examples aren't in its prompt.

The big model's job shifts from *monitoring the delegate* to *writing the spec*. Writing a spec is cheap, declarative, auditable, and composable. Monitoring a delegate is expensive, imperative, and ad-hoc. The asymmetry is enormous.

This is what the [ma framework](../blog/ma/00-intro) has been pointing at the whole time. Coordination is grade adjustment. Grade adjustment, at scale, works because the adjustment is written into structures the enforcement mechanism can check. We've been building the vocabulary — ma, the grade lattice, the specified band, the Harness as constructor — and the tower is what it looks like when you give that vocabulary four different compilers.

## The layer we found while trying to build this

A concrete finding from the design sessions that produced this post, worth recording because it changes where the implementation work lives.

We started by assuming the view runtime (parser, AST, workspace builder, write-back layer, hook dispatcher, the reference `from_view` compiler for nsjail-python) would live inside lackpy — the language-altitude sandbox from the lackey series. It's lackpy-adjacent work, and lackpy already owns delegate orchestration, so the obvious move was "put the view executor in `lackpy.views` as a submodule."

While specifying it, we noticed that **about 83% of the code had no dependency on lackpy at all.** The parser is pure stdlib. The AST is dataclasses. The workspace builder is pathlib plus filesystem operations. The write-back layer is difflib plus hashing. The hook dispatcher is subprocess plus timeouts. The `from_view` compiler only imports nsjail-python. None of that needed lackpy's providers, kits, or inference machinery. The *actually* lackpy-specific code was a thin orchestration layer (~280 lines) that composed the generic runtime into lackpy's delegate-execution pipeline.

Then the same question came up about pluckit — could the view runtime live there, alongside the CSS-selector query engine that already exists? No: pluckit is specifically for *querying code*. The views we're designing are *sandbox specifications* that happen to borrow the CSS surface syntax. They share punctuation but their semantics are disjoint — pluckit has no reason to know what `@source` or `@tools` or `@after-change` mean, and view execution has no reason to know about tree-sitter node types except when it calls *into* pluckit for selector evaluation inside `@source` blocks. Bundling them would muddle two different scopes.

Then kibitzer and agent-riggs: maybe the format lives in one of those? Also no. Both of them are *consumers* of views (kibitzer enforces `@tools` at the hook layer; agent-riggs audits recorded views across sessions), and making a consumer the owner would force every other consumer to depend on it just to parse a view file. Wrong dependency direction.

What we found is that **there's a layer sitting underneath all these tools that doesn't have a home.** It's the layer that defines the view format, parses it, represents it in memory, builds sandboxes from it, and provides reference compilers for the enforcement mechanisms that consume it. Lackpy uses it. nsjail-python and bwrap would compile against it. Kibitzer reads the active view through it. Agent-riggs audits recorded views via it. Pluckit gets called *by* it for selector evaluation. But none of those tools owns it, and none of them should, because every one of them would pull in concerns the others don't need.

The correct architecture is a new leaf-dependency package — working name **`umwelt`**, after Jakob von Uexküll's 1934 biosemiotics term for "the self-centered perceptual world an organism experiences, constituted by what it can sense and act on." Which is precisely the thing a view defines for a delegate: the slice of reality it experiences as its entire world, bounded by `@source` for what it can see and `@tools` for what it can act on. The pun is cheeky on purpose — applying a theory of animal perception to an LLM agent — but also structurally accurate, because the ma framework's "world coupling" axis *is* the umwelt axis seen from a different angle.

The `umwelt` package owns:

- The view format specification
- The parser and AST
- The generic virtual-workspace builder and write-back layer
- The hook dispatcher
- Reference compilers for each enforcement altitude (`umwelt.compilers.nsjail`, `umwelt.compilers.bwrap`, and later others)
- The view bank (storage, retrieval, git-history distillation — future phase)

And every other tool imports from it. The dependency graph stays acyclic: umwelt depends on nothing consumer-specific; every consumer depends on umwelt. Lackpy becomes a ~280-line orchestration layer instead of a 1,200-line monolith. nsjail-python gets a ~300-line reader it can vendor or import. Kibitzer gets a ~40-line hook that reads `umwelt.ast` and enforces `@tools`. Agent-riggs reads the view bank directly.

This partially resolves question 4 in the Unresolved section below ("does the view layer need its own project?"). The answer is yes, and here's the shape of it. The open question is no longer *where* the layer lives but *when* we build it and *what* we bootstrap it inside of in the meantime (probably as `lackpy._umwelt` until the boundary is proven, then extracted).

The finding is small but load-bearing: every time we tried to put this work inside an existing tool, the tool's identity started to bend. Each tool in the stack has a sharp scope — jetsam is git workflow, blq is build-log capture, fledgling is code intelligence, pluckit is code querying, kibitzer is observation and coaching, agent-riggs is cross-session audit, lackpy is restricted Python execution — and view-layer concerns don't belong inside any of them. What view-layer concerns belong inside is a new tool, and the new tool is `umwelt`.

### A further refinement, after writing the vision docs

*This subsection was added after the rest of the post was written, once the umwelt vision docs were drafted and the Ma-grounded framing crystallized. Everything above still stands — the "the layer we found" argument is unchanged at its core. What changed is that the layer's architectural role got sharper than the original "needs its own package" framing implied.*

The finding got sharper once the umwelt vision docs were written. The layer we found isn't just "its own package." It's specifically **Layer 3 of the three-layer regulation strategy** that the OS existence proof demonstrates — the strategy that lets arbitrary computation at high world coupling stay inside the [specified band](../blog/ma/08-the-specified-band).

The OS's proof is that you can regulate an enormous amount of world coupling without losing transparency, via three stacked specified layers:

- **Layer 1 — Constraints**: namespaces, cgroups, seccomp filters, capabilities. These don't observe or decide; they bound what's *possible*.
- **Layer 2 — Observation**: `/proc`, audit logs, strace, cgroup accounting. These don't decide; they report what *happened*, as structured data.
- **Layer 3 — Policy**: SELinux, AppArmor, firewall rules. These decide what's *allowed*, with readable specified rules operating over observed state. The composition of three specified layers is still specified.

umwelt is Layer 3 for the agent stack. Not Layer 1 (nsjail, bwrap, lackpy's validator, kibitzer's hooks already handle that, each at its altitude). Not Layer 2 (blq, ratchet-detect, strace, auditd already handle that). Layer 3: the authoring surface for the specified rules that the other two layers compose around. A view is a Layer-3 artifact — readable, hashable, version-controllable, diffable — and the entire stack's regulatory loop reads it.

This reframes "the common language" from metaphor to mechanism: Core umwelt is *vocabulary-agnostic*. It knows about selectors, cascade, declarations, and compilers; it knows nothing about files, tools, or networks. Consumers register their vocabularies (`world`/`capability`/`state`/`actor`/`policy`) via a plugin API, each taxon corresponding to a load-bearing concept in the Ma framework. Every component in the specified-band Harness — enforcers reading compiler outputs, observers producing evidence the ratchet can consume, auditors reading views from the bank, coaches enforcing `@tools` at the semantic altitude — speaks the same vocabulary because umwelt defines it and imports nothing consumer-specific. That's what "common language of the specified band" means in operational terms: one vocabulary traverses the whole regulatory loop, because the loop has one authoring surface for its policy layer.

The companion post [Umwelt: The Layer We Found](umwelt-the-layer-we-found) captures the Ma-grounded framing in more detail, including the vocabulary-agnostic core, comparison-semantics properties, and the ratchet as a first-class utility — all of which came out of the implementation exploration after this post was written.

## Unresolved

The view-as-sandbox reading opens more questions than it answers. Some of the ones worth examining before this becomes a claim rather than a sketch:

1. **Is the generalization real or just a rhyme?** Do nsjail, lackpy, views, and retrieval actually share a structural pattern you could write down, or do they just *look* alike from a distance? If they share structure, the shared abstraction should have a crisp definition — something you could write a type signature for. *Partial answer in [Umwelt: The Layer We Found](umwelt-the-layer-we-found): the operational definition of "same structural pattern" is "one spec, multiple compilers producing different enforcement mechanisms." umwelt demonstrates this at the architecture level; the empirical confirmation requires the package to actually run end-to-end on a real task.*

2. **What does the full tower look like from the inside?** If you stack all four layers, what does the composite sandbox look like from the delegate's perspective? Where are the seams? Which layer catches which failure class in practice, and how much overlap is there? There's a study here that's more empirical than theoretical. *The compiler taxonomy added a second axis (local vs remote, sync vs async) that reshapes the tower's picture — see [Umwelt: The Layer We Found](umwelt-the-layer-we-found). The empirical question remains open until the package runs.*

3. **What's the smallest useful view system?** The sketch above adds declarations for editability, tests, and hooks. How much of that is load-bearing for the sandbox claim, versus feature creep on the original rendering spec? The minimal version might be: `editable: bool` and nothing else. *Partially resolved: the v1 minimum is parser + AST + workspace builder + write-back + hook dispatcher + two compilers (nsjail and bwrap). Spec'd in `~/Projects/umwelt/docs/vision/package-design.md`.*

4. **Does the view layer need its own project?** We've been calling it a viewer but it's clearly larger than that. "Lens" is one candidate name. But it might belong inside pluckit, or inside lackpy, or as a new layer of nsjail-python, or standalone. I don't know where this lives architecturally yet. **Resolved: yes, and it's called umwelt.** The package is a leaf dependency with its own vision docs at `~/Projects/umwelt/docs/vision/`. Every consumer (lackpy, kibitzer, agent-riggs, the claude-plugins hook layer) imports from umwelt; umwelt imports nothing consumer-specific. See [Umwelt: The Layer We Found](umwelt-the-layer-we-found) for the full story.

5. **How does this connect to the broader coordination framework?** Is a view just a special case of some more general coordination primitive? If so, what's the generalization? If not, what's the principle that separates view-like sandboxes from other coordination mechanisms? *Resolved at the architectural level: umwelt is Layer 3 of the three-layer regulation strategy that the OS existence proof from [Ma post 8](../blog/ma/08-the-specified-band) demonstrates. Views are the authoring surface for specified policy over observed state, with Layer 1 (constraints — nsjail/bwrap/lackpy/kibitzer) and Layer 2 (observation — blq/ratchet-detect/strace) delegated to other tools. The connection to the broader coordination framework is: umwelt IS the specified-coordination layer of the framework, implemented as a common vocabulary shared across every component in the regulatory loop. See [Umwelt: The Layer We Found](umwelt-the-layer-we-found) for the full Ma-grounded argument.*

6. **What's the view layer's escape technique?** Every sandbox has edge cases where the abstraction leaks. nsjail has side channels. lackpy has string-eval tricks and AST confusion. Views will have something. The obvious candidate: a view constrains *visibility* over regions, but the delegate can still produce code that, when the test hook runs, affects things outside the view. Is there a principled way to bound *effects* in addition to *visibility*? Maybe that's where the lackpy layer earns its keep. *Partially resolved: effect-bounding is inherited from the layers below the view, not from the view itself. The view compiles to nsjail/bwrap (OS-altitude effect bounds) and lackpy (language-altitude effect bounds). Views don't bound effects directly; they bound effects by composition with the other layers.*

7. **Where does this fit in the blog's existing arc?** The pieces are here — ma, Harness, conversation-as-fold, [dialect design](../blog/tools/lackey/03-the-specialization-lives-in-the-language), retrieval — but the throughline from them to *this* hasn't been written. The sandbox tower feels like it wants to be the payoff post for the coordination-as-grade-adjustment thread. It's not ready to claim that yet. *[Umwelt: The Layer We Found](umwelt-the-layer-we-found) is the companion post that makes the implementation-level decisions concrete. Together the two posts are starting to look like the "payoff post for coordination-as-grade-adjustment" — but we still need working code before either gets promoted out of the grab bag.*

None of these are objections. They're the shape of what we'd have to build and measure before this writeup becomes a real post instead of a sketch. Several have moved from "open" to "partially answered by the umwelt design work" — see [Umwelt: The Layer We Found](umwelt-the-layer-we-found) for the companion post that captures the resolutions.

## Where this sits

This belongs in the same conceptual neighborhood as:

- [The Ma of Multi-Agent Systems](../blog/ma/00-intro) — the grade lattice the tower is specifying against.
- [The Lackey Papers](../blog/tools/lackey/00-the-ratchet-at-the-small-scale) — where the language-altitude sandbox (lackpy) and the dialect-design argument live.
- [Retrieval Beats Stuffing](retrieval-beats-stuffing) — the attention-altitude sandbox in disguise.
- [The Integration Layer Plan](integration-layer-plan) — the system the view layer would get built into, if it turns out to be load-bearing for delegation.
- [CSS Selectors for Code](../blog/sitting-duck-css-selectors) — the query language the view layer extends.

The writeup is a draft because the pattern is real but the tool stack isn't built yet. The sandbox tower is a theory we'd want to operate before we publish, because every layer in it has edge cases we haven't probed. Promote this to a main-series post only after the delegation use case runs end-to-end on a real codebase — not before.

---

*This draft grew out of a raw thinking piece preserved at [Views Are Sandboxes](views-are-sandboxes). The seven open questions there are the ones this writeup doesn't yet answer.*
