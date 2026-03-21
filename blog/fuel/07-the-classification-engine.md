# The Classification Engine

*The same pattern that restricts an agent's tool set restricts an analyst's field access. Tool restriction IS access control.*

---

## One mechanism

In [Post 4](04-the-failure-driven-controller.md), the agent in implementation mode can't edit tests — the mode boundary removes the capability. The agent doesn't decide not to edit tests. It *can't*. The tool isn't in its tool set.

In [Post 6](06-the-segment-builder.md), the analyst can't construct an arbitrary population query — they select from validated segment definitions. The co-domain funnel narrows what the query can produce.

Access control is the same pattern. An analyst in the `marketing_ops` role can't see credit card numbers — the view definition doesn't include the field. They can't request what they can't see. The schema itself is the enforcement mechanism.

Tool restriction IS access control, viewed from the ratchet framework. The question "what should this agent be able to do?" and the question "what should this role be able to access?" are the same question: **what is the co-domain of this actor's operations?**

This post applies the ratchet to that question in the data platform context, where the cost of getting it wrong isn't wasted inference — it's data exposure, compliance violations, and PCI audit findings.

---

## Classification knowledge

Every data organization has classification knowledge. Someone knows that the `card_number` field is restricted. Someone knows that `transaction_amount` can't be joined with `customer_name` without masking the cardholder data. Someone knows that aggregates over payment data need minimum entity thresholds before they leave the analytics environment.

Where does this knowledge live?

Usually: in someone's head. Sometimes: in an email thread from 2019. Occasionally: in a wiki page that hasn't been updated since the last compliance officer left. Rarely: in the system that actually serves the data.

This is the gap. The knowledge exists. The enforcement doesn't. Between "we know this field is sensitive" and "the query engine refuses to return this field to unauthorized roles" lies a computation channel — a gap filled by human judgment on every access request.

Every time an analyst asks "can I get access to the transactions table?", a human evaluates the request. They check the analyst's role, the business justification, the PCI scope of the fields involved, the downstream use case. They apply judgment. They open a ticket. The analyst waits three days.

This works. It also means your classification knowledge is locked inside a process that scales linearly with headcount and degrades when the compliance officer takes vacation.

The ratchet turns that judgment into infrastructure.

---

## The access control spectrum

Access control enforcement exists on a spectrum. Each step is a ratchet turn — a piece of human judgment that gets crystallized into a specified rule.

### Level 1: Manual review per request

Every access request goes through a human. The compliance officer reads the request, considers the PCI scope, checks the role, and approves or denies. This is a pure computation channel — trained human judgment on every transaction.

It's thorough. It's also expensive, slow, and completely dependent on the officer's availability and memory. When the officer leaves, the knowledge walks out the door. When they're overloaded, approvals take a week. When they're tired, mistakes happen.

The failure mode isn't malice. It's throughput.

### Level 2: LLM-based policy evaluation

Feed the access policy document to an LLM. Let it evaluate requests against the written policy. Faster than a human, available 24/7, doesn't take vacation.

Still a computation channel. The LLM is applying trained judgment to each request. The enforcement is probabilistic — the LLM might misinterpret the policy, might hallucinate an exception, might approve something the policy prohibits because the request was phrased persuasively enough.

You've replaced one computation channel with a faster computation channel. The gap between "policy exists" and "policy enforces itself" is narrower, but it's still there.

### Level 3: Rule engine around the query

Write rules that wrap the query layer. Before a query executes, check the requesting role against a permission table. If the role doesn't have access to the requested fields, reject the query.

This is partially specified. The common cases are handled by rules. The edge cases — "this analyst needs temporary access to cardholder data for a specific fraud investigation" — still require human judgment. But the common cases are instant, auditable, and free.

Most organizations that have access control at all are somewhere around this level. It works for the 80% case. The 20% is still a computation channel.

### Level 4: Access control in the schema

The query literally cannot return non-permissioned data. The analyst's view of the database doesn't include the restricted fields. They can't request what they can't see. The schema itself is the enforcement mechanism.

This is fully specified. Enforcement is instant — it happens at query parse time, before execution begins. It's auditable — the view definition is the access policy, readable by anyone. It's free — no per-query evaluation cost, no human in the loop, no LLM inference.

Level 4 is the destination. Everything before it is a waypoint.

---

## The ratchet on access

The two-stage mechanism from [The Two-Stage Turn](02-the-two-stage-turn.md) applies directly.

### Stage 1: Discovery

Before you can crystallize access rules, you need to observe what access actually looks like. Who accesses what? How often? With what justification? What gets approved and what gets denied?

Log every access request. Log every approval and denial. Log the role, the fields, the justification, the outcome. The access audit log is your ratchet fuel.

### Stage 2: Crystallization

Once you have enough observations, promote the stable patterns into declared rules.

A pattern that's been approved thirty times with zero denials is a ratchet candidate. Promote it to an auto-approval rule. A pattern that's been denied every time is a ratchet candidate too — promote it to an auto-denial rule, or remove the fields from the role's view entirely.

The patterns in between — sometimes approved, sometimes denied — are where the computation channel still needs to exist. Those are the edge cases. Leave them for human review. The ratchet doesn't need to close every channel at once. It needs to close the ones that are stable enough to specify.

---

## SQL as security boundary

Why SQL? Why not a Python-based access control layer?

This isn't a style preference. It's a mathematical property.

SQL is a Level 1 operation in the [computation channel taxonomy](../ma/07-computation-channels.md). A SQL query is a total function over a known schema. Given the schema definition and the query text, you can determine — decidably — which tables, columns, and rows the query will touch. You can inspect it. You can audit it. You can prove properties about it.

Python is Level 4. An arbitrary Python script can do anything a Turing machine can do. By Rice's theorem, non-trivial semantic properties of the script — "will it access restricted data?", "will it exfiltrate records?", "does it respect the access policy?" — are undecidable. You can write rules that catch specific patterns, but the space of programs that violate your policy is not enumerable.

The computation channel boundary IS the security boundary. If the query language is total and the schema is known, the Harness can answer "what will this query return?" before execution. If the language is Turing-complete, it can't.

This is why every serious data access control system works at the SQL layer, not the application layer. It's why database views are a security mechanism, not just a convenience. It's why giving analysts a SQL interface to a curated schema is categorically different from giving them a Python notebook with a database connection string.

The restriction isn't limiting the analyst's power. It's making the access control *decidable*.

---

## Code ships

A DuckDB access control layer with field classification, role-based views, and audit logging. Full implementation in [blog/fuel/code/classification_engine.sql](code/classification_engine.sql) and [blog/fuel/code/generate_access_views.py](code/generate_access_views.py).

### Classification schema

Three tables define the access control surface:

```sql
-- What sensitivity level does each field carry?
CREATE TABLE field_classifications (
    table_name VARCHAR NOT NULL,
    field_name VARCHAR NOT NULL,
    sensitivity_level VARCHAR NOT NULL,  -- 'public', 'internal', 'confidential', 'restricted'
    classification_reason VARCHAR,
    PRIMARY KEY (table_name, field_name)
);

-- What's the maximum sensitivity each role can access?
CREATE TABLE role_access_tiers (
    role VARCHAR NOT NULL PRIMARY KEY,
    max_sensitivity VARCHAR NOT NULL,
    can_access_individual_records BOOLEAN DEFAULT true,
    min_aggregation_threshold INTEGER DEFAULT 0
);

-- Sensitivity ordering for comparison
-- public(1) < internal(2) < confidential(3) < restricted(4)
CREATE TABLE sensitivity_ordering (
    level VARCHAR PRIMARY KEY,
    rank INTEGER NOT NULL UNIQUE
);
```

Bootstrap by classifying everything as `internal`, then promote known-sensitive fields upward:

```sql
-- PCI-scoped fields
UPDATE field_classifications
SET sensitivity_level = 'restricted',
    classification_reason = 'PCI DSS — cardholder data'
WHERE field_name IN ('card_number', 'cvv', 'card_expiry', 'pan')
   OR field_name LIKE '%card_num%';

-- Financial PII
UPDATE field_classifications
SET sensitivity_level = 'confidential',
    classification_reason = 'Financial PII — sensitive account data'
WHERE field_name IN ('ssn', 'tax_id', 'bank_account', 'routing_number');

-- Non-sensitive dimensions
UPDATE field_classifications
SET sensitivity_level = 'public',
    classification_reason = 'Non-sensitive aggregate dimension'
WHERE field_name IN ('year', 'quarter', 'region', 'product_category', 'merchant_category');
```

