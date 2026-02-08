"""Placeholder tests for the LogScale query formatter."""

from __future__ import annotations

import pytest

from logscale_query_language.formatter import format_query


def test_format_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        format_query("error OR warning")
