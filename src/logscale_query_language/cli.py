"""Command-line interface for the LogScale query language tools."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logscale-query",
        description="Parse and format CrowdStrike LogScale queries.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- format ---
    fmt = subparsers.add_parser(
        "format",
        aliases=["fmt"],
        help="Format LogScale query files.",
    )
    fmt.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Input files to format. Reads from stdin if omitted.",
    )
    fmt.add_argument(
        "--in-place",
        "-i",
        action="store_true",
        help="Edit files in place instead of writing to stdout.",
    )
    fmt.add_argument(
        "--check",
        action="store_true",
        help="Check if files are already formatted (exit 1 if not).",
    )
    fmt.add_argument(
        "--query-file",
        type=Path,
        default=None,
        help="Path to a custom topiary .scm formatting query file.",
    )

    # --- parse ---
    prs = subparsers.add_parser(
        "parse",
        help="Parse LogScale queries and display the syntax tree.",
    )
    prs.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Input files to parse. Reads from stdin if omitted.",
    )
    prs.add_argument(
        "--output",
        "-o",
        choices=["sexp", "json"],
        default="sexp",
        help="Output format (default: sexp).",
    )

    # --- check ---
    chk = subparsers.add_parser(
        "check",
        help="Validate LogScale queries for syntax errors.",
    )
    chk.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Input files to validate. Reads from stdin if omitted.",
    )

    return parser


def _get_version() -> str:
    from logscale_query_language import __version__

    return __version__


def _read_input(files: list[Path] | None) -> list[tuple[str, str]]:
    """Return a list of (label, content) pairs from files or stdin."""
    if files:
        pairs: list[tuple[str, str]] = []
        for path in files:
            if not path.exists():
                print(f"error: file not found: {path}", file=sys.stderr)
                sys.exit(1)
            pairs.append((str(path), path.read_text()))
        return pairs
    if sys.stdin.isatty():
        print("error: no input files and stdin is a terminal", file=sys.stderr)
        print("Usage: logscale-query <command> [files...]", file=sys.stderr)
        sys.exit(1)
    return [("<stdin>", sys.stdin.read())]


def _cmd_format(args: argparse.Namespace) -> int:
    from logscale_query_language.formatter import format_query

    inputs = _read_input(args.files)
    exit_code = 0

    for label, content in inputs:
        try:
            formatted = format_query(content, query_file=args.query_file)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"error: {label}: {e}", file=sys.stderr)
            exit_code = 1
            continue

        if args.check:
            if formatted != content:
                print(f"would reformat {label}", file=sys.stderr)
                exit_code = 1
        elif args.in_place:
            if not args.files:
                print("error: --in-place requires file arguments", file=sys.stderr)
                return 1
            Path(label).write_text(formatted)
        else:
            sys.stdout.write(formatted)

    return exit_code


def _cmd_parse(args: argparse.Namespace) -> int:
    import json

    from logscale_query_language.parser import parse_to_dict, tree_to_sexp

    inputs = _read_input(args.files)
    exit_code = 0

    for label, content in inputs:
        if len(inputs) > 1:
            print(f"==> {label} <==")

        if args.output == "sexp":
            print(tree_to_sexp(content))
        else:
            d = parse_to_dict(query=content)
            print(json.dumps(d, indent=2))

    return exit_code


def _cmd_check(args: argparse.Namespace) -> int:
    from logscale_query_language.parser import parse

    inputs = _read_input(args.files)
    exit_code = 0

    for label, content in inputs:
        tree = parse(content)
        if tree.root_node.has_error:
            print(f"error: {label}: syntax error detected", file=sys.stderr)
            exit_code = 1
        else:
            print(f"ok: {label}")

    return exit_code


def _run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "format": _cmd_format,
        "fmt": _cmd_format,
        "parse": _cmd_parse,
        "check": _cmd_check,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


def main() -> None:
    """Entry point for the ``logscale-query`` console script."""
    sys.exit(_run())


if __name__ == "__main__":
    main()
