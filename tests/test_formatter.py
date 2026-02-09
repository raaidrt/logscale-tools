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
        'foo = "bar"'
        " | sort(order=desc, field=_count, limit=100,"
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


def test_namespaced_function_in_eval_shorthand() -> None:
    query = (
        "#repo=main #is_canonical=true CANONICAL-SERVICE-LINE:"
        ' | a:=if(text:contains(field_name, substring="Substr"), then=1, else=0)'
    )
    result = format_query(query)
    assert "text:contains" in result
    assert "a :=" in result or "a:=" in result


def test_deeply_nested_long_lines_do_not_hang() -> None:
    inner = " | ".join(
        f"xf_{i} := if(in(field=zcode, values=[zvar_{i}]), then=1, else=0)"
        for i in range(40)
    )
    query = (
        f"#src=omega #flag=on TAG-MARKER: xyz = 999\n"
        f"| groupBy([mkey], function={{\n{inner}\n}})"
    )
    from logscale_query_language.formatter import _wrap_long_lines

    result = _wrap_long_lines(query)
    assert isinstance(result, str)
    assert len(result) > 0


class TestOperatorSpacing:
    """Spaces around operators in all contexts."""

    def test_eval_shorthand(self) -> None:
        result = format_query("a:=1+2")
        assert "a := 1 + 2" in result

    def test_eval_function_shorthand(self) -> None:
        result = format_query("a:=count()")
        assert "a := count()" in result

    def test_array_eval_function_shorthand(self) -> None:
        result = format_query("groupBy(field, function=[a:=count()])")
        assert "a := count()" in result

    def test_field_shorthand(self) -> None:
        result = format_query('a=~replace("x", with="y")')
        assert "a =~ replace(" in result

    def test_named_function_argument(self) -> None:
        result = format_query("groupBy(field=host, function=count())")
        assert "field = host" in result
        assert "function = count()" in result

    def test_saved_query_argument(self) -> None:
        result = format_query('$savedQuery(a=1, b="two")')
        assert "a = 1" in result
        assert 'b = "two"' in result

    def test_field_comparison_eq(self) -> None:
        result = format_query('status="ok"')
        assert 'status = "ok"' in result

    def test_field_comparison_neq(self) -> None:
        result = format_query('status!="ok"')
        assert 'status != "ok"' in result

    def test_field_comparison_lt(self) -> None:
        result = format_query("count<10")
        assert "count < 10" in result

    def test_field_comparison_lte(self) -> None:
        result = format_query("count<=10")
        assert "count <= 10" in result

    def test_field_comparison_gt(self) -> None:
        result = format_query("count>10")
        assert "count > 10" in result

    def test_field_comparison_gte(self) -> None:
        result = format_query("count>=10")
        assert "count >= 10" in result

    def test_field_comparison_like(self) -> None:
        result = format_query("host like *web*")
        assert "host like *web*" in result

    def test_additive_operator(self) -> None:
        result = format_query("a:=x+y-z")
        assert "x + y - z" in result

    def test_multiplicative_operator(self) -> None:
        result = format_query("a:=x*y/z")
        assert "x * y / z" in result

    def test_comparison_operator(self) -> None:
        result = format_query("a:=if(x>0, then=1, else=0)")
        assert "x > 0" in result

    def test_and_spacing(self) -> None:
        result = format_query('a="1" AND b="2"')
        assert " AND " in result

    def test_or_spacing(self) -> None:
        result = format_query('a="1" OR b="2"')
        assert " OR " in result

    def test_not_spacing(self) -> None:
        result = format_query('NOT a="1"')
        assert "NOT " in result


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
