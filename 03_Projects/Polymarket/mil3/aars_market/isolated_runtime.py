from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .storage import MarketStore


EXECUTION_MODE = "PAPER_ONLY"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def token_sha256(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IsolatedRuntimeSettings:
    lease_seconds: int = 30
    heartbeat_interval_seconds: float = 10.0
    max_cycles: int = 1

    def __post_init__(self) -> None:
        if not 5 <= self.lease_seconds <= 300:
            raise ValueError("lease seconds must be between 5 and 300")
        if self.heartbeat_interval_seconds <= 0:
            raise ValueError("heartbeat interval seconds must be positive")
        if self.heartbeat_interval_seconds >= self.lease_seconds:
            raise ValueError("heartbeat interval must be shorter than the lease")
        if self.max_cycles <= 0:
            raise ValueError("max cycles must be positive")


def acquire_isolated_runtime(
    store: MarketStore,
    sandbox_id: str,
    *,
    worker_id: str,
    settings: IsolatedRuntimeSettings,
    now: datetime | None = None,
    token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
) -> dict[str, object]:
    token = token_factory()
    if len(token) < 16:
        raise ValueError("runtime fencing token is too short")
    result = store.acquire_isolated_paper_runtime(
        sandbox_id,
        worker_id=worker_id,
        fencing_token_sha256=token_sha256(token),
        lease_seconds=settings.lease_seconds,
        now=_utc(now or datetime.now(timezone.utc)),
    )
    return {**result, "fencing_token": token}


def run_isolated_runtime_cycle(
    store: MarketStore,
    session_id: str,
    fencing_token: str,
    *,
    lease_seconds: int,
    now: datetime | None = None,
) -> dict[str, object]:
    """Renew one fenced lease, then run one idempotent paper-ledger cycle."""
    heartbeat = store.heartbeat_isolated_paper_runtime(
        session_id,
        fencing_token_sha256=token_sha256(fencing_token),
        lease_seconds=lease_seconds,
        now=_utc(now or datetime.now(timezone.utc)),
    )
    if heartbeat["effective_status"] != "RUNNING":
        return {**heartbeat, "paper_cycle": {"status": "FENCED"}}
    from .runtime_ledger import execute_runtime_paper_cycle

    cycle_time = _utc(now or datetime.now(timezone.utc))
    try:
        paper_cycle = execute_runtime_paper_cycle(
            store, session_id, fencing_token, now=cycle_time
        )
    except ValueError as exc:
        reason = str(exc)
        waiting = reason.startswith((
            "no stored candle", "insufficient synchronized runtime candles"
        ))
        paper_cycle = {
            "status": "WAITING" if waiting else "BLOCKED",
            "reason": reason,
            "paper_ledger_committed": False,
        }
    return {
        **heartbeat,
        "paper_cycle": paper_cycle,
        "paper_ledger_calculation_enabled": True,
        "external_order_requests_created": False,
    }


def run_isolated_paper_runtime(
    store: MarketStore,
    sandbox_id: str,
    *,
    worker_id: str,
    settings: IsolatedRuntimeSettings = IsolatedRuntimeSettings(),
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
    on_cycle: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    """Run a bounded governed paper-calculation worker without external orders."""
    acquired = acquire_isolated_runtime(
        store,
        sandbox_id,
        worker_id=worker_id,
        settings=settings,
        now=clock(),
        token_factory=token_factory,
    )
    session_id = str(acquired["session_id"])
    token = str(acquired["fencing_token"])
    cycles: list[dict[str, object]] = []
    try:
        for index in range(settings.max_cycles):
            cycle = run_isolated_runtime_cycle(
                store,
                session_id,
                token,
                lease_seconds=settings.lease_seconds,
                now=clock(),
            )
            cycles.append(cycle)
            if on_cycle is not None:
                on_cycle(cycle)
            if cycle["effective_status"] != "RUNNING":
                break
            if index + 1 < settings.max_cycles:
                sleeper(settings.heartbeat_interval_seconds)
    finally:
        current = store.resolve_isolated_paper_runtime_session(session_id, now=clock())
        if current["stored_status"] == "RUNNING":
            store.stop_isolated_paper_runtime(
                session_id,
                operator=worker_id,
                note="Bounded PAPER_ONLY runtime completed.",
                reason="BOUNDED_RUN_COMPLETE",
                now=clock(),
            )
    final = store.resolve_isolated_paper_runtime_session(session_id, now=clock())
    return {
        "schema_version": "mil3.isolated-paper-runtime-run.v1",
        "execution_mode": EXECUTION_MODE,
        "sandbox_id": sandbox_id,
        "session_id": session_id,
        "configuration_id": acquired["configuration_id"],
        "cycles": cycles,
        "final_status": final["effective_status"],
        "paper_configuration_consumed": bool(cycles),
        "paper_ledger_cycles_committed": sum(
            cycle.get("paper_cycle", {}).get("status") == "COMMITTED"
            for cycle in cycles
        ),
        "paper_ledger_cycles_reused": sum(
            cycle.get("paper_cycle", {}).get("status") == "REUSED_COMMITTED"
            for cycle in cycles
        ),
        "replay_started": False,
        "order_path_present": False,
        "shared_configuration_change_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }
