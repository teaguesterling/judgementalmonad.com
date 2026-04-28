# The Pair

*YAML declares the world. CSS governs it. Neither format is safe alone — YAML is permissive about what you can say, CSS is permissive about what it ignores. But the architecture they serve makes those properties load-bearing: restrictive defaults in the vocabulary, the capability model in the world file, and format-enforced separation between declaration and policy. The safety comes from the design. The formats are the right vehicles for it.*

---

## The architecture needs specific format properties

The three-layer architecture (vocabulary / world state / policy) requires:

1. **World declaration** needs a format that is human-readable at scale, structurally deep enough for heterogeneous entities, tolerant of keys that not all consumers understand, and incapable of expressing conditional logic.
2. **Policy** needs a format where unknown constructs default to restriction (not error, not pass-through), conflict resolution is built in, and the subjects of the policy can read it without special training.
3. **The boundary** between them must be enforced by the formats themselves — not by linting, not by discipline, not by convention.

YAML and CSS aren't chosen because their "weaknesses are actually strengths." They're chosen because their specific properties align with these requirements. The safety comes from the architecture. The formats are the vehicles.

### Why YAML for world declaration

**Readability as audit requirement.** A world file is a security artifact. Humans need to read it, diff it, review it in PRs. A 200-entity world file in JSON is nearly unreadable — braces, commas, mandatory quoting. In YAML it's manageable. For an artifact that determines what an agent can see and do, readability isn't a convenience — it's a security property.

**Structural depth for heterogeneous worlds.** The world declares files, tools, network endpoints, modes, principals, and entity types that vocabulary plugins define. Nested structures, lists, maps, multi-line strings. JSON handles this with boilerplate; TOML runs out of structural depth; YAML scales gracefully. The data model — nested maps and lists — provides what world files need.

**Unknown-key tolerance for forward compatibility.** A world file parsed by umwelt v1 may contain keys that umwelt v2 understands. A world file consumed by nsjail's compiler may contain keys only lackpy's compiler reads. Unknown keys aren't errors — they're entries for consumers that aren't in the room yet. This is the same property that let HTML evolve without breaking old browsers: unknown tags are ignored, not rejected.

This tolerance is safe *only because entities don't carry implicit permissions*. An entity existing in the world file is necessary but not sufficient for access — the CSS policy layer must explicitly grant. Unknown YAML keys are safe because the capability model makes existence orthogonal to permission. Without that architectural guarantee, unknown keys would be a confused-deputy risk.

**No conditionals enforces the separation.** YAML can't express `if` or `when`. For configuration files this is a limitation. For the three-layer architecture, it's the enforcement mechanism: policy logic *cannot leak into the world declaration* because the format can't express it. This is format-level enforcement, not convention — stronger than a linting rule, which can be disabled.

The enforcement is real but not absolute. People add templating layers on top of YAML (Helm, Ansible, Kustomize). The world file spec's own `vars:` and `include:` mechanisms create composition points. The format prevents inline conditionals; it doesn't prevent a preprocessing step from generating conditional world files. The linter's job is to catch that gap — flag world files that appear to be templated output rather than authored declarations.

**Safe subset, not full YAML.** YAML's expressiveness includes features that are genuinely dangerous: implicit type coercion (`no` → `false`, the Norway problem), arbitrary object instantiation in unsafe parsers, billion-laughs via recursive anchors. umwelt uses a safe YAML subset — `yaml.safe_load` or equivalent. "Expressiveness" here means the data model (nested maps and lists with readable syntax), not the full YAML feature set with its footguns.

### Why CSS for policy

**Ignore-unknown preserves restrictive defaults.** CSS silently skips properties and selectors it doesn't recognize. In web CSS, this means forward-compatibility: old browsers skip new properties. In policy CSS, this means unrecognized constructs don't weaken the policy.

But CSS's ignore-unknown behavior is *neutral*, not inherently restrictive. In web CSS, `display` defaults to `inline`, not `none`. `visibility` defaults to `visible`, not `hidden`. Web CSS defaults are "render something reasonable," not "restrict everything." The restrict-by-default property comes from *umwelt's vocabulary design* — every `@property` at-rule declares a restrictive `initial-value`. CSS's ignore-unknown behavior *preserves* those restrictive defaults; it doesn't *create* them.

