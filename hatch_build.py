"""Custom hatch build hook that bundles tree-sitter grammar sources."""

from __future__ import annotations

import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class TopiariBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:  # type: ignore[type-arg]
        """Bundle tree-sitter grammar sources in the wheel."""
        # Bundle tree-sitter grammar C sources for runtime compilation
        grammar_dest = (
            Path(self.root) / "src" / "logscale_query_language" / "grammar_src"
        )
        grammar_src = Path(self.root) / "tree-sitter-logscale" / "src"
        if grammar_src.exists():
            if not grammar_dest.exists():
                shutil.copytree(grammar_src, grammar_dest)
            build_data["force_include"][str(grammar_dest)] = (
                "logscale_query_language/grammar_src"
            )
        elif grammar_dest.exists():
            build_data["force_include"][str(grammar_dest)] = (
                "logscale_query_language/grammar_src"
            )
        else:
            raise FileNotFoundError(
                f"Tree-sitter grammar sources not found at {grammar_src}"
            )

    def clean(self, versions: list[str]) -> None:
        """Remove copied grammar sources."""
        path = Path(self.root) / "src" / "logscale_query_language" / "grammar_src"
        if path.exists():
            shutil.rmtree(path)
            print(f"Cleaned {path}")
