# Entities, Selectors, Cascade

*CSS selectors over non-DOM worlds. The entity model as queryable structured data — typed nodes in a graph, matched by selectors, with policy attached by cascade. What changes when the world is tools and files instead of divs and spans, and what stays exactly the same.*

---

## Prior art: CSS selectors outside the DOM

CSS selectors are a general-purpose tree query language. The DOM is only their most famous host. Other hosts have been running for years, at scale, without modification to the selector grammar:

**ESQuery** (estools) queries JavaScript ASTs with CSS selectors. `.CallExpression[callee.name="setTimeout"]` matches every call to setTimeout in a source file. ESLint's no-restricted-syntax rule exposes ESQuery directly — users write CSS selectors over AST nodes to define lint rules. ~58 million weekly npm downloads. The selectors are CSS. The nodes are AST types. The machinery is identical.

**TSQuery** does the same for TypeScript ASTs. `.ClassDeclaration > .PropertyDeclaration[accessibility="private"]` finds private properties in classes. Same selector grammar, different node types.

**JSONSelect** applied CSS selectors to JSON documents. `.object > .string.foo` matched string values under keys named "foo." The project is dormant but demonstrated that the selector/node model generalizes to arbitrary tree-structured data.

**Acquia Web Governance** uses CSS selectors as policy selectors in production — not for styling, but for governance rules applied to web content at enterprise scale.

The pattern across all of these: selectors work when data has typed nodes with named properties and parent-child relationships. That's a tree. CSS selectors are a tree query language that happens to have been invented for the DOM but isn't limited to it.

The entity model in umwelt is another instance of this pattern. The nodes are policy entities (files, tools, modes, resources). The properties are policy attributes (path, language, event, limit). The tree structure comes from entity containment and cross-taxon context. The selectors are CSS.

---

## The entity model

Every entity in umwelt has five dimensions, each mapping directly to a CSS selector mechanism:

| Dimension | CSS mechanism | Example |
|---|---|---|
| Type | Type selector | `file`, `tool`, `mode`, `hook` |
| ID | ID selector | `#auth.py`, `#Bash`, `#implement` |
| Classes | Class selector | `.dangerous`, `.security-critical`, `.tdd` |
| Attributes | Attribute selector | `[path^="src/"]`, `[language="python"]` |
| Containment | Descendant combinator | `dir file`, `mode tool` |

The first four are intra-entity — they describe properties of the entity itself. The fifth is inter-entity — it describes the relationship between entities. CSS handles both with the same grammar. So does umwelt.

Types come from the vocabulary — registered entity kinds like `file`, `tool`, `mode`, `hook`, `resource`, `network`. IDs are unique identifiers within a type: `file#/src/auth.py`, `tool#Bash`, `mode#implement`. Classes are non-unique categories: a mode can be `mode#implement.edit.test` — ID "implement" with classes "edit" and "test." Attributes are key-value pairs: `file[path^="src/"][language="python"]`.

This isn't an analogy. It's the same data model. An HTML element has a tag name (type), an id, classes, and attributes. A policy entity has the same four. The vocabulary declares what types exist and what attributes each type supports — this is the DTD to CSS's stylesheet. The world file populates concrete instances — this is the DOM. The policy selects and declares — this is the CSS.

---

## Cross-taxon compound selectors

Within a single taxonomy, the descendant combinator means structural containment: `dir file` matches files inside directories, just as `div p` matches paragraphs inside divs. The relationship is spatial — one thing is inside another.

Across taxonomies, the combinator means something different. `tool#Edit file[path^="src/"]` doesn't mean "file entities inside tool entities" in a spatial sense. It means "file entities in the context of the Edit tool" — a contextual qualifier. The tool provides the context; the file is the target. The permission attaches to the target within the qualifying context.

This is the novel construct. ESQuery doesn't cross AST types this way — an ImportDeclaration and a FunctionDeclaration live in the same tree. JSONSelect doesn't have multiple taxonomies. No CSS-over-non-DOM system has needed cross-taxon composition because they all operate within a single typed tree.

umwelt operates across multiple typed trees — the world tree (files, directories, networks), the capability tree (tools, kits), the state tree (modes, stances), the actor tree (principals, inferencers, harnesses). The descendant combinator bridges them:

```css
/* Single taxon: structural containment */
dir#src file { editable: true; }

/* Cross-taxon: contextual qualification */
tool#Edit file[path^="src/"] { editable: true; }

/* Multi-taxon: layered context */
principal#Teague mode#implement tool#Edit file[path^="src/"] { editable: true; }
```

The more taxa a selector crosses, the more specific it becomes. This is the axis-count-first specificity model: a rule qualifying four axes beats a rule qualifying three, regardless of the CSS3 specificity weight within each axis. The security intuition is direct — a more narrowly scoped rule should override a broader one.

---

## Cascade as policy composition

