"""Tests for launchd/systemd-based briefing scheduling (no real launchctl/systemctl invoked)."""

import subprocess
from pathlib import Path

import pytest

from lydia.cli import scheduler


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scheduler, "PLIST_PATH", tmp_path / "LaunchAgents" / "com.lydia.briefing.plist")
    monkeypatch.setattr(scheduler, "SYSTEMD_USER_DIR", tmp_path / "systemd-user")
    monkeypatch.setattr(scheduler, "SYSTEMD_SERVICE_PATH", tmp_path / "systemd-user" / "lydia-briefing.service")
    monkeypatch.setattr(scheduler, "SYSTEMD_TIMER_PATH", tmp_path / "systemd-user" / "lydia-briefing.timer")
    monkeypatch.setattr(scheduler, "LOG_PATH", tmp_path / ".lydia" / "briefing.log")


def fake_runner(returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, returncode, stdout="", stderr=stderr)
    return run


def test_parse_time_rejects_bad_input() -> None:
    with pytest.raises(scheduler.ScheduleError):
        scheduler._parse_time("not-a-time")
    with pytest.raises(scheduler.ScheduleError):
        scheduler._parse_time("25:00")
    with pytest.raises(scheduler.ScheduleError):
        scheduler._parse_time("08")


def test_parse_time_accepts_valid_input() -> None:
    assert scheduler._parse_time("08:30") == (8, 30)


def test_backend_unsupported_platform_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scheduler.platform, "system", lambda: "Windows")
    with pytest.raises(scheduler.ScheduleError, match="aren't supported"):
        scheduler._backend()


def test_backend_linux_without_systemctl_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scheduler.platform, "system", lambda: "Linux")
    monkeypatch.setattr(scheduler.shutil, "which", lambda name: None)
    with pytest.raises(scheduler.ScheduleError, match="systemd"):
        scheduler._backend()


class TestLaunchd:
    @pytest.fixture(autouse=True)
    def macos(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scheduler.platform, "system", lambda: "Darwin")

    def test_enable_writes_plist_and_loads_it(self) -> None:
        assert not scheduler.is_enabled()
        path = scheduler.enable("08:00", lydia_path="/usr/local/bin/lydia", runner=fake_runner())
        assert path == scheduler.PLIST_PATH
        assert scheduler.is_enabled()
        contents = scheduler.PLIST_PATH.read_text()
        assert "/usr/local/bin/lydia" in contents
        assert "<integer>8</integer>" in contents
        assert "<integer>0</integer>" in contents

    def test_enable_raises_if_launchctl_fails(self) -> None:
        with pytest.raises(scheduler.ScheduleError):
            scheduler.enable(
                "08:00", lydia_path="/usr/local/bin/lydia", runner=fake_runner(returncode=1, stderr="boom"),
            )

    def test_disable_removes_plist(self) -> None:
        scheduler.enable("08:00", lydia_path="/usr/local/bin/lydia", runner=fake_runner())
        scheduler.disable(runner=fake_runner())
        assert not scheduler.is_enabled()

    def test_disable_is_a_noop_when_not_enabled(self) -> None:
        calls = []

        def tracking_runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0)

        scheduler.disable(runner=tracking_runner)
        assert calls == []


