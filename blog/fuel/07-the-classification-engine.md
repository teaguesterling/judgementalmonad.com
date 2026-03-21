# The Classification Engine

*Every organization has classification knowledge. Most of it lives in someone's head. The ratchet turns it into infrastructure that enforces itself.*

---

## The highest-value ratchet turn

If you've been following this series, you've seen the ratchet applied to tool building, to mode transitions, to segment definitions. Each application follows the same two-stage mechanism: discover the pattern in practice, then crystallize it into specified infrastructure.

This post applies the ratchet to classification and access control. It may be the highest-value application in the series, because the cost of getting access control wrong isn't wasted inference — it's data exposure.

The pattern is the same. The stakes are different.

---

## Classification knowledge

Every data organization has classification knowledge. Someone knows that the `ssn` field is restricted. Someone knows that the `diagnosis_code` column can't be joined with `patient_name` without IRB approval. Someone knows that aggregate counts below five need to be suppressed before they leave the analytics environment.

Where does this knowledge live?

Usually: in someone's head. Sometimes: in an email thread from 2019. Occasionally: in a wiki page that hasn't been updated since the last data steward left. Rarely: in the system that actually serves the data.

This is the gap. The knowledge exists. The enforcement doesn't. Between "we know this field is sensitive" and "the query engine refuses to return this field to unauthorized roles" lies a computation channel — a gap filled by human judgment on every access request.

Every time an analyst asks "can I get access to the demographics table?", a human evaluates the request. They check the analyst's role, the project justification, the sensitivity of the fields involved, the downstream use case. They apply judgment. They send an email. The analyst waits three days.

This works. It also means your classification knowledge is locked inside a process that scales linearly with headcount and degrades when the data steward takes vacation.

The ratchet turns that judgment into infrastructure.

---

## The access control spectrum

Access control enforcement exists on a spectrum. Each step is a ratchet turn — a piece of human judgment that gets crystallized into a specified rule.

### Level 1: Manual review per request

Every access request goes through a human. The data steward reads the request, considers the context, checks the role, and approves or denies. This is a pure computation channel — trained human judgment on every transaction.

It's thorough. It's also expensive, slow, and completely dependent on the steward's availability and memory. When the steward leaves, the knowledge walks out the door. When the steward is overloaded, approvals take a week. When the steward is tired, mistakes happen.

The failure mode isn't malice. It's throughput.

### Level 2: LLM-based policy evaluation

Feed the access policy document to an LLM. Let it evaluate requests against the written policy. Faster than a human, available 24/7, doesn't take vacation.

Still a computation channel. The LLM is applying trained judgment to each request. It's better than email, but the enforcement is probabilistic — the LLM might misinterpret the policy, might hallucinate an exception, might approve something the policy prohibits because the request was phrased persuasively enough.

You've replaced one computation channel with a faster computation channel. The gap between "policy exists" and "policy enforces itself" is narrower, but it's still there.

### Level 3: Rule engine around the query

Write rules that wrap the query layer. Before a query executes, check the requesting role against a permission table. If the role doesn't have access to the requested fields, reject the query.

This is partially specified. The common cases are handled by rules. The edge cases — "this analyst needs temporary access to restricted fields for a specific IRB-approved study" — still require human judgment. But the common cases are instant, auditable, and free.

Most organizations that have access control at all are somewhere around this level. It works for the 80% case. The 20% is still a computation channel.

### Level 4: Access control in the schema

The query literally cannot return non-permissioned data. The analyst's view of the database doesn't include the restricted fields. They can't request what they can't see. The schema itself is the enforcement mechanism.

This is fully specified. Enforcement is instant — it happens at query parse time, before execution begins. It's auditable — the view definition is the access policy, readable by anyone. It's free — no per-query evaluation cost, no human in the loop, no LLM inference.

Row 4 is the destination. Everything before it is a waypoint.

---

## The ratchet on access

The two-stage mechanism from [The Two-Stage Turn](02-the-two-stage-turn.md) applies directly.

### Stage 1: Discovery

Before you can crystallize access rules, you need to observe what access actually looks like. Who accesses what? How often? With what justification? What gets approved and what gets denied?

This is the same discovery stage that powered the segment builder in the [previous post](06-the-segment-builder.md). You're not designing access rules from first principles. You're observing the access patterns that already exist and identifying which ones are stable enough to promote.

Log every access request. Log every approval and denial. Log the role, the fields, the justification, the outcome. The access audit log is your ratchet fuel.

