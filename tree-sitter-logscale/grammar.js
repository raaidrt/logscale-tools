/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

// Character classes from grammar.md Section 12
// UnquotedFieldNameChar: #, %, &, ., 0-9, @, A-Z, \, ^, _, a-z, Latin-1 supplement ranges
const UNQUOTED_FIELD_NAME_CHAR =
  /[#%&.0-9@A-Z\\^_a-z\u00A1-\u00AA\u00AE-\u00BA\u00BC-\u00FF]/;

// UnquotedPatternChar WITHOUT colon: all of UnquotedFieldNameChar plus *, +, -, ~, ¬
// Colon is handled at the grammar rule level to avoid lexer greediness conflicts
// with := (eval shorthand) and namespaced function names (text:contains).
const UNQUOTED_PATTERN_CHAR_NO_COLON =
  /[#%&*.+\-~0-9@A-Z\\^_a-z\u00A1-\u00AA\u00AC\u00AE-\u00BA\u00BC-\u00FF]/;

// Characters that distinguish a pattern segment from an identifier (excluding colon)
const PATTERN_EXTRA_CHAR = /[*+\-~\u00AC]/;

// Precedence levels (from grammar.md Appendix C)
const PREC = {
  AND: 1,
  OR: 2,
  NOT: 3,
  COMPARISON: 4,
  ADDITIVE: 5,
  MULTIPLICATIVE: 6,
  UNARY: 7,
};

module.exports = grammar({
  name: "logscale",

  extras: ($) => [/\s/, $.comment],

  externals: ($) => [$._regex_start],

  conflicts: ($) => [
    // function_call as primary_expression vs eval_function_shorthand
    [$._primary_expression, $.eval_function_shorthand],
    // identifier in filter context: free text pattern vs function name
    [$.free_text_pattern, $.function_name],
  ],

  rules: {
    // Section 1: Query & Pipeline
    query: ($) => optional($.pipeline),

    pipeline: ($) =>
      seq($._pipeline_step, repeat(seq("|", $._pipeline_step))),

    _pipeline_step: ($) =>
      choice(
        $.case_expression,
        $.match_expression,
        $.eval_function_shorthand,
        $.eval_shorthand,
        $.field_shorthand,
        $.stats_shorthand,
        $.saved_query,
        $.function_call,
        $.filter,
      ),

    // Section 2: Filters
    // AND binds less tightly than OR (inverted from most languages)
    filter: ($) => $._logical_and_filter,

    _logical_and_filter: ($) =>
      choice($.and_filter, $._logical_or_filter),

    and_filter: ($) =>
      prec.left(
        PREC.AND,
        seq(
          $._logical_or_filter,
          repeat1(seq(optional("AND"), $._logical_or_filter)),
        ),
      ),

    _logical_or_filter: ($) => choice($.or_filter, $._unary_filter),

    or_filter: ($) =>
      prec.left(
        PREC.OR,
        seq($._unary_filter, repeat1(seq("OR", $._unary_filter))),
      ),

    _unary_filter: ($) => choice($.not_filter, $._primary_filter),

    not_filter: ($) =>
      prec(PREC.NOT, seq("NOT", $._unary_filter)),

    _primary_filter: ($) =>
      choice(
        $.field_comparison,
        $.free_text_pattern,
        $.true_literal,
        $.false_literal,
        $.parenthesized_filter,
      ),

    true_literal: (_) => "true",
    false_literal: (_) => "false",

    parenthesized_filter: ($) => seq("(", $.filter, ")"),

    field_comparison: ($) =>
      choice(
        seq($.field_name, "=", $.equality_pattern),
        seq($.field_name, "like", $.like_pattern),
        seq($.field_name, "!=", $.equality_pattern),
        seq($.field_name, "<", $.number),
        seq($.field_name, "<=", $.number),
        seq($.field_name, ">", $.number),
        seq($.field_name, ">=", $.number),
      ),

    // Section 3: Patterns
    free_text_pattern: ($) =>
      choice(
        $.unquoted_pattern,
        $.identifier,
        $.quoted_string,
        $.regex,
        $.query_parameter,
      ),

    like_pattern: ($) =>
      choice($.unquoted_pattern, $.identifier, $.quoted_string, $.query_parameter),

    equality_pattern: ($) =>
      choice($.anchored_pattern, $.regex, $.query_parameter),

    anchored_pattern: ($) =>
      choice($.unquoted_pattern, $.identifier, $.quoted_string),

    // Section 4: Expressions
    expression: ($) => $._comparative_expression,

    _comparative_expression: ($) =>
      choice($.comparison_expression, $._additive_expression),

    comparison_expression: ($) =>
      prec.left(
        PREC.COMPARISON,
        seq(
          $._additive_expression,
          $.comparison_operator,
          $._additive_expression,
        ),
      ),

    comparison_operator: (_) =>
      choice("==", "!=", ">=", "<=", ">", "<", "<=>"),

    _additive_expression: ($) =>
      choice($.additive_expression, $._multiplicative_expression),

    additive_expression: ($) =>
      prec.left(
        PREC.ADDITIVE,
        seq(
          $._multiplicative_expression,
          $.additive_operator,
          $._additive_expression,
        ),
      ),

    additive_operator: (_) => choice("+", "-"),

    _multiplicative_expression: ($) =>
      choice($.multiplicative_expression, $._unary_expression),

    multiplicative_expression: ($) =>
      prec.left(
        PREC.MULTIPLICATIVE,
        seq(
          $._unary_expression,
          $.multiplicative_operator,
          $._multiplicative_expression,
        ),
      ),

    multiplicative_operator: (_) => choice("*", "/", "%"),

    _unary_expression: ($) =>
      choice($.unary_expression, $._primary_expression),

    unary_expression: ($) =>
      prec(PREC.UNARY, seq($.unary_operator, $._unary_expression)),

    unary_operator: (_) => choice("-", "!"),

    _primary_expression: ($) =>
      choice(
        $.parenthesized_expression,
        $.subquery,
        $.function_call,
        $.array_expression,
        $.query_parameter,
        $.number,
        $.identifier,
        $.quoted_string,
      ),

    parenthesized_expression: ($) => seq("(", $.expression, ")"),

    // Section 5: Function Calls
    function_call: ($) =>
      seq($.function_name, "(", optional($.function_arguments), ")"),

    function_name: ($) =>
      choice($.namespaced_identifier, $.identifier),

    namespaced_identifier: (_) =>
      token(
        prec(2, seq(
          repeat1(UNQUOTED_FIELD_NAME_CHAR),
          ":",
          repeat1(UNQUOTED_FIELD_NAME_CHAR),
        )),
      ),

    function_arguments: ($) =>
      seq($._function_argument, repeat(seq(",", $._function_argument))),

    _function_argument: ($) =>
      choice($.named_function_argument, $.unnamed_function_argument),

    named_function_argument: ($) =>
      prec.dynamic(1, seq($.field_name, "=", $.expression)),

    unnamed_function_argument: ($) => $.expression,

    // Section 6: Shorthands
    eval_shorthand: ($) => seq($.field_name, ":=", $.expression),

    eval_function_shorthand: ($) =>
      prec.dynamic(1, seq($.field_name, ":=", $.function_call)),

    field_shorthand: ($) => seq($.field_name, "=~", $.function_call),

    stats_shorthand: ($) => $.array_expression,

    // Section 7: Arrays
    array_expression: ($) =>
      seq(
        "[",
        optional(seq($._array_element, repeat(seq(",", $._array_element)))),
        "]",
      ),

    _array_element: ($) =>
      choice(
        alias($.eval_function_shorthand, $.array_eval_function_shorthand),
        $.expression,
      ),

    // Section 8: Subqueries
    subquery: ($) =>
      seq(optional(seq($.identifier, ":")), "{", $.pipeline, "}"),

    // Section 9: Case & Match
    case_expression: ($) =>
      seq("case", "{", $.pipeline, repeat(seq(";", $.pipeline)), "}"),

    match_expression: ($) =>
      seq(
        $.field_name,
        "match",
        "{",
        $.match_pipeline,
        repeat(seq(";", $.match_pipeline)),
        "}",
      ),

    match_pipeline: ($) => seq($.match_guard, "=>", $.pipeline),

    match_guard: ($) =>
      choice(
        "*",
        $.regex,
        $.function_call,
        $.query_parameter,
        $.anchored_pattern,
      ),

    // Section 10: Saved Queries & Query Parameters
    saved_query: ($) =>
      seq(
        "$",
        choice($.unquoted_pattern, $.identifier, $.quoted_string),
        "(",
        optional($.saved_query_arguments),
        ")",
      ),

    saved_query_arguments: ($) =>
      seq(
        $.saved_query_argument,
        repeat(seq(",", $.saved_query_argument)),
      ),

    saved_query_argument: ($) =>
      seq(
        choice($.unquoted_pattern, $.identifier, $.quoted_string),
        "=",
        choice($.unquoted_pattern, $.identifier, $.quoted_string),
      ),

    query_parameter: ($) =>
      choice(
        seq("?", $._query_parameter_name),
        seq(
          "?{",
          $._query_parameter_name,
          "=",
          $._query_parameter_default,
          "}",
        ),
      ),

    _query_parameter_name: ($) =>
      choice($.unquoted_pattern, $.identifier, $.quoted_string),

    _query_parameter_default: ($) =>
      choice($.unquoted_pattern, $.identifier, $.quoted_string),

    // Section 11: Lexical Rules

    // field_name can be a quoted string or an identifier with optional array index
    field_name: ($) =>
      choice(
        seq($.identifier, optional($.array_index)),
        $.quoted_string,
      ),

    array_index: ($) => seq("[", /[0-9]+/, "]"),

    // identifier: any sequence of field name chars.
    identifier: (_) => token(repeat1(UNQUOTED_FIELD_NAME_CHAR)),

    quoted_string: (_) =>
      token(
        seq(
          '"',
          repeat(
            choice(
              /[^"\\\n]/,
              /\\["\\/n]/,
            ),
          ),
          '"',
        ),
      ),

    // number has higher token precedence than identifier to win on digit-only strings
    number: (_) =>
      token(prec(1, seq(/[0-9]+/, optional(seq(".", /[0-9]+/))))),

    // unquoted_pattern: composed of segments joined by colons.
    // Colon is excluded from the token-level pattern chars to prevent
    // the lexer from greedily consuming e.g. "a:" before ":=" can be matched.
    // A pattern segment is a token containing at least one pattern-extra char
    // (*, +, -, ~, ¬) but no colon.
    _pattern_segment: ($) =>
      choice($._unquoted_pattern_segment, $.identifier),

    _unquoted_pattern_segment: (_) =>
      token(
        seq(
          repeat(UNQUOTED_PATTERN_CHAR_NO_COLON),
          PATTERN_EXTRA_CHAR,
          repeat(UNQUOTED_PATTERN_CHAR_NO_COLON),
        ),
      ),

    unquoted_pattern: ($) =>
      choice(
        $._unquoted_pattern_segment,
        seq(
          $._pattern_segment,
          repeat1(seq(":", optional($._pattern_segment))),
        ),
      ),

    // Regular expression: handled via external scanner for disambiguation
    regex: ($) =>
      seq($._regex_start, $.regex_body, "/", optional($.regex_flags)),

    regex_body: (_) => token(repeat1(choice(/[^/\\\n]/, /\\[^\n]/))),

    regex_flags: (_) => token(/[dmi]+/),

    comment: (_) => token(seq("//", /[^\n]*/)),
  },
});