class TestSystemd:
    @pytest.fixture(autouse=True)
    def linux(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(scheduler.platform, "system", lambda: "Linux")
        monkeypatch.setattr(scheduler.shutil, "which", lambda name: "/usr/bin/systemctl" if name == "systemctl" else None)

    def test_enable_writes_units_and_starts_timer(self) -> None:
        assert not scheduler.is_enabled()
        path = scheduler.enable("08:00", lydia_path="/usr/local/bin/lydia", runner=fake_runner())
        assert path == scheduler.SYSTEMD_TIMER_PATH
        assert scheduler.is_enabled()

        service = scheduler.SYSTEMD_SERVICE_PATH.read_text()
        assert "ExecStart=/usr/local/bin/lydia briefing run --notify" in service

        timer = scheduler.SYSTEMD_TIMER_PATH.read_text()
        assert "OnCalendar=*-*-* 08:00:00" in timer

    def test_enable_runs_daemon_reload_then_enable(self) -> None:
        calls = []

        def tracking_runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0)

        scheduler.enable("08:00", lydia_path="/usr/local/bin/lydia", runner=tracking_runner)
        assert calls[0] == ["systemctl", "--user", "daemon-reload"]
        assert calls[1] == ["systemctl", "--user", "enable", "--now", "lydia-briefing.timer"]

    def test_enable_raises_if_daemon_reload_fails(self) -> None:
        with pytest.raises(scheduler.ScheduleError, match="daemon-reload"):
            scheduler.enable(
                "08:00", lydia_path="/usr/local/bin/lydia", runner=fake_runner(returncode=1, stderr="boom"),
            )

    def test_enable_raises_if_systemctl_enable_fails(self) -> None:
        calls = []

        def flaky_runner(args, **kwargs):
            calls.append(args)
            returncode = 1 if "enable" in args else 0
            return subprocess.CompletedProcess(args, returncode, stdout="", stderr="boom")

        with pytest.raises(scheduler.ScheduleError, match="systemctl --user enable failed"):
            scheduler.enable("08:00", lydia_path="/usr/local/bin/lydia", runner=flaky_runner)

    def test_disable_removes_units(self) -> None:
        scheduler.enable("08:00", lydia_path="/usr/local/bin/lydia", runner=fake_runner())
        scheduler.disable(runner=fake_runner())
        assert not scheduler.is_enabled()
        assert not scheduler.SYSTEMD_SERVICE_PATH.exists()

    def test_disable_is_a_noop_when_not_enabled(self) -> None:
        calls = []

        def tracking_runner(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0)

        scheduler.disable(runner=tracking_runner)
        assert calls == []

def test_enable_automations_writes_interval_plist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scheduler, "AUTOMATIONS_PLIST_PATH", tmp_path / "auto.plist")
    calls = []

    def fake_runner(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    path = scheduler.enable_automations(
        interval_seconds=300, lydia_path="/bin/lydia", runner=fake_runner
    )
    text = path.read_text()
    assert "<key>StartInterval</key>" in text and "<integer>300</integer>" in text
    assert "<string>automations</string>" in text and "<string>tick</string>" in text
    assert calls[0][:2] == ["launchctl", "load"]


def test_enable_automations_rejects_silly_interval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scheduler, "AUTOMATIONS_PLIST_PATH", tmp_path / "auto.plist")
    with pytest.raises(scheduler.ScheduleError):
        scheduler.enable_automations(
            interval_seconds=10, lydia_path="/bin/lydia", runner=lambda *a, **k: None
        )


def test_disable_automations_unloads_and_removes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plist = tmp_path / "auto.plist"
    plist.write_text("x")
    monkeypatch.setattr(scheduler, "AUTOMATIONS_PLIST_PATH", plist)
    scheduler.disable_automations(
        runner=lambda cmd, **k: subprocess.CompletedProcess(cmd, 0, "", "")
    )
    assert not plist.exists()


def test_enable_listen_writes_runatload_plist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scheduler, "LISTEN_PLIST_PATH", tmp_path / "listen.plist")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    path = scheduler.enable_listen(lydia_path="/usr/local/bin/lydia", runner=fake_run)
    content = path.read_text()
    assert "com.lydia.listen" in content and "RunAtLoad" in content and "KeepAlive" in content
    assert "<string>listen</string>" in content
    assert calls[0][:2] == ["launchctl", "load"]


def test_disable_listen_unloads_and_removes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plist = tmp_path / "listen.plist"
    plist.write_text("x")
    monkeypatch.setattr(scheduler, "LISTEN_PLIST_PATH", plist)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    scheduler.disable_listen(runner=fake_run)
    assert not plist.exists() and calls[0][:2] == ["launchctl", "unload"]
