"""Tests for the project scanner."""

from pathlib import Path

from tessa.context.scanner import scan_project


def write(path: Path, lines: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n" * lines)


def test_scan_detects_languages_and_manifests(tmp_path: Path) -> None:
    write(tmp_path / "pyproject.toml", 5)
    write(tmp_path / "src" / "app.py", 90)
    write(tmp_path / "src" / "util.py", 10)
    write(tmp_path / "web" / "index.ts", 100)
    write(tmp_path / "node_modules" / "junk" / "big.js", 5000)  # must be ignored
    write(tmp_path / ".git" / "objects" / "blob.py", 500)  # must be ignored

    summary = scan_project(tmp_path)
    assert summary.file_count == 4
    assert summary.languages["Python"] == 50.0
    assert summary.languages["TypeScript"] == 50.0
    assert "pyproject.toml" in summary.manifest_files
    assert summary.project_kind == "Python"
    largest_names = [p for p, _ in summary.largest_source_files]
    assert largest_names[0] == "web/index.ts"


def test_scan_empty_directory(tmp_path: Path) -> None:
    summary = scan_project(tmp_path)
    assert summary.file_count == 0
    assert summary.languages == {}
    assert summary.project_kind == "Unknown"
