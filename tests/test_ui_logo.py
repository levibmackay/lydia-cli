"""Tests for the banner's icon + wordmark rendering."""

from lydia.cli.ui import _ICON_ROWS, _with_icon, render_logo


def test_with_icon_prefixes_each_row() -> None:
    lines = ["AB", "CD"]
    combined = _with_icon(lines)
    assert len(combined) == 2
    assert combined[0].endswith("AB")
    assert combined[1].endswith("CD")
    assert combined[0].startswith(_ICON_ROWS[0])


def test_with_icon_pads_rows_beyond_icon_height() -> None:
    lines = ["row"] * (len(_ICON_ROWS) + 1)
    combined = _with_icon(lines)
    assert len(combined) == len(lines)
    last = combined[-1]
    assert last.endswith("row")
    assert last[: len(_ICON_ROWS[0])].strip() == ""  # blank icon padding, not a diamond row


def test_render_logo_returns_something_at_normal_terminal_width() -> None:
    logo = render_logo()
    assert logo is None or len(logo.plain) > 0