This is a critical distinction. The safety property is: **vocabulary defines restrictive initial values** + **CSS preserves them by ignoring what it doesn't understand** + **the capability model ensures missing entities can't be addressed**. Three mechanisms, not one. The post's argument is that the formats are the right *vehicles* for these mechanisms — not that the formats' "weaknesses" are the mechanisms themselves.

A format that errored on unknown input would be *fragile* — breaking forward compatibility. A format that passed unknown input through *permissively* would be *dangerous* — unknown grants could widen the policy. CSS's specific behavior — ignore and fall back to defaults — is the match for a vocabulary with restrictive defaults. It's the right tool for the job, not a happy accident.

**The cascade composes policy layers.** Multiple rules targeting the same entity don't produce an error — specificity picks the winner. This enables layered composition: base policy + project overlay + task refinement + mode override. Each layer adds rules. The cascade composes them. In Rego, overlapping rules that disagree produce a conflict error. In CSS, they compose.

**Specificity as conflict resolution — axis count first.** umwelt extends CSS3 specificity with an axis-count-first model: a rule joining more authorization axes is more specific than a rule naming fewer axes, regardless of within-axis CSS3 counts. `mode#review file { editable: false }` (axis count 2: state + world) overrides `file[path^="src/"] { editable: true }` (axis count 1: world only) because it qualifies more axes. This matches the VSM-lattice view: a rule scoped to more regulatory concerns is more contextualized, so it should win.

Within each axis, standard CSS3 specificity applies: IDs beat classes beat types. So the full specificity is a tuple: `(axis_count, principal_weight, world_weight, state_weight, actor_weight, capability_weight, audit_weight)`. Axis count dominates; within-axis weight breaks ties.

The naming convention matters. Modes are named instances — there's one "review" mode, not a category of review-like things. They're IDs (`mode#review`), not classes (`mode.review`), for the same reason tools are IDs (`tool#Edit`) and principals are IDs (`principal#Teague`). Classes still exist for *categories* modes belong to: `mode#review.read-only`, `mode#implement.destructive`. Classes describe what a mode is like; IDs name which mode it is. ID selectors contribute `id * 10,000` to the axis weight, ensuring mode-qualified rules dominate within their axis.

