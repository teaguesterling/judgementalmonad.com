# Experiment MCP Server

Serves condition-specific tool sets for the Ma framework experimental program. The agent connects to this server and only sees the tools appropriate for its experimental condition. Tools not in the condition don't exist in the agent's tool registry — no denials, no honor system.

## Conditions

| Condition | Tools available | Computation level | Use in experiments |
|-----------|----------------|------------------|--------------------|
| A | file_read, file_search, file_glob, file_list, file_edit, file_write | 0-2 (data channels only) | Exp 3 baseline, Exp 1 Low-D |
| B | Everything in A + bash_readonly | 2-3 (read-only bash) | Exp 3 mid-level |
| C | Everything in A + bash_sandboxed | 4 (computation channel) | Exp 3 high-level, Exp 1 High-D |

For Experiment 1's Low-W conditions, use `--allowed-dirs` to restrict file access to specific paths.

## Usage

### Direct

```bash
python3 server.py --condition A --task-id 01 --log-dir ./logs --workspace /path/to/worktree
```

### Via .mcp.json

Each condition has a pre-configured `.mcp.json` in `experiments/conditions/condition-{a,b,c}/`. Start a Claude Code session from that directory and the experiment server is automatically available.

```bash
cd experiments/conditions/condition-a
TASK_ID=01 WORKSPACE=/path/to/worktree claude
```

### For Experiment 1 (Low W — restricted file access)

```bash
python3 server.py --condition A --task-id 01 --log-dir ./logs \
  --workspace /path/to/repo --allowed-dirs src/module.py src/utils.py tests/test_module.py
```

## What it logs

Every tool call is logged to `{log-dir}/task-{id}-condition-{X}.jsonl`. Each line is a JSON object:

```json
{
  "timestamp": "2026-03-15T...",
  "task_id": "01",
  "condition": "A",
  "tool": "file_read",
  "arguments": {"path": "src/main.py"},
  "result_preview": "     1\timport sys...",
  "success": true,
  "duration_ms": 12.3,
  "sequence_number": 0
}
```

This JSONL format is queryable by DuckDB:

```sql
SELECT tool, count(*) as calls, avg(duration_ms) as avg_ms
FROM read_json_auto('logs/task-01-condition-A.jsonl')
GROUP BY tool ORDER BY calls DESC;
```

## Sandbox diffing

If the workspace has a `.git` directory, the server auto-commits after every file-modifying tool call (file_edit, file_write, bash_sandboxed). This produces a git history queryable by duck_tails.

## Security notes

- bash_readonly rejects shell metacharacters (`;`, `|`, `&`, `` ` ``, `$`, `(`, `)`, `>`, `<`, newlines) before checking the allowlist
- bash_sandboxed sets cwd to workspace but does NOT use a hard sandbox (no bubblewrap/firejail). This is sufficient for the experiment (testing computation channel dynamics) but NOT for adversarial security testing.
- Workspace path escaping is checked on all file operations
