# Materialization and Audit

*The world snapshot as security artifact. The compilation pipeline. The ratchet as specified ILP. How you answer "what could this agent see and do?" with a concrete, diffable, replayable proof.*

---

## Materialization: recipe to snapshot

A world file is a recipe. It names what to scan, what to include, what to declare. Materialization executes the recipe — runs discovery, applies overrides, flattens includes, resolves variables — and produces a concrete inventory. The snapshot answers "what could the delegate see?" deterministically, reproducibly, and with provenance.

The precedent chain:

**Docker inspect / docker history.** A Dockerfile is a recipe. `docker build` materializes it. `docker inspect` shows the result — every layer, every file, every environment variable. The materialized image is the artifact; the Dockerfile is the recipe that produced it.

**Terraform state.** A `.tf` file declares infrastructure. `terraform plan` previews what will exist. `terraform apply` materializes it. The state file records what exists, with drift detection to flag discrepancies between the recipe and reality.

**Nix store paths.** A Nix derivation is a pure function from inputs to outputs. The store path is content-addressed — the derivation *determines* the artifact. Two evaluations of the same derivation produce the same store path. Reproducibility is structural, not aspirational.

**SBOM (SPDX, CycloneDX).** Software Bills of Materials formalize what a build contains. The SBOM is a materialized view of the dependency graph — every component, every version, every license. Supply-chain audit at scale.

umwelt materialization follows the same pattern. The world file is the recipe. `umwelt materialize` executes it and produces a snapshot: every entity in the world, with provenance tracking for how it entered. Explicit entities are marked `provenance: explicit`. Discovered entities are marked `provenance: discovered` with the matcher that found them. Included entities carry `provenance: included` with the source world file. The provenance isn't policy — it's metadata. It tells auditors *how* each entity entered the world, which informs trust decisions.

---

## The compilation pipeline

```
world.yml → materialize → entities → compile with policy.umw → policy.db
```

The SQLite database is the compiled artifact. World state as tables. Policy rules as cascade candidates. Resolution as views. The database is self-contained — everything needed to answer "what can this delegate do?" lives in one file.

The schema:

```sql
-- World state
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    taxon TEXT,
    type TEXT,
    entity_id TEXT,
    classes JSON,
    attributes JSON,
    provenance TEXT,
    parent_id INTEGER
);

-- Policy rules (cascade candidates)
CREATE TABLE cascade_candidates (
    rule_id INTEGER PRIMARY KEY,
    selector TEXT,
    property TEXT,
    value TEXT,
    specificity JSON,
    source_file TEXT,
    source_line INTEGER
);

-- Resolution (what won)
CREATE VIEW effective_properties AS
SELECT entity_id, property, value, winning_rule_id
FROM ...  -- cascade resolution by specificity
```

Each consumer reads its own SQL view. The nsjail compiler queries for mount points, bind mounts, and seccomp rules. The bwrap compiler queries for the same information differently encoded. The kibitzer queries for observation-feed configuration. The lackpy compiler queries for allowed syntax constructs. Same database, different queries. "Compilers become queries" made concrete.

This is the key architectural insight: the compilation pipeline doesn't produce per-consumer artifacts from a shared intermediate representation. It produces a *queryable database* that every consumer reads with plain SQL. No umwelt-specific tooling required. Any program that can open a SQLite file can read its policy slice. The lingua franca is SQL over a well-defined schema.

---

## Fixed constraints as post-cascade clamping

Fixed constraints from the world file apply after cascade resolution. The cascade does its work — specificity picks winners, declarations resolve — and then the fixed constraints clamp:

```yaml
fixed:
  "tool#Bash":
    available: false
  "resource#memory":
    limit: 512MB
```

Policy says `tool#Bash { available: true; }`. The cascade resolves to `true`. The fixed constraint clamps it back to `false`. The `effective_properties` view combines both:

```sql
CREATE VIEW effective_properties AS
SELECT
    e.entity_id,
    cc.property,
    COALESCE(fc.value, cc.value) AS effective_value,
    CASE WHEN fc.value IS NOT NULL THEN 'fixed' ELSE 'cascade' END AS source
FROM entities e
JOIN cascade_resolved cc ON e.id = cc.entity_id
LEFT JOIN fixed_constraints fc ON e.id = fc.entity_id AND cc.property = fc.property;
```