```sql
CREATE TABLE access_audit_log (
    request_id VARCHAR DEFAULT gen_random_uuid()::VARCHAR,
    query_hash VARCHAR,
    role VARCHAR NOT NULL,
    requested_table VARCHAR NOT NULL,
    fields_accessed VARCHAR[] NOT NULL,
    justification VARCHAR,
    outcome VARCHAR NOT NULL,  -- 'approved', 'denied', 'auto_approved'
    reviewed_by VARCHAR,       -- NULL if auto_approved
    ts TIMESTAMP DEFAULT current_timestamp
);
```

The audit log is not optional overhead. It's the substrate the ratchet operates on. Without it, you're guessing which access patterns are stable. With it, you're measuring.

### Stage 2: Crystallization

Once you have enough observations, promote the stable patterns into declared rules. The access pattern that was "ask the data steward" becomes a schema constraint. The computation channel closes.

```sql
-- Which access request patterns are ratchet candidates?
-- These are the patterns stable enough to become rules.
SELECT
    role,
    requested_table,
    fields_accessed,
    count(*) AS frequency,
    count(*) FILTER (WHERE outcome = 'approved') AS approvals,
    count(*) FILTER (WHERE outcome = 'denied') AS denials,
    round(
        count(*) FILTER (WHERE outcome = 'approved') * 100.0 / count(*), 1
    ) AS approval_rate_pct
FROM access_audit_log
WHERE ts >= current_timestamp - INTERVAL '90 days'
GROUP BY role, requested_table, fields_accessed
HAVING count(*) >= 10
ORDER BY frequency DESC;
```

A pattern that's been approved thirty times with zero denials is a ratchet candidate. Promote it to an auto-approval rule. A pattern that's been denied every time is a ratchet candidate too — promote it to an auto-denial rule, or remove the fields from the role's view entirely.

The patterns in between — sometimes approved, sometimes denied — are where the computation channel still needs to exist. Those are the edge cases. Leave them for human review. The ratchet doesn't need to close every channel at once. It needs to close the ones that are stable enough to specify.

---

## SQL as security boundary

Why SQL? Why not a Python-based access control layer?

This isn't a style preference. It's a mathematical property.

SQL is a Level 1 operation in the [computation channel taxonomy](../ma/07-computation-channels.md). A SQL query is a total function over a known schema. Given the schema definition and the query text, you can determine — decidably — which tables, columns, and rows the query will touch. You can inspect it. You can audit it. You can prove properties about it.

Python is Level 4. An arbitrary Python script can do anything a Turing machine can do. By Rice's theorem, non-trivial semantic properties of the script — "will it access restricted data?", "will it exfiltrate records?", "does it respect the access policy?" — are undecidable. You can write rules that catch specific patterns, but the space of programs that violate your policy is not enumerable. The next violation will look different from all the previous ones.

The computation channel boundary IS the security boundary. This is not a convenience — it's a consequence of decidability. If the query language is total and the schema is known, the Harness can answer "what will this query return?" before execution. If the language is Turing-complete, it can't.

This is why every serious data access control system works at the SQL layer, not the application layer. It's why database views are a security mechanism, not just a convenience. It's why giving analysts a SQL interface to a curated schema is categorically different from giving them a Python notebook with a database connection string.

The restriction isn't limiting the analyst's power. It's making the access control *decidable*.

---

## Code ships: DuckDB access control layer

Here's a working access control layer in DuckDB. It implements field classification, role-based access tiers, view generation, and audit logging.

### Classification schema

```sql
-- What sensitivity level does each field carry?
CREATE TABLE field_classifications (
    table_name VARCHAR NOT NULL,
    field_name VARCHAR NOT NULL,
    sensitivity_level VARCHAR NOT NULL,  -- 'public', 'internal', 'confidential', 'restricted'
    classification_reason VARCHAR,
    classified_by VARCHAR,
    classified_at TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (table_name, field_name)
);

-- What's the maximum sensitivity each role can access?
CREATE TABLE role_access_tiers (
    role VARCHAR NOT NULL,
    max_sensitivity VARCHAR NOT NULL,  -- role ceiling
    can_access_individual_records BOOLEAN DEFAULT true,
    min_aggregation_threshold INTEGER DEFAULT 0,  -- 0 = no minimum
    PRIMARY KEY (role)
);

-- Explicit sensitivity ordering for comparison
CREATE TABLE sensitivity_ordering (
    level VARCHAR PRIMARY KEY,
    rank INTEGER NOT NULL UNIQUE
);

INSERT INTO sensitivity_ordering VALUES
    ('public', 1),
    ('internal', 2),
    ('confidential', 3),
    ('restricted', 4);
```

### Populating classifications

