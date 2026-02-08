"""Tests for the LogScale query formatter."""

from __future__ import annotations

from logscale_query_language.formatter import (
    _DEFAULT_QUERY_FILE,
    get_topiary_path,
)


def test_query_file_exists() -> None:
    assert _DEFAULT_QUERY_FILE.exists()


def test_get_topiary_path() -> None:
    path = get_topiary_path()
    assert path.exists()
