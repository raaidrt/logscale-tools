# Development Guide

## Requirements

- Python 3.14+
- A C compiler (`cc` / `gcc` / `clang`) on `PATH` (compiles tree-sitter grammar)
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
git clone https://github.com/raaidrt/logscale-tools.git
cd logscale_query_language
uv sync --extra dev
```

## Commands

```sh
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

## Build System

- **Package manager**: uv
- **Build backend**: hatchling with a custom build hook (`hatch_build.py`)
- **Type checker**: pyrefly
- **Formatter/linter**: ruff (line-length 88, lint rules: E, F, I, UP)
- **Pre-commit**: runs `ruff --fix` and `ruff format` on every commit
- **CI**: GitHub Actions runs lint, typecheck, and test on push/PR to main

### How the build works

1. `hatch_build.py` defines a `TopiariBuildHook` that runs during `uv build`.
2. The hook detects the current platform (macOS arm64/x86_64, Linux arm64/x86_64, Windows x86_64).
3. It downloads the matching topiary-cli v0.7.3 binary from GitHub releases.
4. The binary is extracted into `src/logscale_query_language/bin/` and bundled into the wheel.
5. At runtime, `formatter.py` locates the binary via `Path(__file__).parent / "bin" / "topiary"`.

### How the parser works

1. `parser.py` compiles `tree-sitter-logscale/src/parser.c` and `scanner.c` into a shared library on first use.
2. The compiled `.dylib`/`.so` is cached in `src/logscale_query_language/lib/`.
3. The language is loaded via ctypes/PyCapsule (compatible with tree-sitter >= 0.23).

## Project Structure

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
│   ├── test_cli.py
│   ├── test_parser.py
│   └── test_formatter.py
├── grammar.md                # BNF grammar specification
├── hatch_build.py            # Build hook (downloads topiary)
└── pyproject.toml            # Project configuration
```

## Publishing

Publishing is handled automatically via the `publish.yml` GitHub Actions
workflow. To release a new version:

```sh
# Bump the version
uv version <new-version>

# Commit and tag
git add pyproject.toml
git commit -m "v<new-version>"
git tag -a v<new-version> -m "v<new-version>"
git push && git push --tags
```

The workflow will build and publish to PyPI using trusted publishing.
