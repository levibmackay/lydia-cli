"""Shared data types for the LLM layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class Message:
    """A single chat message."""

    role: Role
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content}


@dataclass
class ModelInfo:
    """An installed Ollama model."""

    name: str
    size_bytes: int = 0
    modified_at: str = ""

    @property
    def size_human(self) -> str:
        size = float(self.size_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@dataclass
class ChatChunk:
    """One streamed piece of an assistant reply.

    Thinking models (qwen3, deepseek-r1, ...) stream their reasoning in
    a separate `thinking` field before any answer content arrives.
    """

    content: str = ""
    thinking: str = ""
    done: bool = False
    stats: dict[str, Any] = field(default_factory=dict)
