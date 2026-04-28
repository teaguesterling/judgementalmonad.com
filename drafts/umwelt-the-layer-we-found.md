# Umwelt: The Layer We Found

*The follow-up to [The Sandbox Tower](the-sandbox-tower). That post described the theory — multiple altitudes, declarative grade specifications, delegation becomes contractual. This post captures the nine architectural decisions that came out of actually designing the package: text-emitting compilers, a compiler taxonomy that includes distributed schedulers, the realization that modes are coarse views, git history as a view corpus, views as the artifact that unifies the ratchet's two products, port-ready decomposition, a vocabulary-agnostic core with Ma-grounded taxa, comparison-semantics properties, and the ratchet as a first-class utility. Together they reshape what "the layer we found" turned out to be — and what it's for.*

---

## Context

[The Sandbox Tower](the-sandbox-tower) made a theoretical claim: nsjail, lackpy, views, and retrieval are all declarative grade specifications rendered into different enforcement mechanisms at different altitudes, and they stack. Once you stack them, delegation stops being nerve-wracking and starts being contractual — you write the spec, the compilers enforce it, and the delegate operates inside a world you designed.

That post ended with a set of unresolved questions. One of them — "does the view layer need its own project?" — turned out to have an answer that changed how the rest of the stack looks. Answering it required making nine architectural decisions that aren't in the original post. This is the companion doc that captures them.

