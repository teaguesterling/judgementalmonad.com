-- schema.sql — Minimal conversation log parsing for ratchet detection.
-- Ported from Fledgling's conversations.sql. No extension dependencies.
--
-- Requires: $conversations_glob variable set to a JSONL glob pattern.

CREATE OR REPLACE TABLE raw_conversations AS
SELECT *, filename AS _source_file
FROM read_json_auto(
    getvariable('conversations_glob'),
    union_by_name=true,
    maximum_object_size=33554432,
    filename=true,
    ignore_errors=true
);

-- Content blocks: unnest assistant message content arrays into rows
CREATE OR REPLACE MACRO content_blocks() AS TABLE
    WITH array_messages AS (
        SELECT uuid, sessionId, slug, timestamp, requestId, message, _source_file
        FROM raw_conversations
        WHERE type = 'assistant'
          AND message.content IS NOT NULL
          AND json_type(message.content) = 'ARRAY'
    )
    SELECT
        r.uuid AS message_id,
        r.sessionId AS session_id,
        r.slug,
        r.timestamp AS created_at,
        r.message.model AS model,
        b.block ->> 'type' AS block_type,
        b.block ->> 'name' AS tool_name,
        b.block ->> 'id' AS tool_use_id,
        b.block -> 'input' AS tool_input,
        r._source_file AS source_file
    FROM array_messages r,
         LATERAL UNNEST(CAST(r.message.content AS JSON[])) AS b(block);

-- Tool calls: extracted tool_use blocks with convenience columns
CREATE OR REPLACE MACRO tool_calls() AS TABLE
    SELECT
        cb.tool_use_id, cb.message_id, cb.session_id,
        cb.slug, cb.model, cb.created_at, cb.tool_name,
        cb.tool_input AS input,
        cb.tool_input ->> 'command' AS bash_command,
        COALESCE(cb.tool_input ->> 'file_path', cb.tool_input ->> 'path') AS file_path,
        cb.tool_input ->> 'pattern' AS grep_pattern,
        cb.source_file
    FROM content_blocks() cb
    WHERE cb.block_type = 'tool_use';

-- Tool results: matched tool_result blocks from user messages
CREATE OR REPLACE MACRO tool_results() AS TABLE
    WITH user_array_messages AS (
        SELECT uuid, sessionId, timestamp, message, _source_file
        FROM raw_conversations
        WHERE type = 'user'
          AND message.content IS NOT NULL
          AND json_type(message.content) = 'ARRAY'
    )
    SELECT
        r.uuid AS message_id,
        r.sessionId AS session_id,
        r.timestamp AS created_at,
        b.block ->> 'tool_use_id' AS tool_use_id,
        b.block ->> 'content' AS result_content,
        CAST(b.block ->> 'is_error' AS BOOLEAN) AS is_error,
        r._source_file AS source_file
    FROM user_array_messages r,
         LATERAL UNNEST(CAST(r.message.content AS JSON[])) AS b(block)
    WHERE b.block ->> 'type' = 'tool_result';

-- Bash commands: parsed with categories and replacement candidates
CREATE OR REPLACE MACRO bash_commands() AS TABLE
    SELECT
        tc.tool_use_id, tc.session_id, tc.created_at,
        tc.bash_command AS command,
        regexp_extract(trim(tc.bash_command), '^(\S+)', 1) AS leading_command,
        CASE WHEN trim(tc.bash_command) LIKE 'git %'
             THEN regexp_extract(trim(tc.bash_command), '^git\s+(\S+)', 1)
             ELSE NULL END AS git_subcommand,
        CASE WHEN trim(tc.bash_command) LIKE 'gh %'
             THEN regexp_extract(trim(tc.bash_command), '^gh\s+(\S+\s*\S*)', 1)
             ELSE NULL END AS gh_subcommand,
        CASE
            WHEN trim(tc.bash_command) LIKE 'git diff%'
              OR trim(tc.bash_command) LIKE 'git log%'
              OR trim(tc.bash_command) LIKE 'git status%'
              OR trim(tc.bash_command) LIKE 'git show%'
              OR trim(tc.bash_command) LIKE 'git rev-parse%'
              OR trim(tc.bash_command) LIKE 'git branch%'
              OR trim(tc.bash_command) LIKE 'git remote%'
              OR trim(tc.bash_command) LIKE 'git config%' THEN 'git_read'
            WHEN trim(tc.bash_command) LIKE 'git %' THEN 'git_write'
            WHEN trim(tc.bash_command) LIKE 'gh %' THEN 'github_cli'
            WHEN trim(tc.bash_command) LIKE 'cargo %'
              OR trim(tc.bash_command) LIKE 'make%'
              OR trim(tc.bash_command) LIKE 'npm %'
              OR trim(tc.bash_command) LIKE 'pip %'
              OR trim(tc.bash_command) LIKE 'uv %' THEN 'build_tools'
            WHEN trim(tc.bash_command) LIKE 'python%'
              OR trim(tc.bash_command) LIKE 'node %'
              OR trim(tc.bash_command) LIKE 'duckdb%' THEN 'runtime_exec'
            WHEN trim(tc.bash_command) LIKE 'grep %'
              OR trim(tc.bash_command) LIKE 'rg %'
              OR trim(tc.bash_command) LIKE 'find %'
              OR trim(tc.bash_command) LIKE 'fd %' THEN 'file_search'
            WHEN trim(tc.bash_command) LIKE 'cat %'
              OR trim(tc.bash_command) LIKE 'head %'
              OR trim(tc.bash_command) LIKE 'tail %' THEN 'file_read'
            WHEN trim(tc.bash_command) LIKE 'ls%'
              OR trim(tc.bash_command) LIKE 'mkdir%'
              OR trim(tc.bash_command) LIKE 'rm %'
              OR trim(tc.bash_command) LIKE 'cp %'
              OR trim(tc.bash_command) LIKE 'mv %' THEN 'filesystem'
            WHEN trim(tc.bash_command) LIKE 'wc %'
              OR trim(tc.bash_command) LIKE 'sort %'
              OR trim(tc.bash_command) LIKE 'awk %'
              OR trim(tc.bash_command) LIKE 'jq %' THEN 'text_processing'
            WHEN trim(tc.bash_command) LIKE 'curl %'
              OR trim(tc.bash_command) LIKE 'wget %' THEN 'network'
            ELSE 'other'
        END AS category,
        tc.source_file
    FROM tool_calls() tc
    WHERE tc.tool_name = 'Bash' AND tc.bash_command IS NOT NULL;