Fixed constraints are physics, not rules. The screen is 1920px wide regardless of what the stylesheet says. The memory limit is 512MB regardless of what the policy says. The distinction matters for audit: when a consumer asks "why is Bash unavailable?" the answer isn't "because rule R₁ said so" — it's "because the world file fixed it as unavailable, and fixed constraints override cascade resolution."

---

## Detail levels

Not every consumer needs the full materialized world. Three detail levels serve different audiences and use cases:

| Level | Contents | Use case |
|---|---|---|
| Summary | Entity counts, projection boundaries, axis values | Quick audit, CI gate checks |
| Outline | Types + IDs + classes, directory trees, tool lists | Session recovery, diff review |
| Full | Every entity, all attributes, all provenance | SQL compilation, deep audit, forensics |

A summary materialization answers "how many files can this delegate see? Which tools does it have? What mode is it in?" in a few lines. A CI gate can check that the delegate has no more than N tools or that no entity outside `src/` is editable.

An outline materialization answers "what specifically can the delegate see?" with enough detail for a human reviewer to assess the delegation. It's the level you'd include in a PR description: "This delegation grants Read and Edit on 47 Python files under src/, in implement mode."

A full materialization is the S3* artifact — Beer's cross-cutting observer, the audit record that sits outside the system it observes. It's the answer to "reconstruct exactly what this delegate could see and do." Diffable between sessions. Replayable. Version-controllable. Two full materializations from different sessions produce a diff that shows exactly what changed in the delegate's reality.

---

## Proof trees as the audit artifact

Datalog evaluation produces proof trees as a byproduct of SLD resolution. Every derived fact traces back through the rules that derived it to the base facts that grounded it. For policy, this means every authorization decision has a proof:

```
Q: Why could the delegate edit /src/auth.py?

A: permission(file#/src/auth.py, editable, true)
   ← rule R₁: mode#implement file[path^="src/"] { editable: true; }
     ← matched: mode#implement (entity 42, provenance: explicit)
     ← matched: file#/src/auth.py (entity 17, provenance: discovered, matcher: filesystem)
     ← specificity: R₁ (2 axes, [0,1,0], [0,0,1]) > R₀ (1 axis, [0,0,0])
   ← defeated: R₀: file { editable: false; } (less specific)
```

The proof tree answers three questions simultaneously:
1. **What was the decision?** `editable: true` for `/src/auth.py`.
2. **Which rule produced it?** R₁, with its selector and source location.
3. **Why did that rule win?** Higher specificity than R₀ — two axes versus one.

Lampson argued for this in "Computer Security in the Real World" (1999): audit requires traceable decisions. The proof tree isn't an add-on logging feature. It's a structural byproduct of how the system evaluates policy. You get it for free because the logic is Datalog and Datalog evaluation *is* proof construction.

In the compiled database, proof trees are queries:

```sql
-- What rules matched this entity for this property?
SELECT * FROM cascade_candidates
WHERE entity_id = 17 AND property = 'editable'
ORDER BY specificity DESC;

-- What's the effective value and which rule won?
SELECT * FROM effective_properties
WHERE entity_id = 17 AND property = 'editable';

-- Was a fixed constraint involved?
SELECT * FROM fixed_constraints
WHERE entity_id = 17 AND property = 'editable';
```

The audit compiler is just another consumer. It reads the same database as nsjail, bwrap, kibitzer, and lackpy. Its queries happen to ask "why?" instead of "what?" — but the data is the same.

---

## The ratchet as specified ILP

