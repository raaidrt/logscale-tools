"""Formatter for LogScale queries, powered by topiary."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

_BIN_DIR = Path(__file__).parent / "bin"
_TOPIARY_BIN = _BIN_DIR / ("topiary.exe" if sys.platform == "win32" else "topiary")
_QUERIES_DIR = Path(__file__).resolve().parent / "queries"
_DEFAULT_QUERY_FILE = _QUERIES_DIR / "logscale.scm"

_GRAMMAR_SRC_DIR = (
    Path(__file__).resolve().parent.parent.parent / "tree-sitter-logscale" / "src"
)
_LIB_DIR = Path(__file__).resolve().parent / "lib"
_LIB_EXT = ".dylib" if sys.platform == "darwin" else ".so"
_LIB_PATH = _LIB_DIR / f"logscale{_LIB_EXT}"


def _build_grammar() -> Path:
    """Compile the tree-sitter grammar C sources into a shared library.

    Returns:
        Path to the compiled shared library.

    Raises:
        FileNotFoundError: If the grammar source files are not found.
        RuntimeError: If compilation fails.
    """
    parser_c = _GRAMMAR_SRC_DIR / "parser.c"
    scanner_c = _GRAMMAR_SRC_DIR / "scanner.c"

    if not parser_c.exists():
        raise FileNotFoundError(
            f"Grammar source not found at {_GRAMMAR_SRC_DIR}. "
            "Ensure the tree-sitter-logscale directory is present."
        )

    _LIB_DIR.mkdir(parents=True, exist_ok=True)

    sources = [str(parser_c)]
    if scanner_c.exists():
        sources.append(str(scanner_c))

    if sys.platform == "darwin":
        shared_flag = "-dynamiclib"
    else:
        shared_flag = "-shared"

    cmd = [
        "cc",
        shared_flag,
        "-fPIC",
        "-O2",
        "-I",
        str(_GRAMMAR_SRC_DIR),
        *sources,
        "-o",
        str(_LIB_PATH),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Failed to compile tree-sitter grammar: {result.stderr}")

    return _LIB_PATH


def get_topiary_path() -> Path:
    """Return the path to the bundled topiary-cli binary.

    Raises:
        FileNotFoundError: If the binary has not been installed.
    """
    if not _TOPIARY_BIN.exists():
        raise FileNotFoundError(
            f"topiary-cli not found at {_TOPIARY_BIN}. "
            "Run `uv build` or `pip install -e .` to download it."
        )
    return _TOPIARY_BIN


def format_query(
    query: str,
    *,
    query_file: str | Path | None = None,
) -> str:
    """Format a LogScale query string using topiary.

    Args:
        query: A LogScale query string.
        query_file: Path to a topiary .scm query file for formatting rules.
            Defaults to the bundled logscale.scm.

    Returns:
        The formatted query string.

    Raises:
        FileNotFoundError: If the topiary binary is not installed.
        RuntimeError: If topiary exits with an error.
    """
    topiary = get_topiary_path()

    if not _LIB_PATH.exists():
        _build_grammar()

    scm_path = Path(query_file) if query_file else _DEFAULT_QUERY_FILE
    if not scm_path.exists():
        raise FileNotFoundError(
            f"Topiary query file not found at {scm_path}. "
            "Provide a .scm formatting query file."
        )

    config = _make_topiary_config(_LIB_PATH)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ncl", delete=False) as cfg_file:
        cfg_file.write(config)
        cfg_path = cfg_file.name

    try:
        cmd = [
            str(topiary),
            "format",
            "--language",
            "logscale",
            "--query",
            str(scm_path),
            "--configuration",
            cfg_path,
            "--skip-idempotence",
        ]

        result = subprocess.run(
            cmd,
            input=query,
            capture_output=True,
            text=True,
        )
    finally:
        Path(cfg_path).unlink(missing_ok=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"topiary exited with code {result.returncode}: {result.stderr}"
        )

    return _wrap_long_lines(result.stdout)


_MAX_LINE_LENGTH = 80


def _find_wrap_point(line: str, limit: int) -> int | None:
    """Find the best position to wrap *line* at or before *limit*.

    Preference order:
      1. After a comma+space inside function arguments (top-level parens).
      2. Before ``AND`` / ``OR`` keywords (with surrounding spaces).

    Returns the character index where the new line should start, or *None*
    if no suitable break point is found.
    """
    depth = 0
    best_comma: int | None = None
    in_string = False
    escape = False

    for i, ch in enumerate(line):
        if i >= limit and (best_comma is not None):
            break

        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue

        if ch == "(" or ch == "[":
            depth += 1
        elif ch == ")" or ch == "]":
            depth = max(depth - 1, 0)

        if ch == "," and i + 1 < len(line) and i < limit:
            best_comma = i + 2 if (i + 1 < len(line) and line[i + 1] == " ") else i + 1

    if best_comma is not None and best_comma <= limit:
        last_good = best_comma
        for i in range(best_comma, len(line)):
            if i > limit:
                break
            ch = line[i]
            if not in_string and ch == ",":
                if i + 1 < len(line) and line[i + 1] == " ":
                    last_good = i + 2
                else:
                    last_good = i + 1
        best_comma = last_good

    for keyword in (" AND ", " OR "):
        idx = line.rfind(keyword, 0, limit + 1)
        if idx != -1:
            kw_break = idx + 1
            if best_comma is None or abs(limit - kw_break) < abs(limit - best_comma):
                return kw_break

    return best_comma


def _wrap_long_lines(text: str, limit: int = _MAX_LINE_LENGTH) -> str:
    """Wrap lines exceeding *limit* characters."""
    result_lines: list[str] = []
    for line in text.split("\n"):
        if len(line) <= limit:
            result_lines.append(line)
            continue

        indent = len(line) - len(line.lstrip())
        continuation_indent = indent + 2

        first_paren = -1
        in_str = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_str = not in_str
            elif not in_str and ch == "(":
                first_paren = i
                break

        if first_paren != -1:
            continuation_indent = first_paren + 1

        remaining = line
        while len(remaining) > limit:
            wp = _find_wrap_point(remaining, limit)
            if wp is None or wp <= indent:
                break
            result_lines.append(remaining[:wp].rstrip())
            remaining = " " * continuation_indent + remaining[wp:].lstrip()
        result_lines.append(remaining)

    return "\n".join(result_lines)


def _make_topiary_config(grammar_path: Path) -> str:
    """Generate a Nickel configuration for topiary with the logscale language."""
    escaped = str(grammar_path).replace("\\", "\\\\").replace('"', '\\"')
    return (
        "{\n"
        "  languages = {\n"
        "    logscale = {\n"
        '      extensions = ["logscale", "lql"],\n'
        f'      grammar.source.path = "{escaped}",\n'
        "    },\n"
        "  },\n"
        "}\n"
    )