The discovery stage produces the initial classification. Start conservative — classify everything as `internal` and promote specific fields upward or downward based on observed access patterns.

```sql
-- Bootstrap: classify all fields as 'internal' by default
INSERT INTO field_classifications (table_name, field_name, sensitivity_level, classification_reason)
SELECT
    table_name,
    column_name,
    'internal',
    'Default classification — awaiting review'
FROM information_schema.columns
WHERE table_schema = 'main'
  AND table_name NOT IN (
    'field_classifications', 'role_access_tiers',
    'sensitivity_ordering', 'access_audit_log'
  );

-- Then promote known-sensitive fields
UPDATE field_classifications
SET sensitivity_level = 'restricted',
    classification_reason = 'PII — direct identifier'
WHERE field_name IN ('ssn', 'social_security_number', 'tax_id')
   OR field_name LIKE '%_ssn';

UPDATE field_classifications
SET sensitivity_level = 'confidential',
    classification_reason = 'PHI — protected health information'
WHERE field_name IN ('diagnosis_code', 'treatment_code', 'medication')
   OR field_name LIKE 'dx_%';

UPDATE field_classifications
SET sensitivity_level = 'public',
    classification_reason = 'Non-sensitive aggregate dimension'
WHERE field_name IN ('year', 'quarter', 'region', 'product_category');
```

### View generator

This is the crystallization step. Given a role, generate a view that enforces access control at the schema level.

```sql
-- Query to determine field access for a given role and table.
-- Fields above the role's sensitivity ceiling are masked or excluded.
SELECT
    fc.field_name,
    fc.sensitivity_level,
    so_field.rank AS field_rank,
    so_role.rank AS role_max_rank,
    CASE
        WHEN so_field.rank <= so_role.rank THEN 'visible'
        WHEN so_field.rank = so_role.rank + 1 THEN 'masked'
        ELSE 'excluded'
    END AS access_action
FROM field_classifications fc
JOIN sensitivity_ordering so_field
    ON fc.sensitivity_level = so_field.level
JOIN role_access_tiers rat
    ON rat.role = 'analyst'  -- parameterize per role
JOIN sensitivity_ordering so_role
    ON rat.max_sensitivity = so_role.level
WHERE fc.table_name = 'patients';
```

To generate the actual views from this metadata, use a thin script that reads the classification tables and emits DDL:

```python
#!/usr/bin/env python3
"""
View generator: creates role-scoped views from classification metadata.

Usage:
    python generate_access_views.py --db analytics.duckdb --role analyst
"""

import argparse
import duckdb


def generate_view(con, table_name: str, role: str) -> str:
    """Generate a CREATE VIEW statement for the given role and table."""
    fields = con.execute("""
        SELECT
            fc.field_name,
            fc.sensitivity_level,
            so_field.rank AS field_rank,
            so_role.rank AS role_max_rank
        FROM field_classifications fc
        JOIN sensitivity_ordering so_field
            ON fc.sensitivity_level = so_field.level
        JOIN role_access_tiers rat
            ON rat.role = ?
        JOIN sensitivity_ordering so_role
            ON rat.max_sensitivity = so_role.level
        WHERE fc.table_name = ?
        ORDER BY fc.field_name
    """, [role, table_name]).fetchall()

    if not fields:
        return None

    select_parts = []
    for field_name, sens_level, field_rank, role_max_rank in fields:
        if field_rank <= role_max_rank:
            # Visible: include as-is
            select_parts.append(f"    {field_name}")
        elif field_rank == role_max_rank + 1:
            # One level above ceiling: mask with hash
            select_parts.append(
                f"    md5({field_name}::VARCHAR) AS {field_name}"
            )
        # else: excluded entirely — field does not appear in the view

    if not select_parts:
        return None

    view_name = f"{table_name}_{role}_v"
    select_clause = ",\n".join(select_parts)
    return f"CREATE OR REPLACE VIEW {view_name} AS\nSELECT\n{select_clause}\nFROM {table_name};"


def generate_all_views(db_path: str, role: str):
    """Generate views for all classified tables for the given role."""
    con = duckdb.connect(db_path)

    tables = con.execute("""
        SELECT DISTINCT table_name
        FROM field_classifications
    """).fetchall()

    for (table_name,) in tables:
        ddl = generate_view(con, table_name, role)
        if ddl:
            print(f"-- View for {role} on {table_name}")
            print(ddl)
            print()
            con.execute(ddl)
            print(f"-- Created: {table_name}_{role}_v")

    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate role-scoped access views"
    )
    parser.add_argument("--db", required=True, help="Path to DuckDB database")
    parser.add_argument("--role", required=True, help="Role to generate views for")
    args = parser.parse_args()
    generate_all_views(args.db, args.role)
```

