from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from weather_telegram_console.settings import get_dashboard_intent_preview_path


class IntentWriter:
    def __init__(self, output_dir: str = "data/outputs/pending_intents") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_small_intent(
        self,
        signal_payload: dict,
        side: str = "buy",
        price: float = 0.42,
        size: float = 10.0,
    ) -> dict:
        intent_id = f"intent_{uuid4().hex[:10]}"
        signal_id = signal_payload.get("signal_id")
        probability_contract = signal_payload.get("probability_contract")
        if not isinstance(probability_contract, dict):
            probability_contract = {
                "contract_version": "probability_contract.v1",
                "probability_mode": str(signal_payload.get("probability_mode") or "heuristic_not_calibrated"),
                "calibration_status": str(signal_payload.get("calibration_status") or "not_calibrated"),
                "execution_constraint": str(
                    signal_payload.get("execution_constraint") or "manual_advisory_only"
                ),
            }

        return {
            "schema_version": "execution_intent.v1",
            "intent_id": intent_id,
            "market_id": signal_payload["market_id"],
            "signal_id": signal_id,
            "decision_ref": f"decision_telegram_{signal_id or intent_id}",
            "authorization_ref": "approval_required",
            "side": side,
            "price": price,
            "size": size,
            "post_only": True,
            "max_slippage_pct": 0.02,
            "approved": True,
            "probability_mode": probability_contract.get("probability_mode"),
            "execution_constraint": probability_contract.get("execution_constraint"),
            "calibration_status": probability_contract.get("calibration_status"),
            "contract_version": probability_contract.get("contract_version"),
            "probability_contract": probability_contract,
        }

    def write(self, intent_payload: dict) -> Path:
        intent_id = intent_payload["intent_id"]
        path = self.output_dir / f"{intent_id}.json"
        path.write_text(
            json.dumps(intent_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def find_pending_by_signal_id(self, signal_id: str) -> Path | None:
        for path in sorted(self.output_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("signal_id") == signal_id:
                return path
        return None

    def find_pending_by_market_id(self, market_id: str) -> Path | None:
        for path in sorted(self.output_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("market_id") == market_id:
                return path
        return None

    def load_payload(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def find_dashboard_preview_by_market_id(self, market_id: str) -> Path | None:
        path = get_dashboard_intent_preview_path()
        if not path.exists():
            return None
        payload = self.load_payload(path)
        if payload.get("market_id") == market_id:
            return path
        return None
