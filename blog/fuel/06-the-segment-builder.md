# The Segment Builder

*Every data platform builds this. The ratchet explains why it works.*

---

## The first thing you build

Every data platform, regardless of domain, builds the same thing first: a way to define populations.

B2B analytics platforms call it audience segmentation. Marketing tools call it list management. Financial platforms call it account classification. Research platforms call it cohort building. Clinical trial systems call it eligibility screening.

Strip the branding and the vertical language and you get the same structural pattern:

```
segment(criteria) → entity_set
```

A user defines criteria. The system returns the set of entities that match. The criteria might be revenue thresholds, behavioral signals, transaction patterns, purchase history, risk scores, or compliance flags. The entities might be accounts, customers, transactions, devices, or counterparties. The structure is the same.

This post applies the ratchet to that pattern. Same two-stage turn from [Post 2](02-the-two-stage-turn.md). Different substrate. The segment builder is the first of two data platform case studies that show the ratchet isn't specific to agent architecture — it's a property of any system where human judgment navigates complex signals to produce structured outputs.

---

## The computation channel hiding in your segment builder

Here's how segment definition works in practice. An analyst gets a request from the revenue team: "Find enterprise accounts with ARR over $100K that haven't logged in for 90 days and had a support escalation in the last quarter." The analyst opens a SQL editor and writes:

```sql
SELECT a.account_id, a.company_name
FROM accounts a
JOIN subscriptions s ON a.account_id = s.account_id
JOIN activity_log al ON a.account_id = al.account_id
JOIN support_tickets st ON a.account_id = st.account_id
WHERE s.arr > 100000
  AND s.plan_type = 'enterprise'
  AND s.status = 'active'
  AND al.last_login < current_date - INTERVAL '90 days'
  AND st.severity IN ('high', 'critical')
  AND st.created_at >= current_date - INTERVAL '3 months'
  AND NOT EXISTS (
      SELECT 1 FROM activity_log
      WHERE account_id = a.account_id
        AND event_type = 'login'
        AND event_date >= current_date - INTERVAL '90 days'
  );
```

This query is a computation channel. Arbitrary SQL against the database. The analyst's judgment — knowing that ARR lives in the subscriptions table, knowing that "haven't logged in" means checking the activity log for absence, knowing that escalations need severity filtering — navigates business and technical signals to produce a population definition.

The query works. It runs. It returns 147 accounts. The analyst validates the result, adjusts the inactivity threshold, runs it again. Eventually the segment is good enough for the downstream use case — the customer success team gets the list and starts outreach.

This is Stage 1. Discovery. The analyst explored the data, used trained judgment to translate a business concept into a technical definition, iterated until the result made sense. Every step required expertise. Every step was expensive.

Now the same request comes in next quarter. A different analyst. Same business concept — high-value accounts at risk of churning. The new analyst writes a different query. Maybe they join to a different activity table. Maybe they use a different ARR threshold. Maybe they forget the "active subscription" filter and include accounts that already churned. Maybe they get it right but spend four hours rediscovering what the first analyst already knew.

This is the ratchet not turning. The knowledge from the first analyst's discovery — which tables to join, which thresholds to use, which edge cases to handle — stayed in the first analyst's head and in a query buried in their SQL history. The organization paid for discovery twice. It will pay again next quarter.

---

## The two-stage turn on segments

The fix is the same mechanism from [Post 2](02-the-two-stage-turn.md), applied to a different substrate.

### Stage 1: Discovery

The analyst writes ad-hoc SQL. This is the high-*ma* process — trained judgment navigating complex signals. The analyst needs business knowledge (what constitutes "at risk," which ARR threshold matters for enterprise accounts), technical knowledge (how the schema is structured, which joins are correct), and domain knowledge (what "inactivity" means operationally — login absence, not just low usage).

The query log captures everything. Not just the final query, but every iteration — the first attempt, the revised version, the threshold adjustments, the validation queries run alongside. The log is append-only. The analyst's exploration is recorded.

### Stage 2: Crystallization

Common patterns get promoted to validated, named definitions. The analyst's bespoke SQL becomes a parameterized template:

```sql
-- Before: computation channel
SELECT a.account_id FROM accounts a
JOIN subscriptions s ON ...
WHERE s.arr > 100000 AND al.last_login < current_date - INTERVAL '90 days' AND ...

-- After: data channel
SELECT * FROM churn_risk_enterprise(arr_min := 100000, inactive_days := 90, escalation_window := 90);
```

The computation channel closed. The next analyst doesn't need to know which tables to join, which subquery handles login absence, or which edge cases to watch for. They call a function with named parameters. The function encodes all of that knowledge — type-honestly, backed by an implementation that makes specific commitments about which tables it queries and how it handles edge cases.

Same functionality. Categorically different grade.

---

## The reference insight

Here is the architectural decision most segment builder implementations get wrong.

The segment builder's output should be a **reference** — a segment ID — not raw data. The function doesn't return account IDs directly. It returns a segment identifier that downstream systems use to request the entity set through the segment builder's own interface.

