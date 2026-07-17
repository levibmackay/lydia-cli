"""ntfy.sh push connector — send a notification to the user's phone.

The topic name is effectively a password (anyone who knows it can subscribe),
so it lives in the OS keychain (config/secrets.py::NTFY_TOPIC), generated
randomly by `lydia auth login ntfy`. `transport` is injectable for tests,
same pattern as the Canvas connector.
"""

from __future__ import annotations

import httpx

from lydia.connectors import ConnectorError

NTFY_BASE_URL = "https://ntfy.sh"


def send_push(
    topic: str,
    title: str,
    message: str,
    priority: str = "default",
    transport: httpx.BaseTransport | None = None,
) -> None:
    try:
        # Use UTF-8 encoding for headers to support non-ASCII characters like the middle dot (·)
        headers = httpx.Headers([("Title", title), ("Priority", priority)], encoding="utf-8")
        with httpx.Client(base_url=NTFY_BASE_URL, timeout=10.0, transport=transport) as client:
            response = client.post(
                f"/{topic}",
                content=message.encode("utf-8"),
                headers=headers,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ConnectorError(f"ntfy push failed: {exc}") from exc