The axis-count-first model makes the specificity order match the security order: a mode-level lockdown (2 axes) naturally defeats a per-file grant (1 axis). A principal + mode + tool + resource rule (4 axes) defeats all of the above. More qualification = more specific = wins. CSS also provides `!important` and cascade layers (`@layer`) as escape hatches when the axis-count order is wrong for a specific case. The [cross-format linter](https://github.com/teaguesterling/umwelt/blob/main/docs/vision/linter.md) flags cases where a restrictive rule is defeated by a more-specific permissive grant, using directional metadata on properties to detect widening mechanically.

**Both halves readable by all parties.** The agent can read its own world file (YAML) and its own policy (CSS) without fine-tuning or special tooling. The auditor can read both without executing either. The human author can read both without learning a custom DSL. No other format pairing achieves this three-way legibility. Post 2 develops the training-data-saturation argument for CSS; the pairing argument adds that YAML is equally legible to models and humans.

### The pairing: what makes it safe

The web platform demonstrated that separating structure from presentation into two permissive-but-complementary formats enables graceful evolution. umwelt applies the same separation to world state and policy — but the security implications are different.

| Layer | Permissiveness | Unknown handled as | Safety depends on |
|---|---|---|---|
| YAML world file | Unknown keys pass through | Not consumed by this tool | Capability model (existence ≠ permission) |
| CSS policy | Unknown properties/selectors ignored | Default value applies | Vocabulary (restrictive initial values) |
| Format boundary | YAML can't express conditionals | N/A | Format-level separation (not convention) |

The safety envelope is closed *within the umwelt compilation pipeline*: world file → materialize → entities → compile with policy → database. Every step preserves the restrict-by-default invariant. But consumers that read the YAML directly, bypassing the pipeline, are *outside* the envelope. A downstream tool that interprets unknown world-file entities as resources to expose would violate the capability model. The linter catches this at the boundary: it validates world files against the registered vocabulary and flags entities that no consumer handles.

The pairing means:
- **Unknown entity types** in the world file are visible to consumers that understand them, invisible to consumers that don't. Safe because the capability model requires explicit policy grants.
- **Unknown entity types** in CSS selectors match nothing. The entity gets the restrictive default from the vocabulary. Safe because vocabulary defaults are restrictive.
- **Unknown properties** in CSS declarations are skipped. The entity retains its restrictive initial value. Safe for the same reason.
- **Missing entities** in the world file mean the entity doesn't exist. No selector can match it. No CSS rule can grant access to something that isn't in the world. This is the capability model: no holding, no doing.

### The linter: catching what the formats can't

The format-level safety properties are real but not complete. They need a linter that operates across both formats simultaneously — comparing the world file and the policy *as a pair*. The linter's job is not to replace format-level enforcement; it's to catch the cases the formats can't: specificity conflicts, coverage gaps, vocabulary violations, and permissive drift.

#### Prerequisite: directional properties

The linter's most important capability — detecting specificity conflicts that weaken security — requires one vocabulary extension: **directional metadata on properties.** Each `@property` declaration must indicate which direction is restrictive:

```css
@property editable {
  syntax: "<boolean>";
  initial-value: false;
  restrictive-direction: false;  /* false is more restrictive */
}

@property max-output-tokens {
  syntax: "<integer>";
  initial-value: 0;
  restrictive-direction: min;    /* lower is more restrictive */
}

@property allowed-hosts {
  syntax: "<list>";
  initial-value: [];
  restrictive-direction: subset; /* fewer is more restrictive */
}
```

Three directionality kinds cover the property types: `boolean` (one value is restrictive), `min`/`max` (numeric ordering), `subset`/`superset` (set containment). Given this metadata, the linter can mechanically determine whether one property value is "more permissive" than another.

Without directionality metadata, the linter can still detect *structural* conflicts (a rule with fewer axis qualifiers defeated by one with more) but can't distinguish intentional overrides from accidental security weakening.

#### World-file checks

**Unknown entities.** Flag entities whose type no registered vocabulary plugin handles. These pass through YAML safely (unknown-key tolerance) but sit outside the policy pipeline — no CSS rule can meaningfully govern what no vocabulary defines. Not necessarily an error (could be a future consumer), but the linter should report them as ungoverned.

**Safe-subset violations.** Flag YAML features outside the safe parsing subset: anchors creating circular references, non-string keys, tags that trigger type coercion (`!!python/object`, `!!binary`), values that hit the Norway problem (`no`, `on`, `off` parsed as booleans). These are parse-level risks that `yaml.safe_load` handles but that authoring can still produce accidentally.

**Templating artifacts.** Flag world files that appear to be templated output rather than authored declarations: Jinja2 `{{ }}` markers, Helm `{{ .Values }}` references, shell variable `${VAR}` interpolation. The format-level "no conditionals" guarantee holds for raw YAML but breaks if a preprocessing step generates it. The linter catches the gap.

**Duplicate entity IDs.** Within a type, IDs must be unique — `tool#Edit` can appear once. Across types, the same ID is fine (`file#auth.py` and `tool#auth` are different entities). Flag duplicates within type.

**Empty discovery.** Flag `discover:` patterns that resolve to zero entities at materialization time. Not necessarily wrong (the directory might be empty), but worth reporting — a world file that discovers nothing may be misconfigured.

**Include cycles.** Flag `include:` chains that form cycles. YAML's anchor/alias mechanism doesn't catch this because includes are semantic, not syntactic.

#### Policy-file checks

**Dead selectors.** Flag CSS selectors that match no entity in the current world file. Either the world file is incomplete or the rule is stale. Dead selectors aren't a security risk (they're inert), but they're a maintenance risk — someone wrote a rule expecting it to apply, and it doesn't.

**Unknown types and properties.** Flag entity types in selectors that no vocabulary plugin defines. Flag property names in declarations that no vocabulary declares. These are CSS's "ignore unknown" in action — which is safe, but the linter should report them because they may indicate typos or version mismatches.

**Vocabulary invariant violation.** Flag `@property` declarations that lack `initial-value` or whose initial value is not the restrictive direction. The restrict-by-default invariant depends on every property defaulting to its restrictive value. A property whose initial value is permissive breaks the invariant. This is the linter's most important vocabulary check.

