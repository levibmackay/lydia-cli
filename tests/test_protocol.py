"""Both concrete clients must satisfy the ModelClient protocol structurally."""

from lydia.llm.client import OllamaClient
from lydia.llm.protocol import ModelClient
from lydia.llm.remote_client import RemoteClient


def test_ollama_client_satisfies_model_client() -> None:
    client = OllamaClient()
    assert isinstance(client, ModelClient)
    client.close()


def test_remote_client_satisfies_model_client() -> None:
    client = RemoteClient(base_url="https://example.com")
    assert isinstance(client, ModelClient)
    client.close()