### View generation

Given a role and a table, generate a view that enforces access control at the schema level. Fields above the role's sensitivity ceiling are either masked (one level above — hashed) or excluded entirely (two or more levels above). A Python script reads the classification tables and emits DDL — see the [full implementation](code/generate_access_views.py).

The result: the `marketing_ops` role sees `customer_id, region, merchant_category, transaction_count` but not `card_number`, `ssn`, or `bank_account`. The fields don't exist in their view. The query can't return what the schema doesn't contain.

### Aggregation views with suppression

For roles that shouldn't see individual records — only aggregates — apply minimum entity thresholds:

```sql
-- Aggregation-only view with small-cell suppression.
CREATE OR REPLACE VIEW transactions_aggregate_v AS
SELECT
    region, quarter, merchant_category,
    CASE WHEN count(*) < 5 THEN NULL ELSE count(*) END AS txn_count,
    CASE WHEN count(*) < 5 THEN NULL ELSE round(avg(amount), 2) END AS avg_amount
FROM transactions
GROUP BY region, quarter, merchant_category;
```

The suppression threshold is a ratchet artifact. Someone knew that counts below five risk re-identification of high-value transactions. That knowledge used to live in a policy document. Now it lives in the view definition. The analyst can't produce a re-identifiable count because the view won't return one.

### Audit

Every query through the access layer gets logged. The audit log feeds the next discovery cycle — access patterns tell you which rules to crystallize next. The log does double duty: compliance artifact and ratchet fuel.

---

## The connection

The mechanism that restricts an agent's tool set is the same mechanism that restricts an analyst's field access.

```{mermaid}
%%{init: {'theme': 'neutral'}}%%
graph TD
    subgraph agent ["Agent Mode Boundary"]
        AM["Implementation mode"] --> AT["Tools: Read, Edit, Write, RunTests"]
        AM --> AX["Excluded: Edit(tests)"]
    end

    subgraph data ["Data Access Boundary"]
        DM["marketing_ops role"] --> DT["Fields: customer_id, region,<br/>merchant_category, txn_count"]
        DM --> DX["Excluded: card_number,<br/>ssn, bank_account"]
    end

    subgraph mech ["Same Mechanism"]
        M1["Define the actor's co-domain"]
        M2["Observe what the actor<br/>actually does (logs)"]
        M3["Crystallize stable patterns<br/>into boundaries"]
        M1 --> M2 --> M3 --> M1
    end

    style agent fill:#fff5f5,stroke:#c53030
    style data fill:#f0fff4,stroke:#276749
    style mech fill:#fffff0,stroke:#975a16
```

| Agent architecture | Data access control |
|---|---|
| Mode removes tool from tool set | View removes field from schema |
| Agent can't call `Edit(tests)` | Analyst can't query `card_number` |
| Mode transition tightens/loosens | Role change tightens/loosens |
| Failure stream → promote to constraint | Audit log → promote to rule |
| Tightening is safe to automate | Revoking access is safe to automate |
| Loosening requires human authorization | Granting access requires human review |

The ratchet answers both the same way: observe what the actor actually does, identify the stable patterns, crystallize those patterns into specified boundaries. The boundary becomes the role. The role becomes the view. The view becomes the schema. The computation channel closes.

---

## Same pattern, different stakes

The classification engine follows the same two-stage mechanism as every other ratchet application in this series. Discovery feeds crystallization. Observation becomes specification. The computation channel — human judgment on every access request — closes as the rules stabilize.

But the stakes here are different from tool building. A misconfigured tool wastes inference. A misconfigured access control exposes cardholder data. The ratchet's conservatism — start broad, observe, then tighten — maps naturally onto PCI compliance, where the safe default is restriction and the burden of proof is on expansion.

The asymmetry is the same as the [failure-driven controller](04-the-failure-driven-controller.md): tightening is safe to automate, loosening requires authorization. In access control: revoking access can be automated (the rule fires, the field disappears from the view), granting access requires human review (the request goes to a compliance officer who evaluates the justification).

The ratchet only turns one direction. For access control, that's not a limitation. It's the point.

---

*Previously: [The Segment Builder](06-the-segment-builder.md)*
*Next: [Teaching Without Theory](08-teaching-without-theory.md)*
*For the level taxonomy: [Computation Channels](../ma/07-computation-channels.md)*
