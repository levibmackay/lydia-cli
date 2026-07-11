"""The model provider this server proxies to — currently always Ollama.

`lydia.llm.client.OllamaClient` already satisfies everything a provider
needs to (chat_stream, embed, list_models, is_alive) via the same
`ModelClient` protocol the CLI itself is built around — see
`lydia.llm.protocol`. A future provider (OpenAI, Anthropic, Gemini) is
just another class satisfying that same protocol; nothing in api/v1.py
would need to change beyond what `build_provider` constructs.
"""

from __future__ import annotations

from lydia.llm.client import OllamaClient
from lydia.llm.protocol import ModelClient

from lydia_server.config.settings import ServerSettings


def build_provider(settings: ServerSettings) -> ModelClient:
    return OllamaClient(host=settings.ollama_host)