Why this matters: the segment builder is the natural enforcement point for access control. It's where criteria meet data. It's where the query is constructed and executed. Everything downstream — reports, dashboards, care management workflows, export pipelines — should accept a segment reference and request data through the builder.

This is the co-domain funnel from the framework. The segment builder does deep processing internally — complex joins, clinical logic, threshold evaluation — and produces a narrow output: a segment ID. Downstream tools never construct their own queries against the raw data. They present a segment ID and receive a validated result set, filtered according to the access controls that the segment builder enforces.

The alternative — returning raw account IDs that downstream tools use to query the database directly — means every downstream tool needs its own access control logic. Every report writer, every export pipeline, every dashboard needs to independently enforce row-level security, column-level restrictions, PII masking, and audit logging. The access control surface area grows with every downstream consumer.

With the reference pattern, the surface area is one: the segment builder. Everything else trusts the reference.

---

## The promotion pipeline

The ratchet turns through a concrete pipeline:

**1. Analyst writes ad-hoc SQL.** A new clinical concept, a novel research question, an operational request nobody has seen before. The analyst explores.

**2. The query gets logged.** Query text, parameters, result count, execution time, who ran it, when. Append-only.

**3. Analysis identifies promotion candidates.** DuckDB queries over the log find patterns: queries that run frequently, that succeed consistently, that share structural similarity. These are ratchet candidates.

**4. Validated patterns become named definitions.** A human reviews the candidate. The query gets cleaned up, parameterized, tested against edge cases, and promoted to a named segment definition with a version number.

**5. Named definitions enter a library.** Future analysts browse the library before writing SQL. "High-risk uncontrolled diabetic" is already defined. They select it, adjust the parameters, and get results.

**6. New ad-hoc queries continue at the frontier.** The library handles the known. Novel requests still go through Stage 1. The analyst's judgment still navigates the complex signals. The frontier shrinks, but it never disappears.

**7. The ratchet turns again.** New ad-hoc queries generate new log entries. New patterns emerge. New candidates get promoted. The library grows.

Each cycle converts a piece of clinical knowledge from "lives in an analyst's head" to "lives in a validated, versioned, parameterized definition." The knowledge survives the analyst leaving. The *ma* doesn't.

---

## Code ships

A DuckDB segment builder. The full implementation is in [blog/fuel/code/segment_builder.sql](code/segment_builder.sql). Here are the key pieces.

### Schema

Three tables: definitions (the library), query log (the capture mechanism), and results (materialized entity sets).

```sql
-- Segment definitions: the library of validated segments
CREATE TABLE segment_definitions (
    segment_id UUID DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    description VARCHAR,
    criteria_sql VARCHAR NOT NULL,
    parameters JSON,          -- parameter names, types, defaults
    created_by VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT current_timestamp,
    status VARCHAR DEFAULT 'draft',  -- draft | validated | deprecated
    version INTEGER DEFAULT 1,
    promoted_from UUID,       -- links to the query_log entry that spawned this
    PRIMARY KEY (segment_id)
);

-- Query log: append-only record of every segment execution
CREATE TABLE query_log (
    log_id UUID DEFAULT gen_random_uuid(),
    query_sql VARCHAR NOT NULL,
    query_hash VARCHAR NOT NULL,  -- structural hash for grouping similar queries
    -- ... parameters, result_count, executed_by, execution_ms, segment_id
);

-- Segment results: materialized entity sets, keyed by segment reference
CREATE TABLE segment_results (
    segment_id UUID NOT NULL,
    run_id UUID DEFAULT gen_random_uuid(),
    entity_id VARCHAR NOT NULL,
    computed_at TIMESTAMP DEFAULT current_timestamp
);
```

Execution requires dynamic SQL — the `criteria_sql` stored in the definition gets evaluated at runtime with parameter substitution, results materialized, and the run logged. See the full implementation for the driver script.

### The promotion query

This is the crystallization engine — the query that finds ad-hoc queries worth promoting to validated definitions:

```sql
-- Which ad-hoc queries are ratchet candidates?
WITH ad_hoc AS (
    SELECT query_hash,
           any_value(query_sql) AS example_sql,
           count(*) AS run_count,
           count(DISTINCT executed_by) AS distinct_users,
           avg(CASE WHEN success THEN 1.0 ELSE 0.0 END) AS success_rate
    FROM query_log
    WHERE segment_id IS NULL  -- ad-hoc only
    GROUP BY query_hash
)
SELECT *, CASE
    WHEN run_count >= 5 AND success_rate > 0.8 AND distinct_users >= 2
        THEN 'STRONG: multiple users, high success'
    WHEN run_count >= 10 AND success_rate > 0.8
        THEN 'STRONG: high frequency single user'
    WHEN run_count >= 3 AND success_rate > 0.9
        THEN 'CANDIDATE: emerging pattern'
    ELSE 'WATCH: not enough signal yet'
END AS recommendation
FROM ad_hoc WHERE run_count >= 3
ORDER BY run_count * success_rate DESC;
```

