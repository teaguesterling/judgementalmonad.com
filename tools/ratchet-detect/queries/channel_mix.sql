-- channel_mix.sql — Computation channel vs data channel breakdown.

SELECT
    CASE
        WHEN tool_name IN ('Bash', 'bash') THEN 'computation'
        ELSE 'data'
    END AS channel_type,
    count(*) AS calls,
    round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM tool_calls()
GROUP BY 1
ORDER BY calls DESC;
