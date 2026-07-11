"""Picks which ModelClient implementation to construct from config.

If `server_url` is set, talk to a remote Lydia Server; otherwise, exactly
today's behavior — a local Ollama daemon at `ollama_host`. This is the one
place that needs to know both concrete client types; everything else in
the codebase only ever sees the `ModelClient` protocol.
"""

from __future__ import annotations

from lydia.config.settings import LydiaConfig
from lydia.llm.client import OllamaClient
from lydia.llm.protocol import ModelClient
from lydia.llm.remote_client import RemoteClient


def build_client(config: LydiaConfig) -> ModelClient:
    if config.server_url:
        return RemoteClient(base_url=config.server_url, api_key=config.api_key)
    return OllamaClient(host=config.ollama_host)
