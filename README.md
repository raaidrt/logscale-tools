# LogScale Tools

A tree-sitter parser and topiary-based formatter for the
[CrowdStrike LogScale](https://www.crowdstrike.com/products/observability/falcon-logscale/)
query language.

## Installation

```sh
pip install logscale-tools
```

Or with [uv](https://docs.astral.sh/uv/):

```sh
uv pip install logscale-tools
```

A C compiler (`cc` / `gcc` / `clang`) must be available on `PATH` — the
tree-sitter grammar is compiled automatically on first use.

## CLI Usage

Installing the package provides the `logscale-query` command:

```sh
logscale-query --version
```

### Format files

```sh
# Print formatted output to stdout
logscale-query format query.logscale

# Format in place
logscale-query format --in-place query.logscale
logscale-query fmt -i *.logscale   # "fmt" is a shorthand alias

# Check whether files are already formatted (exit code 1 if not)
logscale-query format --check query.logscale

# Read from stdin
echo 'error|count()|sort(_count)' | logscale-query format

# Use a custom topiary formatting query file
logscale-query format --query-file custom.scm query.logscale
```

### Parse queries

```sh
# Display the syntax tree as an S-expression
logscale-query parse query.logscale

# Output as JSON
logscale-query parse --output json query.logscale

# Parse from stdin
echo 'status = 200 | count()' | logscale-query parse
```

### Validate syntax

```sh
logscale-query check query.logscale another.lql
```

Exit code is 0 if all files are valid, 1 if any contain errors.

### Visualize tokens

```sh
logscale-query tokenize query.logscale
logscale-query tok query.logscale   # "tok" is a shorthand alias

# From stdin
echo 'error | count()' | logscale-query tokenize

# Disable colors (e.g. for piping)
logscale-query tokenize --no-color query.logscale
```

## Further Reading

- [Python Library Reference](docs/library.md) — API docs and grammar reference
- [Development Guide](docs/developing.md) — contributing, building, and project structure

## License

MIT
