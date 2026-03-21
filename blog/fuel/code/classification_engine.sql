-- classification_engine.sql — DuckDB access control layer.
--
-- Field classification, role-based access tiers, audit logging,
-- and promotion queries for crystallizing access rules.
--
-- From Ratchet Fuel Post 7: The Classification Engine
-- https://judgementalmonad.com/blog/fuel/07-the-classification-engine

-- ============================================================
-- SCHEMA
-- ============================================================

CREATE TABLE IF NOT EXISTS field_classifications (
    table_name VARCHAR NOT NULL,
    field_name VARCHAR NOT NULL,
    sensitivity_level VARCHAR NOT NULL,  -- 'public', 'internal', 'confidential', 'restricted'
    classification_reason VARCHAR,
    classified_by VARCHAR,
    classified_at TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (table_name, field_name)
);

CREATE TABLE IF NOT EXISTS role_access_tiers (
    role VARCHAR NOT NULL PRIMARY KEY,
    max_sensitivity VARCHAR NOT NULL,
    can_access_individual_records BOOLEAN DEFAULT true,
    min_aggregation_threshold INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sensitivity_ordering (
    level VARCHAR PRIMARY KEY,
    rank INTEGER NOT NULL UNIQUE
);

INSERT OR IGNORE INTO sensitivity_ordering VALUES
    ('public', 1),
    ('internal', 2),
    ('confidential', 3),
    ('restricted', 4);

CREATE TABLE IF NOT EXISTS access_audit_log (
    request_id VARCHAR DEFAULT gen_random_uuid()::VARCHAR,
    query_hash VARCHAR,
    role VARCHAR NOT NULL,
    requested_table VARCHAR NOT NULL,
    fields_accessed VARCHAR[] NOT NULL,
    justification VARCHAR,
    outcome VARCHAR NOT NULL,  -- 'approved', 'denied', 'auto_approved'
    reviewed_by VARCHAR,
    ts TIMESTAMP DEFAULT current_timestamp
);

-- ============================================================
-- BOOTSTRAP: classify all fields as 'internal' by default
-- ============================================================

-- INSERT INTO field_classifications (table_name, field_name, sensitivity_level, classification_reason)
-- SELECT table_name, column_name, 'internal', 'Default — awaiting review'
-- FROM information_schema.columns
-- WHERE table_schema = 'main'
--   AND table_name NOT IN ('field_classifications', 'role_access_tiers',
--                          'sensitivity_ordering', 'access_audit_log');

-- Then promote known-sensitive fields:
-- PCI DSS cardholder data
-- UPDATE field_classifications
-- SET sensitivity_level = 'restricted',
--     classification_reason = 'PCI DSS — cardholder data'
-- WHERE field_name IN ('card_number', 'cvv', 'card_expiry', 'pan');

-- Financial PII
-- UPDATE field_classifications
-- SET sensitivity_level = 'confidential',
--     classification_reason = 'Financial PII'
-- WHERE field_name IN ('ssn', 'tax_id', 'bank_account', 'routing_number');

-- ============================================================
-- FIELD ACCESS QUERY: determine visibility per role
-- ============================================================

-- For a given role and table, returns each field with its access action:
--   'visible'  — field appears as-is in the role's view
--   'masked'   — field appears hashed (one level above ceiling)
--   'excluded' — field does not appear (two+ levels above ceiling)
CREATE OR REPLACE MACRO field_access(target_role, target_table) AS TABLE
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
        ON rat.role = target_role
    JOIN sensitivity_ordering so_role
        ON rat.max_sensitivity = so_role.level
    WHERE fc.table_name = target_table;

-- ============================================================
-- PROMOTION QUERY: find access patterns worth crystallizing
-- ============================================================

CREATE OR REPLACE MACRO access_promotion_candidates() AS TABLE
    SELECT
        role,
        requested_table,
        fields_accessed,
        count(*) AS frequency,
        count(*) FILTER (WHERE outcome = 'approved') AS approvals,
        count(*) FILTER (WHERE outcome = 'denied') AS denials,
        round(
            count(*) FILTER (WHERE outcome = 'approved') * 100.0 / count(*), 1
        ) AS approval_rate_pct,
        CASE
            WHEN count(*) FILTER (WHERE outcome = 'denied') = count(*)
                THEN 'AUTO-DENY: always denied — remove from view'
            WHEN count(*) FILTER (WHERE outcome = 'approved') = count(*)
                AND count(*) >= 10
                THEN 'AUTO-APPROVE: always approved — add to view'
            WHEN count(*) >= 5
                THEN 'REVIEW: mixed outcomes — needs policy clarification'
            ELSE 'WATCH: not enough data'
        END AS recommendation
    FROM access_audit_log
    WHERE ts >= current_timestamp - INTERVAL '90 days'
    GROUP BY role, requested_table, fields_accessed
    HAVING count(*) >= 5
    ORDER BY frequency DESC;

-- ============================================================
-- EXAMPLE ROLES
-- ============================================================

-- INSERT INTO role_access_tiers VALUES
--     ('marketing_ops', 'internal', true, 0),
--     ('finance_analyst', 'confidential', true, 0),
--     ('external_auditor', 'internal', false, 5),
--     ('compliance_officer', 'restricted', true, 0);
