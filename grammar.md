# CrowdStrike Query Language — BNF Grammar Specification

> Derived from the official CrowdStrike/LogScale grammar documentation.
> This grammar is intended for **programmatically generating** LogScale queries,
> not for parsing them. The actual LogScale parser contains additional quirks
> (see [Appendix D](#appendix-d--quirks--edge-cases)).

---

## 1. Query & Pipeline

```bnf
Query            ::= Pipeline?

Pipeline         ::= PipelineStep ( '|' PipelineStep )*

PipelineStep     ::= Filter
                    | FunctionCall
                    | EvalFunctionShorthand
                    | EvalShorthand
                    | FieldShorthand
                    | Case
                    | Match
                    | StatsShorthand
                    | SavedQuery
```

## 2. Filters

OR binds **more tightly** than AND (reversed from most languages).
Adjacent filters without an explicit operator are joined by implicit AND.

```bnf
Filter           ::= LogicalAndFilter

LogicalAndFilter ::= LogicalOrFilter ( 'AND'? LogicalOrFilter )*

LogicalOrFilter  ::= UnaryFilter ( 'OR' UnaryFilter )*

UnaryFilter      ::= 'NOT'* PrimaryFilter

PrimaryFilter    ::= FieldName '='  EqualityPattern
                    | FieldName 'like' LikePattern
                    | FieldName '!=' EqualityPattern
                    | FieldName '<'  Number
                    | FieldName '<=' Number
                    | FieldName '>'  Number
                    | FieldName '>=' Number
                    | FreeTextPattern
                    | 'true'
                    | 'false'
                    | '(' Filter ')'
```

## 3. Patterns

```bnf
FreeTextPattern      ::= UnquotedPattern
                        | QuotedString
                        | Regex
                        | QueryParameter

LikePattern          ::= UnquotedPattern
                        | QuotedString
                        | QueryParameter

EqualityPattern      ::= AnchoredPattern
                        | Regex
                        | QueryParameter

AnchoredPattern      ::= UnquotedPattern
                        | QuotedString
```

### Pattern semantics

| Context | Anchoring | Wildcard `*` |
|---|---|---|
| **FreeTextPattern** | Unanchored — implicit `*…*` wrapping | Glob-style wildcard |
| **EqualityPattern** | Anchored — exact match by default | Glob-style; lone `*` tests field **presence**, not `true` |
| **LikePattern** | Anchored | `*` is a wildcard |

- Empty string patterns and multiple consecutive `*` collapse to the base wildcard.
- The `*` wildcard **cannot** be escaped in anchored patterns.

## 4. Expressions

```bnf
Expression              ::= ComparativeExpression ExpressionAttribute*

ExpressionAttribute     ::= Identifier ':' ComparativeExpression

ComparativeExpression   ::= AdditiveExpression
                           ( ComparisonOperator AdditiveExpression )?

ComparisonOperator      ::= '==' | '!=' | '>=' | '<=' | '>' | '<' | '<=>'

AdditiveExpression      ::= MultiplicativeExpression
                           ( AdditiveOperator MultiplicativeExpression )*

AdditiveOperator        ::= '+' | '-'

MultiplicativeExpression ::= UnaryExpression
                            ( MultiplicativeOperator UnaryExpression )*

MultiplicativeOperator  ::= '*' | '/' | '%'

UnaryExpression         ::= UnaryOperator? PrimaryExpression

UnaryOperator           ::= '-' | '!'

PrimaryExpression       ::= '(' Expression ')'
                           | Subquery
                           | FunctionCall
                           | ArrayExpression
                           | QueryParameter
                           | BareWord
                           | QuotedString

BareWord                ::= FieldName | UnquotedPattern
```

> The `<=>` link operator was added in **v1.192+**.

## 5. Function Calls

```bnf
FunctionCall          ::= FunctionName '(' FunctionArguments? ')'

FunctionName          ::= Identifier

FunctionArguments     ::= FunctionArgument ( ',' FunctionArgument )*

FunctionArgument      ::= NamedFunctionArgument
                         | UnnamedFunctionArgument

NamedFunctionArgument   ::= FieldName '=' Expression

UnnamedFunctionArgument ::= Expression
```

> At most **one** `UnnamedFunctionArgument` is allowed per call.

## 6. Shorthands

```bnf
EvalShorthand          ::= FieldName ':=' Expression

EvalFunctionShorthand  ::= FieldName ':=' FunctionCall

FieldShorthand         ::= FieldName '=~' FunctionCall

StatsShorthand         ::= ArrayExpression
```

`StatsShorthand` is syntactic sugar: `[e1, e2, …, en]` is equivalent to `stats([e1, e2, …, en])`.

## 7. Arrays

```bnf
ArrayExpression ::= '[' ( ArrayElement ( ',' ArrayElement )* )? ']'

ArrayElement    ::= EvalFunctionShorthand
                   | Expression
```

## 8. Subqueries

```bnf
Subquery ::= ( Identifier ':' )? '{' Pipeline '}'
```

> Named subqueries (with `Identifier ':'` prefix) were added in **v1.192+**.

## 9. Case & Match

```bnf
Case          ::= 'case' '{' Pipeline ( ';' Pipeline )* '}'

Match         ::= FieldName 'match' '{' MatchPipeline ( ';' MatchPipeline )* '}'

MatchPipeline ::= MatchGuard '=>' Pipeline

MatchGuard    ::= '*'
                 | Regex
                 | FunctionCall
                 | QueryParameter
                 | AnchoredPattern
```

> `match` is **not** shorthand for `case` — it routes on a single field's value.

## 10. Saved Queries & Query Parameters

```bnf
SavedQuery          ::= '$' ( UnquotedPattern | QuotedString )
                        '(' SavedQueryArguments? ')'

SavedQueryArguments ::= SavedQueryArgument ( ',' SavedQueryArgument )*

SavedQueryArgument  ::= ( UnquotedPattern | QuotedString )
                        '=' ( UnquotedPattern | QuotedString )

QueryParameter      ::= '?' QueryParameterName
                        | '?{' QueryParameterName '=' QueryParameterDefault '}'

QueryParameterName    ::= UnquotedPattern | QuotedString

QueryParameterDefault ::= UnquotedPattern | QuotedString
```

> Query parameter arguments are **never** interpreted as regular expressions.

## 11. Lexical Rules

### Field Names

```bnf
FieldName          ::= UnquotedFieldName | QuotedString

UnquotedFieldName  ::= UnquotedFieldNameChar+  ArrayIndex?

ArrayIndex         ::= '[' Digits ']'

Identifier         ::= UnquotedFieldNameChar+
```

### Strings & Numbers

```bnf
QuotedString       ::= '"' QuotedChar* '"'

QuotedChar         ::= <any char except '"', '\', newline>
                      | '\"' | '\\' | '\n'

Number             ::= Digits ( '.' Digits )?

Digits             ::= [0-9]+
```

> Quoted strings **cannot** span multiple lines.

### Unquoted Tokens

```bnf
UnquotedPattern    ::= UnquotedPatternChar+

UnquotedFieldName  ::= UnquotedFieldNameChar+ ArrayIndex?
```

Constraints on `UnquotedPattern`:
- Must not start with `/`
- Must not end with `//`
- May contain `*` as a glob wildcard

### Regular Expressions

```bnf
Regex       ::= '/' RegexBody '/' RegexFlags?

RegexBody   ::= ( <any char except unescaped '/'> | '\/' )+

RegexFlags  ::= [dmi]*
```

| Flag | Meaning |
|------|---------|
| `d`  | Unix lines |
| `m`  | Multiline (`^`/`$` match line boundaries) |
| `i`  | Case-insensitive |

> Regular expressions are **not anchored** by default.

### Comments

```bnf
Comment ::= '//' <any char>* <end-of-line>
```

## 12. Character Classes (ISO/IEC 8859-1)

### Whitespace

| Code Points | Characters |
|---|---|
| U+0009 | Tab |
| U+000A | Line Feed |
| U+000C | Form Feed |
| U+000D | Carriage Return |
| U+0020 | Space |

### UnquotedFieldNameChar

Characters valid in unquoted field names (and identifiers):

| Code Points | Characters |
|---|---|
| U+0023 | `#` |
| U+0025–U+0026 | `%` `&` |
| U+002E | `.` |
| U+0030–U+0039 | `0`–`9` |
| U+0040–U+005A | `@` `A`–`Z` |
| U+005C | `\` |
| U+005E–U+005F | `^` `_` |
| U+0061–U+007A | `a`–`z` |
| U+00A1–U+00AA | Latin-1 Supplement (¡–ª) |
| U+00AE–U+00BA | Latin-1 Supplement (®–º) |
| U+00BC–U+00FF | Latin-1 Supplement (¼–ÿ) |

### UnquotedPatternChar

All of `UnquotedFieldNameChar` **plus**:

| Code Points | Characters |
|---|---|
| U+002A–U+002B | `*` `+` |
| U+002D | `-` |
| U+003A | `:` |
| U+007E | `~` |
| U+00AC | `¬` |

### ReservedCharacter

Characters that **cannot** appear unquoted:

| Code Points | Characters / Description |
|---|---|
| U+0000–U+0008 | Control characters |
| U+000B | Vertical Tab |
| U+000E–U+001F | Control characters |
| U+0021–U+0022 | `!` `"` |
| U+0024 | `$` |
| U+0027–U+0029 | `'` `(` `)` |
| U+002C | `,` |
| U+002F | `/` |
| U+003B–U+003F | `;` `<` `=` `>` `?` |
| U+005B | `[` |
| U+005D | `]` |
| U+0060 | `` ` `` |
| U+007B–U+007D | `{` `\|` `}` |
| U+007F–U+00A0 | DEL + Latin-1 control block |
| U+00AB | `«` |
| U+00AD | Soft Hyphen |
| U+00BB | `»` |

## Appendix A — Reserved Words

The following identifiers are reserved. To use a reserved word as a literal
string in a filter, it **must** be quoted.

```
accumulate, array:append, array:contains, array:dedup, array:drop,
array:eval, array:exists, array:filter, array:intersection, array:length,
array:reduceAll, array:reduceColumn, array:reduceRow, array:regex,
array:rename, array:sort, array:union, asn, avg, base64Decode,
base64Encode, beta:param, beta:repeating, bitfield:extractFlags,
bitfield:extractFlagsAsArray, bitfield:extractFlagsAsString, bucket,
callFunction, case, cidr, coalesce, collect, communityId, concat,
concatArray, copyEvent, correlate, count, counterAsRate, createEvents,
crypto:md5, crypto:sha1, crypto:sha256, default, defineTable, drop,
dropEvent, duration, end, eval, eventFieldCount, eventInternals,
eventSize, fieldset, fieldstats, findTimestamp, format, formatDuration,
formatTime, geography:distance, geohash, getField, groupBy, hash,
hashMatch, hashRewrite, head, if, in, ioc:lookup, ipLocation, join,
json:prettyPrint, kvParse, length, like, linReg, lower, lowercase,
match, matchAsArray, math:abs, math:arccos, math:arcsin, math:arctan,
math:arctan2, math:ceil, math:cos, math:cosh, math:deg2rad, math:exp,
math:expm1, math:floor, math:log, math:log10, math:log1p, math:log2,
math:mod, math:pow, math:rad2deg, math:sin, math:sinh,
math:spherical2cartesian, math:sqrt, math:tan, math:tanh, max, min,
neighbor, now, objectArray:eval, objectArray:exists, parseCEF, parseCsv,
parseFixedWidth, parseHexString, parseInt, parseJson, parseLEEF,
parseTimestamp, parseUri, parseUrl, parseXml, partition, percentage,
percentile, range, rdns, readFile, regex, rename, replace, reverseDns,
round, sample, sankey, select, selectFromMax, selectFromMin, selectLast,
selfJoin, selfJoinFilter, series, session, setField, setTimeInterval,
shannonEntropy, slidingTimeWindow, slidingWindow, sort, split,
splitString, start, stats, stdDev, stripAnsiCodes, subnet, sum, table,
tail, test, text:contains, text:editDistance, text:editDistanceAsArray,
text:endsWith, text:length, text:positionOf, text:startsWith,
text:substring, time:dayOfMonth, time:dayOfWeek, time:dayOfWeekName,
time:dayOfYear, time:hour, time:millisecond, time:minute, time:month,
time:monthName, time:second, time:weekOfYear, time:year, timeChart,
tokenHash, top, transpose, unit:convert, upper, urlDecode, urlEncode,
wildcard, window, worldMap, writeJson, xml:prettyPrint
```

## Appendix B — Notation Key

| Notation | Meaning |
|---|---|
| `Name ::= …` | Grammar rule definition |
| `A \| B` | Alternative (A or B) |
| `R*` | Zero or more repetitions |
| `R+` | One or more repetitions |
| `R?` | Optional (zero or one) |
| `'xyz'` | Literal token (exact match with word boundary) |
| `[a-z]` | Character class |

## Appendix C — Operator Precedence Summary

Listed from **lowest** to **highest** precedence:

| Precedence | Operator(s) | Associativity |
|---|---|---|
| 1 | `AND` (explicit or implicit) | Left |
| 2 | `OR` | Left |
| 3 | `NOT` | Right (prefix) |
| 4 | `==` `!=` `>=` `<=` `>` `<` `<=>` | — |
| 5 | `+` `-` | Left |
| 6 | `*` `/` `%` | Left |
| 7 | `-` (unary) `!` | Right (prefix) |

> **Note:** The AND/OR precedence is **inverted** compared to C, Java, and most
> other languages. `OR` binds tighter than `AND`. Use parentheses for clarity.

## Appendix D — Quirks & Edge Cases

1. **Slash overloading** — `/` is used for comments (`//`), regex literals (`/…/`), and division. The tokenizer cannot always disambiguate these:
   - `a := m/fisk/i` → division (`m / fisk / i`)
   - `/fisk/i` at pipeline start → regex
   - `a := /fisk/i` → syntax error

2. **Comparison asymmetry** — The left side of `=` is always a field name; the right side is always a literal. `foo = bar` checks if field `foo` contains the string `"bar"`, **not** if two fields are equal. Use `test(foo == bar)` for field-to-field comparison.

3. **Implicit AND ambiguity** — `ERROR groupBy(host)` is ambiguous (free-text filter vs. function call). Function names are therefore reserved words.

4. **Reserved word inconsistency** — `test` alone is a syntax error (reserved), but `test=fisk` is a valid field comparison.

5. **Best practices for generation:**
   - Prefer `|` over `AND` to separate pipeline steps
   - Always quote string literals in filters
   - Use parentheses around `AND`/`OR` expressions
   - Use `test()` or `eval()` for field-to-field comparisons
   - Avoid implicit AND
