; Topiary formatting queries for LogScale query language
;
; These rules control how topiary formats LogScale queries.
; See https://topiary.tweag.io/ for the query format.

; Pipeline steps separated by pipes get newlines
(pipeline "|" @prepend_hardline)

; Indentation for case/match bodies
(case_expression "{" @append_hardline @append_indent_start)
(case_expression "}" @prepend_hardline @prepend_indent_end)
(match_expression "{" @append_hardline @append_indent_start)
(match_expression "}" @prepend_hardline @prepend_indent_end)

; Semicolons in case/match get newlines
(case_expression ";" @append_hardline)
(match_expression ";" @append_hardline)

; Spaces around operators
(field_comparison "=" @prepend_space @append_space)
(field_comparison "!=" @prepend_space @append_space)
(field_comparison "<" @prepend_space @append_space)
(field_comparison "<=" @prepend_space @append_space)
(field_comparison ">" @prepend_space @append_space)
(field_comparison ">=" @prepend_space @append_space)

; Spaces around expression operators
(additive_operator) @prepend_space @append_space
(multiplicative_operator) @prepend_space @append_space
(comparison_operator) @prepend_space @append_space

; Spaces around shorthand operators
(eval_shorthand ":=" @prepend_space @append_space)
(eval_function_shorthand ":=" @prepend_space @append_space)
(field_shorthand "=~" @prepend_space @append_space)

; Spaces around logical operators
(and_filter "AND" @prepend_space @append_space)
(or_filter "OR" @prepend_space @append_space)
(not_filter "NOT" @append_space)

; Commas followed by space
(function_arguments "," @append_space)
(saved_query_arguments "," @append_space)
(array_expression "," @append_space)

; Match arrow
(match_pipeline "=>" @prepend_space @append_space)
