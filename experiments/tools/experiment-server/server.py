"""
Experiment MCP Server for The Ma of Multi-Agent Systems

Serves different tool sets based on the experimental condition (A, B, or C).
Logs every tool call for the specified observer and gap rate computation.

Conditions:
  A (data-channel):   File tools only. No bash. Levels 0-2.
  B (readonly):       File tools + read-only bash. Levels 2-3.
  C (computation):    File tools + sandboxed bash (read-write). Level 4.

Usage:
  python server.py --condition A --task-id 01 --log-dir ./logs
  python server.py --condition B --task-id 01 --log-dir ./logs --workspace /path/to/worktree

The server exposes only the tools appropriate for the condition.
Tools not in the condition simply don't exist in the agent's tool registry.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONDITION_TOOLS = {
    # Original conditions (A-C)
    "A": {"file_tools", "run_tests"},                          # Structured tools only
    "B": {"file_tools", "run_tests", "bash_readonly"},         # + exploration
    "C": {"file_tools", "run_tests", "bash_sandboxed"},        # Everything
    # Factorial conditions (D-F): isolate each capability's contribution
    "D": {"bash_sandboxed"},                                   # Bash only
    "E": {"file_tools", "bash_sandboxed"},                     # File tools + bash, no run_tests
    "F": {"run_tests", "bash_sandboxed"},                      # run_tests + bash, no file tools
    # Minimal conditions (J+): reduced tool set for weaker models
    "J": {"batch_tools", "run_tests"},                         # Batch-only file tools + run_tests
    "K": {"simple_tools", "run_tests"},                        # Simple file tools only + run_tests
    # Semantic conditions: AST-aware tools via sitting_duck/DuckDB
    "L": {"simple_tools", "run_tests", "semantic_tools"},      # Simple tools + semantic + run_tests
}

# Tools are tagged by capability group:
#   "file_tools"     - file_read, file_search, file_glob, file_list, file_edit,
#                      file_edit_batch, file_write, file_read_batch,
#                      file_search_context, file_count
#   "run_tests"      - run_tests (structured pytest wrapper)
#   "bash_readonly"  - bash_readonly (read-only commands in bwrap)
#   "bash_sandboxed" - bash_sandboxed (any command in bwrap)
#
# The 2×2×2 factorial (file_tools × run_tests × bash):
#   A = file + tests          C = file + tests + bash
#   D = bash only             E = file + bash
#   F = tests + bash          (file only = useless, nothing = useless)
#
# B (file + tests + readonly bash) is outside the factorial — it tests
# exploration without execution, a different question.

BASH_READONLY_ALLOWLIST = [
    "cat", "head", "tail", "wc", "grep", "find", "ls", "tree",
    "file", "stat", "realpath", "basename", "dirname", "pwd",
    "sort", "uniq", "cut", "tr", "diff",
    "git status", "git diff", "git log", "git show", "git branch",
]

# ---------------------------------------------------------------------------
# Globals set by CLI args
# ---------------------------------------------------------------------------

_condition: str = "A"
_task_id: str = "00"
_log_dir: Path = Path("./logs")
_workspace: Path = Path(".")
_allowed_dirs: list[str] = []
_test_detail: str = "detailed"  # "detailed" or "minimal"
_call_log: list[dict] = []

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log_call(tool: str, args: dict, result: str, success: bool, duration_ms: float):
    """Append a tool call record to the in-memory log and flush to disk."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": _task_id,
        "condition": _condition,
        "tool": tool,
        "arguments": args,
        "result_preview": result[:500] if result else "",
        "success": success,
        "duration_ms": round(duration_ms, 1),
        "sequence_number": len(_call_log),
    }
    _call_log.append(entry)
    _flush_log()


def _flush_log():
    """Write the full call log to disk as JSONL."""
    log_file = _log_dir / f"task-{_task_id}-condition-{_condition}.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w") as f:
        for entry in _call_log:
            f.write(json.dumps(entry) + "\n")


