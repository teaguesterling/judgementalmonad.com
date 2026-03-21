-- search.sql — DuckDB structured codebase search macro.
--
-- Replaces: Bash("grep -r pattern path")
-- Requires: codebase table indexed from filesystem.
--
-- From Ratchet Fuel Post 5: Closing the Channel
-- https://judgementalmonad.com/blog/fuel/05-closing-the-channel

-- Index the codebase into a DuckDB table.
-- Uses read_text() to read all source files, then splits into lines.
-- Run this once, or after significant codebase changes.
CREATE OR REPLACE TABLE codebase AS
WITH raw_files AS (
    SELECT filename as file_path,
           content
    FROM read_text('src/**/*.py')
),
lines AS (
    SELECT file_path,
           unnest(generate_series(1, length(content) - length(replace(content, chr(10), '')) + 1)) as line_number,
           unnest(string_split(content, chr(10))) as line_content
    FROM raw_files
)
SELECT file_path, line_number, line_content
FROM lines
WHERE length(trim(line_content)) > 0;

-- The structured search macro.
-- Input: regex pattern + path prefix.
-- Output: matching lines with file path and line number.
-- Level 1 data channel: known input language, known effects, bounded output.
CREATE OR REPLACE MACRO search(search_pattern, search_path) AS TABLE
    SELECT file_path,
           line_number,
           line_content
    FROM codebase
    WHERE regexp_matches(line_content, search_pattern)
      AND file_path LIKE (search_path || '%')
    ORDER BY file_path, line_number
    LIMIT 200;

-- Usage:
-- FROM search('def test_', 'src/tests/');
-- FROM search('class.*Error', 'src/');
-- FROM search('import re', '');
