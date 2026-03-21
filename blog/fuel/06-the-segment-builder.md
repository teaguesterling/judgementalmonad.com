# The Segment Builder

*Every data platform builds this. The ratchet explains why it works.*

---

## The first thing you build

Every data platform, regardless of domain, builds the same thing first: a way to define populations.

UK Biobank calls it the Cohort Builder. NIH's All of Us calls it the Cohort Builder too. Every B2B analytics platform calls it audience segmentation. Every marketing tool calls it list management. Every clinical trial recruitment system calls it eligibility screening.

Strip the branding and the vertical language and you get the same structural pattern:

```
segment(criteria) → entity_set
```

A user defines criteria. The system returns the set of entities that match. The criteria might be demographic filters, behavioral signals, clinical measurements, purchase history, gene variants, or sensor readings. The entities might be patients, customers, genomic samples, devices, or trial participants. The structure is the same.

This post applies the ratchet to that pattern. Same two-stage turn from [Post 2](02-the-two-stage-turn.md). Different substrate. The segment builder is the first of two data platform case studies that show the ratchet isn't specific to agent architecture — it's a property of any system where human judgment navigates complex signals to produce structured outputs.

---

## The computation channel hiding in your segment builder

Here's how segment definition works in practice. An analyst gets a request: "Find patients over 65 with uncontrolled diabetes who haven't been seen in the last six months." The analyst opens a SQL editor and writes:

```sql
SELECT patient_id
FROM patients p
JOIN lab_results l ON p.patient_id = l.patient_id
JOIN encounters e ON p.patient_id = e.patient_id
WHERE p.age > 65
  AND l.test_name = 'HbA1c'
  AND l.value > 9.0
  AND l.sample_date = (
      SELECT max(sample_date) FROM lab_results
      WHERE patient_id = p.patient_id AND test_name = 'HbA1c'
  )
  AND e.encounter_date < current_date - INTERVAL '6 months'
  AND NOT EXISTS (
      SELECT 1 FROM encounters
      WHERE patient_id = p.patient_id
        AND encounter_date >= current_date - INTERVAL '6 months'
  );
```

This query is a computation channel. Arbitrary SQL against the database. The analyst's judgment — knowing which lab test maps to diabetes control, knowing that "most recent" means a correlated subquery, knowing that "haven't been seen" means the absence of an encounter — navigates complex clinical and technical signals to produce a population definition.

The query works. It runs. It returns 2,847 patients. The analyst validates the result, adjusts the HbA1c threshold, runs it again. Eventually the segment is good enough for the downstream use case. The analyst emails the patient IDs to the care management team.

This is Stage 1. Discovery. The analyst explored the data, used trained judgment to translate a clinical concept into a technical definition, iterated until the result made sense. Every step required expertise. Every step was expensive.

Now the same request comes in next month. A different analyst. Same clinical concept — high-risk uncontrolled diabetics who've fallen out of care. The new analyst writes a different query. Maybe they join to a different lab table. Maybe they use a different HbA1c threshold. Maybe they forget the "most recent" constraint and get results contaminated by historical values. Maybe they get it right but spend four hours rediscovering what the first analyst already knew.

This is the ratchet not turning. The knowledge from the first analyst's discovery — which tables to join, which thresholds to use, which edge cases to handle — stayed in the first analyst's head and in a query buried in their SQL history. The organization paid for discovery twice. It will pay again next month.

---

## The two-stage turn on segments

The fix is the same mechanism from [Post 2](02-the-two-stage-turn.md), applied to a different substrate.

### Stage 1: Discovery

The analyst writes ad-hoc SQL. This is the high-*ma* process — trained judgment navigating complex signals. The analyst needs clinical knowledge (what HbA1c means, what threshold indicates poor control), technical knowledge (how the schema is structured, which joins are correct), and domain knowledge (what "fallen out of care" means operationally).

The query log captures everything. Not just the final query, but every iteration — the first attempt, the revised version, the threshold adjustments, the validation queries run alongside. The log is append-only. The analyst's exploration is recorded.

### Stage 2: Crystallization

Common patterns get promoted to validated, named definitions. The analyst's bespoke SQL becomes a parameterized template:

```sql
-- Before: computation channel
SELECT patient_id FROM patients p
JOIN lab_results l ON ...
WHERE p.age > 65 AND l.test_name = 'HbA1c' AND l.value > 9.0 AND ...

-- After: data channel
SELECT * FROM high_risk_diabetic(age_threshold := 65, hba1c_min := 9.0, gap_months := 6);
```

The computation channel closed. The next analyst doesn't need to know which tables to join, which subquery handles "most recent," or which edge cases to watch for. They call a function with named parameters. The function encodes all of that knowledge — type-honestly, backed by an implementation that makes specific commitments about which tables it queries and how it handles edge cases.

Same functionality. Categorically different grade.

---

## The reference insight

Here is the architectural decision most segment builder implementations get wrong.

The segment builder's output should be a **reference** — a segment ID — not raw data. The function doesn't return patient IDs directly. It returns a segment identifier that downstream systems use to request the entity set through the segment builder's own interface.

Why this matters: the segment builder is the natural enforcement point for access control. It's where criteria meet data. It's where the query is constructed and executed. Everything downstream — reports, dashboards, care management workflows, export pipelines — should accept a segment reference and request data through the builder.

This is the co-domain funnel from the framework. The segment builder does deep processing internally — complex joins, clinical logic, threshold evaluation — and produces a narrow output: a segment ID. Downstream tools never construct their own queries against the raw data. They present a segment ID and receive a validated result set, filtered according to the access controls that the segment builder enforces.

The alternative — returning raw patient IDs that downstream tools use to query the database directly — means every downstream tool needs its own access control logic. Every report writer, every export pipeline, every dashboard needs to independently enforce row-level security, column-level restrictions, minimum cell sizes, and audit logging. The access control surface area grows with every downstream consumer.

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

A DuckDB segment builder. This is the schema, the execution interface, the audit log, and the promotion query.

### Schema

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
    parameters JSON,
    result_count INTEGER,
    executed_by VARCHAR NOT NULL,
    executed_at TIMESTAMP DEFAULT current_timestamp,
    execution_ms INTEGER,
    segment_id UUID,              -- NULL for ad-hoc, populated for library calls
    success BOOLEAN DEFAULT true
);

-- Segment results: materialized entity sets, keyed by segment reference
CREATE TABLE segment_results (
    segment_id UUID NOT NULL,
    run_id UUID DEFAULT gen_random_uuid(),
    entity_id VARCHAR NOT NULL,
    computed_at TIMESTAMP DEFAULT current_timestamp,
    FOREIGN KEY (segment_id) REFERENCES segment_definitions(segment_id)
);
```

### Executing a segment

```sql
-- run_segment: the single entry point
-- Takes a segment ID, executes the criteria SQL, logs the run,
-- materializes the result, returns the entity set
CREATE OR REPLACE MACRO run_segment(seg_id) AS TABLE (
    WITH definition AS (
        SELECT criteria_sql, name
        FROM segment_definitions
        WHERE segment_id = seg_id
          AND status = 'validated'
    )
    SELECT entity_id, current_timestamp AS computed_at
    FROM segment_results
    WHERE segment_id = seg_id
      AND run_id = (
          SELECT max(run_id) FROM segment_results
          WHERE segment_id = seg_id
      )
);
```

In practice, segment execution requires dynamic SQL — the `criteria_sql` stored in the definition needs to be evaluated at runtime. DuckDB macros are compile-time constructs, so a real implementation uses a driver script that:

1. Reads the `criteria_sql` from `segment_definitions`
2. Substitutes parameters
3. Executes the query
4. Inserts results into `segment_results`
5. Logs the execution to `query_log`
6. Returns the `run_id` as the reference

```sql
-- Step-by-step segment execution (driver script logic)

-- 1. Fetch the definition
SELECT criteria_sql, parameters
FROM segment_definitions
WHERE segment_id = ?
  AND status = 'validated';

-- 2. Execute the criteria (after parameter substitution)
-- e.g., the stored criteria_sql might be:
--   SELECT patient_id FROM patients p
--   JOIN lab_results l ON p.patient_id = l.patient_id
--   WHERE p.age > $age_threshold
--     AND l.test_name = 'HbA1c' AND l.value > $hba1c_min
--     ...