CSS cascade is defeasible conflict resolution. García and Simari (2004) formalized defeasible logic programming: rules can be defeated by more specific rules. CSS has been doing this since 1996. When multiple rules match the same element and set the same property, specificity picks the winner. The losing rules aren't wrong — they're defeated.

This makes the cascade a *composition* mechanism, not a priority mechanism. You don't declare "rule A has priority 3." You write rules at different levels of specificity and the cascade composes them:

```css
/* Layer 1: base policy — all files read-only */
file { editable: false; }

/* Layer 2: project policy — source files editable */
file[path^="src/"] { editable: true; }

/* Layer 3: task policy — auth files need approval */
file[path="src/core/auth.py"] { editable: true; requires-approval: true; }

/* Layer 4: mode-qualified — in review mode, nothing editable */
mode#review file { editable: false; }
```

Four rules, four specificity levels, zero explicit priority declarations. The base policy says "read-only." The project policy overrides for source files. The task policy refines for auth files. The mode-qualified policy wins when review mode is active because it crosses two taxa (mode + file) while the file-only rules cross one.

The composition is additive. Each layer builds on the previous without needing to know what the previous layers said. The base policy author doesn't coordinate with the task policy author. The cascade handles the composition. This is the same property that makes CSS stylesheets composable in web development — and it's the property that makes policy layers composable in authorization.

Nute showed that propositional defeasible logic has linear complexity. The cascade isn't expensive. It's O(n) in the number of applicable rules — evaluated once at materialization time, not at every policy decision.

---

## Comparison-semantics properties

Not all properties are simple values. Some carry built-in comparison semantics registered as vocabulary metadata:

```css
@property max-level {
  entity: resource;
  syntax: "<integer>";
  initial-value: 0;
  restrictive-direction: min;
}

@property allowed-kits {
  entity: tool;
  syntax: "<ident-list>";
  initial-value: none;
  restrictive-direction: subset;
}
```

`max-level: 2` doesn't set the level to 2 — it *caps* it. If a more general rule says `max-level: 5` and a more specific rule says `max-level: 2`, the effective value is 2 — the more restrictive wins. The `restrictive-direction: min` metadata tells the cascade how to resolve conflicts for this property.

`allowed-kits: python-dev, data-science` doesn't set the kit list — it *restricts* it. A more specific rule can only narrow the set, never widen it. `restrictive-direction: subset` encodes this.

Three comparison types cover the policy space:
- **Boolean** (`restrictive-direction: false` or `true`) — `false` is more restrictive for permissions, `true` for denials.
- **Numeric** (`min` or `max`) — lower caps or upper caps.
- **Set** (`subset` or `superset`) — restriction by narrowing or widening.

The cascade uses these semantics to detect widening. If a more specific rule would widen a property — allowing what a more general rule restricted — the linter flags it. The detection is mechanical, not heuristic. The vocabulary metadata makes it possible.

---

## Vocabulary-agnostic core

The selector/cascade machinery knows nothing about files, tools, or modes. It doesn't know what `editable` means or that `file` is a type. The core provides:

1. **Parsing** — CSS selectors and declaration blocks.
2. **Matching** — selector evaluation against an entity graph.
3. **Cascade** — specificity computation and conflict resolution.
4. **Compilation** — lowering resolved properties to consumer-specific formats.

Everything else — entity types, attributes, properties, comparison semantics — comes from the vocabulary. The sandbox vocabulary (`file`, `tool`, `mode`, `hook`, `resource`, `network`, `budget`) is a first-party plugin, not privileged code. It registers its types and properties through the same API any third-party consumer uses.

A CI/CD vocabulary could register `pipeline`, `stage`, `job`, `artifact` types with `timeout`, `retry-count`, `parallelism` properties. A data-governance vocabulary could register `dataset`, `column`, `query` types with `pii-level`, `retention-days`, `access-tier` properties. Each gets the full selector/cascade/compilation pipeline for free.

The vocabulary is the specialization. The grammar is the invariant. This is the "specialization lives in the language" principle from the [lackey series](../tools/lackey/03-the-specialization-lives-in-the-language), applied to the policy layer: the model already knows CSS syntax, so the only thing you teach it is the vocabulary — what the selectors match and what the properties mean.

---

## Key citations

- ESQuery: github.com/estools/esquery (~58M weekly npm downloads)
- TSQuery: github.com/phenomnomnominal/tsquery
- JSONSelect: github.com/lloyd/JSONSelect
- García & Simari (2004), "Defeasible Logic Programming"
- Nute, "Propositional Defeasible Logic has Linear Complexity"
- CSS Selectors Level 4 specification (W3C)
- Acquia Web Governance — CSS selectors as policy selectors in production

---

*Next: [The Seven Axes](06-the-seven-axes) — Why Cedar's three axes aren't enough. How Beer's Viable System Model derives seven, and what the S0/S2 deconvolution reveals about execution environment as an authorization dimension.*
