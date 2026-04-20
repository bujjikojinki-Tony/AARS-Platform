from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from weather_comparison_engine.schemas import (
    ComparisonPoint,
    ForecastSnapshot,
    MarketSnapshot,
)


class LiveSchemaValidator:
    """Validate existing live JSON files without changing their output format."""

    def validate(
        self,
        *,
        market_path: str | Path,
        forecast_path: str | Path,
        comparison_history_path: str | Path,
    ) -> dict:
        sections = {
            "market_snapshot": self._validate_single(Path(market_path), MarketSnapshot),
            "forecast_snapshot": self._validate_single(Path(forecast_path), ForecastSnapshot),
            "comparison_history": self._validate_comparison_history(Path(comparison_history_path)),
        }
        errors = [
            error
            for section in sections.values()
            for error in section.get("errors", [])
        ]
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "valid" if not errors else "invalid",
            "sections": sections,
            "errors": errors,
        }

    def write_report(self, report: dict, path: str | Path) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    def _validate_single(self, path: Path, model_class: type) -> dict:
        if not path.exists():
            return self._missing(path)

        try:
            payload = self._read_json(path)
            parsed = model_class.model_validate(payload)
        except Exception as exc:
            return self._invalid(path, exc)

        return {
            "status": "valid",
            "path": str(path),
            "market_id": getattr(parsed, "market_id", None),
            "schema_version": getattr(parsed, "schema_version", None),
            "errors": [],
        }

    def _validate_comparison_history(self, path: Path) -> dict:
        if not path.exists():
            return self._missing(path)

        try:
            payload = self._read_json(path)
            if not isinstance(payload, list):
                raise TypeError("comparison history must be a JSON list")
            parsed_rows = [ComparisonPoint.model_validate(row) for row in payload]
        except Exception as exc:
            return self._invalid(path, exc)

        latest = parsed_rows[-1] if parsed_rows else None
        market_ids = sorted({row.market_id for row in parsed_rows})
        return {
            "status": "valid",
            "path": str(path),
            "row_count": len(parsed_rows),
            "market_count": len(market_ids),
            "latest_market_id": latest.market_id if latest else None,
            "latest_timestamp": latest.timestamp if latest else None,
            "schema_version": "comparison_point.v1",
            "errors": [],
        }

    @staticmethod
    def _read_json(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _missing(path: Path) -> dict:
        return {
            "status": "missing",
            "path": str(path),
            "errors": [f"missing file: {path}"],
        }

    @staticmethod
    def _invalid(path: Path, exc: Exception) -> dict:
        if isinstance(exc, ValidationError):
            message = exc.errors()
        else:
            message = str(exc)
        return {
            "status": "invalid",
            "path": str(path),
            "errors": [f"{path}: {message}"],
        }

