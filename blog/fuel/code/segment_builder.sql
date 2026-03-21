-- segment_builder.sql — DuckDB segment builder with promotion pipeline.
--
-- Three tables (definitions, query log, results), execution logic,
-- promotion query, and access control enforcement.
--
-- From Ratchet Fuel Post 6: The Segment Builder
-- https://judgementalmonad.com/blog/fuel/06-the-segment-builder

-- ============================================================
-- SCHEMA
-- ============================================================

-- Segment definitions: the library of validated segments
CREATE TABLE IF NOT EXISTS segment_definitions (
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
CREATE TABLE IF NOT EXISTS query_log (
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
CREATE TABLE IF NOT EXISTS segment_results (
    segment_id UUID NOT NULL,
    run_id UUID DEFAULT gen_random_uuid(),
    entity_id VARCHAR NOT NULL,
    computed_at TIMESTAMP DEFAULT current_timestamp,
    FOREIGN KEY (segment_id) REFERENCES segment_definitions(segment_id)
);

-- Access policies: role-based access control at the segment builder level
CREATE TABLE IF NOT EXISTS access_policies (
    policy_id UUID DEFAULT gen_random_uuid(),
    role VARCHAR NOT NULL,
    segment_pattern VARCHAR,          -- which segments this role can run (LIKE pattern)
    allowed_columns VARCHAR[] NOT NULL, -- which columns to include in results
    min_cell_size INTEGER DEFAULT 1,  -- minimum count for aggregation suppression
    require_approval BOOLEAN DEFAULT false,
    PRIMARY KEY (policy_id)
);

-- ============================================================
-- EXECUTION
-- ============================================================

-- run_segment: retrieve the most recent materialized result set
-- for a validated segment definition.
--
-- In practice, segment execution requires dynamic SQL:
--   1. Read criteria_sql from segment_definitions
--   2. Substitute parameters
--   3. Execute the query
--   4. Insert results into segment_results with a new run_id
--   5. Log the execution to query_log
--   6. Return the run_id as the reference
--
-- DuckDB macros are compile-time constructs, so the dynamic
-- execution step requires a driver script (Python, shell, etc.).
-- This macro retrieves the latest materialized results.
CREATE OR REPLACE MACRO run_segment(seg_id) AS TABLE (
    SELECT entity_id, computed_at
    FROM segment_results
    WHERE segment_id = seg_id
      AND run_id = (
          SELECT max(run_id) FROM segment_results
          WHERE segment_id = seg_id
      )
);

-- ============================================================
-- PROMOTION QUERY (the crystallization engine)
-- ============================================================

-- Find ad-hoc queries that should become validated definitions.
-- Criteria: run frequently, succeed consistently, not yet promoted.
-- A human reviews the candidates and decides which to promote.
CREATE OR REPLACE MACRO promotion_candidates() AS TABLE (
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
    ORDER BY run_count * success_rate DESC
);

-- ============================================================
-- ACCESS CONTROL ENFORCEMENT (pseudocode for driver script)
-- ============================================================

-- The segment builder checks policy before returning results:
--
-- 1. Look up policy for (requesting_role, segment_name)
--    SELECT * FROM access_policies
--    WHERE role = $requesting_role
--      AND $segment_name LIKE segment_pattern;
--
-- 2. If require_approval, check approval table
--
-- 3. Execute criteria SQL
--
-- 4. Filter columns to allowed_columns
--    SELECT {allowed_columns} FROM (<criteria results>)
--
-- 5. Apply min_cell_size suppression
--    -- For aggregation queries, suppress groups with count < min_cell_size
--
-- 6. Log to query_log with role and policy_id
--
-- 7. Return filtered, controlled result set

-- ============================================================
-- EXAMPLE: Creating a segment definition
-- ============================================================

-- Promote an ad-hoc query to a validated definition:
-- INSERT INTO segment_definitions (name, description, criteria_sql, parameters, created_by, status)
-- VALUES (
--     'churn_risk_enterprise',
--     'Enterprise accounts with high ARR, inactive for N days, with recent escalations',
--     'SELECT a.account_id FROM accounts a
--      JOIN subscriptions s ON a.account_id = s.account_id
--      JOIN activity_log al ON a.account_id = al.account_id
--      JOIN support_tickets st ON a.account_id = st.account_id
--      WHERE s.arr > $arr_min
--        AND s.plan_type = ''enterprise''
--        AND s.status = ''active''
--        AND al.last_login < current_date - INTERVAL ''$inactive_days days''
--        AND st.severity IN (''high'', ''critical'')
--        AND st.created_at >= current_date - INTERVAL ''$escalation_window days''',
--     '{"arr_min": {"type": "integer", "default": 100000},
--       "inactive_days": {"type": "integer", "default": 90},
--       "escalation_window": {"type": "integer", "default": 90}}',
--     'analyst_1',
--     'validated'
-- );