-- 3. Materialize results
INSERT INTO segment_results (segment_id, run_id, entity_id)
SELECT ?, gen_random_uuid(), patient_id
FROM (<executed criteria SQL>);

-- 4. Log the execution
INSERT INTO query_log (query_sql, query_hash, parameters,
                       result_count, executed_by, segment_id)
SELECT criteria_sql,
       md5(criteria_sql),
       parameters,
       (SELECT count(*) FROM segment_results WHERE run_id = ?),
       current_user,
       ?
FROM segment_definitions
WHERE segment_id = ?;
```

### The promotion query

This is the crystallization engine. Run it against the query log to find ad-hoc queries that should become validated definitions.

```sql
-- Which ad-hoc queries are ratchet candidates?
-- Criteria: run frequently, succeed consistently, not yet promoted
WITH ad_hoc AS (
    SELECT query_hash,
           any_value(query_sql) AS example_sql,
           count(*) AS run_count,
           count(DISTINCT executed_by) AS distinct_users,
           avg(CASE WHEN success THEN 1.0 ELSE 0.0 END) AS success_rate,
           avg(result_count) AS avg_results,
           avg(execution_ms) AS avg_ms,
           min(executed_at) AS first_run,
           max(executed_at) AS last_run
    FROM query_log
    WHERE segment_id IS NULL  -- ad-hoc only, not library calls
    GROUP BY query_hash
)
SELECT query_hash,
       example_sql,
       run_count,
       distinct_users,
       round(success_rate, 2) AS success_rate,
       round(avg_results, 0) AS avg_results,
       round(avg_ms, 0) AS avg_ms,
       last_run - first_run AS active_span,
       CASE
           WHEN run_count >= 5 AND success_rate > 0.8 AND distinct_users >= 2
               THEN 'STRONG: multiple users, high success'
           WHEN run_count >= 10 AND success_rate > 0.8
               THEN 'STRONG: high frequency single user'
           WHEN run_count >= 3 AND success_rate > 0.9
               THEN 'CANDIDATE: emerging pattern'
           ELSE 'WATCH: not enough signal yet'
       END AS recommendation
FROM ad_hoc
WHERE run_count >= 3
ORDER BY run_count * success_rate DESC;
```

The promotion query is itself specified — SQL over structured data, zero trained judgment. A human reviews the candidates, decides which ones to promote, cleans up the SQL, adds parameter names. That review is the judgment step. Everything else is lookup.

### Before and after

The grade drop is visible in the interface:

```sql
-- BEFORE: computation channel
-- The analyst writes this from scratch every time.
-- Requires: clinical knowledge, schema knowledge, SQL expertise
-- Grade: high — arbitrary SQL, full decision surface engaged
SELECT patient_id
FROM patients p
JOIN lab_results l ON p.patient_id = l.patient_id
JOIN encounters e ON p.patient_id = e.patient_id
WHERE p.age > 65
  AND l.test_name = 'HbA1c'
  AND l.value > 9.0
  AND l.sample_date = (
      SELECT max(sample_date) FROM lab_results
      WHERE patient_id = p.patient_id AND test_name = 'HbA1c'
  )
  AND NOT EXISTS (
      SELECT 1 FROM encounters
      WHERE patient_id = p.patient_id
        AND encounter_date >= current_date - INTERVAL '6 months'
  );

-- AFTER: data channel
-- The analyst selects from a library and adjusts parameters.
-- Requires: knowing which segment to pick, choosing thresholds
-- Grade: low — parameterized function, bounded input language
SELECT * FROM run_segment(
    (SELECT segment_id FROM segment_definitions
     WHERE name = 'high_risk_diabetic'
       AND status = 'validated')
);

