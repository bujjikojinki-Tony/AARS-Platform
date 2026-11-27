from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class RuntimeConfig:
    values: Mapping[str, Any]

    def get(self, path: str, default: Any = None) -> Any:
        current: Any = self.values
        for part in path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return default
            current = current[part]
        return current


class ConfigLoader:
    """Loads defaults < JSON file < AARS_* environment < explicit overrides."""

    def __init__(self, defaults: Mapping[str, Any] | None = None) -> None:
        self.defaults = dict(defaults or {})

    def load(
        self,
        file_path: str | Path | None = None,
        environ: Mapping[str, str] | None = None,
        overrides: Mapping[str, Any] | None = None,
    ) -> RuntimeConfig:
        values = _merge({}, self.defaults)
        if file_path:
            file_values = json.loads(Path(file_path).read_text(encoding="utf-8"))
            if not isinstance(file_values, dict):
                raise ValueError("Runtime configuration root must be an object")
            values = _merge(values, file_values)
        for key, value in sorted((environ or {}).items()):
            if key.startswith("AARS_"):
                _set_path(values, key[5:].lower().split("__"), _decode(value))
        values = _merge(values, overrides or {})
        return RuntimeConfig(values)


def _merge(base: dict[str, Any], incoming: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in incoming.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _merge(dict(result[key]), value)
        elif isinstance(value, Mapping):
            result[key] = _merge({}, value)
        else:
            result[key] = value
    return result


def _set_path(target: dict[str, Any], parts: list[str], value: Any) -> None:
    current = target
    for part in parts[:-1]:
        child = current.setdefault(part, {})
        if not isinstance(child, dict):
            raise ValueError(f"Configuration path conflicts at {part}")
        current = child
    current[parts[-1]] = value


def _decode(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value

