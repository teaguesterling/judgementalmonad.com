-- ratchet_dashboard.sql — DuckDB queries for the six ratchet metrics.
--
-- Assumes:
--   - tool_calls view (from conversation logs, see Post 1)
--   - tool_promotions table (tracks Stage 2 promotions)
--   - mode_transitions table (logs mode changes)
--   - observer_checks table (logs review-mode verifications)
--   - query_log table (for data platform self-service ratio)
--
-- From Ratchet Fuel Post 10: Ratchet Metrics
-- https://judgementalmonad.com/blog/fuel/10-ratchet-metrics

-- ============================================================
-- SCHEMA (tracking tables — create these in your project)
-- ============================================================

CREATE TABLE IF NOT EXISTS tool_promotions (
    promotion_id INTEGER PRIMARY KEY,
    pattern_description VARCHAR,
    tool_name VARCHAR,
    promoted_at TIMESTAMP,
    source_frequency INTEGER,
    source_success_rate DOUBLE
);

CREATE TABLE IF NOT EXISTS mode_transitions (
    transition_id INTEGER PRIMARY KEY,
    session_id VARCHAR,
    from_mode VARCHAR,
    to_mode VARCHAR,
    triggered_by VARCHAR,
    transitioned_at TIMESTAMP,
    duration_ms BIGINT
);

CREATE TABLE IF NOT EXISTS observer_checks (
    check_id INTEGER PRIMARY KEY,
    session_id VARCHAR,
    check_type VARCHAR,       -- 'file_diff', 'test_run', 'schema_compare'
    agent_claim VARCHAR,
    observed_result VARCHAR,
    divergence BOOLEAN,
    checked_at TIMESTAMP
);

-- ============================================================
-- METRIC 1: Ratchet rate
-- ============================================================

CREATE OR REPLACE MACRO ratchet_rate() AS TABLE
    SELECT date_trunc('week', promoted_at) as week,
           count(*) as promotions,
           round(avg(source_frequency), 0) as avg_pattern_frequency,
           round(avg(source_success_rate), 2) as avg_source_success_rate
    FROM tool_promotions
    GROUP BY 1
    ORDER BY 1;

-- ============================================================
-- METRIC 2: Trust gap — boundary hit rate and observer gap
-- ============================================================

CREATE OR REPLACE MACRO observer_gap_rate() AS TABLE
    SELECT date_trunc('week', checked_at) as week,
           check_type,
           count(*) as total_checks,
           sum(CASE WHEN divergence THEN 1 ELSE 0 END) as divergences,
           round(100.0 * sum(CASE WHEN divergence THEN 1 ELSE 0 END) /
               count(*), 1) as divergence_rate_pct
    FROM observer_checks
    GROUP BY 1, 2
    ORDER BY 1, check_type;

-- ============================================================
-- METRIC 3: Failure stream composition
-- ============================================================

-- Note: uses simplified tool_calls schema.
-- Adapt column names for your actual log format.
-- CREATE OR REPLACE MACRO failure_composition() AS TABLE
--     WITH classified AS (
--         SELECT timestamp,
--                CASE
--                    WHEN NOT success AND result ILIKE '%permission%denied%'
--                        THEN 'permission_denial'
--                    WHEN NOT success AND duration_ms > 30000
--                        THEN 'timeout'
--                    WHEN NOT success
--                        THEN 'other_failure'
--                    ELSE 'success'
--                END as category
--         FROM tool_calls
--     )
--     SELECT date_trunc('week', timestamp) as week,
--            category,
--            count(*) as count,
--            round(100.0 * count(*) /
--                sum(count(*)) OVER (PARTITION BY date_trunc('week', timestamp)),
--                1) as pct
--     FROM classified
--     GROUP BY 1, 2
--     ORDER BY 1, count DESC;

-- ============================================================
-- METRIC 4: Mode utilization
-- ============================================================

CREATE OR REPLACE MACRO mode_utilization() AS TABLE
    SELECT to_mode as mode,
           count(*) as transitions_into,
           round(sum(duration_ms) / 1000.0, 1) as total_seconds,
           round(100.0 * sum(duration_ms) /
               sum(sum(duration_ms)) OVER (),
               1) as pct_of_total,
           round(avg(duration_ms) / 1000.0, 1) as avg_seconds_per_stay
    FROM mode_transitions
    WHERE duration_ms IS NOT NULL
    GROUP BY 1
    ORDER BY total_seconds DESC;

-- ============================================================
-- METRIC 5: Computation channel fraction
-- ============================================================

-- Note: adapt tool name lists for your actual tool set.
-- CREATE OR REPLACE MACRO computation_fraction() AS TABLE
--     WITH classified AS (
--         SELECT date_trunc('week', timestamp) as week,
--                CASE
--                    WHEN tool IN ('Bash', 'bash') THEN 'computation'
--                    ELSE 'data'
--                END as channel_type
--         FROM tool_calls
--     )
--     SELECT week, channel_type,
--            count(*) as calls,
--            round(100.0 * count(*) /
--                sum(count(*)) OVER (PARTITION BY week),
--                1) as pct
--     FROM classified
--     GROUP BY 1, 2
--     ORDER BY 1, channel_type;

-- ============================================================
-- METRIC 6: Self-service ratio (data platforms)
-- ============================================================

-- Requires query_log table with query_type column.
-- CREATE OR REPLACE MACRO self_service_ratio() AS TABLE
--     SELECT date_trunc('month', executed_at) as month,
--            count(*) FILTER (WHERE query_type = 'validated') as validated,
--            count(*) FILTER (WHERE query_type = 'ad_hoc') as ad_hoc,
--            round(100.0 * count(*) FILTER (WHERE query_type = 'validated') /
--                count(*), 1) as self_service_pct
--     FROM query_log
--     GROUP BY 1
--     ORDER BY 1;
