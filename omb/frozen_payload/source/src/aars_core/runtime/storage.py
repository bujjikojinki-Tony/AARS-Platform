from __future__ import annotations

from threading import RLock
from typing import Protocol


class StorageAdapter(Protocol):
    def get(self, namespace: str, key: str) -> bytes | None: ...
    def put(self, namespace: str, key: str, value: bytes) -> None: ...
    def delete(self, namespace: str, key: str) -> bool: ...
    def list_keys(self, namespace: str, prefix: str = "") -> tuple[str, ...]: ...


class InMemoryStorage:
    """Generic reference backend for tests and ephemeral runtime metadata."""

    def __init__(self) -> None:
        self._values: dict[tuple[str, str], bytes] = {}
        self._lock = RLock()

    def get(self, namespace: str, key: str) -> bytes | None:
        with self._lock:
            return self._values.get((namespace, key))

    def put(self, namespace: str, key: str, value: bytes) -> None:
        if not namespace or not key:
            raise ValueError("namespace and key are required")
        with self._lock:
            self._values[(namespace, key)] = bytes(value)

    def delete(self, namespace: str, key: str) -> bool:
        with self._lock:
            return self._values.pop((namespace, key), None) is not None

    def list_keys(self, namespace: str, prefix: str = "") -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(key for candidate_namespace, key in self._values if candidate_namespace == namespace and key.startswith(prefix)))

