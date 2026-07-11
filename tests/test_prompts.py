"""Tests for system prompt assembly."""

from lydia.agent.facts import Fact
from lydia.agent.prompts import SYSTEM_PROMPT, build_system_prompt


def test_no_summary_or_facts_returns_base_prompt() -> None:
    assert build_system_prompt() == SYSTEM_PROMPT


def test_facts_are_folded_into_prompt() -> None:
    facts = [Fact(text="uses PostgreSQL", created_at="t1"), Fact(text="tabs not spaces", created_at="t2")]
    prompt = build_system_prompt(facts=facts)
    assert "uses PostgreSQL" in prompt
    assert "tabs not spaces" in prompt
    assert "Remembered facts" in prompt


def test_empty_facts_list_adds_no_section() -> None:
    prompt = build_system_prompt(facts=[])
    assert "Remembered facts" not in prompt


def test_plan_mode_appends_addendum() -> None:
    prompt = build_system_prompt(mode="plan")
    assert "plan mode" in prompt
    assert "edit_file" in prompt


def test_ask_and_auto_mode_do_not_append_plan_addendum() -> None:
    assert "plan mode" not in build_system_prompt(mode="ask")
    assert "plan mode" not in build_system_prompt(mode="auto")


def test_verify_command_appended_when_set() -> None:
    prompt = build_system_prompt(mode="ask", verify_command="pytest -q")
    assert "pytest -q" in prompt
    assert "run_command" in prompt


def test_verify_command_absent_by_default() -> None:
    assert "run_command" not in build_system_prompt(mode="ask")


def test_verify_command_suppressed_in_plan_mode() -> None:
    # Telling the model to run something via run_command while also saying
    # run_command isn't available would be self-contradictory.
    prompt = build_system_prompt(mode="plan", verify_command="pytest -q")
    assert "pytest -q" not in prompt