def _sandbox_commit(tool: str, args_summary: str):
    """If workspace is a git repo, commit current state for sandbox diffing."""
    git_dir = _workspace / ".git"
    if not git_dir.exists():
        return
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=_workspace, capture_output=True, timeout=10
        )
        subprocess.run(
            ["git", "commit", "-m", f"after {tool}({args_summary})",
             "--allow-empty", "--no-gpg-sign"],
            cwd=_workspace, capture_output=True, timeout=10
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _resolve_path(path: str) -> Path:
    """Resolve a path relative to workspace, enforcing sandbox bounds."""
    resolved = (_workspace / path).resolve()
    ws_resolved = _workspace.resolve()
    if not str(resolved).startswith(str(ws_resolved)):
        raise ValueError(f"Path {path} escapes workspace {_workspace}")
    if _allowed_dirs:
        if not any(str(resolved).startswith(str(Path(d).resolve())) for d in _allowed_dirs):
            raise ValueError(f"Path {path} not in allowed directories: {_allowed_dirs}")
    return resolved


def _validate_bash_readonly(command: str) -> bool:
    """Check if a bash command is in the read-only allowlist.

    Rejects commands containing shell metacharacters that could bypass
    the allowlist (pipes, semicolons, subshells, redirects, etc.).
    This is a conservative check — some safe uses of pipes are rejected.
    """
    cmd_stripped = command.strip()

    # Reject shell metacharacters that enable command chaining or injection
    dangerous_chars = [";", "|", "&", "`", "$", "(", ")", ">", "<", "\n"]
    for char in dangerous_chars:
        if char in cmd_stripped:
            return False

    for allowed in BASH_READONLY_ALLOWLIST:
        if cmd_stripped == allowed or cmd_stripped.startswith(allowed + " "):
            return True
    return False


# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------

server = FastMCP(
    "Experiment Server",
    instructions=(
        "This server provides tools for working with code.\n\n"
        "Efficiency tips:\n"
        "- Use file_glob to find files by pattern (e.g. '**/*.py') instead of listing directories one at a time.\n"
        "- Use file_read_batch to read multiple files in one call.\n"
        "- Use file_edit_batch to apply multiple edits to one or more files in a single call.\n"
        "- Use file_search or file_search_context to find code patterns across the codebase.\n"
        "- Use run_tests to verify your changes (if available).\n"
    ),
)


# --- File tools (all conditions) ---

@server.tool(tags={"group:file_tools", "group:simple_tools"})
def file_read(path: str, offset: int = 0, limit: int = 0) -> str:
    """Read a file's contents. Returns the file text with line numbers.

    Args:
        path: Path to the file (relative to workspace)
        offset: Line number to start reading from (0 = beginning)
        limit: Maximum number of lines to read (0 = all)
    """
    t0 = time.monotonic()
    try:
        resolved = _resolve_path(path)
        lines = resolved.read_text().splitlines(keepends=True)
        if offset > 0:
            lines = lines[offset:]
        if limit > 0:
            lines = lines[:limit]
        numbered = "".join(
            f"{i + offset + 1:>6}\t{line}" for i, line in enumerate(lines)
        )
        result = numbered or "(empty file)"
        _log_call("file_read", {"path": path, "offset": offset, "limit": limit}, result, True, (time.monotonic() - t0) * 1000)
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("file_read", {"path": path}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:file_tools"})
def file_search(pattern: str, path: str = ".", glob_filter: str = "") -> str:
    """Search file contents using grep-like pattern matching.

    Args:
        pattern: Regex pattern to search for
        path: Directory or file to search in (relative to workspace)
        glob_filter: Optional glob to filter files (e.g. "*.py")
    """
    t0 = time.monotonic()
    try:
        resolved = _resolve_path(path)
        cmd = ["grep", "-rn", "--color=never"]
        if glob_filter:
            cmd.extend(["--include", glob_filter])
        cmd.extend([pattern, str(resolved)])
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=_workspace)
        result = proc.stdout or "(no matches)"
        _log_call("file_search", {"pattern": pattern, "path": path, "glob": glob_filter}, result, True, (time.monotonic() - t0) * 1000)
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("file_search", {"pattern": pattern, "path": path}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:file_tools", "group:batch_tools", "group:simple_tools"})
def file_glob(pattern: str, path: str = ".") -> str:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g. "**/*.py", "src/**/*.ts")
        path: Base directory to search from (relative to workspace)
    """
    t0 = time.monotonic()
    try:
        resolved = _resolve_path(path)
        matches = sorted(resolved.glob(pattern))
        ws = _workspace.resolve()
        relative = [str(m.relative_to(ws)) for m in matches if m.is_file()]
        result = "\n".join(relative) or "(no matches)"
        _log_call("file_glob", {"pattern": pattern, "path": path}, result, True, (time.monotonic() - t0) * 1000)
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("file_glob", {"pattern": pattern, "path": path}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:file_tools"})
def file_list(path: str = ".") -> str:
    """List files and directories at a path.

    Args:
        path: Directory to list (relative to workspace)
    """
    t0 = time.monotonic()
    try:
        resolved = _resolve_path(path)
        entries = sorted(resolved.iterdir())
        lines = []
        for e in entries:
            prefix = "d " if e.is_dir() else "f "
            lines.append(prefix + e.name)
        result = "\n".join(lines) or "(empty directory)"
        _log_call("file_list", {"path": path}, result, True, (time.monotonic() - t0) * 1000)
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("file_list", {"path": path}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:file_tools", "group:simple_tools"})
def file_edit(path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing an exact string match.

    Args:
        path: Path to the file (relative to workspace)
        old_string: The exact text to find and replace (must be unique in the file)
        new_string: The replacement text
    """
    t0 = time.monotonic()
    try:
        resolved = _resolve_path(path)
        content = resolved.read_text()
        count = content.count(old_string)
        if count == 0:
            err = f"Error: old_string not found in {path}"
            _log_call("file_edit", {"path": path, "old_string": old_string[:100]}, err, False, (time.monotonic() - t0) * 1000)
            return err
        if count > 1:
            err = f"Error: old_string found {count} times in {path} (must be unique)"
            _log_call("file_edit", {"path": path, "old_string": old_string[:100]}, err, False, (time.monotonic() - t0) * 1000)
            return err
        new_content = content.replace(old_string, new_string, 1)
        resolved.write_text(new_content)
        result = f"Edited {path}: replaced 1 occurrence"
        _log_call("file_edit", {"path": path, "old_len": len(old_string), "new_len": len(new_string)}, result, True, (time.monotonic() - t0) * 1000)
        _sandbox_commit("file_edit", path)
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("file_edit", {"path": path}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:file_tools", "group:batch_tools"})
def file_edit_batch(edits: list[dict]) -> str:
    """Apply multiple edits across one or more files in a single call.
    Much more efficient than calling file_edit repeatedly.

    Each edit is a dict with: path, old_string, new_string.
    Edits are applied in order. Each old_string must be unique in its file
    (at the time that edit is applied — earlier edits in the batch may
    change the file content).

    Args:
        edits: List of {"path": "...", "old_string": "...", "new_string": "..."}
    """
    t0 = time.monotonic()
    results = []
    errors = []
    files_modified = set()

    for i, edit in enumerate(edits):
        path = edit.get("path", "")
        old_string = edit.get("old_string", "")
        new_string = edit.get("new_string", "")

        if not path or not old_string:
            errors.append(f"Edit {i}: missing path or old_string")
            continue

        try:
            resolved = _resolve_path(path)
            content = resolved.read_text()
            count = content.count(old_string)
            if count == 0:
                errors.append(f"Edit {i} ({path}): old_string not found")
                continue
            if count > 1:
                errors.append(f"Edit {i} ({path}): old_string found {count} times (must be unique)")
                continue
            new_content = content.replace(old_string, new_string, 1)
            resolved.write_text(new_content)
            results.append(f"Edit {i} ({path}): OK")
            files_modified.add(path)
        except Exception as e:
            errors.append(f"Edit {i} ({path}): {e}")

    for path in files_modified:
        _sandbox_commit("file_edit_batch", path)

    summary = f"Applied {len(results)}/{len(edits)} edits across {len(files_modified)} files"
    if errors:
        summary += f"\nErrors:\n" + "\n".join(f"  {e}" for e in errors)

    success = len(errors) == 0
    _log_call("file_edit_batch", {"edit_count": len(edits), "files": list(files_modified)},
              summary, success, (time.monotonic() - t0) * 1000)
    return summary


@server.tool(tags={"group:file_tools", "group:batch_tools", "group:simple_tools"})
def file_write(path: str, content: str) -> str:
    """Write content to a file (creates or overwrites).

    Args:
        path: Path to the file (relative to workspace)
        content: The full content to write
    """
    t0 = time.monotonic()
    try:
        resolved = _resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content)
        result = f"Wrote {len(content)} chars to {path}"
        _log_call("file_write", {"path": path, "content_length": len(content)}, result, True, (time.monotonic() - t0) * 1000)
        _sandbox_commit("file_write", path)
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("file_write", {"path": path}, err, False, (time.monotonic() - t0) * 1000)
        return err


# --- Enhanced data channel tools (all conditions) ---

@server.tool(tags={"group:file_tools", "group:batch_tools"})
def file_read_batch(paths: list[str], limit_per_file: int = 200) -> str:
    """Read multiple files in a single call. Returns each file's contents
    with a header showing the path.

    Args:
        paths: List of file paths (relative to workspace)
        limit_per_file: Max lines per file (default 200, 0 = all)
    """
    t0 = time.monotonic()
    results = []
    errors = []
    for path in paths[:20]:  # cap at 20 files per call
        try:
            resolved = _resolve_path(path)
            lines = resolved.read_text().splitlines(keepends=True)
            if limit_per_file > 0:
                lines = lines[:limit_per_file]
            numbered = "".join(
                f"{i + 1:>6}\t{line}" for i, line in enumerate(lines)
            )
            truncated = f" (first {limit_per_file} lines)" if limit_per_file > 0 and len(lines) >= limit_per_file else ""
            results.append(f"── {path}{truncated} ──\n{numbered}")
        except Exception as e:
            errors.append(f"── {path} ── Error: {e}")

    result = "\n\n".join(results + errors)
    _log_call("file_read_batch", {"paths": paths, "limit_per_file": limit_per_file, "count": len(paths)},
              result, len(errors) == 0, (time.monotonic() - t0) * 1000)
    return result or "(no files read)"


@server.tool(tags={"group:file_tools"})
def file_search_context(pattern: str, path: str = ".", context: int = 3,
                        glob_filter: str = "") -> str:
    """Search file contents with context lines around each match.
    Like grep -C but returns structured output.

    Args:
        pattern: Regex pattern to search for
        path: Directory or file to search in (relative to workspace)
        context: Number of context lines before and after each match (default 3)
        glob_filter: Optional glob to filter files (e.g. "*.py")
    """
    t0 = time.monotonic()
    try:
        resolved = _resolve_path(path)
        cmd = ["grep", "-rn", f"-C{context}", "--color=never", "--group-separator=──"]
        if glob_filter:
            cmd.extend(["--include", glob_filter])
        cmd.extend([pattern, str(resolved)])
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=_workspace)
        result = proc.stdout or "(no matches)"
        _log_call("file_search_context", {"pattern": pattern, "path": path, "context": context, "glob": glob_filter},
                  result, True, (time.monotonic() - t0) * 1000)
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("file_search_context", {"pattern": pattern, "path": path}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:file_tools"})
def file_count(path: str = ".", glob_filter: str = "") -> str:
    """Count files and lines matching a pattern. Returns file counts,
    line counts, and a breakdown by file.

    Args:
        path: Directory to analyze (relative to workspace)
        glob_filter: Optional glob to filter files (e.g. "*.py", "*.cpp")
    """
    t0 = time.monotonic()
    try:
        resolved = _resolve_path(path)
        if glob_filter:
            matches = sorted(resolved.glob(glob_filter))
        else:
            matches = sorted(resolved.rglob("*"))
        matches = [m for m in matches if m.is_file()]

        ws = _workspace.resolve()
        lines = []
        total_lines = 0
        for m in matches[:100]:  # cap at 100 files
            try:
                count = len(m.read_text().splitlines())
                total_lines += count
                rel = str(m.relative_to(ws))
                lines.append(f"  {count:>6} {rel}")
            except Exception:
                rel = str(m.relative_to(ws))
                lines.append(f"  (err) {rel}")

        result = f"Files: {len(matches)}\nTotal lines: {total_lines}\n\n" + "\n".join(lines)
        _log_call("file_count", {"path": path, "glob": glob_filter}, result, True, (time.monotonic() - t0) * 1000)
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("file_count", {"path": path}, err, False, (time.monotonic() - t0) * 1000)
        return err


# --- Semantic tools (Fledgling-powered, via DuckDB + sitting_duck) ─

def _get_ast_db():
    """Get a DuckDB connection with sitting_duck loaded."""
    import duckdb
    db = duckdb.connect()
    db.execute("INSTALL sitting_duck FROM community")
    db.execute("LOAD sitting_duck")
    return db


@server.tool(tags={"group:semantic_tools"})
def find_definitions(file_pattern: str = "**/*.py", name_pattern: str = "") -> str:
    """Find function, class, and variable definitions across the codebase.
    Understands code structure — not just text matching.

    Args:
        file_pattern: Glob pattern for files to search (default: all Python files)
        name_pattern: Optional filter on definition name (substring match)
    """
    t0 = time.monotonic()
    try:
        db = _get_ast_db()
        ws = _workspace.resolve()
        matches = sorted(ws.glob(file_pattern))
        matches = [m for m in matches if m.is_file() and "__pycache__" not in str(m)]

        results = []
        for m in matches[:20]:
            rel = str(m.relative_to(ws))
            try:
                query = f"""
                    SELECT name, type, semantic_type, start_line, end_line
                    FROM read_ast('{m}')
                    WHERE semantic_type LIKE 'DEFINITION%'
                    AND name IS NOT NULL AND name != ''
                    {"AND name LIKE '%" + name_pattern + "%'" if name_pattern else ""}
                    ORDER BY start_line
                """
                rows = db.execute(query).fetchall()
                if rows:
                    results.append(f"── {rel} ──")
                    for name, typ, sem, start, end in rows:
                        kind = typ.replace("_definition", "").replace("_", " ")
                        results.append(f"  {start:>4} {kind:<20} {name}")
            except Exception:
                pass

        result = "\n".join(results) or "(no definitions found)"
        _log_call("find_definitions", {"file_pattern": file_pattern, "name_pattern": name_pattern},
                  result, True, (time.monotonic() - t0) * 1000)
        db.close()
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("find_definitions", {"file_pattern": file_pattern}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:semantic_tools"})
def find_callers(file_pattern: str = "**/*.py", function_name: str = "") -> str:
    """Find all call sites for a function across the codebase.

    Args:
        file_pattern: Glob pattern for files to search
        function_name: Name of the function to find calls to
    """
    t0 = time.monotonic()
    try:
        db = _get_ast_db()
        ws = _workspace.resolve()
        matches = sorted(ws.glob(file_pattern))
        matches = [m for m in matches if m.is_file() and "__pycache__" not in str(m)]

        results = []
        for m in matches[:20]:
            rel = str(m.relative_to(ws))
            try:
                query = f"""
                    SELECT name, start_line, type
                    FROM read_ast('{m}')
                    WHERE type = 'call'
                    AND name = '{function_name}'
                    ORDER BY start_line
                """
                rows = db.execute(query).fetchall()
                if rows:
                    results.append(f"── {rel} ──")
                    for name, line, typ in rows:
                        results.append(f"  {line:>4} {name}()")
            except Exception:
                pass

        result = "\n".join(results) or f"(no calls to '{function_name}' found)"
        _log_call("find_callers", {"file_pattern": file_pattern, "function_name": function_name},
                  result, True, (time.monotonic() - t0) * 1000)
        db.close()
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("find_callers", {"file_pattern": file_pattern}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:semantic_tools"})
def code_structure(file_path: str) -> str:
    """Show the structural outline of a file: classes, functions, methods
    with nesting. Like a table of contents for code.

    Args:
        file_path: Path to the file (relative to workspace)
    """
    t0 = time.monotonic()
    try:
        db = _get_ast_db()
        resolved = _resolve_path(file_path)
        query = f"""
            SELECT name, type, semantic_type, start_line, end_line, depth
            FROM read_ast('{resolved}')
            WHERE (type LIKE '%definition%' OR type LIKE '%class%')
            AND name IS NOT NULL AND name != ''
            ORDER BY start_line
        """
        rows = db.execute(query).fetchall()

        results = [f"── {file_path} ──"]
        for name, typ, sem, start, end, depth in rows:
            kind = typ.replace("_definition", "").replace("_", " ")
            indent = "  " * min(depth, 4)
            size = end - start + 1
            results.append(f"  {start:>4}-{end:<4} {indent}{kind} {name} ({size} lines)")

        result = "\n".join(results) or "(no structure found)"
        _log_call("code_structure", {"file_path": file_path},
                  result, True, (time.monotonic() - t0) * 1000)
        db.close()
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("code_structure", {"file_path": file_path}, err, False, (time.monotonic() - t0) * 1000)
        return err


@server.tool(tags={"group:semantic_tools"})
def find_imports(file_pattern: str = "**/*.py") -> str:
    """Find all import statements across the codebase.

    Args:
        file_pattern: Glob pattern for files to search
    """
    t0 = time.monotonic()
    try:
        db = _get_ast_db()
        ws = _workspace.resolve()
        matches = sorted(ws.glob(file_pattern))
        matches = [m for m in matches if m.is_file() and "__pycache__" not in str(m)]

        results = []
        for m in matches[:20]:
            rel = str(m.relative_to(ws))
            try:
                query = f"""
                    SELECT name, type, start_line
                    FROM read_ast('{m}')
                    WHERE semantic_type LIKE '%IMPORT%'
                    AND name IS NOT NULL AND name != ''
                    ORDER BY start_line
                """
                rows = db.execute(query).fetchall()
                if rows:
                    results.append(f"── {rel} ──")
                    for name, typ, line in rows:
                        results.append(f"  {line:>4} {name}")
            except Exception:
                pass

        result = "\n".join(results) or "(no imports found)"
        _log_call("find_imports", {"file_pattern": file_pattern},
                  result, True, (time.monotonic() - t0) * 1000)
        db.close()
        return result
    except Exception as e:
        err = f"Error: {e}"
        _log_call("find_imports", {"file_pattern": file_pattern}, err, False, (time.monotonic() - t0) * 1000)
        return err


# --- Test runner (all conditions) ─────────────────────────────────

@server.tool(tags={"group:run_tests"})
def run_tests(test_file: str = "", verbose: bool = False) -> str:
    """Run pytest on the workspace's test suite. Tests are read-only —
    if any test file has been modified, this tool refuses to run.

    This is a data channel tool (level 1): it runs a fixed program
    (pytest) on fixed inputs (the original test files) and returns
    structured output. Available in ALL conditions.

    The level of detail in the output depends on the server configuration.

    Args:
        test_file: Specific test file to run (relative to workspace).
                   Empty string runs all tests.
        verbose: If true, show full output including passing tests.
    """
    t0 = time.monotonic()

    # Check that test files haven't been modified since the worktree was created.
    # We compare against the FIRST commit in the worktree (the original state).
    tests_dir = _workspace / "tests"
    if tests_dir.exists():
        try:
            # Find the initial commit (the one the worktree was created from)
            initial = subprocess.run(
                ["git", "rev-list", "--max-parents=0", "HEAD"],
                capture_output=True, text=True, timeout=10,
                cwd=_workspace,
            )
            # If this is a worktree branched from a repo, the first commit
            # is the repo root. Use the merge-base with the branch point instead.
            # Simpler: just diff the tests/ directory between the first commit
            # on this branch and the current working tree.
            first_commit = initial.stdout.strip().splitlines()[0] if initial.stdout.strip() else "HEAD"

            check = subprocess.run(
                ["git", "diff", first_commit, "--", "tests/",
                 ":(exclude)tests/__pycache__", ":(exclude)**/__pycache__"],
                capture_output=True, text=True, timeout=10,
                cwd=_workspace,
            )
            if check.stdout.strip():
                err = "Error: Test files have been modified. This tool only runs unmodified tests.\nYou must fix the source code, not the tests."
                _log_call("run_tests", {"test_file": test_file}, err, False, (time.monotonic() - t0) * 1000)
                return err
        except Exception:
            pass  # If git check fails, allow the run anyway

    try:
        pytest_args = ["python3", "-m", "pytest"]
        if test_file:
            resolved = _resolve_path(test_file)
            pytest_args.append(str(resolved))
        else:
            pytest_args.append(str(tests_dir))

        if _test_detail == "minimal":
            # Minimal: just pass/fail counts, no tracebacks, no test names
            pytest_args.extend(["--tb=no", "-q", "--no-header"])
        elif _test_detail == "diagnostic":
            # Diagnostic: failures only, with expected vs actual, no passing tests.
            # Designed for agent workflows — actionable failure info, no noise.
            pytest_args.extend(["--tb=short", "-v", "--no-header", "-x"])
            # -x stops after first failure group for faster feedback
            # --tb=short gives assertion + location without full stack
            # -v gives test names (tells agent WHAT was tested, not just that it failed)
        elif verbose:
            # Verbose: full tracebacks with local variables, all test names
            pytest_args.extend(["--tb=long", "-v"])
        else:
            # Detailed (default): short tracebacks, quiet output
            pytest_args.extend(["--tb=short", "-q", "--no-header"])

        # Run pytest inside bwrap: read-only workspace, no network, isolated PIDs.
        # This sandboxes the *consequences* of what the agent wrote — if it injected
        # malicious code into the source files, the code runs but can't exfiltrate
        # data, access the network, or see other processes.
        pytest_cmd_str = f"PYTHONPATH={_workspace.resolve()} {' '.join(pytest_args)}"
        bwrap_cmd = _build_bwrap_cmd(pytest_cmd_str, readonly=True)

        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/tmp",
            "TERM": os.environ.get("TERM", "xterm"),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
        }

        proc = subprocess.run(
            bwrap_cmd,
            capture_output=True, text=True, timeout=60,
            env=env,
        )

        result = proc.stdout
        if proc.stderr:
            # Filter out warnings, keep only errors
            stderr_lines = [l for l in proc.stderr.splitlines()
                          if not l.startswith("Warning") and l.strip()]
            if stderr_lines:
                result += "\n(stderr: " + "\n".join(stderr_lines) + ")"

        success = proc.returncode == 0
        _log_call("run_tests", {"test_file": test_file, "verbose": verbose},
                  result, success, (time.monotonic() - t0) * 1000)
        return result or "(no output)"

    except subprocess.TimeoutExpired:
        err = "Error: tests timed out after 60 seconds"
        _log_call("run_tests", {"test_file": test_file}, err, False, (time.monotonic() - t0) * 1000)
        return err
    except Exception as e:
        err = f"Error: {e}"
        _log_call("run_tests", {"test_file": test_file}, err, False, (time.monotonic() - t0) * 1000)
        return err


# --- Bash read-only (Condition B) ---

@server.tool(tags={"group:bash_readonly"})
def bash_readonly(command: str) -> str:
    """Execute a read-only bash command. Only safe, non-modifying commands are allowed.

    Allowed commands: cat, head, tail, wc, grep, find, ls, tree, file, stat,
    realpath, basename, dirname, pwd, sort, uniq, cut, tr, diff,
    git status, git diff, git log, git show, git branch.

    The command runs in a sandbox with no network access and read-only
    filesystem access to the workspace.

    Args:
        command: The bash command to execute
    """
    t0 = time.monotonic()
    if not _validate_bash_readonly(command):
        err = f"Error: command not in read-only allowlist: {command.split()[0] if command.strip() else '(empty)'}"
        _log_call("bash_readonly", {"command": command}, err, False, (time.monotonic() - t0) * 1000)
        return err
    try:
        bwrap_cmd = _build_bwrap_cmd(command, readonly=True)
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/workspace",
            "TERM": os.environ.get("TERM", "xterm"),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
        }
        proc = subprocess.run(
            bwrap_cmd,
            capture_output=True, text=True, timeout=60,
            env=env,
        )
        result = proc.stdout
        if proc.stderr:
            result += f"\n(stderr: {proc.stderr})"
        if proc.returncode != 0:
            result += f"\n(exit code: {proc.returncode})"
        success = proc.returncode == 0
        _log_call("bash_readonly", {"command": command}, result, success, (time.monotonic() - t0) * 1000)
        return result or "(no output)"
    except subprocess.TimeoutExpired:
        err = "Error: command timed out after 60 seconds"
        _log_call("bash_readonly", {"command": command}, err, False, (time.monotonic() - t0) * 1000)
        return err
    except Exception as e:
        err = f"Error: {e}"
        _log_call("bash_readonly", {"command": command}, err, False, (time.monotonic() - t0) * 1000)
        return err


# --- Bash sandboxed read-write (Condition C) ---

def _build_bwrap_cmd(command: str, *, readonly: bool = False) -> list[str]:
    """Build a bubblewrap command that sandboxes bash execution.

    Provides:
    - Filesystem: workspace bound (read-only or read-write depending on mode),
      /usr /bin /lib* /etc are read-only, /tmp is a fresh tmpfs,
      everything else is inaccessible
    - Network: blocked (--unshare-net)
    - PID namespace: isolated (--unshare-pid)
    - No new privileges (--new-session)
    """
    ws = str(_workspace.resolve())
    bind_flag = "--ro-bind" if readonly else "--bind"
    return [
        "bwrap",
        # Filesystem: read-only base system
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/bin", "/bin",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64",
        "--ro-bind", "/etc", "/etc",
        # Workspace: read-only or read-write depending on condition
        bind_flag, ws, ws,
        bind_flag, ws, "/workspace",
        # Writable /tmp (even readonly needs scratch space)
        "--tmpfs", "/tmp",
        # Proc (needed by many tools)
        "--proc", "/proc",
        # Dev (minimal)
        "--dev", "/dev",
        # Isolation
        "--unshare-net",
        "--unshare-pid",
        "--new-session",
        "--die-with-parent",  # kill all children when bwrap exits (prevents level 7)
        # Working directory
        "--chdir", ws,
        # Run bash
        "bash", "-c", command,
    ]


@server.tool(tags={"group:bash_sandboxed"})
def bash_sandboxed(command: str) -> str:
    """Execute a bash command in a sandboxed environment.

    The command runs within the workspace directory. It CAN modify files
    in the workspace but CANNOT access files outside it, use the network,
    or see other processes.

    Args:
        command: The bash command to execute
    """
    t0 = time.monotonic()
    try:
        bwrap_cmd = _build_bwrap_cmd(command)
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/workspace",
            "TERM": os.environ.get("TERM", "xterm"),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
        }
        proc = subprocess.run(
            bwrap_cmd,
            capture_output=True, text=True, timeout=120,
            env=env,
        )
        result = proc.stdout
        if proc.stderr:
            result += f"\n(stderr: {proc.stderr})"
        if proc.returncode != 0:
            result += f"\n(exit code: {proc.returncode})"
        success = proc.returncode == 0
        _log_call("bash_sandboxed", {"command": command}, result, success, (time.monotonic() - t0) * 1000)
        _sandbox_commit("bash_sandboxed", command[:80])
        return result or "(no output)"
    except subprocess.TimeoutExpired:
        err = "Error: command timed out after 120 seconds"
        _log_call("bash_sandboxed", {"command": command}, err, False, (time.monotonic() - t0) * 1000)
        return err
    except Exception as e:
        err = f"Error: {e}"
        _log_call("bash_sandboxed", {"command": command}, err, False, (time.monotonic() - t0) * 1000)
        return err


