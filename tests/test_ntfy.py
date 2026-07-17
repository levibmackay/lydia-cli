import httpx
import pytest

from lydia.connectors import ConnectorError
from lydia.connectors.ntfy import send_push


def test_send_push_posts_to_topic():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["title"] = request.headers.get("Title")
        captured["priority"] = request.headers.get("Priority")
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(200)

    send_push("lydia-abc123", "Lydia · test", "hello phone",
              transport=httpx.MockTransport(handler))
    assert captured["url"] == "https://ntfy.sh/lydia-abc123"
    assert captured["title"] == "Lydia · test"
    assert captured["priority"] == "default"
    assert captured["body"] == "hello phone"


def test_send_push_raises_connector_error_on_http_failure():
    transport = httpx.MockTransport(lambda r: httpx.Response(500))
    with pytest.raises(ConnectorError):
        send_push("t", "x", "y", transport=transport)
