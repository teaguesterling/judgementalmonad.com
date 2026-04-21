# CSS as Policy Syntax

*Every prior policy language invented its own DSL. Rego. Cedar. Polar. XACML. Each cost its users cognitive load on day one. CSS costs nothing — because every LLM already reads it fluently, and so does every developer who ever styled a web page.*

---

## The dialect-design argument

When you design a domain-specific language, you face a tradeoff: expressiveness costs familiarity. A bespoke syntax can be perfectly tailored to your domain, but every user has to learn it from scratch. Van Deursen, Klint, and Visser (2000) call the alternative "piggyback DSL design" — borrowing grammar and tooling from a host language. The DSL gains parsing infrastructure, editor support, and user familiarity. The tradeoff flips: you accept the host grammar's constraints in exchange for zero learning cost.

For agent-facing policy, the tradeoff flips further. The subjects of the policy aren't just humans — they're LLMs. Model weights encode syntactic patterns from training data. CSS is, after HTML and JSON, the most over-represented structured language in the training corpora that every frontier model saw during pretraining. A 1.5B coder model produces `.class#Foo { property: value; }` without hesitation. A frontier model reasons about selector specificity, composition, and cascade interaction.

You aren't *teaching* agents CSS. They already know it. The specialization — what the selectors match, what the properties mean — lives in the vocabulary, not in the grammar. This is the move the [lackey series](../tools/lackey/03-the-specialization-lives-in-the-language) describes: borrow a grammar the model already knows and let the validator do the work the fine-tune would have done.

The consequence is larger than it sounds. CSS becomes a *coordination medium* between agents. Any model in the system can read, write, and reason about policy without specialized training or retrieval-augmented prompting. The outer agent can emit a view as plain text. The delegate can parse it. The human can inspect it in a text editor. The diff tool can compare two versions. No participant has to be taught what a view is — they all already know the syntax at both halves: the selector and the declaration block.

---

## Why not Rego, Cedar, or Polar?

Each is a well-designed language for its domain. OPA/Rego is CNCF-graduated, deployed at scale at Netflix and Pinterest. Cedar has Amazon's machine-checked soundness proofs. Oso's Polar does elegant principal/resource authorization with Prolog-derived syntax. They're real achievements.

None of them is readable by the subjects they govern:

| Language | Designed for | Agent familiarity | Human familiarity |
|---|---|---|---|
| Rego | Cloud-native infra policy | Low (custom DSL) | Low without training |
| Cedar | Service authorization | Low (custom DSL) | Medium (clean syntax) |
| Polar | Application auth | Low (Prolog-derived) | Low without Prolog |
| CSS | Styling (repurposed) | Very high | Very high |

This matters because agent policy has a property that service policy doesn't: the governed subject benefits from reading its own constraints. Ma post 8's [SELinux coda](../ma/08-the-specified-band) makes the argument: specified policy opaque to the governed actor wastes the actor's decision surface. The actor has to learn the rules empirically by probing and failing — each probe costs tokens, latency, and trust. Policy the actor can read is policy the actor can follow on the first try.

Rego is powerful but opaque to everything except its evaluator. Cedar is clean but unfamiliar. CSS is the language every agent already speaks. The UX bet is that the familiarity advantage dominates the expressiveness cost — and for the specific domain of entity matching with property assignment, the expressiveness cost is near zero, because that's what CSS already does.

---

## The semantic mismatch risk

Van Deursen et al. warn about the cost of piggyback design: the host grammar creates expectations about behavior. CSS syntax makes people think of web styling, not authorization. When they see `file { editable: false; }`, some part of their brain expects `font-size: 14px` to follow.

umwelt addresses this by staying close to CSS semantics — not just borrowing the syntax but preserving the mechanics:

- **Selectors match entities.** CSS selectors match DOM elements by type, ID, class, and attribute. umwelt selectors match policy entities by the same four dimensions. The matching rules are identical.
- **Declarations attach properties.** CSS declarations set visual properties on matched elements. umwelt declarations set policy properties on matched entities. The assignment mechanic is the same.
- **Cascade resolves conflicts.** When multiple CSS rules match the same element and set the same property, specificity picks the winner. umwelt's cascade works identically — with an axis-count extension for cross-taxon rules ([Post 3](03-the-pair) details the specificity model).
- **Unknown constructs degrade gracefully.** CSS skips properties and selectors it doesn't recognize. umwelt does the same, falling back to restrictive vocabulary defaults.

The domain is new. The mechanics aren't. This minimizes the semantic mismatch: CSS behavior in umwelt is CSS behavior, applied to a different set of entities. The surprises are in the vocabulary (what `editable` means), not in the language (how specificity works).

---

## CSS Houdini as precedent

CSS Houdini's `@property` rule declares type information within the stylesheet itself:

```css
@property --accent-color {
  syntax: "<color>";
  inherits: true;
  initial-value: blue;
}
```

This is CSS defining its own schema in its own syntax — what types exist, how they inherit, what their defaults are. It shipped in Chrome 85 and is a W3C standard.

umwelt follows the same pattern. Vocabulary declarations use CSS at-rules to register entity types, attributes, and properties:

```css
@entity file {
  taxon: world;
  parent: dir;
  attributes: path (str, required), name (str, required), language (str);
}

@property editable {
  entity: file;
  syntax: "<boolean>";
  initial-value: false;
  restrictive-direction: false;
}
```

