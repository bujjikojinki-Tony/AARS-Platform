from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable

from .forward import ForwardObservationSettings, build_forward_observation
from .storage import MarketStore


EXECUTION_MODE = "PAPER_ONLY"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class ForwardMonitorSettings:
    minimum_forward_bars: int = 24
    confirmation_bars: int = 168
    trial_limit: int = 100

    def __post_init__(self) -> None:
        ForwardObservationSettings(
            minimum_forward_bars=self.minimum_forward_bars,
            confirmation_bars=self.confirmation_bars,
        )
        if self.trial_limit <= 0:
            raise ValueError("trial limit must be positive")


def run_forward_monitor_cycle(
    store: MarketStore,
    *,
    settings: ForwardMonitorSettings = ForwardMonitorSettings(),
    now: datetime | None = None,
) -> dict[str, object]:
    """Advance every eligible trial by at most one immutable market endpoint."""
    generated = _utc(now or datetime.now(timezone.utc))
    trials = [
        item
        for item in store.list_paper_trial_results(limit=settings.trial_limit)
        if item["disposition"] == "ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION"
    ]
    records: list[dict[str, object]] = []
    observation_settings = ForwardObservationSettings(
        minimum_forward_bars=settings.minimum_forward_bars,
        confirmation_bars=settings.confirmation_bars,
    )
    for trial in trials:
        trial_id = str(trial["trial_id"])
        lifecycle = store.get_forward_candidate_lifecycle(trial_id)
        lifecycle_state = lifecycle["current_state"] if lifecycle else "OBSERVING"
        if lifecycle_state in {"PAUSED", "TERMINATED"}:
            records.append({
                "trial_id": trial_id,
                "status": lifecycle_state,
                "reason": (
                    "immutable human review paused forward observation"
                    if lifecycle_state == "PAUSED"
                    else "immutable human review terminated this candidate"
                ),
            })
            continue
        latest = store.latest_forward_observation_for_trial(trial_id)
        if latest and latest["disposition"] == "STOP_FORWARD_OBSERVATION":
            records.append({
                "trial_id": trial_id,
                "status": "STOPPED",
                "observation_id": latest["observation_id"],
                "observed_through": latest["observed_through"],
                "reason": "latest checkpoint triggered a hard stop",
            })
            continue
        envelope = store.get_paper_trial_result(trial_id)
        if envelope is None:
            records.append({
                "trial_id": trial_id,
                "status": "DEGRADED",
                "reason": "archived trial envelope is unavailable",
            })
            continue
        try:
            payload = build_forward_observation(
                store,
                envelope,
                settings=observation_settings,
                generated_at=generated,
            )
            endpoint = payload["boundary"]["synchronized_forward_end"]
            reused = bool(latest and latest["observed_through"] == endpoint)
            observation_id = store.archive_forward_observation(payload)
            records.append({
                "trial_id": trial_id,
                "status": "REUSED" if reused else "ARCHIVED",
                "observation_id": observation_id,
                "observed_through": endpoint,
                "disposition": payload["review_gate"]["disposition"],
                "forward_bars": payload["results"]["forward_bars"],
            })
        except ValueError as exc:
            reason = str(exc)
            waiting = reason.startswith("insufficient forward history")
            records.append({
                "trial_id": trial_id,
                "status": "WAITING" if waiting else "DEGRADED",
                "reason": reason,
            })

    statuses = {str(item["status"]) for item in records}
    if "DEGRADED" in statuses:
        status = "DEGRADED"
    elif "WAITING" in statuses or not records:
        status = "WAITING"
    else:
        status = "SUCCESS"
    return {
        "schema_version": "mil3.forward-monitor-cycle.v1",
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        "status": status,
        "settings": asdict(settings),
        "eligible_trials": len(trials),
        "records": records,
        "observation_application_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }


def run_forward_monitor(
    store: MarketStore,
    *,
    interval_seconds: float,
    settings: ForwardMonitorSettings = ForwardMonitorSettings(),
    max_cycles: int | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    on_cycle: Callable[[dict[str, object]], None] | None = None,
) -> list[dict[str, object]]:
    if interval_seconds <= 0:
        raise ValueError("interval seconds must be positive")
    if max_cycles is not None and max_cycles <= 0:
        raise ValueError("max cycles must be positive when supplied")
    completed = []
    while max_cycles is None or len(completed) < max_cycles:
        summary = run_forward_monitor_cycle(store, settings=settings, now=clock())
        completed.append(summary)
        if on_cycle is not None:
            on_cycle(summary)
        if max_cycles is not None and len(completed) >= max_cycles:
            break
        sleeper(interval_seconds)
    return completed
