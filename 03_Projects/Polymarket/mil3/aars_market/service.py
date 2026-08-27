from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .dashboard import build_dashboard_payload
from .portfolio import build_portfolio_payload
from .stable_diff import compare_stable_views
from .storage import MarketStore


DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
WINDOWS: dict[str, timedelta | None] = {
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "180d": timedelta(days=180),
    "365d": timedelta(days=365),
    "all": None,
}


@dataclass(frozen=True)
class DashboardRequest:
    symbol: str = "SOLUSDT"
    timeframe: str = "1h"
    replay_window: str = "90d"


@dataclass(frozen=True)
class PortfolioRequest:
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS
    timeframe: str = "1h"
    replay_window: str = "90d"
    strategy: str = "AARS_DYNAMIC"


class DashboardService:
    """Orchestration over persisted market data and PAPER_ONLY shadow replay."""

    def __init__(self, store: MarketStore, *, warmup_bars: int = 120) -> None:
        self.store = store
        self.warmup_bars = warmup_bars

    def markets(self) -> list[dict[str, object]]:
        return self.store.list_markets()

    def funding_cadence(self, symbol: str) -> dict[str, Any]:
        normalized = symbol.upper()
        if normalized not in DEFAULT_SYMBOLS:
            raise ValueError(f"unsupported symbol: {normalized}")
        observations = self.store.load_funding_cadence_observations(normalized)
        history = [
            {
                "symbol": item.symbol,
                "observed_at": item.observed_at.astimezone(timezone.utc).isoformat(),
                "interval_hours": item.interval_hours,
                "adjusted_rate_cap": item.adjusted_rate_cap,
                "adjusted_rate_floor": item.adjusted_rate_floor,
                "disclaimer": item.disclaimer,
                "source_status": item.source_status,
            }
            for item in observations
        ]
        current = history[-1] if history else {
            "symbol": normalized,
            "observed_at": None,
            "interval_hours": 8,
            "adjusted_rate_cap": None,
            "adjusted_rate_floor": None,
            "disclaimer": False,
            "source_status": "DEFAULT_8H_FALLBACK",
        }
        return {
            "schema_version": "mil3.funding-cadence.v1",
            "execution_mode": "PAPER_ONLY",
            "current": current,
            "observations": history,
        }

    def build(
        self,
        request: DashboardRequest,
        *,
        now: datetime | None = None,
        archive: bool = True,
        max_trace_points: int = 240,
    ) -> dict[str, Any]:
        symbol = request.symbol.upper()
        if symbol not in DEFAULT_SYMBOLS:
            raise ValueError(f"unsupported symbol: {symbol}")
        if request.replay_window not in WINDOWS:
            raise ValueError(f"unsupported replay window: {request.replay_window}")
        current = now or datetime.now(timezone.utc)
        duration = WINDOWS[request.replay_window]
        latest = self.store.latest_open_time(symbol, request.timeframe)
        if latest is None:
            raise ValueError(f"no candles stored for {symbol} {request.timeframe}")
        start = latest - duration if duration is not None else None
        candles = self.store.load_candles(symbol, request.timeframe, start=start, end=latest)
        if len(candles) <= self.warmup_bars:
            raise ValueError(
                f"need > {self.warmup_bars} candles for {symbol} {request.timeframe} "
                f"window={request.replay_window}; stored={len(candles)}"
            )
        funding = self.store.load_funding_rates(
            symbol,
            start=candles[0].open_time,
            end=candles[-1].open_time,
        )
        cadence_observations = self.store.load_funding_cadence_observations(
            symbol,
            start=candles[self.warmup_bars - 1].open_time,
            end=candles[-1].open_time,
            include_previous=True,
        )
        payload = build_dashboard_payload(
            candles,
            warmup_bars=self.warmup_bars,
            funding_rates=funding,
            funding_cadence_observations=cadence_observations,
            data_fresh=self.store.is_fresh(symbol, request.timeframe, now=current),
            source="SQLite normalized Binance public market data",
            generated_at=current,
            max_trace_points=max_trace_points,
        )
        payload["selection"] = {
            "symbol": symbol,
            "timeframe": request.timeframe,
            "replay_window": request.replay_window,
        }
        payload["available_markets"] = self.markets()
        payload["available_windows"] = list(WINDOWS)
        if archive:
            view_id = self.store.archive_latest_stable_view(
                payload, replay_window=request.replay_window, created_at=current
            )
            payload["latest_stable_view_archive"] = {
                "view_id": view_id,
                "archived_at": current.astimezone(timezone.utc).isoformat(),
                "immutable": True,
            }
        else:
            payload["latest_stable_view_archive"] = None
        return payload

    def build_portfolio(
        self,
        request: PortfolioRequest,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(timezone.utc)
        symbols = tuple(symbol.upper() for symbol in request.symbols)
        if not symbols:
            raise ValueError("portfolio symbols must not be empty")
        if len(set(symbols)) != len(symbols):
            raise ValueError("portfolio symbols must be unique")
        payloads = [
            self.build(
                DashboardRequest(symbol, request.timeframe, request.replay_window),
                now=current,
                archive=False,
                max_trace_points=1_000_000,
            )
            for symbol in symbols
        ]
        payload = build_portfolio_payload(
            payloads,
            strategy_id=request.strategy,
            generated_at=current,
        )
        payload["selection"] = {
            "symbols": list(symbols),
            "timeframe": request.timeframe,
            "replay_window": request.replay_window,
        }
        return payload

    def compare_views(self, before_id: str, after_id: str) -> dict[str, Any]:
        before = self.store.get_latest_stable_view(before_id)
        after = self.store.get_latest_stable_view(after_id)
        if before is None:
            raise ValueError(f"stable view not found: {before_id}")
        if after is None:
            raise ValueError(f"stable view not found: {after_id}")
        before_market = before.get("market", {})
        after_market = after.get("market", {})
        if (
            before_market.get("symbol"),
            before_market.get("timeframe"),
        ) != (
            after_market.get("symbol"),
            after_market.get("timeframe"),
        ):
            raise ValueError("stable views must use the same symbol and timeframe")
        return compare_stable_views(
            before,
            after,
            before_id=before_id,
            after_id=after_id,
        )

    def list_shadow_snapshots(
        self, *, limit: int = 30, target_strategy: str | None = None
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.shadow-daily-index.v1",
            "execution_mode": "PAPER_ONLY",
            "shadow_snapshots": self.store.list_shadow_daily_snapshots(
                limit=limit, target_strategy=target_strategy
            ),
            "read_only": True,
        }

    def shadow_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        payload = self.store.get_shadow_daily_snapshot(snapshot_id)
        if payload is None:
            raise KeyError(f"shadow snapshot not found: {snapshot_id}")
        return payload

    def shadow_stability(
        self, *, limit: int = 90, target_strategy: str | None = None
    ) -> dict[str, Any]:
        # Local import avoids coupling the base dashboard path to validation code.
        from .shadow import build_shadow_stability

        snapshots = self.store.load_shadow_daily_snapshots(
            limit=limit, target_strategy=target_strategy
        )
        return build_shadow_stability(snapshots)

    def promotion_governance(
        self, *, limit: int = 90, target_strategy: str | None = None
    ) -> dict[str, Any]:
        from .governance import build_promotion_governance

        stability = self.shadow_stability(
            limit=limit, target_strategy=target_strategy
        )
        return build_promotion_governance(stability)

    def list_paper_proposals(
        self, *, limit: int = 30, target_strategy: str | None = None
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.paper-configuration-proposal-index.v1",
            "execution_mode": "PAPER_ONLY",
            "proposals": self.store.list_paper_configuration_proposals(
                limit=limit, target_strategy=target_strategy
            ),
            "read_only": True,
            "proposal_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def paper_proposal(self, proposal_id: str) -> dict[str, Any]:
        payload = self.store.get_paper_configuration_proposal(proposal_id)
        if payload is None:
            raise KeyError(f"paper proposal not found: {proposal_id}")
        return payload

    def list_paper_trials(
        self, *, limit: int = 30, target_strategy: str | None = None
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.paper-trial-result-index.v1",
            "execution_mode": "PAPER_ONLY",
            "trials": self.store.list_paper_trial_results(
                limit=limit, target_strategy=target_strategy
            ),
            "read_only": True,
            "trial_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def paper_trial(self, trial_id: str) -> dict[str, Any]:
        payload = self.store.get_paper_trial_result(trial_id)
        if payload is None:
            raise KeyError(f"paper trial not found: {trial_id}")
        return payload

    def list_forward_observations(
        self, *, limit: int = 30, target_strategy: str | None = None, trial_id: str | None = None
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.forward-observation-index.v1",
            "execution_mode": "PAPER_ONLY",
            "observations": self.store.list_forward_observations(
                limit=limit, target_strategy=target_strategy, trial_id=trial_id
            ),
            "read_only": True,
            "observation_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def forward_observation(self, observation_id: str) -> dict[str, Any]:
        payload = self.store.get_forward_observation(observation_id)
        if payload is None:
            raise KeyError(f"forward observation not found: {observation_id}")
        return payload

    def forward_stability(
        self, trial_id: str, *, limit: int = 90
    ) -> dict[str, Any]:
        from .forward_stability import build_forward_stability

        trial = self.store.get_paper_trial_result(trial_id)
        if trial is None:
            raise KeyError(f"paper trial not found: {trial_id}")
        observations = self.store.load_forward_observations(trial_id, limit=limit)
        payload = build_forward_stability(observations)
        if not observations:
            payload["trial_id"] = trial_id
            payload["target_strategy"] = trial["trial"]["target_strategy"]
        return payload

    def forward_candidate_lifecycle(self, trial_id: str) -> dict[str, Any]:
        payload = self.store.get_forward_candidate_lifecycle(trial_id)
        if payload is None:
            raise KeyError(f"paper trial not found: {trial_id}")
        return payload

    def forward_candidate_review(self, review_id: str) -> dict[str, Any]:
        payload = self.store.get_forward_candidate_review(review_id)
        if payload is None:
            raise KeyError(f"forward candidate review not found: {review_id}")
        return {
            "schema_version": "mil3.forward-candidate-review-envelope.v1",
            "execution_mode": "PAPER_ONLY",
            "review_id": review_id,
            "review": payload,
            "read_only": True,
            "review_action_applies_parameters": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def forward_evidence_manifest(self, trial_id: str) -> dict[str, Any]:
        from .evidence_export import build_forward_evidence_bundle

        bundle = build_forward_evidence_bundle(self.store, trial_id)
        return {
            "schema_version": "mil3.forward-evidence-manifest.v1",
            "execution_mode": "PAPER_ONLY",
            "trial_id": trial_id,
            "target_strategy": bundle["target_strategy"],
            "lifecycle_state": bundle["lifecycle_state"],
            "manifest": bundle["manifest"],
            "read_only": True,
            "evidence_export_only": True,
            "review_action_applies_parameters": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def evidence_governance_policy(self) -> dict[str, Any]:
        from .evidence_offline import (
            DEFAULT_MINIMUM_COPIES,
            DEFAULT_RETENTION_DAYS,
        )

        return {
            "schema_version": "mil3.evidence-governance-policy.v1",
            "execution_mode": "PAPER_ONLY",
            "offline_verification_required": True,
            "strict_duplicate_key_rejection": True,
            "retention_days": DEFAULT_RETENTION_DAYS,
            "minimum_verified_copies": DEFAULT_MINIMUM_COPIES,
            "prune_scope": "RECOGNIZED_FORWARD_EVIDENCE_ARTIFACTS_ONLY",
            "read_only": True,
            "approval_applies_configuration": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def isolated_activation_lifecycle(
        self, trial_id: str, *, now: datetime | None = None
    ) -> dict[str, Any]:
        return self.store.get_isolated_activation_lifecycle(trial_id, now=now)

    def isolated_activation_review(self, review_id: str) -> dict[str, Any]:
        payload = self.store.get_isolated_activation_review(review_id)
        if payload is None:
            raise KeyError(f"isolated activation review not found: {review_id}")
        return {
            "schema_version": "mil3.isolated-paper-activation-review-envelope.v1",
            "execution_mode": "PAPER_ONLY",
            "review_id": review_id,
            "review": payload,
            "read_only": True,
            "isolated_paper_activation_allowed": payload["authority"][
                "isolated_paper_activation_allowed"
            ],
            "approval_applies_configuration": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def list_isolated_configurations(
        self, *, sandbox_id: str | None = None, limit: int = 100
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.isolated-paper-configuration-index.v1",
            "execution_mode": "PAPER_ONLY",
            "configurations": self.store.list_isolated_paper_configurations(
                sandbox_id=sandbox_id, limit=limit
            ),
            "read_only": True,
            "registry_entries_inert": True,
            "starts_strategy_process": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def isolated_configuration(self, configuration_id: str) -> dict[str, Any]:
        payload = self.store.get_isolated_paper_configuration(configuration_id)
        if payload is None:
            raise KeyError(f"isolated paper configuration not found: {configuration_id}")
        return {
            "schema_version": "mil3.isolated-paper-configuration-envelope.v1",
            "execution_mode": "PAPER_ONLY",
            "configuration_id": configuration_id,
            "configuration": payload,
            "read_only": True,
            "registry_entry_inert": True,
            "starts_strategy_process": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def isolated_sandbox(
        self, sandbox_id: str, *, now: datetime | None = None
    ) -> dict[str, Any]:
        return self.store.resolve_isolated_paper_sandbox(sandbox_id, now=now)

    def list_isolated_sandbox_events(
        self, sandbox_id: str, *, limit: int = 100
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.isolated-paper-sandbox-event-index.v1",
            "execution_mode": "PAPER_ONLY",
            "sandbox_id": sandbox_id,
            "events": list(reversed(self.store.list_isolated_paper_sandbox_events(
                sandbox_id, limit=limit
            ))),
            "read_only": True,
            "starts_strategy_process": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def isolated_sandbox_event(self, event_id: str) -> dict[str, Any]:
        payload = self.store.get_isolated_paper_sandbox_event(event_id)
        if payload is None:
            raise KeyError(f"isolated paper sandbox event not found: {event_id}")
        return {
            "schema_version": "mil3.isolated-paper-sandbox-event-envelope.v1",
            "execution_mode": "PAPER_ONLY",
            "event_id": event_id,
            "event": payload,
            "read_only": True,
            "starts_strategy_process": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def isolated_runtime(self, sandbox_id: str, *, limit: int = 100) -> dict[str, Any]:
        sessions = self.store.list_isolated_paper_runtime_sessions(
            sandbox_id, limit=limit
        )
        return {
            "schema_version": "mil3.isolated-paper-runtime-index.v1",
            "execution_mode": "PAPER_ONLY",
            "sandbox_id": sandbox_id,
            "kill_switch": self.store.isolated_paper_runtime_kill_switch(sandbox_id),
            "sessions": sessions,
            "latest_session": sessions[0] if sessions else None,
            "read_only": True,
            "browser_control_allowed": False,
            "configuration_consumption_only": True,
            "replay_started": False,
            "order_path_present": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def isolated_runtime_session(self, session_id: str) -> dict[str, Any]:
        return self.store.resolve_isolated_paper_runtime_session(session_id)

    def isolated_runtime_events(
        self, session_id: str, *, limit: int = 100
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.isolated-paper-runtime-event-index.v1",
            "execution_mode": "PAPER_ONLY",
            "session_id": session_id,
            "events": list(reversed(self.store.list_isolated_paper_runtime_events(
                session_id, limit=limit
            ))),
            "read_only": True,
            "browser_control_allowed": False,
            "replay_started": False,
            "order_path_present": False,
            "live_execution_allowed": False,
        }

    def isolated_runtime_kill_events(
        self, sandbox_id: str, *, limit: int = 100
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.isolated-paper-runtime-kill-event-index.v1",
            "execution_mode": "PAPER_ONLY",
            "sandbox_id": sandbox_id,
            "events": list(reversed(self.store.list_isolated_paper_runtime_kill_events(
                sandbox_id, limit=limit
            ))),
            "read_only": True,
            "browser_control_allowed": False,
            "starts_runtime": False,
            "live_execution_allowed": False,
        }
