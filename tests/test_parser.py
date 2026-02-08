"""Tests for the LogScale query language parser."""

from __future__ import annotations

import pytest

from logscale_query_language.parser import (
    get_language,
    parse,
    parse_to_dict,
    tree_to_sexp,
)


def test_get_language() -> None:
    lang = get_language()
    assert lang is not None


def test_parse_returns_tree() -> None:
    tree = parse("error OR warning")
    assert tree is not None
    assert tree.root_node is not None


def test_parse_no_error() -> None:
    tree = parse("error OR warning")
    assert not tree.root_node.has_error


def test_parse_to_dict_with_query() -> None:
    result = parse_to_dict(query="error")
    assert isinstance(result, dict)
    assert "type" in result
    assert "children" in result
    assert result["has_error"] is False


def test_parse_to_dict_with_node() -> None:
    tree = parse("error")
    result = parse_to_dict(node=tree.root_node)
    assert isinstance(result, dict)
    assert result["type"] == tree.root_node.type


def test_parse_to_dict_raises_without_args() -> None:
    with pytest.raises(ValueError, match="Either node or query"):
        parse_to_dict()


def test_tree_to_sexp() -> None:
    sexp = tree_to_sexp("error")
    assert isinstance(sexp, str)
    assert len(sexp) > 0


class TestParseNoError:
    """All queries should parse without errors."""

    @pytest.mark.parametrize(
        "query",
        [
            pytest.param("", id="empty_query"),
            pytest.param("error | count()", id="simple_pipeline"),
            pytest.param("error | count() | sort(_count)", id="multi_step_pipeline"),
            pytest.param("status = 200", id="field_equality"),
            pytest.param("status != error", id="field_inequality"),
            pytest.param("status < 400", id="numeric_comparison"),
            pytest.param("error OR warning", id="or_filter"),
            pytest.param("error warning", id="implicit_and_filter"),
            pytest.param("error AND warning", id="explicit_and_filter"),
            pytest.param("NOT error", id="not_filter"),
            pytest.param("(error OR warning) AND critical", id="parenthesized_filter"),
            pytest.param("true", id="true_literal"),
            pytest.param("false", id="false_literal"),
            pytest.param("host like server*", id="like_filter"),
            pytest.param("x := 1 + 2", id="eval_shorthand"),
            pytest.param("x := lower(host)", id="eval_function_shorthand"),
            pytest.param('host =~ regex("web-.*")', id="field_shorthand"),
            pytest.param("groupBy(field=host)", id="function_named_args"),
            pytest.param(
                "case { error | count() ; warning | count() }", id="case_expression"
            ),
            pytest.param("x := { error | count() }", id="subquery"),
            pytest.param("[count(), avg(duration)]", id="stats_shorthand"),
            pytest.param("$myQuery()", id="saved_query"),
            pytest.param("?param", id="query_parameter"),
            pytest.param('"connection timeout"', id="quoted_string"),
        ],
    )
    def test_no_parse_error(self, query: str) -> None:
        tree = parse(query)
        assert not tree.root_node.has_error


class TestEmptyQuery:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("")
        assert sexp == "(query)"

    def test_dict_no_children(self) -> None:
        result = parse_to_dict(query="")
        assert result["type"] == "query"
        assert result["children"] == []


class TestSimplePipeline:
    def test_sexp_contains_pipeline_and_function(self) -> None:
        sexp = tree_to_sexp("error | count()")
        assert "pipeline" in sexp
        assert "function_call" in sexp
        assert "free_text_pattern" in sexp

    def test_dict_structure(self) -> None:
        result = parse_to_dict(query="error | count()")
        pipeline = result["children"][0]
        assert pipeline["type"] == "pipeline"
        step_types = [c["type"] for c in pipeline["children"] if c["type"] != "|"]
        assert "filter" in step_types
        assert "function_call" in step_types


class TestMultiStepPipeline:
    def test_sexp_has_pipeline(self) -> None:
        sexp = tree_to_sexp("error | count() | sort(_count)")
        assert "pipeline" in sexp

    def test_multiple_pipe_separators(self) -> None:
        result = parse_to_dict(query="error | count() | sort(_count)")
        pipeline = result["children"][0]
        pipes = [c for c in pipeline["children"] if c["type"] == "|"]
        assert len(pipes) == 2


