"""Tests for model auto-selection."""

from lydia.llm.models import pick_default_model
from lydia.llm.types import ModelInfo


def m(name: str, size: int = 1) -> ModelInfo:
    return ModelInfo(name=name, size_bytes=size)


def test_empty_returns_none() -> None:
    assert pick_default_model([]) is None


def test_prefers_coder_models() -> None:
    chosen = pick_default_model([m("llama3.2:latest", 100), m("qwen2.5-coder:7b", 10)])
    assert chosen == "qwen2.5-coder:7b"


def test_prefers_larger_within_family() -> None:
    chosen = pick_default_model([
        m("qwen3.5:0.8b", 1), m("qwen3.5:9b", 9), m("qwen3.5:4b", 4),
    ])
    assert chosen == "qwen3.5:9b"


def test_unknown_models_fall_back_to_largest() -> None:
    chosen = pick_default_model([m("mystery:1b", 1), m("mystery:13b", 13)])
    assert chosen == "mystery:13b"
