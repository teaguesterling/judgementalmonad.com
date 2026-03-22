-- tool_gaps.sql — Compare bash usage against all structured tools in use.
-- No hardcoded tool names — discovers what's available from the logs.

WITH bash_by_category AS (
    SELECT category, count(*) AS bash_calls
    FROM bash_commands()
    GROUP BY category
),
all_structured AS (
    SELECT tool_name, count(*) AS calls
    FROM tool_calls()
    WHERE tool_name NOT IN ('Bash', 'bash')
    GROUP BY tool_name
),
-- Map structured tools to the bash categories they replace
-- based on functional equivalence
tool_category_map AS (
    SELECT tool_name, calls,
        CASE
            WHEN tool_name IN ('Grep', 'grep') THEN 'file_search'
            WHEN tool_name IN ('Glob', 'glob') THEN 'file_search'
            WHEN tool_name IN ('Read', 'read', 'file_read') THEN 'file_read'
            WHEN tool_name IN ('Write', 'write', 'file_write') THEN 'filesystem'
            WHEN tool_name IN ('Edit', 'edit') THEN 'filesystem'
            ELSE NULL  -- MCP tools and others don't map to bash categories
        END AS replaces_category
    FROM all_structured
)
SELECT
    bc.category AS bash_category,
    bc.bash_calls,
    COALESCE(sum(tcm.calls), 0) AS structured_calls,
    CASE
        WHEN COALESCE(sum(tcm.calls), 0) = 0 THEN 0.0
        ELSE round(100.0 * sum(tcm.calls)
            / (bc.bash_calls + sum(tcm.calls)), 1)
    END AS adoption_pct,
    CASE
        WHEN COALESCE(sum(tcm.calls), 0) = 0
            THEN 'OPEN: no structured alternative detected'
        WHEN sum(tcm.calls) < bc.bash_calls
            THEN 'PARTIAL: structured tools exist but Bash dominates'
        ELSE 'ADOPTED: structured tools are primary'
    END AS status,
    string_agg(DISTINCT tcm.tool_name, ', ')
        FILTER (WHERE tcm.tool_name IS NOT NULL) AS structured_tools
FROM bash_by_category bc
LEFT JOIN tool_category_map tcm ON bc.category = tcm.replaces_category
GROUP BY bc.category, bc.bash_calls
ORDER BY bc.bash_calls DESC;
