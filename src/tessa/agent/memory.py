"""Conversation history persistence.

Each chat session is one JSONL file under the history directory
(~/.tessa/history/ globally, or <project>/.tessa/history/ inside a
project). One line per message keeps writes append-only and crash-safe.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from tessa.config.settings import GLOBAL_DIR, PROJECT_DIR_NAME
from tessa.llm.types import Message

logger = logging.getLogger(__name__)


def history_dir(project_root: Path | None) -> Path:
    base = project_root / PROJECT_DIR_NAME if project_root else GLOBAL_DIR
    return base / "history"


class SessionHistory:
    """Append-only log of one chat session."""

    def __init__(self, project_root: Path | None = None) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        self.path = history_dir(project_root) / f"session-{stamp}.jsonl"
        self._started = False

    def append(self, message: Message) -> None:
        try:
            if not self._started:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self._started = True
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(message.to_dict(), ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("Could not write history: %s", exc)


def list_sessions(project_root: Path | None = None, limit: int = 10) -> list[Path]:
    directory = history_dir(project_root)
    if not directory.is_dir():
        return []
    sessions = sorted(directory.glob("session-*.jsonl"), reverse=True)
    return sessions[:limit]


def load_session(path: Path) -> list[Message]:
    messages: list[Message] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            messages.append(Message(role=data["role"], content=data["content"]))
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        logger.warning("Could not load session %s: %s", path, exc)
    return messages
