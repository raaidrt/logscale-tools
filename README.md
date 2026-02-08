# LogScale Query Language

A tree-sitter parser and topiary-based formatter for the
[CrowdStrike LogScale](https://www.crowdstrike.com/products/observability/falcon-logscale/)
query language.

## Features

- **Parser** — Parse LogScale queries into concrete syntax trees using
  [tree-sitter](https://tree-sitter.github.io/) with full grammar support
  (filters, pipelines, functions, expressions, case/match, subqueries, and more).
- **Formatter** — Format LogScale queries with consistent style using
  [topiary](https://topiary.tweag.io/), a universal code formatter built on
  tree-sitter.
- **Python API** — Simple functions to parse, inspect, and format queries from
  Python.
- **CLI** — `logscale-query` command for formatting files, parsing queries,
  validating syntax, and visualizing tokens from the terminal.

## Requirements

- Python 3.14+
- A C compiler (`cc` / `gcc` / `clang`) available on `PATH` (used to compile
  the tree-sitter grammar on first use)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

```sh
# Clone the repository
git clone <repo-url>
cd logscale_query_language

# Install with uv (recommended)
uv sync --extra dev

# Or install with pip
pip install -e ".[dev]"
```

The tree-sitter grammar is compiled automatically on first use. The topiary
binary is downloaded during `uv build` (or `pip install`).

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

## Command-Line Interface

Installing the package provides the `logscale-query` command:

```sh
logscale-query --version
```

### Format files

Format one or more `.logscale` / `.lql` files and print the result to stdout:

```sh
logscale-query format query.logscale
```

Format in place (overwrites the file):

```sh
logscale-query format --in-place query.logscale
logscale-query fmt -i *.logscale   # "fmt" is a shorthand alias
```

Check whether files are already formatted (exit code 1 if not):

```sh
logscale-query format --check query.logscale
```

Read from stdin:

```sh
echo 'error|count()|sort(_count)' | logscale-query format
```

Use a custom topiary formatting query file:

```sh
logscale-query format --query-file custom.scm query.logscale
```

### Parse queries

Display the syntax tree as an S-expression:

```sh
logscale-query parse query.logscale
```

Output as JSON:

```sh
logscale-query parse --output json query.logscale
```

Parse from stdin:

```sh
echo 'status = 200 | count()' | logscale-query parse
```

### Validate syntax

Check that files parse without syntax errors:

```sh
logscale-query check query.logscale another.lql
```

Exit code is 0 if all files are valid, 1 if any contain errors.

### Visualize tokens

Display each token with its type label printed above it, using colored output:

```sh
logscale-query tokenize query.logscale
logscale-query tok query.logscale   # "tok" is a shorthand alias
```

From stdin:

```sh
echo 'error | count()' | logscale-query tokenize
```

Disable colors (e.g. for piping):

```sh
logscale-query tokenize --no-color query.logscale
```

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

## Development

```sh
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with verbose output
uv run pytest -xvs

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run pyrefly check
```

### Project Structure

```
logscale_query_language/
├── src/logscale_query_language/
│   ├── __init__.py          # Public API exports
│   ├── cli.py               # Command-line interface (logscale-query)
│   ├── parser.py            # Tree-sitter parser (compiles + loads grammar)
│   ├── formatter.py         # Topiary formatter wrapper
│   ├── queries/
│   │   └── logscale.scm     # Topiary formatting rules
│   ├── bin/                  # Downloaded topiary binary (gitignored)
│   └── lib/                  # Compiled grammar .dylib/.so (gitignored)
├── tree-sitter-logscale/
│   ├── grammar.js            # Tree-sitter grammar definition
│   ├── src/
│   │   ├── parser.c          # Generated parser
│   │   └── scanner.c         # External scanner (regex disambiguation)
│   └── test/corpus/          # Tree-sitter test corpus
├── tests/
│   ├── test_cli.py            # CLI tests
│   ├── test_parser.py         # Parser tests
│   └── test_formatter.py      # Formatter tests
├── grammar.md                # BNF grammar specification
├── hatch_build.py            # Build hook (downloads topiary)
└── pyproject.toml            # Project configuration
```

## License

MIT
