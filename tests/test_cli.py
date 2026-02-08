"""Tests for the LogScale query language CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logscale_query_language.cli import _run


class TestParseCommand:
    def test_parse_file_sexp(self, tmp_path: Path) -> None:
        f = tmp_path / "q.logscale"
        f.write_text("error | count()")
        code = _run(["parse", str(f)])
        assert code == 0

    def test_parse_file_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:  # type: ignore[type-arg]
        f = tmp_path / "q.logscale"
        f.write_text("error | count()")
        code = _run(["parse", "--output", "json", str(f)])
        assert code == 0
        out = capsys.readouterr().out
        d = json.loads(out)
        assert d["type"] == "query"
        assert d["has_error"] is False

    def test_parse_multiple_files(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:  # type: ignore[type-arg]
        f1 = tmp_path / "a.logscale"
        f2 = tmp_path / "b.logscale"
        f1.write_text("error")
        f2.write_text("warning")
        code = _run(["parse", str(f1), str(f2)])
        assert code == 0
        out = capsys.readouterr().out
        assert "==> " in out

    def test_parse_missing_file(self) -> None:
        with pytest.raises(SystemExit):
            _run(["parse", "/nonexistent/file.logscale"])


class TestCheckCommand:
    def test_check_valid_query(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:  # type: ignore[type-arg]
        f = tmp_path / "q.logscale"
        f.write_text("error | count()")
        code = _run(["check", str(f)])
        assert code == 0
        out = capsys.readouterr().out
        assert "ok:" in out

    def test_check_multiple_valid(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.logscale"
        f2 = tmp_path / "b.logscale"
        f1.write_text("error")
        f2.write_text('status = "ok"')
        code = _run(["check", str(f1), str(f2)])
        assert code == 0


class TestFormatCommand:
    def test_format_file_to_stdout(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,  # type: ignore[type-arg]
    ) -> None:
        f = tmp_path / "q.logscale"
        f.write_text("error|count()")
        code = _run(["format", str(f)])
        assert code == 0
        out = capsys.readouterr().out
        assert "count()" in out

    def test_format_in_place(self, tmp_path: Path) -> None:
        f = tmp_path / "q.logscale"
        f.write_text("error|count()")
        code = _run(["format", "--in-place", str(f)])
        assert code == 0
        result = f.read_text()
        assert "count()" in result

    def test_format_check_already_formatted(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,  # type: ignore[type-arg]
    ) -> None:
        f = tmp_path / "q.logscale"
        f.write_text("error|count()")
        _run(["format", str(f)])
        formatted = capsys.readouterr().out
        f.write_text(formatted)
        code = _run(["format", "--check", str(f)])
        assert code == 0

    def test_format_check_unformatted(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,  # type: ignore[type-arg]
    ) -> None:
        f = tmp_path / "q.logscale"
        f.write_text("error|count()")
        code = _run(["format", "--check", str(f)])
        err = capsys.readouterr().err
        assert code == 1
        assert "would reformat" in err


class TestNoCommand:
    def test_no_command_shows_help(self, capsys: pytest.CaptureFixture) -> None:  # type: ignore[type-arg]
        code = _run([])
        assert code == 0

    def test_version(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            _run(["--version"])
        assert exc_info.value.code == 0
