"""CLI-level tests for `tessa memory add/list/forget`."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from tessa.cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_memory_list_when_empty() -> None:
    result = runner.invoke(app, ["memory", "list"])
    assert result.exit_code == 0
    assert "No facts remembered" in result.stdout


def test_memory_add_and_list() -> None:
    add_result = runner.invoke(app, ["memory", "add", "uses PostgreSQL"])
    assert add_result.exit_code == 0
    assert "Remembered" in add_result.stdout

    list_result = runner.invoke(app, ["memory", "list"])
    assert "uses PostgreSQL" in list_result.stdout


def test_memory_forget(tmp_path: Path) -> None:
    runner.invoke(app, ["memory", "add", "first"])
    runner.invoke(app, ["memory", "add", "second"])
    forget_result = runner.invoke(app, ["memory", "forget", "1"])
    assert forget_result.exit_code == 0
    assert "Forgot: first" in forget_result.stdout

    list_result = runner.invoke(app, ["memory", "list"])
    assert "second" in list_result.stdout
    assert "first" not in list_result.stdout


def test_memory_forget_invalid_index_fails() -> None:
    result = runner.invoke(app, ["memory", "forget", "99"])
    assert result.exit_code == 1
