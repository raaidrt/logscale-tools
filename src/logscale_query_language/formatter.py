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

    return result.stdout


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
