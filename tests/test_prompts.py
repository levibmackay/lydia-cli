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
