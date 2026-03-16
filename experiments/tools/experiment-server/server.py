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
    "A": {"file_read", "file_search", "file_glob", "file_edit", "file_write", "file_list"},
    "B": {"file_read", "file_search", "file_glob", "file_edit", "file_write", "file_list", "bash_readonly"},
    "C": {"file_read", "file_search", "file_glob", "file_edit", "file_write", "file_list", "bash_sandboxed"},
}

# Tags: file tools have no condition tags (always available).
# Only bash tools are tagged with their specific condition.
# server.disable(tags={"condition:X"}) disables ANY tool with that tag,
# so universal tools must NOT carry condition tags.

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
        "This server provides tools for working with code. "
        "Use the available tools to read, search, edit, and write files."
    ),
)


# --- File tools (all conditions) ---

@server.tool()
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


@server.tool()
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


@server.tool()
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


@server.tool()
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


@server.tool()
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


@server.tool()
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


# --- Bash read-only (Condition B) ---

@server.tool(tags={"condition:B"})
def bash_readonly(command: str) -> str:
    """Execute a read-only bash command. Only safe, non-modifying commands are allowed.

    Allowed commands: cat, head, tail, wc, grep, find, ls, tree, file, stat,
    realpath, basename, dirname, pwd, sort, uniq, cut, tr, diff,
    git status, git diff, git log, git show, git branch.

    Args:
        command: The bash command to execute
    """
    t0 = time.monotonic()
    if not _validate_bash_readonly(command):
        err = f"Error: command not in read-only allowlist: {command.split()[0] if command.strip() else '(empty)'}"
        _log_call("bash_readonly", {"command": command}, err, False, (time.monotonic() - t0) * 1000)
        return err
    try:
        proc = subprocess.run(
            ["bash", "-c", command],
            capture_output=True, text=True, timeout=60,
            cwd=_workspace,
            env={**os.environ, "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
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

@server.tool(tags={"condition:C"})
def bash_sandboxed(command: str) -> str:
    """Execute a bash command in a sandboxed environment.

    The command runs within the workspace directory with a 120-second timeout.
    The command CAN modify files within the workspace.

    Args:
        command: The bash command to execute
    """
    # NOTE: This is a soft sandbox — cwd is set to workspace but the command
    # can still access files outside it or make network calls. For the
    # experiment (testing computation channel dynamics, not security), this
    # is acceptable. For production use, wrap with bubblewrap/firejail.
    t0 = time.monotonic()
    try:
        env = {
            **os.environ,
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(_workspace),
        }
        proc = subprocess.run(
            ["bash", "-c", command],
            capture_output=True, text=True, timeout=120,
            cwd=_workspace,
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

def _apply_condition(condition: str):
    """Disable bash tools not in the specified condition.

    File tools have no condition tags and are always available.
    Only bash_readonly (tagged "condition:B") and bash_sandboxed
    (tagged "condition:C") need conditional disabling.
    """
    if condition == "A":
        # No bash tools — disable both
        server.disable(tags={"condition:B"})
        server.disable(tags={"condition:C"})
    elif condition == "B":
        # Read-only bash only — disable sandboxed
        server.disable(tags={"condition:C"})
    # Condition C: both bash tools? No — B gets bash_readonly, C gets bash_sandboxed.
    # They're different tools, not cumulative. Disable read-only in C.
    elif condition == "C":
        server.disable(tags={"condition:B"})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    global _condition, _task_id, _log_dir, _workspace, _allowed_dirs

    parser = argparse.ArgumentParser(description="Experiment MCP Server")
    parser.add_argument("--condition", choices=["A", "B", "C"], required=True,
                        help="Experimental condition (A=data-channel, B=readonly, C=computation)")
    parser.add_argument("--task-id", required=True,
                        help="Task identifier (e.g. '01', 'task-03-condition-A')")
    parser.add_argument("--log-dir", default="./logs",
                        help="Directory for tool call logs (default: ./logs)")
    parser.add_argument("--workspace", default=".",
                        help="Workspace directory the agent operates in")
    parser.add_argument("--allowed-dirs", nargs="*", default=[],
                        help="For low-W conditions: restrict file access to these directories only")

    args = parser.parse_args()

    _condition = args.condition
    _task_id = args.task_id
    _log_dir = Path(args.log_dir)
    _workspace = Path(args.workspace).resolve()
    _allowed_dirs = args.allowed_dirs or []

    _apply_condition(_condition)

    print(f"[experiment-server] Condition {_condition} | Task {_task_id} | Workspace {_workspace}", file=sys.stderr)
    print(f"[experiment-server] Tools: {CONDITION_TOOLS[_condition]}", file=sys.stderr)
    if _allowed_dirs:
        print(f"[experiment-server] Allowed dirs: {_allowed_dirs}", file=sys.stderr)
    print(f"[experiment-server] Logging to: {_log_dir}", file=sys.stderr)

    server.run()


if __name__ == "__main__":
    main()
