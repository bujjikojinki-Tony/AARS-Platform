from __future__ import annotations


class ReadOnlyConnectorError(RuntimeError):
    """Base error for PWB-04D read-only connector."""


class ReadOnlyConnectorNetworkDisabled(ReadOnlyConnectorError):
    """Raised when network access is disabled by config."""


class ReadOnlyConnectorRequestError(ReadOnlyConnectorError):
    """Raised when a read-only request fails."""


class ReadOnlyConnectorInvalidResponse(ReadOnlyConnectorError):
    """Raised when a read-only response cannot be parsed."""
