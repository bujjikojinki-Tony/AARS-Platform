from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from uuid import uuid4

from weather_comparison_engine.polymarket_bot.models import AuditLog
from weather_comparison_engine.polymarket_bot.risk_manager import RiskManager
from weather_comparison_engine.polymarket_bot.risk_manager import RiskRules


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass(slots=True)
class RuleRegistry:
    min_edge_percent: float = 10.0
    min_liquidity: float = 100.0
    max_spread: float = 0.08
    max_position_percent: float = 2.0
    max_daily_loss_percent: float = 5.0
    circuit_breaker_loss_percent: float = 10.0
    execution_mode: str = "OBSERVE_ONLY"

    def as_dict(self) -> dict:
        return asdict(self)


class SettingsRoutes:
    def __init__(self, repositories, risk_manager: RiskManager, registry: RuleRegistry | None = None) -> None:
        self.repositories = repositories
        self.risk_manager = risk_manager
        self.registry = registry or RuleRegistry(
            min_edge_percent=risk_manager.rules.min_edge_percent,
            min_liquidity=risk_manager.rules.min_liquidity,
            max_spread=risk_manager.rules.max_spread,
            max_position_percent=risk_manager.rules.max_position_percent,
            max_daily_loss_percent=risk_manager.rules.max_daily_loss_percent,
            circuit_breaker_loss_percent=risk_manager.rules.circuit_breaker_loss_percent,
        )

    def get_rules(self) -> dict:
        return {"ok": True, "rules": self.registry.as_dict()}

    def post_rules(self, updates: dict) -> dict:
        allowed = {
            "min_edge_percent",
            "min_liquidity",
            "max_spread",
            "max_position_percent",
            "max_daily_loss_percent",
            "circuit_breaker_loss_percent",
        }
        for key, value in updates.items():
            if key not in allowed:
                continue
            setattr(self.registry, key, float(value))
        self.risk_manager.rules = RiskRules(
            min_edge_percent=self.registry.min_edge_percent,
            min_liquidity=self.registry.min_liquidity,
            max_spread=self.registry.max_spread,
            max_position_percent=self.registry.max_position_percent,
            max_daily_loss_percent=self.registry.max_daily_loss_percent,
            circuit_breaker_loss_percent=self.registry.circuit_breaker_loss_percent,
        )
        self.repositories.audit_logs.save(
            AuditLog(
                event_id=_make_id("audit"),
                event_type="RULES_UPDATED",
                object_type="RuleRegistry",
                object_id="default",
                payload_json=str({k: updates[k] for k in updates if k in allowed}),
                created_at=_now_iso(),
            )
        )
        return self.get_rules()

    def get_mode(self) -> dict:
        return {"ok": True, "mode": self.registry.execution_mode}

    def post_mode(self, mode: str) -> dict:
        normalized = mode.strip().upper()
        if normalized not in {"OBSERVE_ONLY", "SIMULATION"}:
            return {"ok": False, "error": "unsupported mode"}
        self.registry.execution_mode = normalized
        self.repositories.audit_logs.save(
            AuditLog(
                event_id=_make_id("audit"),
                event_type="MODE_UPDATED",
                object_type="ExecutionMode",
                object_id="default",
                payload_json=str({"mode": normalized}),
                created_at=_now_iso(),
            )
        )
        return self.get_mode()
