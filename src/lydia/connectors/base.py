"""Base classes for connectors."""

from __future__ import annotations


class ConnectorError(Exception):
    """A connector could not fetch data; message is shown to the model."""