### Aggregation-only views with suppression

For roles that shouldn't see individual records — only aggregates — apply minimum entity thresholds. This is small-cell suppression: if a group has fewer than N records, suppress the count.

```sql
-- Aggregation-only view with small-cell suppression.
-- Roles with min_aggregation_threshold > 0 see this instead of row-level access.
CREATE OR REPLACE VIEW patients_aggregate_v AS
SELECT
    region,
    year,
    diagnosis_category,
    CASE
        WHEN count(*) < 5 THEN NULL  -- suppressed: cell too small
        ELSE count(*)
    END AS patient_count,
    CASE
        WHEN count(*) < 5 THEN NULL
        ELSE round(avg(age), 1)
    END AS avg_age,
    CASE
        WHEN count(*) < 5 THEN NULL
        ELSE round(avg(length_of_stay), 1)
    END AS avg_length_of_stay
FROM patients
GROUP BY region, year, diagnosis_category;
```

The suppression threshold is a ratchet artifact. Someone knew that counts below five risk re-identification. That knowledge used to live in a policy document. Now it lives in the view definition. The analyst can't produce a re-identifiable count because the view won't return one.

### Audit logging

Every query through the access layer gets logged. This closes the loop — the audit log feeds the next discovery cycle.

```sql
-- Log a query execution against the access layer.
-- In practice, wrap this in the query execution path.
INSERT INTO access_audit_log (query_hash, role, requested_table, fields_accessed, outcome)
VALUES (
    md5('SELECT region, patient_count FROM patients_aggregate_v'),
    'external_researcher',
    'patients',
    ['region', 'patient_count'],
    'auto_approved'
);

-- What does the access pattern look like over the last quarter?
SELECT
    role,
    requested_table,
    outcome,
    count(*) AS query_count,
    count(DISTINCT fields_accessed::VARCHAR) AS distinct_field_sets
FROM access_audit_log
WHERE ts >= current_timestamp - INTERVAL '90 days'
GROUP BY role, requested_table, outcome
ORDER BY query_count DESC;
```

The audit log does double duty. It's a compliance artifact — you can demonstrate who accessed what and when. It's also ratchet fuel — the access patterns in the log tell you which rules to crystallize next.

---

## Tool restriction IS access control

Here's the connection that makes the ratchet generalize.

In [the segment builder](06-the-segment-builder.md), we restricted the analyst's query surface to validated segment definitions. The analyst couldn't construct an arbitrary population — they could only compose from the segments the system knew about. The co-domain funnel narrowed what the query could produce.

Access control is the same pattern. The analyst sees only the fields their role justifies. The query can't return data outside the funnel. The view definition IS the co-domain funnel, applied to data instead of to tool outputs.

And the mechanism that restricts an agent's tool set in posts [3](03-where-the-failures-live.md) and [4](04-the-failure-driven-controller.md) is the same mechanism. The agent in implementation mode can't edit tests — the mode boundary removes the capability. The analyst in the `external_researcher` role can't see SSNs — the view definition removes the field. Same structure. Same enforcement point. Different substrate.

Tool restriction IS access control, viewed from the ratchet framework. The question "what should this role be able to access?" and the question "what tools should this agent have?" are the same question: what is the co-domain of this actor's operations?

The ratchet answers both the same way: observe what the actor actually does, identify the stable patterns, crystallize those patterns into specified boundaries. The boundary becomes the role. The role becomes the view. The view becomes the schema. The computation channel closes.

---

## Same pattern, different stakes

The classification engine follows the same two-stage mechanism as every other ratchet application in this series. Discovery feeds crystallization. Observation becomes specification. The computation channel — human judgment on every access request — closes as the rules stabilize.

But the stakes here are different from tool building. A misconfigured tool wastes inference. A misconfigured access control exposes data. The ratchet's conservatism — start broad, observe, then tighten — maps naturally onto access control, where the safe default is restriction and the burden of proof is on expansion.

Notice the asymmetry. It's the same asymmetry from the [failure-driven controller](04-the-failure-driven-controller.md): tightening is safe to automate, loosening requires authorization. In access control, this becomes: revoking access can be automated (the rule fires, the field disappears from the view), granting access requires human review (the request goes to a data steward who evaluates the justification).

The ratchet only turns one direction. For access control, that's not a limitation. It's the point.

---

*Previously: [The Segment Builder](06-the-segment-builder.md)*
*Next: [Teaching Without Theory](08-teaching-without-theory.md)*
*For the level taxonomy: [Computation Channels](../ma/07-computation-channels.md)*
