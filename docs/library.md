# Python Library Reference

`logscale-query-language` exposes a Python API for parsing, inspecting, and
formatting LogScale queries.

## Quick Start

### Parsing a query

```python
from logscale_query_language import parse, tree_to_sexp, parse_to_dict

# Parse a query into a tree-sitter Tree
tree = parse('status != 200 | groupBy(field=host, function=count())')
root = tree.root_node
print(root.has_error)  # False — the query is syntactically valid

# Get the S-expression (useful for debugging)
print(tree_to_sexp('error OR warning'))
# (query (pipeline (filter (or_filter (free_text_pattern (identifier)) ...))))

# Get a dictionary representation
d = parse_to_dict(query='status = 200')
print(d["type"])       # "query"
print(d["has_error"])  # False
```

### Working with the syntax tree

```python
from logscale_query_language import parse

tree = parse('error | count() | sort(_count)')
root = tree.root_node

# Walk the tree
for child in root.children:
    print(child.type, child.text.decode())

# Use tree-sitter queries
from logscale_query_language import get_language
from tree_sitter import Query

lang = get_language()
query = Query(lang, '(function_call (function_name (identifier) @fn))')
captures = query.captures(root)
for node, name in captures:
    print(f"{name}: {node.text.decode()}")
# fn: count
# fn: sort
```

### Formatting a query

```python
from logscale_query_language import format_query

formatted = format_query('error|count()|sort(_count)')
print(formatted)
```

> **Note:** The formatter requires the topiary binary. Run `uv build` first to
> download it, or it will raise `FileNotFoundError`.

## API Reference

### `parse(query: str) -> Tree`

Parse a LogScale query string and return a tree-sitter `Tree`.

```python
tree = parse("error OR warning")
assert not tree.root_node.has_error
```

### `tree_to_sexp(query: str) -> str`

Parse a query and return its S-expression representation. Useful for debugging
and testing.

```python
sexp = tree_to_sexp("status = 200")
assert "field_comparison" in sexp
```

### `parse_to_dict(node=None, *, query=None) -> dict`

Convert a tree-sitter node (or parse a query) into a nested dictionary with
keys: `type`, `text`, `children`, `start_point`, `end_point`, `has_error`.

```python
d = parse_to_dict(query="error | count()")
print(d["children"][0]["type"])  # "pipeline"
```

### `get_language() -> Language`

Return the tree-sitter `Language` object for LogScale. The grammar is compiled
on first call and cached for subsequent calls.

```python
from tree_sitter import Query
lang = get_language()
q = Query(lang, '(function_call) @fn')
```

### `format_query(query: str, *, query_file=None) -> str`

Format a LogScale query using topiary. Optionally provide a custom `.scm`
formatting query file.

### `get_topiary_path() -> Path`

Return the path to the bundled topiary-cli binary. Raises `FileNotFoundError`
if it hasn't been downloaded yet.

## Supported Grammar

The parser supports the full LogScale query language as specified in
`grammar.md`:

| Construct | Example |
|---|---|
| Free text search | `error`, `"connection timeout"` |
| Field comparisons | `status = 200`, `host != prod*`, `latency >= 100` |
| Regex patterns | `/error\|warn/i` |
| Like patterns | `host like server*` |
| Logical operators | `error OR warning`, `NOT debug`, implicit AND |
| Pipelines | `error \| count() \| sort(_count)` |
| Functions | `groupBy(field=host, function=count())` |
| Eval shorthand | `duration_ms := duration * 1000` |
| Field shorthand | `host =~ regex("web-.*")` |
| Case expressions | `case { error \| count() ; warning \| count() }` |
| Match expressions | `level match { "error" => count() ; * => drop() }` |
| Subqueries | `x := { error \| count() }` |
| Arrays / stats | `[count(), avg(duration)]` |
| Saved queries | `$myQuery(host="server1")` |
| Query parameters | `?param`, `?{param=default}` |
| Comments | `// this is a comment` |

### Operator Precedence

LogScale has **inverted** AND/OR precedence compared to most languages — `OR`
binds more tightly than `AND`:

| Precedence | Operator |
|---|---|
| 1 (lowest) | `AND` |
| 2 | `OR` |
| 3 | `NOT` |
| 4 | `==` `!=` `>=` `<=` `>` `<` `<=>` |
| 5 | `+` `-` |
| 6 | `*` `/` `%` |
| 7 (highest) | `-` (unary) `!` |
