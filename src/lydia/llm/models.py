"""Model selection heuristics.

When the user has not configured a model, pick the best coding-capable
model they already have installed. Matching is by substring on the model
name, in priority order.
"""

from __future__ import annotations

from lydia.llm.types import ModelInfo

# Higher in the list = preferred. Substrings matched against model names.
MODEL_PRIORITY: tuple[str, ...] = (
    "qwen3.5-coder",
    "qwen3-coder",
    "qwen2.5-coder",
    "deepseek-coder",
    "codellama",
    "codegemma",
    "qwen3.5",
    "qwen3",
    "llama3",
    "mistral",
)


def pick_default_model(models: list[ModelInfo]) -> str | None:
    """Choose the best installed model for coding work.

    Among models matching the same priority tier, prefer the largest
    (more parameters generally means better code quality).
    """
    if not models:
        return None
    for pattern in MODEL_PRIORITY:
        matches = [m for m in models if pattern in m.name.lower()]
        if matches:
            return max(matches, key=lambda m: m.size_bytes).name
    return max(models, key=lambda m: m.size_bytes).name
