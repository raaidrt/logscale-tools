"""Placeholder tests for the LogScale query language parser."""

from __future__ import annotations

import pytest

from logscale_query_language.parser import parse


def test_parse_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        parse("error OR warning")
