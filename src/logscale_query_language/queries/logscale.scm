; Topiary formatting queries for LogScale query language
;
; These rules control how topiary formats LogScale queries.
; See https://topiary.tweag.io/ for the query format.

; Leaf nodes — do not touch internal whitespace
(quoted_string) @leaf
(regex_body) @leaf
(unquoted_pattern) @leaf
(identifier) @leaf
(number) @leaf
(comment) @leaf

; ---------------------------------------------------------------------------
; Pipeline
; ---------------------------------------------------------------------------

; Pipeline steps separated by pipes get newlines
(pipeline "|" @prepend_hardline @append_space)

; ---------------------------------------------------------------------------
; Case & Match
; ---------------------------------------------------------------------------

; Space before opening brace, then newline + indent
(case_expression "case" @append_space)
(case_expression "{" @append_hardline @append_indent_start)
(case_expression "}" @prepend_hardline @prepend_indent_end)

(match_expression "match" @prepend_space @append_space)
(match_expression "{" @append_hardline @append_indent_start)
(match_expression "}" @prepend_hardline @prepend_indent_end)

; Semicolons in case/match get newlines
(case_expression ";" @append_hardline)
(match_expression ";" @append_hardline)

; Match arrow
(match_pipeline "=>" @prepend_space @append_space)

; ---------------------------------------------------------------------------
; Subqueries
; ---------------------------------------------------------------------------

; Space around subquery braces
(subquery "{" @prepend_space @append_space)
(subquery "}" @prepend_space)

; ---------------------------------------------------------------------------
; Field comparisons
; ---------------------------------------------------------------------------

; Spaces around comparison operators in filters
(field_comparison
  [
    "="
    "!="
    "<"
    "<="
    ">"
    ">="
    "like"
  ] @prepend_space @append_space
)

; ---------------------------------------------------------------------------
; Logical operators (filters)
; ---------------------------------------------------------------------------

; Explicit AND / OR / NOT
(and_filter "AND" @prepend_space @append_space)
(or_filter "OR" @prepend_space @append_space)
(not_filter "NOT" @append_space)

; Implicit AND — space between consecutive filter children when no AND keyword.
; These use the `.` anchor to match consecutive named siblings.
(and_filter
  (_) @append_space
  .
  (_)
)

; ---------------------------------------------------------------------------
; Expressions
; ---------------------------------------------------------------------------

; Spaces around expression operators
(additive_operator) @prepend_space @append_space
(multiplicative_operator) @prepend_space @append_space
(comparison_operator) @prepend_space @append_space

; Spaces around shorthand operators
(eval_shorthand ":=" @prepend_space @append_space)
(eval_function_shorthand ":=" @prepend_space @append_space)
(field_shorthand "=~" @prepend_space @append_space)

; Parenthesized expressions — spaces inside parens are handled by default
(parenthesized_filter "(" @append_empty_softline)
(parenthesized_filter ")" @prepend_empty_softline)

; ---------------------------------------------------------------------------
; Function calls & commas
; ---------------------------------------------------------------------------

; Commas followed by space
(function_arguments "," @append_space)
(saved_query_arguments "," @append_space)
(array_expression "," @append_space)