**`!important` audit.** Flag every `!important` declaration. In web CSS, `!important` is a maintenance smell. In policy CSS, it's an escape hatch — legitimate when a security rule must override all specificity. The linter reports them as an audit surface: each `!important` should be intentional, documented, and reviewed.

**Redundant rules.** Flag rules that are completely shadowed — every entity they match is also matched by a higher-specificity rule that sets the same property. These are dead weight that makes the policy harder to read without affecting behavior.

#### Specificity and cascade checks

These are the linter's core security contribution. They operate over the *computed* cascade — all rules resolved against all entities.

**Permissive override detection.** For each entity × property pair, compute the cascade winner. If the winner is more permissive than a lower-specificity rule that also matches, flag it. This is the mechanical version of "does a narrow grant defeat a broad lockdown?"

Example: `mode#review file { editable: false }` (specificity 1,0,2) matches `file#auth.py`. But `principal#Teague mode#implement file#auth.py tool#Edit { editable: true }` (specificity 3,0,4) also matches and wins. The linter flags: "permissive override — `editable: true` at (3,0,4) defeats restrictive `editable: false` at (1,0,2) for entity `file#auth.py`." The human reviews and decides: is this override intentional?

**Shadowed restrictive rules.** Flag restrictive rules that *never win* for any entity in the current world file. These are rules someone wrote expecting them to enforce a constraint, but they're always overridden. Different from dead selectors (which match nothing) — these match entities but always lose the cascade.

**Permissive drift detection.** Compare effective policy against a baseline (previous materialization, or the vocabulary's initial values). Report entities whose effective policy became more permissive. This catches gradual weakening across policy edits — no single edit looks dangerous, but the cumulative effect widens the policy.

**Axis-coverage gaps.** For each entity, report which authorization axes (S0-S5) the winning rule qualifies. A rule that wins with `file#auth.py { editable: true }` qualifies only the resource axis (S0). A rule that wins with `principal#Teague mode#implement tool#Edit file#auth.py { editable: true }` qualifies four axes. The linter can report the "axis depth" of each effective permission — shallow grants (few axes) are more worth reviewing than deep ones (many axes).

**Fixed-constraint conflicts.** Flag CSS rules that set a property to a value that the world file's `fixed:` block overrides. These rules are inert — fixed constraints clamp after cascade resolution — but they indicate confusion about what the policy controls vs what the environment enforces.

#### Cross-format checks

**Coverage.** Report entities in the world file that no CSS rule targets for any property. These entities exist in the agent's world but have no explicit policy — they get vocabulary defaults. That's safe (defaults are restrictive) but may indicate an incomplete policy.

**Consistency.** Verify that every entity type referenced in CSS selectors exists in either the world file or the vocabulary. A selector for `container#docker` when neither the world file nor any vocabulary defines `container` is either a typo or a missing vocabulary plugin.

**Effective policy report.** The linter's most useful output: for each entity, report the effective value of every property after cascade resolution, with provenance — which rule set the value, at what specificity, and whether any lower-specificity restrictive rule was overridden. This is the audit view that answers "what can this agent actually do?" It's the materialized policy, human-readable, diffable across sessions.

#### What's mechanically detectable vs what needs human judgment

| Check | Mechanical? | Why / why not |
|---|---|---|
| Dead selectors | Yes | Compare selectors against world entities |
| Unknown types/properties | Yes | Compare against vocabulary |
| Permissive overrides | Yes, given directional metadata | Compare cascade winner against lower-specificity matches |
| Shadowed restrictive rules | Yes | Compute which rules never win |
| Permissive drift | Yes, given baseline | Diff effective policy against prior materialization |
| Intentional vs accidental override | No | Linter flags; human decides |
| Whether a permissive grant is appropriate | No | Context-dependent — the linter reports, the reviewer judges |
| Vocabulary completeness | Partial | Can flag missing properties but can't know what *should* exist |

The linter's role is to make the security-relevant cascade decisions *visible* — not to decide whether they're correct. It turns implicit specificity outcomes into explicit, reviewable audit entries. The human reviews. The ratchet tightens.

The linter doesn't replace the format-level safety. Format enforcement is the first line (YAML can't express conditionals, CSS ignores unknown). The vocabulary is the second line (restrictive defaults). The linter is the third line — defense in depth, catching what the first two miss.