The package that emerged is called **umwelt** (after von Uexküll's term for the perceptual world an organism experiences, constituted by what it can sense and act on). The complete vision docs live in `~/Projects/umwelt/docs/vision/` — this post is the narrative companion that explains the decisions to anyone who reads it, not the specification.

**Two framings of the same thing.** The first six decisions below describe *what we built*: compilers that emit text, a taxonomy of enforcement targets, the realization that the artifact we wanted (views) subsumes the older concepts (modes, tools, strategy) and can be bootstrapped retroactively from git history. Decisions 7 through 9 describe *what the whole package is for*, in a framing that only became clear after the vision docs were written: **umwelt is Layer 3 of the three-layer regulation strategy that the [OS existence proof](../blog/ma/08-the-specified-band) demonstrates.** Layer 1 is constraints (nsjail, bwrap, lackpy validator, kibitzer hooks). Layer 2 is observation (blq, ratchet-detect, strace). Layer 3 is the authoring surface for specified policy composed over observed state. umwelt is that authoring surface, generalized to the agent stack — and because it sits in the specified band, the whole regulatory loop can read and produce views in the same vocabulary. The Ma-grounded framing is the reason the rest of the architectural decisions hold together, and it's the reason the package is the shape it is rather than any of the earlier shapes we tried.

---

## Decision 1: Text-emitting compilers

**The original sketch**: umwelt is a Python package that imports nsjail-python, calls its `Jail()` builder to construct a jail config programmatically, and eventually asks the nsjail-python maintainers to accept an upstream `from_view()` reader so users can write views instead of imperative Python.

**What was wrong with that**:

1. It required umwelt to import nsjail-python at runtime, tying umwelt's version compatibility to nsjail-python's API.
2. It required a cross-repo proposal for every enforcement target. Asking nsjail-python to adopt the view format, then bwrap's Python wrapper to adopt it, then kubernetes client libraries to adopt it — that's a coordination nightmare across projects we don't control.
3. Users without nsjail-python installed couldn't use umwelt with nsjail at all, even though `nsjail` (the binary) was sitting right there on the system.
4. Testing required mocking nsjail-python's `Jail` class and inspecting the resulting object graph — more complex than string comparison.
5. For bwrap — which doesn't really have a canonical Python wrapper — the whole plan broke down, because there was nothing to extend.

**The better architecture**: umwelt emits the enforcement tools' *native text configs* directly. nsjail takes protobuf textproto on `--config`; umwelt emits textproto. bwrap takes a list of argv flags; umwelt emits argv. kubernetes takes YAML manifests; umwelt will emit YAML. slurm takes sbatch scripts; umwelt will emit sbatch. The enforcement tools don't change; umwelt targets what they already accept.

This is obvious in retrospect and I walked past it the first time because I was thinking "Python-to-Python composition." The better frame is Unix composition: text in, text out. Every downstream tool becomes composable via the primitive every tool already supports — reading a config file or command-line flags.

**What this unlocks**:

- **Zero cross-repo coordination.** umwelt ships. nsjail-python doesn't change. bwrap doesn't change. The upstream proposal thread dies entirely.
- **umwelt stays a true leaf dependency.** No runtime imports of any enforcement tool's Python wrapper. Only required dependency is `tinycss2` for CSS tokenization.
- **Works on systems without the Python wrappers.** You can use umwelt with stock `nsjail` on a box that has no Python bindings installed. The umwelt CLI writes a textproto file and invokes `nsjail --config` directly. Same for bwrap.
- **Lower version coupling.** If nsjail's protobuf schema changes, umwelt updates its compiler. If nsjail-python's API changes, umwelt doesn't care at all. The binary's config format is usually more stable than any wrapper library's API, which means the coupling surface is smaller.
- **Universal composability.** Text-in, text-out is the Unix composition primitive. You can pipe, redirect, diff, commit, version-control, and remix umwelt's output with any tool that eats text. Python-object-out is composable only within Python, and only if the wrapper is installed.
- **Testing becomes string comparison.** "Does umwelt produce correct nsjail textproto for this view?" is a reference-file comparison. No subprocess, no object-graph walking, no mocking.

The decision generalizes: **compilers are pure text transformations from the umwelt AST to each target's native format.** Every planned compiler — nsjail, bwrap, docker, podman, apptainer, slurm, kubernetes — targets the underlying tool's native config format, not a Python wrapper around it.

This is the decision that made the rest of the architecture snap into place. It's load-bearing in a way that wasn't visible until we tried to write the spec.

---

## Decision 2: The compiler taxonomy

The sandbox tower post named four altitudes: OS, language, semantic, conversational. They're still correct, but they're not enough to describe the compiler design space. Two new axes emerged while cataloging the compiler targets:

### Axis 1: Locality

Some enforcement tools run the delegate on the **same machine** as umwelt. Others submit a job to a **remote scheduler** that runs the delegate on a different host.

- **Local**: nsjail, bwrap, firejail, podman-foreground, docker-foreground. Write-back and `@after-change` hooks run synchronously after the delegate finishes. `@budget` maps to rlimits or cgroups on the local kernel. Familiar process model.
- **Remote (container)**: apptainer (often invoked inside slurm), docker in detach mode, podman in detach mode. Delegate runs on a possibly-different host; the process may be part of a larger orchestration.
- **Remote (scheduler)**: slurm, kubernetes, nomad, AWS Batch. The delegate is a *job* submitted to a scheduler that runs it on whatever compute node has capacity. umwelt's role is producing the job spec; actual execution happens asynchronously, somewhere else.

### Axis 2: Execution model (synchronous vs asynchronous)

- **Synchronous**: umwelt's runner blocks until the delegate finishes. Familiar API. Suitable for interactive and CI workflows.
- **Asynchronous**: umwelt submits a job and returns a handle. The caller polls, waits, or listens for completion separately. Required for schedulers, because the job may be queued behind other jobs and its completion is independent of umwelt's local process lifetime.

### The grid

|  | Synchronous | Asynchronous |
|---|---|---|
| **Local** | nsjail, bwrap, firejail, docker-foreground | docker-detach, podman-detach |
| **Remote (container)** | apptainer-inside-slurm | apptainer-standalone |
| **Remote (scheduler)** | *(rare; SSH-equivalent)* | slurm, kubernetes, nomad, aws-batch |

### Why this matters

Three things in the view format behave differently once you cross the local-to-remote boundary:

**`@source` compilation.** For a local compiler, `@source("src/auth")` becomes a bind-mount flag (`--bind src/auth /workspace/src/auth` for bwrap, or equivalent in nsjail). For a remote compiler, `@source` becomes a *stage-in directive* — the workspace files have to travel to the compute node. The compilation has two strategies: shared filesystem (the path is already reachable on the compute node, no transfer needed) or explicit transfer (the compiler emits `sbcast` commands, or `kubectl cp`, or container volume mounts from an object store). The compiler doesn't pick; it emits the appropriate stage-in metadata and the runner executes the transfer.

**`@after-change` hook dispatch.** Local: hooks run synchronously in umwelt's process after the delegate exits and write-back completes. Remote: hooks have two options. Either umwelt blocks, waits for the remote job to finish, pulls results back, and runs hooks locally (a sync-ish remote mode). Or umwelt submits a follow-up job with `--dependency=afterok` on the main job, so hooks run on the scheduler after the main job completes (a truly async mode). The choice is per-runner, not per-compiler.

**`@budget` as request vs enforcement.** Local: `@budget { wall-time: 60s }` maps to nsjail's strict `time_limit: 60` — the kernel kills the process at 60 seconds, period. Remote: `@budget { wall-time: 60s }` maps to slurm's `#SBATCH --time=00:01:00`, which is a *request* to the scheduler. The scheduler *may* kill the job at 60 seconds, but the guarantee is weaker than local enforcement. Documentation has to be explicit about this — "strict" vs "best-effort" limits — so users aren't surprised when a remote job runs longer than its budget because the scheduler was generous.

### What the compiler taxonomy means for the sandbox tower

The original tower was four altitudes stacked vertically. The new picture is that each altitude also has a locality dimension: each altitude can have local-enforcement compilers and remote-enforcement compilers targeting the same abstract altitude differently. nsjail and bwrap enforce the OS altitude locally; slurm and kubernetes enforce the OS altitude remotely (through scheduler-mediated resource allocation plus the container runtime the scheduler uses internally). They're at the same altitude but different locality classes.

This isn't a contradiction of the tower; it's a refinement. The altitude determines *which class of violation* the layer catches. Locality determines *how the enforcement is delivered*. You can stack them independently: a delegate can run inside a kubernetes Pod (remote) that itself uses seccomp and read-only filesystem mounts (OS-altitude enforcement), and also inside a lackpy-restricted interpreter (language altitude) that bounds which functions its Python code can call. Two altitudes, two locality classes, same abstract view.

The practical consequence: **the same view can compile to different targets for different deployment contexts.** A developer iterates locally under bwrap. CI runs the same view under Docker. A batch inference job submits the same view via slurm. A production service runs the same view as a kubernetes Job. One spec, multiple compilers, multiple deployment targets — without any of the view authoring changing. The view bank (see Decision 4) accumulates views that work across all of these.

---

## Decision 3: Views supersede modes

"Modes" — plan mode, implement mode, edit mode — have been a concept in Claude Code and in the ratchet series for a while. You switch modes to change what the agent can do. Plan mode denies Write/Edit; implement mode allows them. Review mode is read-only. Mode is a coarse grade directive.

We noticed: **modes are just very primitive views.** Every mode is a special case of a view where `@source("**/*") { * { editable: <mode-dependent> } }` and `@tools { ... }` are set to coarse values. Implement-mode-for-tests is `@source("tests/") * { editable: false }`. Plan mode is `@source("**/*") { * { editable: false } }` with `@tools { deny: Write, Edit }`. Review mode is `@source("changed_files") { * { show: body; editable: false } }`. Every existing mode decomposes into a view.

Views subsume modes entirely, with two properties modes never had:

1. **Expressiveness.** Modes are a fixed set of presets. Views are arbitrary combinations of file scopes, tool allow/deny lists, hooks, and budgets. A view can be any mode; a mode can only be the preset it is.
2. **Per-task granularity.** Modes are global (one session, one mode). Views can be per-task, per-delegation, per-subtask. The outer agent writes a view for the specific thing the inner agent should do, not the broad category the session is in.

**The mode system collapses into a small set of named views.** "Plan mode" becomes `modes/plan.umw` in the view bank. "Implement mode" becomes `modes/implement.umw`. "Hotfix mode" becomes `modes/hotfix.umw`. Users who reached for modes reach for named views instead. Users who want finer control write one-off views. Same conceptual affordance, two orders of magnitude more expressive, unified artifact format.

This is worth naming because the mode vocabulary is load-bearing in how people talk about agent behavior today, and the view frame retires it without losing anything. You don't need modes once you have views. Modes were always coarse views in disguise.

---

## Decision 4: Git history is a view corpus

The view bank — a stored, queryable, version-controlled database of views that accumulates over time — is a natural phase-2 feature of umwelt. The obvious question is: how do you bootstrap it? Hand-writing the initial corpus is a lot of work; asking users to accumulate views one task at a time means the bank is empty until months of usage. Neither is great.

The realization: **every commit, PR, and branch is already a view retroactively.** The view you would have written for the task that produced a given commit is reconstructable from the diff: the files touched become `@source` blocks, the files with edits become editable, the files read-only. The commit message becomes a task description. The test suite that ran and passed becomes `@after-change`. The commit is a historical record of "here's a bounded piece of work that succeeded," which is exactly the shape of a view.

Distilling views from git history is structural, not semantic:

1. Walk `git log` (or PR metadata, or branch diffs) at the desired granularity.
2. For each commit, take the diff. Identify files touched.
3. Emit a view with `@source` blocks for the touched files' parent directories, `editable: true` on the modified files, `editable: false` on read-only context files.
4. Store the view in the bank alongside the commit metadata as the task description.

No LLM in the loop for the extraction. Pure diff analysis plus glob construction. The corpus writes itself from however many years of git history the repo has.

The payoff is bigger than "free corpus." It means the view bank is **pre-populated on day one** with examples that are guaranteed to correspond to real, completed work. Retrieval over the bank (find views similar to a new task) starts working immediately instead of needing months of accumulation. And the distilled views encode the *shape* of successful past work: which files cluster together, which changes are local vs cross-cutting, which tests correlate with which file regions.

This turns the view bank from a speculative phase-2 feature into something you can bootstrap in an afternoon. Every git repo becomes a view corpus by running the distiller.

---

## Decision 5: Views unify the ratchet's two products

The ratchet series previously argued that the ratchet has [two products](the-two-products): **tools** (narrowing world coupling) and **strategy** (narrowing decision surface). Both matter. Getting either wrong costs you — the experimental program measured exactly this, and the cost of getting strategy wrong was often higher than getting tools wrong.

We treated tools and strategy as parallel crystallization streams. The ratchet produced new MCP commands (tool crystallization) *and* new CLAUDE.md principles (strategy crystallization), and both flowed separately into the accumulated artifact pile.

The view format collapses this. A view expresses both axes in one artifact:

- `@source` and `editable` narrow **world coupling** — they specify which files and which regions the actor can see and modify.
- `@tools` narrows **world coupling** — which callable functions the actor can reach.
- `show:` and `@after-change` and retrieval declarations (future) narrow **decision surface** — which patterns the delegate's attention is primed by, which constraints its output must satisfy.

A single view is a crystallized grade directive along both axes simultaneously. When the ratchet crystallizes successful work, the output is a view, not a tool-and-principle pair. The view bank is the accumulated crystallization.

This isn't a repudiation of the two-products framing — it's the framing seen from the artifact side. "Two products" was correct at the level of "what changes during the ratchet turn" (world coupling gets tightened, decision surface gets shaped). But the *artifact* that captures a successful turn is one thing: a view. You store views. You retrieve views. You compose views. You learn from views. The bank is the crystallization store, and the crystallization is views.

One caveat worth preserving: views capture *configuration*, not *judgment*. A CLAUDE.md principle like "prefer editing existing files over creating new ones" is guidance that requires taste to apply — it's not something a view can fully express. Principles stay as a secondary crystallization target for the taste-requiring parts. But the *primary* target, the one that captures both world-coupling and decision-surface in one enforceable artifact, is the view.

---

## Decision 6: Port-ready decomposition

A language question came up while designing the package: should umwelt be Python, or Rust with Python bindings? A full Rust core would be faster at parsing and filesystem operations, memory-safer, able to support non-Python consumers, and would ship as a standalone binary. A pure Python implementation is faster to develop, easier to iterate on, easier to contribute to, and doesn't require a cross-platform build pipeline.

We went with Python for v1, but the decision came with an architectural constraint worth naming: **the internal architecture is decomposed cleanly enough that a later port to Rust — if ever needed — is mechanical rather than a rewrite.**

Concretely:

- The **parser** is a pure function: `text → View AST`. No side effects. Testable in isolation. A Rust replacement swaps in behind the same interface.
- **Compilers** are pure functions: `View → native format`. No side effects. No dependencies on the runtime. A Rust replacement swaps in behind the same `Compiler` protocol.
- **Workspace operations** are filesystem I/O; they stay in whatever language the orchestration lives in. Not a port candidate regardless.
- **Hook dispatch** is subprocess invocation. Same.

If the parser or compilers ever become bottlenecks (they won't, but hypothetically), we port just those modules to Rust without touching anything else. The rest of the package stays Python forever. Consumers don't notice the difference because the interface is unchanged.

This is "port-ready decomposition" as a design discipline. It doesn't mandate a language. It doesn't require any Rust code today. It just requires that the pure-function boundaries exist, so the escape hatch is there if it's ever needed.

The broader principle behind this is worth extracting: **when you're not sure whether a design decision (language, library, architecture) will hold up long-term, structure the code so that changing your mind later is mechanical.** Don't eagerly commit. Don't eagerly avoid committing either. Pick the cheap-and-obvious option for v1, but draw the internal boundaries where the expensive option would want them if it ever came. The cost of doing this is small — usually just "write pure functions and keep them behind narrow interfaces" — and the option value is large.

This is the same move the sandbox tower makes at the theory level: pick enforcement mechanisms that *could* be replaced independently, so the stack can evolve one layer at a time without rewrites. Port-ready decomposition is that principle applied to the implementation layer.

---

## Decision 7: Vocabulary-agnostic core with Ma-grounded taxa

The first six decisions above were written assuming umwelt's parser would have `@source`, `@tools`, `@after-change`, `@network`, `@budget`, `@env` as first-class at-rules baked into the grammar. That was the shape of every example I wrote. It's the wrong level of abstraction.

While working out the entity model, we noticed that none of those at-rules actually need to be in the parser. They're a *vocabulary* for one specific policy domain — sandboxing. The selector/cascade/compiler machinery applies equally well to any policy domain: a rate-limiting policy language, an access-control language, a tool-choice-routing policy, anything that wants declarative rules matched against a structured world. The at-rules aren't the language; they're the dictionary for one user of the language.

The refactor: **core umwelt is vocabulary-agnostic.** It knows about parsers, ASTs, selectors, cascade, declarations, and compilers. It knows nothing about files, tools, or networks. Consumers register their vocabularies through a plugin API:

```python
register_taxon(name="world", description="...", ma_concept="world_coupling_axis")
register_entity(taxon="world", name="file", parent="dir", attributes={...})
register_property(taxon="world", entity="file", name="editable", value_type=bool, ...)
register_matcher(taxon="world", matcher=FilesystemMatcher())
```

The sandbox vocabulary ships as a first-party consumer (`umwelt.sandbox`) in the same package, using the same registration API any third-party consumer would use. It's not privileged. It's the canonical example.

**Two forms, same AST.** The refactor introduces an entity-selector form as the canonical representation, with the original at-rule form preserved as sugar that desugars at parse time. The two forms look different on the page but compile to the same parsed AST:

Entity-selector form (canonical):

```
file[path^="src/auth/"]       { editable: true; }
file                           { editable: false; }

tool[name="Read"]              { allow: true; }
tool[name="Edit"]              { allow: true; }
tool[name="Bash"]              { allow: false; }
tool                           { max-level: 2; }

network                        { deny: "*"; }
resource[kind="memory"]        { limit: 512MB; }
resource[kind="wall-time"]     { limit: 60s; }

hook[event="after-change"] {
  run: "pytest tests/test_auth.py";
  run: "ruff check src/auth.py";
}
```

At-rule sugar form (equivalent):

```
@source("src/auth/**/*.py")    { * { editable: true; } }
@source("**/*.py")              { * { editable: false; } }

@tools {
  allow: Read, Edit;
  deny:  Bash;
}

@network { deny: *; }
@budget  { memory: 512MB; wall-time: 60s; }

@after-change {
  test: pytest tests/test_auth.py;
  lint: ruff check src/auth.py;
}
```

Both specify the same policy — auth editable, everything else read-only, Read and Edit allowed, Bash denied, capped at computation level 2, no network, 512MB memory, 60s wall-time, tests and lint must pass after any change. Authors pick whichever form is clearer for the task. The at-rule form is shorter for sandbox-specific views; the entity-selector form generalizes to any registered taxon and is what the ratchet utility emits when proposing revisions from observation data. The parser canonicalizes both to the same AST internally.

**Entity names are bare, not taxon-prefixed.** Earlier iterations of the vision docs used `world file[path^="src/"]` with the taxon name as a prefix. That was overly explicit — it exposed the plugin system at the view-authoring layer for a disambiguation that matters in ~0% of views, and it broke the "borrow CSS exactly" dialect-design move by introducing a non-CSS namespace convention. Bare entity names are cleaner. The registry tags each match with its owning taxon at parse time, so cascade scoping and property validation still work. When a real collision occurs between taxa, that's a registration-time error, not a grammar problem.

**Cross-taxon compound selectors have context-qualifier semantics.** The descendant combinator between entities from different taxa means "in the context of the left entity, the right entity is the target." This is a small but real divergence from CSS's strict DOM-descendant combinator — but it's the minimum deviation needed to express actor-conditioned policies in a single rule:

```
tool[name="Bash"] file[path="src/auth/"] { editable: false; }
```

reads as "when the acting tool is Bash, files in `src/auth/` are not editable." The cascade treats this as a `file` rule with extra specificity contributed by the `tool` qualifier, so it refines (rather than replaces) the baseline `file[path="src/auth/"] { editable: true; }` rule. For non-Bash invocations, the baseline applies; for Bash, the qualified rule wins on specificity.

Cross-taxon compound selectors also compose with within-taxon structural descent. The three-level form

```
tool[name="Bash"] file[path="src/auth/"] .fn#protected { editable: false; }
```

means "when Bash acts on files in `src/auth/`, the `protected` function inside those files is not editable." The first combinator is cross-taxon context qualification; the second is within-taxon structural descent via the `file → node` parent-child relationship (where `.fn` is the class selector for a semantic-type class on the `node` entity).

Cascade is **per target taxon**, not per rule — a rule's target is the rightmost entity, and it competes against other rules targeting the same entity type in the same taxon. Specificity accumulates rightward across all selectors in the rule. More-qualified rules override less-qualified ones when their context applies.

The other examples in this post use at-rule sugar for brevity and because it's what pre-dates the refactor, but the entity-selector form is the thing you'll see in the vision docs and in any ratchet-proposed view. If you read the umwelt vision docs and see `file[path^="src/"]` where the blog post says `@source("src/")`, that's why.

This is the decision that makes the "common language" claim operational rather than metaphorical. Every component in a specified-band Harness can register its own taxon and participate in the regulatory loop — not by extending umwelt, but by plugging into its extension surface. A blq integration registers `blq/` entities for command registries. An access-control consumer registers `identity/` and `resource/` entities. A rate-limiter registers `quota/` entities. Each gets the parser, cascade, validator, CLI, and ratchet utility for free, because the core is shared and vocabulary-agnostic.

**The five canonical taxa aren't arbitrary.** They correspond to load-bearing concepts in the Ma framework:

| Taxon | Ma concept | What it regulates |
|---|---|---|
| `world/` | World coupling axis ([post 2](../blog/ma/02-the-space-between)) | Filesystem, network, environment, resources — the W axis of the grade |
| `capability/` | Decision surface + [computation channels](../blog/ma/07-computation-channels) | Tools, kits, effects, and computation levels 0–8 |
| `state/` | Observation layer ([post 8, Layer 2](../blog/ma/08-the-specified-band)) | Jobs, hooks, budgets, observations — the substrate for Layer-2 observation |
| `actor/` | [Four-actor taxonomy (post 1)](../blog/ma/01-actors-and-their-grades) | Principal, Inferencer, Executor, Harness — minimal in v1 |
| `policy/` | [The configuration ratchet](../blog/ma/the-configuration-ratchet) | Views-about-views — meta-level, deferred to v2 |

Each taxon is a regulatory concern the Harness needs vocabulary for: *what can the actor couple to*, *what can the actor do*, *what did we observe*, *who is in the room*, and *how do the rules themselves evolve*. The grouping isn't hierarchical — all five sit at the same level, and views can attach policy to entities from any taxon in the same file. But the separation keeps cascade scoped (a `world file` rule never competes with a `capability tool` rule), which makes plugin composition safe.

**A subtler consequence: view transparency is a first-class concern.** Ma post 8's [SELinux coda](../blog/ma/08-the-specified-band) warns that specified policy opaque to the governed actor wastes the actor's decision surface — the actor has to learn the rules empirically by probing and failing, which is a direct tax on performance. The entity model addresses this via plugin description metadata: every taxon, entity, and property carries a description string suitable for inclusion in a prompt. A planned v1.1 compiler, `compilers/delegate_context.py`, walks a view and renders it as a prompt fragment the governed actor can read. Plugin authors who write sparse descriptions produce unhelpful projections; good descriptions are operationally load-bearing. This is the "variety amplifier" move from Beer's cybernetics, applied at the policy-authoring layer.

---

## Decision 8: Comparison-semantics properties

In CSS, a declaration `color: red` sets a property value. In umwelt, some declarations have *comparison semantics* built into the property name. `max-level: 2` on a tool entity doesn't mean "set the tool's level to 2" — it means "cap the permitted level at 2." A tool with declared level ≤ 2 passes the policy check; a tool with level > 2 does not.

The pattern generalizes to a small set of prefixes:

| Prefix | Comparison | Example |
|---|---|---|
| (none) | exact / assignment | `editable: true` |
| `max-` | value ≤ declared | `max-level: 2`, `max-memory: 512MB` |
| `min-` | value ≥ declared | `min-budget: 256MB` |
| `only-` | value ∈ declared set | `only-kits: python-dev, rust-dev` |
| `any-of-` | value overlaps declared set | `any-of-effects: read, write` |

Plugins register properties with explicit metadata — `value_attribute`, `comparison`, `value_type`, `value_range`, `description`, `category` — so comparison semantics are *data*, not hard-coded grammar.

**Why this matters architecturally**: it keeps the selector grammar CSS-native while letting declarations carry policy semantics. The alternative would be introducing new selector operators like `[level<=2]`, which (a) drifts from CSS and loses the dialect-design familiarity payoff, (b) breaks selector-evaluation decidability in edge cases, and (c) complicates the cascade because comparison predicates would participate in specificity calculations. Encoding the comparison in the property name keeps selectors pure structural-and-equality predicates (decidable, fast, familiar) and pushes the interesting policy semantics into the declaration layer where they're property-typed and well-bounded.

**Why this matters for the ratchet**: the ratchet utility enumerates the property vocabulary to propose view revisions in a form consumers understand. If observation data shows a tool was actually invoked at computation level 3, the ratchet can propose raising `max-level` from 2 to 3 — and it knows exactly what the comparison means because the plugin declared it. The declarative semantics make automated policy proposal tractable in a way ad-hoc comparison operators would not.

**Why this matters for the delegate**: the view-projection compiler (Decision 7's transparency story) can render `max-level: 2` as "Your tool computation level is capped at level 2 (read + compute only)" because the comparison semantics are attached to the property declaration. The actor gets a readable description instead of raw syntax.

This is the kind of decision that looks like a minor language feature until you notice it's doing structural work at three different layers simultaneously. Pure-function selectors, structured property metadata, enumerable policy vocabulary — the same architectural property lets all three work.

---

## Decision 9: The ratchet as a first-class utility

The sandbox tower post described the ratchet conceptually — observe what happens, crystallize a revised view, apply it. In the original umwelt design, "producing a view from observations" was a thing the user would do by hand: look at a failure, write a new view, test it. The automation was implicit.

The vision docs made the ratchet **a first-class CLI utility**:

```bash
umwelt ratchet --observations blq://run-1234
umwelt ratchet --observations ratchet-detect://session-abc
umwelt ratchet --observations strace://trace.log --current-view auth-fix.umw --output auth-fix-v2.umw
```

The utility takes an observation source (blq database, ratchet-detect output, strace log, or any plugin-supplied converter) and runs specified narrowing analysis to propose a minimal view consistent with the observations. The proposed view is written to stdout or a file for human review. No auto-commit — the crystallization step is automated, the commit step is human judgment.

This generalizes blq's existing `sandbox suggest` and `sandbox tighten` workflows. blq already does this at the single-spec level: given a run's recorded resource usage and strace output, propose a tighter sandbox spec for the next run. umwelt generalizes that to multi-spec views that span workspaces, tools, budgets, and hooks simultaneously. The same underlying mechanic (observation → narrowing → proposal) applied to the richer policy format.

The load-bearing property: **the observation-to-view transformation is specified end-to-end.** No trained judgment anywhere in the loop. The observation source is specified data (blq's DuckDB schema, ratchet-detect's event store, strace's structured output). The narrowing algorithm is specified analysis (SQL, set intersection, range containment). The output is a specified view file. The human applies judgment at the commit point, not the analysis point. This keeps the ratchet inside the specified band even though it's automated — exactly the property Ma post 8 demands for Harness-layer automation.

The observation sources are pluggable: each observation tool registers a converter that normalizes its raw data into the umwelt vocabulary (entities with attributes). The ratchet utility then runs a narrowing algorithm over the normalized observations. A blq-observation-source plugin maps a blq run record to a set of `world file` entities (actually read), `world resource` entities (actually used), `capability tool` entities (actually called). The ratchet reads that normalized data and proposes tighter bounds on each. A ratchet-detect-observation-source plugin does the same for Claude Code conversation logs. A strace-observation-source plugin does the same for syscall traces. One ratchet utility, many observation sources, all via plugin registration.

**Why first-class matters**: it converts the ratchet from a conceptual claim to a working tool with a concrete interface. The feedback loop from observation to view revision becomes automatable (up to commit) without requiring humans to hand-write the narrowing for each new task. And because the observation sources are plugins, adding a new source is a leaf feature — you don't have to modify umwelt to add support for a new observation tool. This is the same plug-in architecture that makes the rest of the system composable, applied to the ratchet loop specifically.

The sandbox tower post described the ratchet as the feedback mechanism that closes the loop. The umwelt design makes it a concrete executable. Between the two there's a small but real transition from "theory of how this works" to "utility you can run on the command line against a real observation store and get a real view revision back."

---

## Decision 10: The three-layer architecture (Vocabulary / World State / Policy)

The first nine decisions describe a system where views (CSS) attach policy to entities that exist in a world. But where does the world come from? Through v0.5, the answer was implicit: matchers scan the filesystem, discover entities, and populate the entity graph at runtime. The view author doesn't declare what exists — the matchers just find it.

This is the equivalent of building a web page with no HTML — just CSS and a runtime that generates the DOM by scanning the filesystem. It works for prototyping. It doesn't work once you need reproducibility, composition, or audit.

**The insight:** umwelt's architecture mirrors the web platform's foundational separation, and the mirror has been incomplete. The web has three layers:

| Layer | Web | umwelt (until now) | What was missing |
|---|---|---|---|
| **Type system** | HTML DTD | Plugin registration (Python API) | Declarative surface for vocabulary |
| **Instance data** | The DOM | Runtime matcher discovery | Explicit world declaration |
| **Rules** | CSS stylesheets | `.umw` view files | Nothing — this was always the strength |

The three-layer architecture completes the mirror:

- **Vocabulary** — CSS at-rules (`@entity`, `@attribute`, `@property`) in `.umw` files. The DTD. What kinds of things can exist. Precedented by CSS Houdini's `@property` rule.
- **World State** — YAML (`.world.yml` files). The DOM. What things actually exist right now. Explicit entities, discovery recipes, projections, overrides, fixed constraints, composition via includes.
- **Policy** — CSS (`.umw` view files). The stylesheet. What rules apply to matched entities. Already done.

Each layer has a different rate of change, a different author, and a different reason to exist:

- Vocabulary changes when the conceptual model evolves (monthly, maybe). Authored by tool developers.
- World state changes when the environment changes (per-session, per-delegation). Authored by operators, generated by discovery, composed from includes.
- Policy changes when the rules change (per-task, per-observation). Authored by principals or the ratchet.

Mixing them produces the same pathology as inline styles in HTML: policy entangled with state, neither reusable independently. The separation is load-bearing.

### Why YAML for world state

The world file is deliberately not CSS. Three reasons:

1. **No conditionals.** YAML is a data format, not a rule language. You can't write `if mode == "implement" then add tool X` in YAML. Conditionals belong in policy (CSS), not in world state. The format *enforces* the separation.

2. **Composition.** YAML has established patterns for file inclusion, fragment references, and anchors. World definitions need to compose (base world + project-specific overlay + delegation-specific restrictions). CSS has no native inclusion mechanism.

3. **Familiarity.** Docker Compose, Kubernetes, GitHub Actions, Ansible, Packer — operators already think in YAML for environment declaration. The mental model transfers directly.

### The container analogy

A world file is a container spec for an agent's environment. The analogy is structurally precise:

| Container concept | World file concept |
|---|---|
| Base image | `include:` of a shared base world |
| `COPY` / `ADD` | `discover:` — recipes that populate entities from the filesystem |
| `docker run` args | `entities:` — explicit, hand-declared entities |
| Bind mounts | `projections:` — external data mounted without full enumeration |
| Read-only mounts | `fixed:` — immutable constraints policy cannot override |
| `ENV` / build args | `vars:` (reserved for future) |
| `docker inspect` | `umwelt materialize` — snapshot of the resolved world |
| Multi-stage builds | Multiple `include:` layers |

Both systems solve the same problem: declaring an isolated environment with specific contents, capabilities, and constraints, in a composable way that separates the environment definition from what runs inside it.

### The "doesn't exist" vs "not allowed" distinction

This is the insight that ties world state to capability-based security:

- **Doesn't exist (world layer):** Bash isn't in the world file. No CSS rule can grant access to it. The entity is absent from the entity graph.
- **Not allowed (policy layer):** Bash exists in the world, but `tool#Bash { allow: false; }`. A more specific rule could override this.

The world file is a **capability grant** — an unforgeable token defining what the delegate holds. Policy operates within what the world provides. The capability chain:

```
world file → entity exists → use[of=entity] → policy resolves → permission
```

Cut the first link and permission is impossible, regardless of policy. Fixed constraints in the world file are even stronger — they're hard boundaries that policy cannot relax. `fixed: { "network": { deny: "*" } }` means no network, period. CSS says `network { deny: false; }` and the fixed constraint wins. These are physics, not rules — the screen is 1920px wide regardless of what the stylesheet says.

### Materialization as audit

A world file is a recipe. **Materialization** is what you get when you execute the recipe — a concrete snapshot of every entity in the world, with provenance tracking for how each entity entered:

| Provenance | Meaning |
|---|---|
| `explicit` | Hand-declared in `entities:` |
| `discovered` | Found by a discovery recipe |
| `projected` | Declared as a projection (contents not enumerated) |
| `included` | Came from an included world file |

Materialization at three detail levels:
- **Summary** — entity counts per type, projection boundaries, tools available
- **Outline** — types + IDs + classes, directory trees, no full attributes
- **Full** — every entity with all attributes, replayable as a standalone world file

A full materialization *is* the answer to "what could the delegate see?" It's the S3* (audit) artifact from Beer's VSM, made concrete. Two runs of the same world file with a changed filesystem produce different materializations — the diff tells you exactly what changed in the delegate's reality.

### World state → SQL schema

Materialization and SQL compilation are the same operation at different levels. The materialized world populates the same `entities` table the SQL compiler uses. Three new tables extend the schema:

- `entity_provenance` — where each entity came from (explicit, discovered, projected, included)
- `projections` — external data mounted without full enumeration, with depth and boundary metadata
- `fixed_constraints` — world-level hard boundaries, applied after cascade resolution as a final clamp

The `effective_properties` view combines cascade-resolved values with fixed-constraint clamping:

```sql
SELECT entity_id, property_name,
       COALESCE(fc.value, rp.resolved_value) AS effective_value,
       CASE WHEN fc.id IS NOT NULL THEN 'fixed' ELSE 'cascade' END AS source
FROM resolved_properties rp
LEFT JOIN fixed_constraints fc ON ...
```

### Where this sits in the Ma framework

Each section of the world file maps to a VSM role:

| VSM | Role | World file section |
|---|---|---|
| S0 | Environment | `discover:` — filesystem, network, external sources |
| S1 | Operations | `entities:` with `type: tool` |
| S2 | Coordination | implicit — the harness itself |
| S3 | Control | `entities:` with `type: mode` |
| S3* | Audit | materialization — the complete snapshot |
| S4 | Intelligence | `inferencer:` |
| S5 | Identity | `principal:` |

The world file isn't infrastructure. It's the instantiation of the viable system for a specific delegation. Each delegate gets its own VSM, specified declaratively, auditable via materialization. The full design spec is in [`docs/vision/world-state.md`](https://github.com/teaguesterling/umwelt/blob/main/docs/vision/world-state.md).

---

## The decisions in one sentence each

1. **Text-emitting compilers.** umwelt emits nsjail textproto, bwrap argv, kubernetes YAML, etc. directly — no runtime dependency on any enforcement tool's Python wrapper. Unix composition, not Python composition.
2. **The compiler taxonomy.** Compilers split along locality (local vs remote) and execution model (sync vs async), which means distributed schedulers like slurm and kubernetes are first-class targets, and `@after-change`/`@budget`/`@source` each behave differently across local and remote compilers in documented ways.
3. **Views supersede modes.** Modes were always coarse grade directives in disguise. Named views in the view bank replace the mode system entirely, with two orders of magnitude more expressiveness.
4. **Git history is a view corpus.** Every commit, PR, and branch distills to a view via structural diff analysis. The view bank bootstraps on day one from however many years of history the repo has.
5. **Views unify the ratchet's two products.** Tools + strategy collapses into views-with-two-axes. The view bank is the crystallization store; the ratchet produces views, and views encode both world-coupling and decision-surface in one artifact.
6. **Port-ready decomposition.** Pure functions at the parser and compiler layers keep the option open to swap the implementation language without rewriting downstream code. The architecture is language-agnostic even though v1 is Python.
7. **Vocabulary-agnostic core with Ma-grounded taxa.** Core umwelt knows about parsers, selectors, cascade, and compilers — but nothing about files, tools, or networks. The sandbox vocabulary is a first-party consumer (`umwelt.sandbox`) registering five canonical taxa (`world`/`capability`/`state`/`actor`/`policy`) that correspond one-to-one with load-bearing concepts in the Ma framework. Third-party consumers plug in the same way. View transparency (rendering views as prompt fragments the governed actor can read) is a first-class concern, not optional ergonomics.
8. **Comparison-semantics properties.** `max-level: 2` caps a tool's permitted computation level at 2; it doesn't set it. Properties carry built-in comparison operators (`max-`, `min-`, `only-`, `any-of-`) registered as plugin metadata. Keeps selector grammar CSS-native and decidable while letting declarations encode real policy semantics.
9. **The ratchet as a first-class utility.** `umwelt ratchet --observations <source>` takes blq / ratchet-detect / strace output, runs specified narrowing analysis, and proposes a minimal view consistent with the observed behavior. Observation sources are pluggable. End-to-end specified; commit is human judgment. Converts the ratchet from conceptual claim to working tool.
10. **The three-layer architecture.** Vocabulary (CSS at-rules) + World State (YAML `.world.yml`) + Policy (CSS `.umw`) = DTD + DOM + CSS. Each layer has a different rate of change, author, and reason to exist. The world file is a capability grant; materialization is the audit artifact; fixed constraints are physics policy cannot override. The web got this split right; umwelt follows the same structure for the same reason.

---

## What kind of language is this?

One thing the nine decisions above don't name directly: the formal shape of what we built. Worth pinning down, because it situates umwelt in a forty-year tradition that the rest of the design quietly inherits from.

**A umwelt view is a Datalog program with CSS-shaped concrete syntax, a Viable-System-Model-partitioned predicate schema, and defeasible cascade semantics.**

Each piece of that sentence has a literature behind it:

- **Datalog** is the logic-programming formalism that every production authorization language of the last twenty years has converged on — OPA/Rego (CNCF graduated), Amazon Cedar (formally verified), Oso/Polar, Zanzibar-family (SpiceDB, Permify). Restricted Prolog: no recursion (yet), guaranteed termination, PTIME evaluation. Every umwelt selector is a conjunction of predicate applications; every declaration block is a rule head; the descendant combinator is the logical `∧`. `use[of="file#..."]` is unification via the `of` relation.
- **CSS-shaped concrete syntax** is the UX bet. Prior policy languages invented custom DSLs (Rego, Cedar, Polar, XACML). Users had to learn a new grammar on day one. umwelt bets that CSS is already a cognitive primitive for the agent-adjacent audience — see [The Specialization Lives in the Language](../blog/tools/lackey/03-the-specialization-lives-in-the-language) for the dialect-design argument.
- **VSM-partitioned schema** is the novel move. Stafford Beer's five systems (S1 operations, S2 coordination, S3 control, S3\* audit, S4 intelligence, S5 identity) plus environment (S0) give seven predicate domains. Agent authorization needs all seven. Human/service authorization (Cedar's principal/action/resource) only needs three. The specific inversion — regulator dominates regulated, S3↔S4 — is the architectural move that makes bounded delegation coherent.
- **Defeasible cascade semantics** matches Defeasible Logic Programming (García & Simari, 2004). Multiple rules can derive contradictory facts; a meta-rule picks the winner by specificity. CSS's cascade is exactly this pattern, minus the formalization.

The companion post [An LLM Is a Subject of Your Policy](an-llm-is-a-subject-of-your-policy) develops the lineage argument in full: where we sit relative to OPA, Cedar, and Oso, what's genuinely novel, and why having an LLM as one of the subjects (not the only one) forces the schema expansion. `docs/vision/notes/logic-semantics.md` in the umwelt repo is the reference note — §7 is the citation pool.

The practical consequence of naming the logic-programming lineage: **compilers become queries.** nsjail asks for all mount facts; bwrap asks for the same facts in a different encoding; kibitzer-hooks asks for writable-path facts per mode; a future audit compiler asks for the proof tree of a specific decision. Same program, different queries. Once umwelt matures, the compiler protocol can collapse into one primitive: `query: ResolvedView × Goal → FactSet`. That's the long-term leverage the v0.5 VSM restructure sets up.

**Update (post-v0.5):** This is no longer theoretical. umwelt now has a built-in SQLite compiler that turns views into queryable databases — policy is materialized as tables, world state is defined by per-tool plugins (each tool registers its own entities via the plugin API), resolution is derived, and each consumer (nsjail, bwrap, kibitzer, lackpy) reads its configuration from a compiler-specific SQL view. The view-stack architecture — materialized policy → live provider views → cascade candidates → resolved properties → compiler projections — is part of umwelt itself, not a separate package. The [Rosetta Stone](https://github.com/teaguesterling/umwelt/blob/main/docs/rosetta-stone.md) doc shows seven worked examples translating between CSS, SQL, and Datalog — "compilers become queries" went from thesis to implementation. What was originally prototyped as a standalone tool (ducklog) decomposed naturally: the SQL compiler belongs in the policy language, and world-state definition belongs in the tools that know their own domain.

---

## What this resolves in the sandbox tower's Unresolved section

The sandbox tower post left seven questions unresolved. After writing the umwelt vision docs and the subsequent implementation exploration that produced the vocabulary-agnostic-core / comparison-semantics-properties / ratchet-as-first-class-utility decisions, several are now answered at the architectural level. Empirical confirmation still waits on code.

**Q1: Is the generalization real or just a rhyme?** — **Resolved in principle.** The original claim was "nsjail, lackpy, views, and retrieval are all the same declarative grade specification pattern at different altitudes." The Ma-grounded framing makes this precise: umwelt is Layer 3 of the three-layer regulation strategy that Ma post 8 extracts from the OS existence proof. Layer 1 is constraints (nsjail, bwrap, lackpy validator, kibitzer hooks — bounding what's possible at their respective altitudes). Layer 2 is observation (blq, ratchet-detect, strace — reporting what happened). Layer 3 is policy (umwelt views — readable specified rules composing over observed state). The generalization isn't a rhyme; it's the same architectural pattern the OS uses, applied one level up. Still needs working code to confirm empirically.

**Q3: What's the smallest useful view system?** — **Partially resolved**: the v1 minimum is (parser + AST + workspace builder + write-back + hook dispatcher + two compilers: nsjail and bwrap). Everything else — selector-level extraction, the view bank, additional compilers — is v1.1 or later. Concretely spec'd in `~/Projects/umwelt/docs/vision/package-design.md`. The vocabulary-agnostic-core refactor (Decision 7) further clarified this: the minimum is core umwelt + the `umwelt.sandbox` first-party consumer registering `world`/`capability`/`state`. Everything else is pluggable on top.

**Q4: Does the view layer need its own project?** — **Resolved: yes, umwelt.** The finding about umwelt being a leaf-dependency package (rather than a submodule of lackpy, pluckit, kibitzer, or agent-riggs) is now fully worked out. Vision docs live in `~/Projects/umwelt/docs/vision/`.

**Q5: How does this connect to the broader coordination framework?** — **Resolved.** This was the most interesting resolution the Ma-grounding produced. The view layer isn't *like* a coordination primitive; it **is** the specified-coordination layer of the framework, implemented as a common vocabulary shared across every component in the regulatory loop. Every other tool in the stack (nsjail, bwrap, lackpy, kibitzer, agent-riggs, blq) plays a role at Layer 1 or Layer 2; umwelt is Layer 3. The whole stack is one three-layer regulation strategy where umwelt is the authoring surface for the policy layer. This is the "how does this connect to the Ma framework" answer the sandbox tower post was reaching for without quite landing.

**Q6: What's the view layer's escape technique?** — **Partially addressed**: the view grammar bounds *visibility and declared capability*, but the delegate can still cause effects outside the view via hooks that run arbitrary commands. The mitigation is layered: views compile to OS-altitude sandboxes (nsjail/bwrap) that bound what the delegate's subprocesses can actually reach, regardless of what the view's `@tools` block says. The language-altitude sandbox (lackpy) catches code paths that slip past the view's tool list. Effect-bounding is inherited from the layers below, not from the view itself.

**Q7: Where does this fit in the blog's existing arc?** — **Resolved in principle.** The sandbox tower post + this post + the integration layer plan together are the payoff post for the coordination-as-grade-adjustment thread — they're the concrete instantiation of what ma + ratchet + lackey + retrieval-beats-stuffing were all pointing at. The Ma-grounded framing (Layer 3 of the three-layer strategy) is the throughline from the Ma series' specified-band argument to working code. But the payoff post doesn't graduate to the main blog until the v0.1 walking skeleton runs end-to-end on a real task. Drafts stay drafts.

**Q2** remains empirically open — "what does the full tower look like from the inside?" needs the package to actually run under load before anyone can report on seams and failure classes.

---

## Where this goes next

Implementation is being handed off to another agent. The complete vision docs are in:

```
~/Projects/umwelt/docs/vision/
├── README.md                    orientation — the common language of the specified band
├── policy-layer.md              framing — Ma grounding, why umwelt sits at Layer 3
├── entity-model.md              taxa, entities, properties, cascade, plugin registration
├── view-format.md               grammar, syntactic forms, worked examples
├── world-state.md               three-layer architecture, YAML world files, materialization
├── package-design.md            module layout, public API, runtime, roadmap
├── implementation-language.md   Python + tinycss2 decision, port-ready decomposition
└── compilers/
    ├── index.md                 compiler taxonomy + planned targets
    ├── nsjail.md                view → nsjail textproto mapping
    └── bwrap.md                 view → bwrap argv mapping
```

**The read order** for someone coming to the vision docs cold: start with `policy-layer.md` for the Ma-grounded framing (why umwelt exists at all), then `entity-model.md` for the structural model (what views attach policy to), then `world-state.md` for the three-layer architecture (how the world views attach policy to gets declared and materialized), then `view-format.md` for the surface grammar, then `package-design.md` for the implementation shape. The README sits above these as a one-screen orientation.

The v0.1 walking skeleton is roughly: core parser + AST + registry + selector engine + cascade resolver, plus the first-party sandbox consumer registering `world`/`capability`/`state` taxa, plus the nsjail compiler. From there, bwrap, lackpy-namespace, kibitzer-hooks, the ratchet utility, and the view bank can be written incrementally without blocking each other. The core/sandbox split means the first-party sandbox package is a regular consumer of core umwelt — no special cases, no privileged access, same plugin API any third-party consumer would use.

This blog post is the narrative companion to those specs. Any reader who wants to understand *why* umwelt exists and *why* its architecture is what it is starts here. The specs answer *what* and *how*; this post answers *why*. The `policy-layer.md` doc in the vision directory serves a similar role inside the repo — it's the "why" counterpart to the rest of the vision, but scoped to readers who are going to touch code. This blog post is for readers who won't.

---

## Where this sits in the blog's existing arc

- **[The Ma of Multi-Agent Systems](../blog/ma/00-intro)** — the grade lattice that views specify against, and the theoretical home umwelt bottoms out in. umwelt is specifically **Layer 3 of the three-layer regulation strategy the OS existence proof demonstrates** ([Ma post 8](../blog/ma/08-the-specified-band)) — the specified policy-authoring surface that composes over Layer-1 constraints (nsjail/bwrap/lackpy/kibitzer) and Layer-2 observation (blq/ratchet-detect/strace). The entire package's architecture bottoms out in that framing, and the design decisions that would otherwise look arbitrary (why only specified rules, why CSS, why vocabulary-agnostic core, why comparison-semantics properties) become necessary once the Ma grounding is in place.
- **[The Lackey Papers](../blog/tools/lackey/00-the-ratchet-at-the-small-scale)** — dialect design argument: borrow a grammar the model already knows. Views extend this from "query language" to "sandbox spec language," applying the same move at a new altitude.
- **[Retrieval Beats Stuffing](retrieval-beats-stuffing)** — the conversational-altitude sandbox in disguise. Views include retrieval declarations (future) to fold this into the same format.
- **[The Two Products of the Ratchet](the-two-products)** — the framing this post partially retires. Tools and strategy are still real, but views unify them into one artifact per crystallization.
- **[The Sandbox Tower](the-sandbox-tower)** — the theory this post builds on. Read that first for the altitude framing and the delegation-becomes-contractual argument.
- **[The Integration Layer Plan](integration-layer-plan)** — the implementation plan this post reshapes. The plan's "unified context" substrate is now concretely umwelt + the view bank, and the phased build-out references umwelt specs instead of hypothetical in-lackpy modules.
- **[An LLM Is a Subject of Your Policy](an-llm-is-a-subject-of-your-policy)** — the positioning companion. Situates umwelt in the Datalog-for-policy lineage (OPA, Cedar, Oso), names what's genuinely novel, and makes the agent-as-subject-alongside-others reframe explicit.

---

*This post is a draft captured at the moment of maximum design clarity, before any umwelt code exists. The reader-unfriendly thing about drafts written at this moment is that they describe architecture that hasn't been tested. The reader-friendly thing is that the decisions are fresh and the reasoning is legible. Promote to the main blog only after the v0.1 walking skeleton runs end-to-end on a real task — not before.*