class TestFieldComparisons:
    def test_equality_sexp(self) -> None:
        sexp = tree_to_sexp("status = 200")
        assert "field_comparison" in sexp
        assert "field_name" in sexp
        assert "equality_pattern" in sexp

    def test_inequality_sexp(self) -> None:
        sexp = tree_to_sexp("status != error")
        assert "field_comparison" in sexp
        assert "equality_pattern" in sexp

    def test_numeric_comparison_sexp(self) -> None:
        sexp = tree_to_sexp("status < 400")
        assert "field_comparison" in sexp
        assert "number" in sexp


class TestLogicalFilters:
    def test_or_filter_sexp(self) -> None:
        sexp = tree_to_sexp("error OR warning")
        assert "or_filter" in sexp

    def test_implicit_and_sexp(self) -> None:
        sexp = tree_to_sexp("error warning")
        assert "and_filter" in sexp

    def test_explicit_and_sexp(self) -> None:
        sexp = tree_to_sexp("error AND warning")
        assert "and_filter" in sexp

    def test_not_filter_sexp(self) -> None:
        sexp = tree_to_sexp("NOT error")
        assert "not_filter" in sexp

    def test_parenthesized_filter_sexp(self) -> None:
        sexp = tree_to_sexp("(error OR warning) AND critical")
        assert "parenthesized_filter" in sexp
        assert "or_filter" in sexp
        assert "and_filter" in sexp


class TestBooleanLiterals:
    def test_true_literal(self) -> None:
        sexp = tree_to_sexp("true")
        assert "true_literal" in sexp

    def test_false_literal(self) -> None:
        sexp = tree_to_sexp("false")
        assert "false_literal" in sexp


class TestLikeFilter:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("host like server*")
        assert "field_comparison" in sexp
        assert "like_pattern" in sexp
        assert "unquoted_pattern" in sexp


class TestEvalShorthand:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("x := 1 + 2")
        assert "eval_shorthand" in sexp
        assert "additive_expression" in sexp
        assert "additive_operator" in sexp
        assert "number" in sexp


class TestEvalFunctionShorthand:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("x := lower(host)")
        assert "eval_function_shorthand" in sexp
        assert "function_call" in sexp
        assert "field_name" in sexp


class TestFieldShorthand:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp('host =~ regex("web-.*")')
        assert "field_shorthand" in sexp
        assert "function_call" in sexp
        assert "quoted_string" in sexp


class TestFunctionNamedArgs:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("groupBy(field=host)")
        assert "function_call" in sexp
        assert "named_function_argument" in sexp
        assert "function_arguments" in sexp


class TestCaseExpression:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("case { error | count() ; warning | count() }")
        assert "case_expression" in sexp
        assert sexp.count("pipeline") >= 2

    def test_dict_has_two_pipelines(self) -> None:
        result = parse_to_dict(query="case { error | count() ; warning | count() }")
        pipeline = result["children"][0]
        case_expr = next(
            c for c in pipeline["children"] if c["type"] == "case_expression"
        )
        inner_pipelines = [c for c in case_expr["children"] if c["type"] == "pipeline"]
        assert len(inner_pipelines) == 2


class TestSubquery:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("x := { error | count() }")
        assert "subquery" in sexp
        assert "eval_shorthand" in sexp

    def test_subquery_contains_pipeline(self) -> None:
        sexp = tree_to_sexp("x := { error | count() }")
        assert "pipeline" in sexp
        assert "function_call" in sexp


class TestStatsShorthand:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("[count(), avg(duration)]")
        assert "stats_shorthand" in sexp
        assert "array_expression" in sexp
        assert "function_call" in sexp


class TestSavedQuery:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("$myQuery()")
        assert "saved_query" in sexp

    def test_dict_structure(self) -> None:
        result = parse_to_dict(query="$myQuery()")
        pipeline = result["children"][0]
        saved = next(c for c in pipeline["children"] if c["type"] == "saved_query")
        assert saved["type"] == "saved_query"


class TestQueryParameter:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp("?param")
        assert "query_parameter" in sexp

    def test_nested_in_free_text(self) -> None:
        sexp = tree_to_sexp("?param")
        assert "free_text_pattern" in sexp


class TestQuotedString:
    def test_sexp(self) -> None:
        sexp = tree_to_sexp('"connection timeout"')
        assert "quoted_string" in sexp

    def test_nested_in_free_text(self) -> None:
        sexp = tree_to_sexp('"connection timeout"')
        assert "free_text_pattern" in sexp
