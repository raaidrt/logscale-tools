# LogScale Query Language

A tree-sitter parser and topiary-based formatter for the CrowdStrike LogScale query language.

## Project Structure

```
logscale_query_language/
├── CLAUDE.md                 # This file
├── grammar.md                # BNF grammar specification for LogScale queries
├── pyproject.toml            # Project config (hatchling, pyrefly, pytest)
├── hatch_build.py            # Custom build hook — downloads topiary binary
├── .python-version           # Pins Python 3.14
├── src/
│   └── logscale_query_language/
│       ├── __init__.py
│       ├── py.typed          # PEP 561 type marker
│       ├── parser.py         # Tree-sitter parser (skeleton)
│       ├── formatter.py      # Topiary formatter wrapper (skeleton)
│       └── bin/              # Downloaded topiary binary (gitignored)
└── tests/
    ├── test_parser.py
    └── test_formatter.py
```

## Build System

- **Package manager**: uv
- **Build backend**: hatchling with a custom build hook (`hatch_build.py`)
- **Type checker**: pyrefly (configured in `[tool.pyrefly]` in `pyproject.toml`)

### How the build works

1. `hatch_build.py` defines a `TopiariBuildHook` that runs during `uv build` (or any PEP 517 build).
2. The hook detects the current platform (macOS arm64/x86_64, Linux arm64/x86_64, Windows x86_64).
3. It downloads the matching topiary-cli v0.7.3 binary from https://github.com/tweag/topiary/releases/tag/v0.7.3.
4. The binary is extracted into `src/logscale_query_language/bin/` and bundled into the wheel.
5. At runtime, `formatter.py` locates the binary via `Path(__file__).parent / "bin" / "topiary-cli"`.

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
```

## Grammar Reference

The full BNF grammar for LogScale queries is in `grammar.md`. Key notes:
- OR binds more tightly than AND (inverted from most languages)
- `=` in filters is field-to-literal comparison, not field-to-field
- Use `test()` or `eval()` for field-to-field comparisons
- Function names are reserved words