-- Or with parameter override at the driver level:
-- high_risk_diabetic(age_threshold := 65, hba1c_min := 9.0, gap_months := 6)
```

The before version is a computation channel. The analyst can write anything. The full expressiveness of SQL is engaged. The result depends on the analyst's judgment about schema, thresholds, edge cases, and clinical definitions.

The after version is a data channel. The analyst picks a name and adjusts parameters. The input language is bounded — a segment name and a small set of typed parameters. The clinical knowledge, schema knowledge, and edge case handling are encoded in the definition.

Same result set. The *ma* dropped because the knowledge moved from the analyst's head to the segment definition.

---

## Access control through the funnel

The segment builder, with the reference pattern, becomes the single enforcement point for data access. All access control logic lives in one place.

**Row-level security.** The segment definition determines which entities are in the result set. The criteria SQL is the row filter. Downstream tools never construct their own filters — they present a segment ID and get back the entities that the definition includes and the requesting user is authorized to see.

**Column-level security.** The segment builder controls which fields appear in the result set. A research user might get `patient_id, age_group, hba1c_category` — de-identified, bucketed. A clinical user might get `patient_id, full_name, phone_number, hba1c_value` — identified, precise. Same segment definition, different column projections based on the requesting role.

**Aggregation controls.** Minimum cell sizes, suppression rules, noise injection — the statistical disclosure controls that health data and research data require. The segment builder applies these before returning results. Downstream tools receive already-controlled data.

**Audit.** Every segment execution is logged. Who requested it, when, which definition, which parameters, how many results. The audit trail is complete because all access flows through one point.

```sql
-- Access control enforcement at the segment builder level
CREATE TABLE access_policies (
    policy_id UUID DEFAULT gen_random_uuid(),
    role VARCHAR NOT NULL,
    segment_pattern VARCHAR,          -- which segments this role can run
    allowed_columns VARCHAR[] NOT NULL, -- which columns to return
    min_cell_size INTEGER DEFAULT 1,  -- minimum count for aggregations
    require_approval BOOLEAN DEFAULT false,
    PRIMARY KEY (policy_id)
);

-- The segment builder checks policy before returning results
-- (pseudocode for the driver script)
--
-- 1. Look up policy for (requesting_role, segment_id)
-- 2. If require_approval, check approval table
-- 3. Execute criteria SQL
-- 4. Filter columns to allowed_columns
-- 5. Apply min_cell_size suppression
-- 6. Log to query_log with role and policy_id
-- 7. Return filtered, controlled result set
```

The co-domain funnel means downstream tools are simpler. A dashboard that displays segment results doesn't need access control logic. It presents a segment ID, receives a controlled result set, and renders it. The access control complexity is concentrated at the funnel, not distributed across consumers.

This is the same architectural insight from the framework: put the constraint where it does the most good. The segment builder is the natural chokepoint. Making it the enforcement point means access control is auditable in one place, testable in one place, and maintainable in one place.

---

## Same ratchet, different substrate

The segment builder is not an agent system. There's no LLM in the loop. The "explorer" is a human analyst, not a frontier model. The "log" is a query history table, not a conversation JSONL. The "crystallization" is a SQL promotion pipeline, not a bash-to-macro conversion.

But the mechanism is identical.

| Component | Agent architecture | Segment builder |
|---|---|---|
| **Explorer** | LLM with bash access | Analyst with SQL editor |
| **Computation channel** | Arbitrary bash command | Ad-hoc SQL query |
| **Capture** | Conversation log (JSONL) | Query log table |
| **Crystallization** | DuckDB analysis of logs | Promotion query over query log |
| **Artifact** | Structured tool / macro | Named segment definition |
| **Data channel** | `search(pattern, path)` | `high_risk_diabetic(threshold)` |
| **Application** | Agent calls structured tool | Analyst selects from library |

The two-stage turn doesn't care whether the explorer is carbon or silicon. It cares that there's a high-*ma* process discovering what works, a capture mechanism recording the evidence, and a crystallization step promoting the patterns into specified infrastructure.

The segment builder proves the ratchet generalizes. The substrate is different — SQL instead of bash, human analysts instead of LLMs, clinical data instead of codebases. The pattern is the same: exploration produces artifacts, artifacts encode knowledge, knowledge reduces the *ma* required for equivalent future work. The specified base grows. The frontier shrinks to the novel. The system gets more trustworthy with use.

---

Previous: [Closing the Channel](05-closing-the-channel.md) | Next: [The Classification Engine](07-the-classification-engine.md)

For the mechanism: [The Two-Stage Turn](02-the-two-stage-turn.md)
