from dataclasses import dataclass

from aars_weather_trading.contracts.contract_versions import UNIFIED_STATUS_CONTRACT_VERSION


@dataclass(frozen=True)
class WorkerStatus:
    freshness: str
    last_success_at: str | None
    last_error: str | None = None


@dataclass(frozen=True)
class UnifiedStatusContract:
    overall_status: str
    market_worker: WorkerStatus
    forecast_worker: WorkerStatus
    comparison_worker: WorkerStatus
    dashboard_worker: WorkerStatus | None = None
    telegram_bridge: WorkerStatus | None = None
    updated_at: str | None = None
    contract_version: str = UNIFIED_STATUS_CONTRACT_VERSION