The precedent matters because it establishes that CSS at-rules are the right place for schema declarations — not a separate schema language, not a JSON sidecar, not a Python registration API (though umwelt has that too, for programmatic consumers). Authors who know CSS at-rules already know how to read vocabulary declarations.

---

## Content Security Policy as precedent

CSP uses a rudimentary selector-like syntax for policy directives:

```
Content-Security-Policy: script-src 'self' https://cdn.example.com; default-src 'none'
```

`script-src` is a policy rule with source matching. `default-src` functions like a cascade default — it applies when no more specific directive exists. CSP proves that CSS-adjacent syntax works for security policy in production, deployed on billions of pages.

umwelt generalizes the same pattern: typed policy directives with specificity-based conflict resolution. CSP has a flat directive model. umwelt has a full selector/cascade model. But the lineage is visible — both use declarative rules that match subjects and set permissions, with a default-deny baseline.

---

## The two forms

umwelt views have two equivalent surface syntaxes. The entity-selector form is canonical — it generalizes to any registered taxon. The at-rule sugar form is familiar to anyone who's written sandbox configs:

```css
/* Entity-selector form (canonical) */
file[path^="src/auth/"] { editable: true; }
tool#Bash { allow: false; }
hook[event="after-change"] { run: "pytest tests/test_auth.py"; }
resource[kind="memory"] { limit: 512MB; }
network { deny: "*"; }

/* At-rule sugar (equivalent) */
@source("src/auth/**/*.py") { * { editable: true; } }
@tools { deny: Bash; }
@after-change { test: pytest tests/test_auth.py; }
@budget { memory: 512MB; }
@network { deny: *; }
```

Both compile to the same parsed AST. Authors pick whichever form is clearer for the task. The at-rule form is shorter for simple sandbox views. The entity-selector form scales to complex multi-axis policies:

```css
principal#Teague mode#implement tool#Edit use[of="file#/src/auth.py"] {
  editable: true;
}
```

Four axes, one rule, one descendant combinator repeated. No at-rule sugar would make this shorter — and at this level of specificity, the entity-selector form reads naturally as a sentence: "Teague's delegate, in implement mode, via Edit, use of auth.py — editable."

The at-rule sugar is a desugar step, not a separate language. New consumers register vocabulary through the plugin API. The desugar layer is itself a plugin. The core parser knows only entity selectors and declarations.

---

## What the subjects can read

The delegate-context compiler renders views as prompt fragments the governed actor can read:

```
Your workspace contains:
  - 12 Python files under src/ (editable)
  - 3 test files under tests/ (read-only)
  - Tools: Read, Edit (allowed), Bash (denied)
  - Memory limit: 512MB, wall time: 60s
  - After any file change: pytest runs automatically
```

This is generated from the same policy that the enforcement compilers read. The property metadata — descriptions, types, ranges — is attached to every registered property by the vocabulary plugin. Good descriptions produce helpful projections. Sparse descriptions produce useless ones. Plugin authors who care about their users write good descriptions.

This is Beer's "variety amplifier" applied to the policy layer. The governed actor's decision surface improves when it can read its own constraints rather than discovering them empirically. A model that knows "Bash is denied" before trying it avoids the wasted tool call, the error handling, the retry. A model that knows "memory limit is 512MB" can size its operations accordingly. Transparency isn't just an audit convenience — it's an efficiency mechanism.

---

## The expressiveness question

The obvious objection: CSS can't express everything Rego can. No `for` loops, no function definitions, no arbitrary computation. Rego is Turing-complete (modulo termination guarantees). CSS is declarative.

This is the point, not the objection. Policy that requires computation to evaluate is policy that requires computation to *understand*. Rego rules that chain through helper functions and comprehensions are powerful and sometimes necessary — and they're opaque to anyone who hasn't traced the evaluation. CSS rules are flat. Each rule says "this selector matches these entities, this declaration sets these properties." You can read them in any order. You can evaluate them in your head.

For agent authorization, the evaluation complexity lives in the *cascade*, not in the *rules*. Individual rules are trivially readable. The cascade — which rule wins when multiple rules match — requires understanding specificity, which is nonobvious but small (one algorithm, well-documented, unchanged since CSS2). The linter makes the cascade visible by computing the effective policy for each entity and flagging surprises.

The things CSS can't express — arbitrary computation, recursive queries, aggregation over entity sets — are things that don't belong in the policy layer. They belong either in the world file (which is data, not rules) or in the compilation pipeline (which is code, not policy). The restriction is structural discipline, not a limitation.

---

## Key citations

- Van Deursen, Klint & Visser (2000), "Domain-Specific Languages: An Annotated Bibliography"
- Fowler, *Domain-Specific Languages* (2010) (internal/external DSL distinction)
- CSS Houdini `@property` specification (W3C)
- Content Security Policy Level 3 (W3C)
- ESQuery (estools) — CSS selectors over JS ASTs, ~58M weekly npm downloads
- TSQuery — CSS selectors over TypeScript ASTs
- Acquia Web Governance — CSS selectors as policy selectors in production
- CSS Selectors Level 4 specification (W3C)

---

*Next: [The Pair](03-the-pair) — Why YAML and CSS together. What each format's properties contribute to the safety envelope, and what the cross-format linter catches.*