### The contrast: monolithic approaches

**Terraform HCL** mixes world declaration with conditionals, loops, and dynamic blocks. The world file becomes a program. Policy logic leaks into resource declaration. Linting and auditing require executing the code.

**OPA/Rego** separates input documents from policy rules — `input` is JSON, rules query it. The separation exists but isn't format-enforced: Rego can access `input` and `data` in the same evaluation context, and nothing prevents policy rules from constructing world state or world files from embedding policy hints. umwelt's format boundary prevents this structurally.

**Ansible YAML** adds `when:` clauses, Jinja2 templates, and loops to YAML. The format gains computational power and loses the guarantee that the file is a pure declaration. You can't audit an Ansible playbook without executing it.

**Nix** takes the opposite extreme: a purely functional language where the world file is a derivation. The purity guarantee is strong and the content-addressing is sound, but the format requires learning a full programming language. The security story is excellent; the adoption cost is prohibitive for the "every agent should have a policy" goal.

umwelt's pairing is a deliberate middle ground. YAML stays declarative (no conditionals). CSS stays cascading (no imperative logic). The format boundary enforces what discipline can't. The linter catches what the formats can't.

### The "schema" lives in the vocabulary, not the format

Neither YAML nor CSS has a built-in schema system. In umwelt, schemas are declared in the vocabulary layer via `@entity`, `@attribute`, and `@property` at-rules — CSS syntax for schema declarations (following the Houdini `@property` precedent). The world file is validated against the vocabulary at materialization time, not at parse time.

This means the format never rejects a structurally valid file. Validation is deferred to the layer that knows what's valid — the vocabulary. The world file is a *document*, not a *program*. It can be stored, diffed, versioned, and transmitted without any tool understanding its contents. Any tool that does understand can validate and consume its slice.

### What this enables

1. **Forward-compatible world files.** A world file authored for umwelt v1 works with v2. New entity types and attributes are simply consumed by new vocabulary plugins.
2. **Multi-consumer world files.** nsjail, bwrap, lackpy, and kibitzer all read the same world file. Each reads the entities and attributes it understands. Unknown entries are invisible, not errors.
3. **Auditable separation.** An auditor can read the YAML world file and know what exists. They can read the CSS policy and know what's allowed. The two artifacts are independent, composable, and each is readable without executing the other.
4. **Three-way legibility.** Human, auditor, and agent can all read both formats without special tooling or training. The contract is legible to every party.
5. **Defense in depth.** Format-level separation prevents mixing. Vocabulary-level defaults prevent permissive gaps. The cross-format linter catches what the layers miss. No single mechanism carries the full safety argument.

## Key citations

- Van Deursen, Klint & Visser (2000), "Domain-Specific Languages: An Annotated Bibliography" (piggyback DSL design)
- CSS Houdini `@property` specification (W3C) (schema in CSS syntax, restrictive initial values)
- Dolstra (2006), "The Purely Functional Software Deployment Model" (the pure-functional extreme)
- HashiCorp, "Terraform Language Documentation" (the conditional-in-declaration extreme)
- Ben-Kiki, Evans & dot Net (2021), YAML 1.2 specification
- Dennis & Van Horn (1966), "Programming Semantics for Multiprogrammed Computations" (capability model)
- Miller (2006), "Robust Composition" (entities don't carry implicit permissions — constructive security)
- CSS Cascading and Inheritance Level 5 (W3C) (cascade layers, `!important`, specificity)

## Connection to adjacent posts

[Post 1 (The World as Capability)](01-world-as-capability) explains *what* the world file declares and *why* it's a capability grant. [Post 2 (CSS as Policy Syntax)](02-css-as-policy-syntax) explains *why* CSS and not Rego/Cedar/Polar. This post explains why the *pairing* works — why the architecture needs formats with these specific properties, and why a single format (or a more "rigorous" one) would be worse.

*Next: [The Datalog Underneath](04-the-datalog-underneath) — The formalism underneath the CSS surface. Views as Datalog programs. What we borrow and what we don't.*
