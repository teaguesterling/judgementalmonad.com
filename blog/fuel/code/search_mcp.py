"""
search_mcp.py — MCP tool wrapper for structured codebase search.

Replaces: Bash("grep -r pattern path")
Exposes search_tool.search() as an MCP tool with typed parameters.

From Ratchet Fuel Post 5: Closing the Channel
https://judgementalmonad.com/blog/fuel/05-closing-the-channel
"""

from mcp.server.fastmcp import FastMCP

from search_tool import search, SearchResult

server = FastMCP("codebase-search")


@server.tool()
def codebase_search(
    pattern: str,
    root: str = ".",
    include: str | None = None,
    max_results: int = 200,
    case_sensitive: bool = True,
) -> str:
    """Search codebase files for a regex pattern.

    Returns structured match results with file paths,
    line numbers, and match content. Read-only operation.
    """
    result = search(
        pattern=pattern,
        root=root,
        include=include,
        max_results=max_results,
        case_sensitive=case_sensitive,
    )
    return _format_result(result)


def _format_result(result: SearchResult) -> str:
    """Format SearchResult for LLM consumption."""
    if result.error:
        return f"Search error: {result.error}"

    lines = [
        f"Found {len(result.matches)} matches "
        f"in {result.files_matched} files "
        f"({result.files_searched} files searched)",
    ]

    if result.truncated:
        lines.append(f"(truncated at {len(result.matches)} results)")

    lines.append("")

    current_file = None
    for match in result.matches:
        if match.file != current_file:
            current_file = match.file
            lines.append(f"--- {current_file} ---")
        lines.append(f"{match.line_number}: {match.line_content}")

    return "\n".join(lines)


if __name__ == "__main__":
    server.run()
