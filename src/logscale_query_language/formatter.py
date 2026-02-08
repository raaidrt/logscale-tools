"""Formatter for LogScale queries, powered by topiary."""

from __future__ import annotations

import sys
from pathlib import Path

_BIN_DIR = Path(__file__).parent / "bin"
_TOPIARY_BIN = _BIN_DIR / ("topiary.exe" if sys.platform == "win32" else "topiary")


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


def format_query(query: str) -> str:
    """Format a LogScale query string using topiary.

    Args:
        query: A LogScale query string.

    Returns:
        The formatted query string.

    Raises:
        NotImplementedError: Formatter is not yet implemented.
    """
    raise NotImplementedError("Formatter not yet implemented")