The promotion query is itself specified — SQL over structured data, zero trained judgment. A human reviews the candidates, decides which ones to promote, cleans up the SQL, adds parameter names. That review is the judgment step. Everything else is lookup.

### Before and after

```sql
-- BEFORE: computation channel — the analyst writes this from scratch
-- Requires: business knowledge, schema knowledge, SQL expertise
SELECT a.account_id, a.company_name
FROM accounts a JOIN subscriptions s ON ... JOIN activity_log al ON ...
WHERE s.arr > 100000 AND al.last_login < current_date - INTERVAL '90 days' AND ...

-- AFTER: data channel — the analyst selects from a library
SELECT * FROM churn_risk_enterprise(arr_min := 100000, inactive_days := 90, escalation_window := 90);
```

The before version is a computation channel — arbitrary SQL, full decision surface. The after version is a data channel — a name and typed parameters. The business knowledge, schema knowledge, and edge case handling are encoded in the definition. Same result set. The *ma* dropped because the knowledge moved from the analyst's head to the segment definition.

---

## Access control through the funnel

The segment builder, with the reference pattern, becomes the single enforcement point for data access. All access control logic lives in one place.

**Row-level security.** The segment definition determines which entities are in the result set. The criteria SQL is the row filter. Downstream tools never construct their own filters — they present a segment ID and get back the entities that the definition includes and the requesting user is authorized to see.

**Column-level security.** The segment builder controls which fields appear in the result set. A marketing analyst might get `account_id, company_size, plan_type` — no financial details. A finance user might get `account_id, company_name, arr, payment_status` — sensitive financial data included. Same segment definition, different column projections based on the requesting role.

**Aggregation controls.** Minimum cell sizes, suppression rules — the controls that prevent re-identification from small groups. The segment builder applies these before returning results. Downstream tools receive already-controlled data.

**Audit.** Every segment execution is logged. Who requested it, when, which definition, which parameters, how many results. The audit trail is complete because all access flows through one point. The access policy schema and enforcement logic are in the [full implementation](code/segment_builder.sql).

The co-domain funnel means downstream tools are simpler. A dashboard that displays segment results doesn't need access control logic. It presents a segment ID, receives a controlled result set, and renders it. The access control complexity is concentrated at the funnel, not distributed across consumers.

Put the constraint where it does the most good. The segment builder is the natural chokepoint. Access control auditable in one place, testable in one place, maintainable in one place.

---

## Same ratchet, different substrate

The segment builder is not an agent system. There's no LLM in the loop. The "explorer" is a human analyst, not a frontier model. The "log" is a query history table, not a conversation JSONL. The "crystallization" is a SQL promotion pipeline, not a bash-to-macro conversion.

But the mechanism is identical.

```{mermaid}
%%{init: {'theme': 'neutral'}}%%
graph LR
    subgraph agent ["Agent Architecture"]
        A1["LLM + Bash"] -->|"explore"| A2["Conversation<br/>Log (JSONL)"]
        A2 -->|"analyze"| A3["DuckDB<br/>Queries"]
        A3 -->|"promote"| A4["Structured<br/>Tool"]
        A4 -->|"apply"| A5["search(pattern,<br/>path)"]
    end

    subgraph segment ["Segment Builder"]
        S1["Analyst +<br/>SQL Editor"] -->|"explore"| S2["Query<br/>Log Table"]
        S2 -->|"analyze"| S3["Promotion<br/>Query"]
        S3 -->|"promote"| S4["Named<br/>Definition"]
        S4 -->|"apply"| S5["churn_risk(<br/>arr, days)"]
    end

    style agent fill:#fff5f5,stroke:#c53030
    style segment fill:#f0fff4,stroke:#276749
```

| Component | Agent architecture | Segment builder |
|---|---|---|
| **Explorer** | LLM with bash access | Analyst with SQL editor |
| **Computation channel** | Arbitrary bash command | Ad-hoc SQL query |
| **Capture** | Conversation log (JSONL) | Query log table |
| **Crystallization** | DuckDB analysis of logs | Promotion query over query log |
| **Artifact** | Structured tool / macro | Named segment definition |
| **Data channel** | `search(pattern, path)` | `churn_risk_enterprise(threshold)` |
| **Application** | Agent calls structured tool | Analyst selects from library |

The two-stage turn doesn't care whether the explorer is carbon or silicon. It cares that there's a high-*ma* process discovering what works, a capture mechanism recording the evidence, and a crystallization step promoting the patterns into specified infrastructure.

The segment builder proves the ratchet generalizes. The substrate is different — SQL instead of bash, human analysts instead of LLMs, financial data instead of codebases. The pattern is the same: exploration produces artifacts, artifacts encode knowledge, knowledge reduces the *ma* required for equivalent future work. The specified base grows. The frontier shrinks to the novel. The system gets more trustworthy with use.

---

Previous: [Closing the Channel](05-closing-the-channel.md) | Next: [The Classification Engine](07-the-classification-engine.md)

For the mechanism: [The Two-Stage Turn](02-the-two-stage-turn.md)
