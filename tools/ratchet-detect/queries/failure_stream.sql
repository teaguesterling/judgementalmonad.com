-- failure_stream.sql — Classify failures by category.

WITH errors AS (
    SELECT
        tc.tool_name,
        tc.bash_command,
        tc.session_id,
        left(tr.result_content, 300) AS error_text
    FROM tool_calls() tc
    JOIN tool_results() tr ON tc.tool_use_id = tr.tool_use_id
    WHERE tr.is_error = true
)
SELECT
    CASE
        WHEN error_text ILIKE '%permission denied%'
          OR error_text ILIKE '%EACCES%'
          OR error_text ILIKE '%not permitted%' THEN 'permission_denied'
        WHEN error_text ILIKE '%command not found%' THEN 'command_not_found'
        WHEN error_text ILIKE '%no such file%'
          OR error_text ILIKE '%not found%' THEN 'not_found'
        WHEN error_text ILIKE '%timed out%'
          OR error_text ILIKE '%timeout%' THEN 'timeout'
        WHEN error_text ILIKE '%CONFLICT%' THEN 'merge_conflict'
        WHEN error_text ILIKE '%rejected%' THEN 'push_rejected'
        WHEN error_text ILIKE '%hook%' THEN 'hook_blocked'
        WHEN error_text ILIKE '%Sibling tool call errored%' THEN 'sibling_error'
        ELSE 'other'
    END AS category,
    tool_name,
    count(*) AS occurrences,
    count(DISTINCT session_id) AS sessions,
    mode(error_text) AS example
FROM errors
GROUP BY 1, 2
ORDER BY occurrences DESC;
