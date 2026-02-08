"""Tree-sitter based parser for the LogScale query language."""

from __future__ import annotations

import ctypes
import platform
import subprocess
from ctypes import PYFUNCTYPE, c_char_p, c_void_p, py_object, pythonapi
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Language, Node, Tree

_PKG_DIR = Path(__file__).resolve().parent
_GRAMMAR_SRC_DIR = _PKG_DIR / "grammar_src"
_DEV_GRAMMAR_DIR = _PKG_DIR.parent.parent / "tree-sitter-logscale" / "src"
_SRC_DIR = _GRAMMAR_SRC_DIR if _GRAMMAR_SRC_DIR.exists() else _DEV_GRAMMAR_DIR
_PARSER_C = _SRC_DIR / "parser.c"
_SCANNER_C = _SRC_DIR / "scanner.c"

_LIB_DIR = Path(__file__).resolve().parent / "lib"
_SYSTEM = platform.system()
_LIB_EXT = (
    ".dylib" if _SYSTEM == "Darwin" else ".dll" if _SYSTEM == "Windows" else ".so"
)
_LIB_PATH = _LIB_DIR / f"logscale{_LIB_EXT}"

_language: Language | None = None


def _build_library() -> Path:
    """Compile the tree-sitter LogScale parser into a shared library."""
    _LIB_DIR.mkdir(parents=True, exist_ok=True)

    sources = [str(_PARSER_C)]
    if _SCANNER_C.exists():
        sources.append(str(_SCANNER_C))

    cmd = [
        "cc",
        "-shared",
        "-fPIC",
        "-fno-exceptions",
        f"-I{_SRC_DIR}",
        "-O2",
        "-o",
        str(_LIB_PATH),
        *sources,
    ]

    if _SYSTEM == "Darwin":
        cmd.insert(1, "-dynamiclib")
        cmd.remove("-shared")

    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return _LIB_PATH


def _load_language() -> Language:
    """Load the LogScale tree-sitter language."""
    import tree_sitter

    if not _LIB_PATH.exists():
        _build_library()

    cdll = ctypes.CDLL(str(_LIB_PATH))
    func = cdll.tree_sitter_logscale
    func.restype = c_void_p
    ptr = func()

    PyCapsule_New = PYFUNCTYPE(py_object, c_void_p, c_char_p, c_void_p)(
        ("PyCapsule_New", pythonapi)
    )
    capsule = PyCapsule_New(ptr, b"tree_sitter.Language", None)
    return tree_sitter.Language(capsule)


def get_language() -> Language:
    """Return the LogScale tree-sitter Language, building if necessary.

    Returns:
        The tree-sitter Language for LogScale queries.

    Raises:
        RuntimeError: If the shared library cannot be compiled or loaded.
    """
    global _language
    if _language is None:
        _language = _load_language()
    return _language


def parse(query: str) -> Tree:
    """Parse a LogScale query string into a syntax tree.

    Args:
        query: A LogScale query string.

    Returns:
        The parsed tree-sitter Tree.

    Raises:
        RuntimeError: If the parser cannot be initialized.
    """
    import tree_sitter

    language = get_language()
    parser = tree_sitter.Parser(language)
    return parser.parse(query.encode("utf-8"))


def parse_to_dict(node: Node | None = None, *, query: str | None = None) -> dict:
    """Parse a LogScale query and return a dictionary representation of the tree.

    Either provide a pre-parsed Node or a query string to parse.

    Args:
        node: A tree-sitter Node to convert to dict. If None, query must be provided.
        query: A LogScale query string to parse. Ignored if node is provided.

    Returns:
        A dictionary with keys: "type", "text", "children", "start_point", "end_point",
        and "has_error".
    """
    if node is None:
        if query is None:
            raise ValueError("Either node or query must be provided")
        tree = parse(query)
        node = tree.root_node

    result: dict = {
        "type": node.type,
        "text": node.text.decode("utf-8") if node.text else "",
        "start_point": (node.start_point.row, node.start_point.column),
        "end_point": (node.end_point.row, node.end_point.column),
        "has_error": node.has_error,
        "children": [],
    }

    for child in node.children:
        result["children"].append(parse_to_dict(node=child))

    return result


def tree_to_sexp(query: str) -> str:
    """Parse a LogScale query and return its S-expression representation.

    This is useful for debugging and testing the parser.

    Args:
        query: A LogScale query string.

    Returns:
        The S-expression string of the parsed tree.
    """
    tree = parse(query)
    return str(tree.root_node)