# ---------------------------------------------------------------------------
# Condition-based tool filtering
# ---------------------------------------------------------------------------

ALL_GROUPS = {
    "file_tools", "batch_tools", "simple_tools", "run_tests",
    "semantic_tools", "bash_readonly", "bash_sandboxed",
}


def _apply_condition(condition: str):
    """Disable tools not in the specified condition.

    Uses name-based disabling to avoid the multi-tag problem where
    disabling group:file_tools would also disable tools that have
    both group:file_tools AND group:batch_tools.
    """
    active_groups = CONDITION_TOOLS.get(condition, set())

    # Build the set of tool names that should be active
    # by checking each tool's tags against the active groups
    group_to_tools = {
        "file_tools": {"file_read", "file_search", "file_glob", "file_list",
                       "file_edit", "file_edit_batch", "file_write",
                       "file_read_batch", "file_search_context", "file_count"},
        "batch_tools": {"file_glob", "file_read_batch", "file_edit_batch", "file_write"},
        "simple_tools": {"file_read", "file_edit", "file_glob", "file_write"},
        "run_tests": {"run_tests"},
        "semantic_tools": {"find_definitions", "find_callers", "code_structure", "find_imports"},
        "bash_readonly": {"bash_readonly"},
        "bash_sandboxed": {"bash_sandboxed"},
    }

    active_tools = set()
    for group in active_groups:
        active_tools.update(group_to_tools.get(group, set()))

    all_tools = set()
    for tools in group_to_tools.values():
        all_tools.update(tools)

    inactive_tools = all_tools - active_tools
    if inactive_tools:
        server.disable(names=inactive_tools)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    global _condition, _task_id, _log_dir, _workspace, _allowed_dirs

    parser = argparse.ArgumentParser(description="Experiment MCP Server")
    parser.add_argument("--condition", choices=["A", "B", "C", "D", "E", "F", "J", "K", "L"], required=True,
                        help="Experimental condition (A=file+tests, B=A+readonly-bash, C=A+bash, D=bash-only, E=file+readonly-bash, F=tests+bash)")
    parser.add_argument("--task-id", required=True,
                        help="Task identifier (e.g. '01', 'task-03-condition-A')")
    parser.add_argument("--log-dir", default="./logs",
                        help="Directory for tool call logs (default: ./logs)")
    parser.add_argument("--workspace", default=".",
                        help="Workspace directory the agent operates in")
    parser.add_argument("--allowed-dirs", nargs="*", default=[],
                        help="For low-W conditions: restrict file access to these directories only")
    parser.add_argument("--test-detail", choices=["detailed", "minimal", "diagnostic"], default="detailed",
                        help="Test output detail: 'detailed' (short tracebacks), 'minimal' (counts only), 'diagnostic' (failures with expected vs actual, stops early)")

    args = parser.parse_args()

    _condition = args.condition
    _task_id = args.task_id
    _log_dir = Path(args.log_dir)
    _workspace = Path(args.workspace).resolve()
    _allowed_dirs = args.allowed_dirs or []
    _test_detail = args.test_detail

    _apply_condition(_condition)

    print(f"[experiment-server] Condition {_condition} | Task {_task_id} | Workspace {_workspace}", file=sys.stderr)
    print(f"[experiment-server] Tools: {CONDITION_TOOLS[_condition]}", file=sys.stderr)
    print(f"[experiment-server] Test detail: {_test_detail}", file=sys.stderr)
    if _allowed_dirs:
        print(f"[experiment-server] Allowed dirs: {_allowed_dirs}", file=sys.stderr)
    print(f"[experiment-server] Logging to: {_log_dir}", file=sys.stderr)

    server.run()


if __name__ == "__main__":
    main()
