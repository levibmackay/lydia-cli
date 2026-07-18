import pytest
from typer.testing import CliRunner

from lydia.automations import store
from lydia.automations.model import Automation, Notify, Step, Trigger
from lydia.cli.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "AUTOMATIONS_DIR", tmp_path)


def _saved(name="daily") -> Automation:
    auto = Automation(name=name, description="d",
                      trigger=Trigger(type="schedule", time="08:00"),
                      steps=[Step(kind="connector", tool="check_news"),
                             Step(kind="model", instructions="Summarize.")],
                      notify=Notify())
    store.save_automation(auto)
    return auto


def test_list_empty():
    result = runner.invoke(app, ["automations", "list"])
    assert result.exit_code == 0
    assert "No automations" in result.output


def test_list_and_show():
    _saved()
    result = runner.invoke(app, ["automations", "list"])
    assert result.exit_code == 0 and "daily" in result.output
    result = runner.invoke(app, ["automations", "show", "daily"])
    assert result.exit_code == 0 and "08:00" in result.output


def test_enable_disable_remove():
    _saved()
    assert runner.invoke(app, ["automations", "disable", "daily"]).exit_code == 0
    assert store.load_automation("daily").enabled is False
    assert runner.invoke(app, ["automations", "enable", "daily"]).exit_code == 0
    assert store.load_automation("daily").enabled is True
    assert runner.invoke(app, ["automations", "remove", "daily"]).exit_code == 0
    assert store.list_automations() == []


def test_show_missing_errors():
    result = runner.invoke(app, ["automations", "show", "nope"])
    assert result.exit_code == 1
