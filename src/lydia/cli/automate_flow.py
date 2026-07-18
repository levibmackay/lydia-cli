"""Shared plain-English automation creation flow, used by `lydia automate`
and the /automate slash command in chat."""

from __future__ import annotations

import typer

from lydia.automations import store
from lydia.automations.model import describe
from lydia.automations.parser import AutomationParseError, parse_automation
from lydia.cli import ui
from lydia.config.settings import LydiaConfig
from lydia.llm.protocol import ModelClient


def create_from_english(text: str, client: ModelClient, model: str,
                        config: LydiaConfig) -> bool:
    try:
        auto = parse_automation(text, client, model, config)
    except AutomationParseError as exc:
        ui.print_error(str(exc))
        return False
    ui.console.print(f"\nHere's what I understood:\n  {describe(auto)}\n")
    exists = store.recipe_path(auto.name).exists()
    prompt = "Overwrite this existing automation?" if exists else "Save this automation?"
    if not typer.confirm(prompt):
        ui.print_info("Discarded.")
        return False
    store.save_automation(auto)
    from lydia.cli import scheduler
    hint = ("" if scheduler.automations_enabled()
            else " Heartbeat is off — run `lydia automations schedule enable` so it actually fires.")
    ui.print_info(f"Saved '{auto.name}'.{hint}")
    return True
