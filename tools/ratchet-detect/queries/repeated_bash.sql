-- repeated_bash.sql — Find bash commands worth promoting to structured tools.
-- Ranked by frequency * success_rate (ratchet score).

WITH bash_with_results AS (
    SELECT bc.*, tr.is_error
    FROM bash_commands() bc
    LEFT JOIN tool_results() tr ON bc.tool_use_id = tr.tool_use_id
)
SELECT
    leading_command AS command,
    category,
    count(*) AS calls,
    round(100.0 * count(*) FILTER (WHERE NOT COALESCE(is_error, false))
        / count(*), 1) AS success_pct,
    count(DISTINCT session_id) AS sessions,
    mode(command) AS example
FROM bash_with_results
GROUP BY leading_command, category
HAVING count(*) >= 3
ORDER BY count(*) * count(*) FILTER (WHERE NOT COALESCE(is_error, false)) / count(*) DESC;
