# LogScale Tools

A tree-sitter parser and topiary-based formatter for the CrowdStrike LogScale query language.

## Project Structure

```
logscale_query_language/
├── CLAUDE.md                 # This file
├── README.md                 # User guide and API reference
├── grammar.md                # BNF grammar specification for LogScale queries
├── .pre-commit-config.yaml   # Pre-commit hooks (ruff lint + format)
├── .github/workflows/ci.yml  # GitHub Actions CI (lint, typecheck, test)
├── pyproject.toml            # Project config (hatchling, pyrefly, pytest, ruff)
├── hatch_build.py            # Custom build hook — downloads topiary binary
├── .python-version           # Pins Python 3.14
├── src/
│   └── logscale_query_language/
│       ├── __init__.py       # Public API exports
│       ├── py.typed          # PEP 561 type marker
│       ├── cli.py            # CLI entry point (logscale-query command)
│       ├── parser.py         # Tree-sitter parser (compiles + loads grammar)
│       ├── formatter.py      # Topiary formatter wrapper
│       ├── queries/
│       │   └── logscale.scm  # Topiary formatting rules
│       ├── bin/              # Downloaded topiary binary (gitignored)
│       └── lib/              # Compiled grammar .dylib/.so (gitignored)
├── tree-sitter-logscale/
│   ├── grammar.js            # Tree-sitter grammar definition (JavaScript)
│   ├── src/
│   │   ├── parser.c          # Generated C parser
│   │   └── scanner.c         # External scanner (regex/division disambiguation)
│   └── test/corpus/          # Tree-sitter test corpus (.txt files)
└── tests/
    ├── test_cli.py           # CLI tests
    ├── test_parser.py        # Parser tests
    └── test_formatter.py     # Formatter tests
```

## Build System

- **Package manager**: uv
- **Build backend**: hatchling with a custom build hook (`hatch_build.py`)
- **Type checker**: pyrefly (configured in `[tool.pyrefly]` in `pyproject.toml`)
- **Formatter/linter**: ruff (line-length 88, lint rules: E, F, I, UP)
- **Pre-commit**: runs `ruff --fix` and `ruff format` on every commit
- **CI**: GitHub Actions runs lint, typecheck, and test on push/PR to main

### How the build works

1. `hatch_build.py` defines a `TopiariBuildHook` that runs during `uv build` (or any PEP 517 build).
2. The hook detects the current platform (macOS arm64/x86_64, Linux arm64/x86_64, Windows x86_64).
3. It downloads the matching topiary-cli v0.7.3 binary from https://github.com/tweag/topiary/releases/tag/v0.7.3.
4. The binary is extracted into `src/logscale_query_language/bin/` and bundled into the wheel.
5. At runtime, `formatter.py` locates the binary via `Path(__file__).parent / "bin" / "topiary"`.

### How the parser works

1. `parser.py` compiles `tree-sitter-logscale/src/parser.c` and `scanner.c` into a shared library on first use.
2. The compiled `.dylib`/`.so` is cached in `src/logscale_query_language/lib/`.
3. The language is loaded via ctypes/PyCapsule (compatible with tree-sitter >= 0.23).
4. A C compiler (`cc`/`gcc`/`clang`) must be available on PATH.

### Commands

```sh
# Create virtualenv and install in dev mode
uv sync --extra dev

# Build a wheel (triggers topiary download)
uv build

# Run tests
uv run pytest

# Type check
uv run pyrefly check

# Format code
uv run ruff format .

# Lint (with auto-fix)
uv run ruff check --fix .
```

### CLI

The package installs a `logscale-query` command with four subcommands:

```sh
# Format a file (stdout)
logscale-query format query.logscale

# Format in place
logscale-query format -i query.logscale

# Parse and show syntax tree
logscale-query parse query.logscale

# Validate syntax
logscale-query check query.logscale

# Visualize tokens with colored type labels
logscale-query tokenize query.logscale
```

## Grammar Reference

The full BNF grammar for LogScale queries is in `grammar.md`. Key notes:
- OR binds more tightly than AND (inverted from most languages)
- `=` in filters is field-to-literal comparison, not field-to-field
- Use `test()` or `eval()` for field-to-field comparisons
- Function names are reserved words
