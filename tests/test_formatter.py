"""Tests for the LogScale query formatter."""

from __future__ import annotations

from logscale_query_language.formatter import (
    _DEFAULT_QUERY_FILE,
    format_query,
    get_topiary_path,
)


def test_query_file_exists() -> None:
    assert _DEFAULT_QUERY_FILE.exists()


def test_get_topiary_path() -> None:
    path = get_topiary_path()
    assert path.exists()


def test_long_function_args_wrap() -> None:
    query = (
        'foo = "bar"'
        " | groupBy(field=[host, source, sourcetype],"
        " function=[count(), sum(bytes), avg(duration)])"
    )
    result = format_query(query)
    for line in result.splitlines():
        assert len(line) <= 80, f"Line exceeds 80 chars ({len(line)}): {line!r}"


def test_long_filter_wraps() -> None:
    query = (
        'status = "error" AND host = "webserver01.example.com"'
        ' AND source = "/var/log/application/debug.log"'
    )
    result = format_query(query)
    for line in result.splitlines():
        assert len(line) <= 80, f"Line exceeds 80 chars ({len(line)}): {line!r}"


def test_short_line_no_wrap() -> None:
    query = 'foo = "bar" | count()'
    result = format_query(query)
    assert result.strip() == 'foo = "bar"\n| count()'


def test_long_pipeline_step_wraps() -> None:
    query = (
        "| sort(order=desc, field=_count, limit=100,"
        ' type="alphabetical", locale="en_US")'
    )
    result = format_query(query)
    for line in result.splitlines():
        assert len(line) <= 80, f"Line exceeds 80 chars ({len(line)}): {line!r}"


def test_long_implicit_and_filters_wrap() -> None:
    query = (
        "#repo=main #is_canonical=true CANONICAL-MANAGE-LINE:"
        " a=alpha b=beta c=gamma d=delta e=epsilon f=figma"
    )
    assert len(query) > 80
    result = format_query(query)
    for line in result.splitlines():
        assert len(line) <= 80, f"Line exceeds 80 chars ({len(line)}): {line!r}"


def test_field_comparison_not_split_across_lines() -> None:
    query = (
        "#repo=main #is_canonical=true CANONICAL-MANAGE-LINE:"
        " a=alpha b=beta c=gamma d=delta e=epsilon f=figma"
    )
    result = format_query(query)
    for line in result.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        assert not stripped.startswith("= "), (
            f"Line starts with bare '=', field comparison was split: {line!r}"
        )
        assert not stripped.endswith(" ="), (
            f"Line ends with bare '=', field comparison was split: {line!r}"
        )
        for op in ("!=", "<=", ">=", "=~", ":=", "=", "<", ">"):
            assert not stripped.startswith(op + " "), (
                f"Line starts with operator '{op}', split mid-comparison: {line!r}"
            )
            assert not stripped.endswith(" " + op), (
                f"Line ends with operator '{op}', split mid-comparison: {line!r}"
            )
