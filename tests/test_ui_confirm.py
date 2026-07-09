"""Tests for the non-interactive auto_confirm used by `tessa ask --yes`."""

from tessa.agent.tools import ConfirmRequest
from tessa.cli.ui import auto_confirm


def test_auto_confirm_approves_non_dangerous() -> None:
    assert auto_confirm(ConfirmRequest(title="Update a.py", detail="diff", danger=False)) is True


def test_auto_confirm_declines_dangerous() -> None:
    assert auto_confirm(ConfirmRequest(title="Run: rm -rf x", detail="rm -rf x", danger=True)) is False