Inductive Logic Programming (Muggleton 1991) learns logic programs from examples. Given positive examples (things the agent did that were fine) and negative examples (things the agent tried that failed or shouldn't have happened), induce a Datalog program that covers the positives and excludes the negatives.

The [configuration ratchet](../ma/the-configuration-ratchet) has been doing this the whole time:

1. **Observe.** The agent runs. blq captures tool calls. ratchet-detect captures file access patterns. strace captures system calls. The observations are structured — not free-text logs but typed events with entity references.

2. **Propose.** The ratchet analyzes observations against the current policy and proposes a tighter view. "The delegate used Read and Edit but never Bash. The delegate accessed files under src/ but never under tests/. Proposed: remove Bash, narrow filesystem scope to src/."

3. **Review.** A human reads the proposed view. The diff is a CSS diff — before and after. The human can see exactly what tightened and decide whether it's correct.

4. **Commit.** The tightened view becomes the new policy. The ratchet turned.

The "specified" qualifier means: no trained component in the mining pipeline. No neural network. No gradient descent. Just structural pattern matching over observation traces — set intersection for tool lists, range containment for file paths, SQL aggregation for resource limits. Classical pre-neural ILP (Progol, Aleph) is in principle sufficient for this. The ratchet reinvented a lineage it didn't know it was in.

Each ratchet turn is monotonically tightening. The proposed view is strictly narrower than the current view — fewer tools, fewer files, tighter limits. Widening requires explicit human approval. This monotonicity matches Datalog's: new facts derive new conclusions but never retract old ones. The ratchet's output is pasteable into a view because both speak the same logic.

---

## Diffing materialized worlds

Two materializations produce a diff:

```
Session A (2026-04-15):
  tools: {Read, Edit, Bash}
  files: 847 (src/**, tests/**, docs/**)
  mode: implement
  memory: 1024MB

Session B (2026-04-18):
  tools: {Read, Edit}
  files: 412 (src/**)
  mode: implement
  memory: 512MB

Diff:
  - Removed: tool#Bash
  - Removed: 435 files (tests/**, docs/**)
  - Changed: resource#memory limit 1024MB → 512MB
  - Unchanged: mode#implement, tool#Read, tool#Edit
```

The diff is the audit trail. "What changed between delegations?" has a concrete, reviewable answer. The ratchet turned: Bash removed, scope narrowed to src/, memory halved. Each change is traceable to either a ratchet proposal or a manual edit. The provenance chain runs from the diff back through the ratchet observation to the specific agent behavior that prompted the change.

Version-controlling materialized worlds gives you a *history of delegation* — not just what the current policy is, but how it evolved. Which sessions prompted tightening. Which tools were removed and when. Whether the delegation has been monotonically narrowing (healthy) or oscillating (suspicious). The history is data, not narrative.

---

## Closing the loop

The series opened with [The Missing Layer](00-the-missing-layer) — the observation that agent security has tools at every altitude except the policy layer. It ends here, with the policy layer's audit story: how materialization, proof trees, and the ratchet close the loop between declared policy and observed behavior.

The loop:

```
declare (world file + policy)
  → materialize (snapshot)
  → delegate (agent runs)
  → observe (blq, ratchet-detect, strace)
  → propose (ratchet)
  → review (human)
  → tighten (commit new policy)
  → declare ...
```

Each iteration is concrete: YAML and CSS in, SQLite out, observations in, tighter YAML and CSS out. Each step is auditable: the world file is version-controlled, the materialization is diffable, the observations are structured, the ratchet proposals are reviewable diffs, the commits have authors. No step requires trust in a black box.

The policy layer isn't a replacement for the tools — nsjail, bwrap, seccomp, Capsicum. It's the layer that *declares what those tools should enforce*, in a language that the governed subjects can read, the operators can author, the auditors can trace, and the ratchet can tighten. Forty years of formalism. Thirty years of CSS. One compilation pipeline. The code is at [umwelt](https://github.com/teague/umwelt).

---

## Key citations

- Dolstra (2006), "The Purely Functional Software Deployment Model"
- Terraform documentation: "State" and "Plan"
- Muggleton (1991), "Inductive Logic Programming"
- Lampson (1999), "Computer Security in the Real World"
- Appel & Felten (1999), "Proof-Carrying Authentication"
- Becker & Nanz (2010), "A Logic for State-Modifying Authorization Policies"
- SPDX and CycloneDX specifications
- Beer, *Brain of the Firm* (1972)

## Connection to the spec

Technical design: [`docs/vision/world-state.md`](https://github.com/teague/umwelt/blob/main/docs/vision/world-state.md) and [`docs/superpowers/specs/2026-04-18-sql-compiler-design.md`](https://github.com/teague/umwelt/blob/main/docs/superpowers/specs/2026-04-18-sql-compiler-design.md) in the umwelt repo.

---

*This post closes the series. The theory is in [Ma](../ma/index). The practice is in [Fuel](../fuel/index). The policy layer is what this series describes. The tools that implement it are in [Tools](../tools/index). What remains is code — and the code will either confirm or refute the architecture.*
