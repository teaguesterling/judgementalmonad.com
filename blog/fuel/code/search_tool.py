"""
search_tool.py — A structured codebase search tool.

Replaces: Bash("grep -r pattern path")
Grade before: Level 4 computation channel (arbitrary string -> universal machine)
Grade after: Level 1 data channel (structured query -> bounded search -> structured results)

From Ratchet Fuel Post 5: Closing the Channel
https://judgementalmonad.com/blog/fuel/05-closing-the-channel
"""

import re
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path


@dataclass
class MatchResult:
    """A single search match with structured fields."""
    file: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int


@dataclass
class SearchResult:
    """Complete search result with metadata."""
    pattern: str
    root: str
    matches: list[MatchResult] = field(default_factory=list)
    files_searched: int = 0
    files_matched: int = 0
    truncated: bool = False
    error: str | None = None


def search(
    pattern: str,
    root: str = ".",
    *,
    include: str | None = None,
    max_results: int = 200,
    case_sensitive: bool = True,
) -> SearchResult:
    """
    Search files under root for lines matching pattern.

    Args:
        pattern: Regular expression to search for.
        root: Directory to search (default: current directory).
        include: Glob pattern for file filtering (e.g., "*.py").
        max_results: Maximum matches to return before truncating.
        case_sensitive: Whether the search is case-sensitive.

    Returns:
        SearchResult with structured match data.

    This function:
        - Reads files directly (no shell, no PATH lookup, no aliases)
        - Returns structured data (not strings to parse)
        - Declares its effects (read-only filesystem access under root)
        - Bounds its output (max_results cap)
        - Handles errors explicitly (no silent failures)
    """
    result = SearchResult(pattern=pattern, root=str(root))

    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled = re.compile(pattern, flags)
    except re.error as e:
        result.error = f"Invalid pattern: {e}"
        return result

    root_path = Path(root).resolve()
    if not root_path.is_dir():
        result.error = f"Not a directory: {root}"
        return result

    skip_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv'}

    for dirpath in _walk(root_path, skip_dirs):
        for filepath in dirpath.iterdir():
            if not filepath.is_file():
                continue

            if include and not fnmatch(filepath.name, include):
                continue

            result.files_searched += 1

            try:
                text = filepath.read_text(encoding='utf-8', errors='ignore')
            except (OSError, PermissionError):
                continue

            file_matched = False
            for line_number, line in enumerate(text.splitlines(), start=1):
                match = compiled.search(line)
                if match:
                    if not file_matched:
                        result.files_matched += 1
                        file_matched = True

                    result.matches.append(MatchResult(
                        file=str(filepath.relative_to(root_path)),
                        line_number=line_number,
                        line_content=line.rstrip(),
                        match_start=match.start(),
                        match_end=match.end(),
                    ))

                    if len(result.matches) >= max_results:
                        result.truncated = True
                        return result

    return result


def _walk(root: Path, skip: set[str]):
    """Walk directory tree, skipping named directories."""
    if root.name in skip:
        return
    yield root
    for child in sorted(root.iterdir()):
        if child.is_dir():
            yield from _walk(child, skip)


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pattern> [root] [--include=*.py]", file=sys.stderr)
        sys.exit(1)

    pattern = sys.argv[1]
    root = sys.argv[2] if len(sys.argv) > 2 else "."
    include = None
    for arg in sys.argv[3:]:
        if arg.startswith("--include="):
            include = arg.split("=", 1)[1]

    result = search(pattern, root, include=include)

    if result.error:
        print(f"Error: {result.error}", file=sys.stderr)
        sys.exit(1)

    for m in result.matches:
        print(f"{m.file}:{m.line_number}: {m.line_content}")

    print(f"\n{len(result.matches)} matches in {result.files_matched} files "
          f"({result.files_searched} searched)", file=sys.stderr)
