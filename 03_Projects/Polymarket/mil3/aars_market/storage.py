from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from .models import Candle, FundingCadenceObservation, FundingRate


_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS candles (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open_time TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    source TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (symbol, timeframe, open_time)
);

CREATE INDEX IF NOT EXISTS idx_candles_symbol_tf_time
ON candles(symbol, timeframe, open_time);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    requested_count INTEGER NOT NULL DEFAULT 0,
    upserted_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    error TEXT
);

CREATE TABLE IF NOT EXISTS funding_rates (
    symbol TEXT NOT NULL,
    funding_time TEXT NOT NULL,
    funding_rate REAL NOT NULL,
    mark_price REAL,
    rate_type TEXT NOT NULL,
    source TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (symbol, funding_time, rate_type)
);

CREATE INDEX IF NOT EXISTS idx_funding_symbol_time
ON funding_rates(symbol, funding_time);

CREATE TABLE IF NOT EXISTS funding_cadence_observations (
    symbol TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    interval_hours INTEGER NOT NULL,
    adjusted_rate_cap REAL,
    adjusted_rate_floor REAL,
    disclaimer INTEGER NOT NULL,
    source_status TEXT NOT NULL,
    source TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (symbol, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_funding_cadence_symbol_time
ON funding_cadence_observations(symbol, observed_at);

CREATE TABLE IF NOT EXISTS latest_stable_views (
    view_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    replay_window TEXT NOT NULL,
    as_of TEXT NOT NULL,
    created_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_stable_views_market_created
ON latest_stable_views(symbol, timeframe, created_at DESC);

CREATE TABLE IF NOT EXISTS ingestion_cycles (
    cycle_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    status TEXT NOT NULL,
    execution_mode TEXT NOT NULL,
    summary_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ingestion_cycles_finished
ON ingestion_cycles(finished_at DESC);

CREATE TABLE IF NOT EXISTS shadow_daily_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    as_of TEXT NOT NULL,
    created_at TEXT NOT NULL,
    target_strategy TEXT NOT NULL,
    symbols_json TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shadow_daily_created
ON shadow_daily_snapshots(created_at DESC, snapshot_id DESC);

CREATE TABLE IF NOT EXISTS paper_configuration_proposals (
    proposal_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    target_strategy TEXT NOT NULL,
    source_snapshot_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (source_snapshot_id) REFERENCES shadow_daily_snapshots(snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_proposals_created
ON paper_configuration_proposals(created_at DESC, proposal_id DESC);

CREATE TABLE IF NOT EXISTS paper_proposal_reviews (
    review_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL UNIQUE,
    reviewed_at TEXT NOT NULL,
    disposition TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (proposal_id) REFERENCES paper_configuration_proposals(proposal_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_reviews_reviewed
ON paper_proposal_reviews(reviewed_at DESC, review_id DESC);

CREATE TABLE IF NOT EXISTS paper_trial_results (
    trial_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL UNIQUE,
    source_snapshot_id TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    target_strategy TEXT NOT NULL,
    disposition TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (proposal_id) REFERENCES paper_configuration_proposals(proposal_id),
    FOREIGN KEY (source_snapshot_id) REFERENCES shadow_daily_snapshots(snapshot_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_trials_completed
ON paper_trial_results(completed_at DESC, trial_id DESC);

CREATE TABLE IF NOT EXISTS forward_observations (
    observation_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL,
    observed_through TEXT NOT NULL,
    created_at TEXT NOT NULL,
    target_strategy TEXT NOT NULL,
    disposition TEXT NOT NULL,
    input_sha256 TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    UNIQUE(trial_id, observed_through),
    FOREIGN KEY (trial_id) REFERENCES paper_trial_results(trial_id)
);

CREATE INDEX IF NOT EXISTS idx_forward_observations_created
ON forward_observations(created_at DESC, observation_id DESC);

CREATE INDEX IF NOT EXISTS idx_forward_observations_trial_end
ON forward_observations(trial_id, observed_through DESC);

CREATE TABLE IF NOT EXISTS forward_candidate_reviews (
    review_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL,
    previous_review_id TEXT,
    reviewed_at TEXT NOT NULL,
    action TEXT NOT NULL,
    resulting_state TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    source_observation_id TEXT NOT NULL,
    stability_sha256 TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (trial_id) REFERENCES paper_trial_results(trial_id),
    FOREIGN KEY (previous_review_id) REFERENCES forward_candidate_reviews(review_id),
    FOREIGN KEY (source_observation_id) REFERENCES forward_observations(observation_id)
);

CREATE INDEX IF NOT EXISTS idx_forward_candidate_reviews_trial_time
ON forward_candidate_reviews(trial_id, reviewed_at DESC, review_id DESC);

CREATE TABLE IF NOT EXISTS isolated_activation_reviews (
    review_id TEXT PRIMARY KEY,
    trial_id TEXT NOT NULL,
    previous_review_id TEXT,
    reviewed_at TEXT NOT NULL,
    action TEXT NOT NULL,
    resulting_state TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    sandbox_id TEXT NOT NULL,
    valid_until TEXT,
    bundle_combined_sha256 TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (trial_id) REFERENCES paper_trial_results(trial_id),
    FOREIGN KEY (previous_review_id) REFERENCES isolated_activation_reviews(review_id)
);

CREATE INDEX IF NOT EXISTS idx_isolated_activation_trial_time
ON isolated_activation_reviews(trial_id, reviewed_at DESC, review_id DESC);

CREATE TABLE IF NOT EXISTS isolated_paper_configurations (
    configuration_id TEXT PRIMARY KEY,
    sandbox_id TEXT NOT NULL,
    trial_id TEXT NOT NULL,
    approval_review_id TEXT NOT NULL UNIQUE,
    registered_at TEXT NOT NULL,
    valid_until TEXT NOT NULL,
    target_strategy TEXT NOT NULL,
    configuration_sha256 TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (trial_id) REFERENCES paper_trial_results(trial_id),
    FOREIGN KEY (approval_review_id) REFERENCES isolated_activation_reviews(review_id)
);

CREATE INDEX IF NOT EXISTS idx_isolated_paper_config_sandbox_time
ON isolated_paper_configurations(sandbox_id, registered_at DESC, configuration_id DESC);

CREATE TABLE IF NOT EXISTS isolated_paper_sandboxes (
    sandbox_id TEXT PRIMARY KEY,
    active_configuration_id TEXT,
    state_version INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (active_configuration_id) REFERENCES isolated_paper_configurations(configuration_id)
);

CREATE TABLE IF NOT EXISTS isolated_paper_sandbox_events (
    event_id TEXT PRIMARY KEY,
    sandbox_id TEXT NOT NULL,
    previous_event_id TEXT,
    event_at TEXT NOT NULL,
    action TEXT NOT NULL,
    previous_configuration_id TEXT,
    next_configuration_id TEXT,
    state_version INTEGER NOT NULL,
    rollback_of_event_id TEXT UNIQUE,
    operator TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (sandbox_id) REFERENCES isolated_paper_sandboxes(sandbox_id),
    FOREIGN KEY (previous_event_id) REFERENCES isolated_paper_sandbox_events(event_id),
    FOREIGN KEY (previous_configuration_id) REFERENCES isolated_paper_configurations(configuration_id),
    FOREIGN KEY (next_configuration_id) REFERENCES isolated_paper_configurations(configuration_id),
    FOREIGN KEY (rollback_of_event_id) REFERENCES isolated_paper_sandbox_events(event_id)
);

CREATE INDEX IF NOT EXISTS idx_isolated_sandbox_events_time
ON isolated_paper_sandbox_events(sandbox_id, event_at DESC, event_id DESC);

CREATE TABLE IF NOT EXISTS isolated_paper_runtime_kill_switches (
    sandbox_id TEXT PRIMARY KEY,
    armed INTEGER NOT NULL CHECK (armed IN (0, 1)),
    state_version INTEGER NOT NULL,
    changed_at TEXT NOT NULL,
    latest_event_id TEXT
);

CREATE TABLE IF NOT EXISTS isolated_paper_runtime_kill_events (
    event_id TEXT PRIMARY KEY,
    sandbox_id TEXT NOT NULL,
    action TEXT NOT NULL,
    event_at TEXT NOT NULL,
    operator TEXT NOT NULL,
    note TEXT NOT NULL,
    state_version INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (sandbox_id) REFERENCES isolated_paper_runtime_kill_switches(sandbox_id)
);

CREATE INDEX IF NOT EXISTS idx_isolated_runtime_kill_events_time
ON isolated_paper_runtime_kill_events(sandbox_id, state_version DESC, event_id DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_isolated_runtime_kill_event_version
ON isolated_paper_runtime_kill_events(sandbox_id, state_version);

CREATE TABLE IF NOT EXISTS isolated_paper_runtime_sessions (
    session_id TEXT PRIMARY KEY,
    sandbox_id TEXT NOT NULL,
    configuration_id TEXT NOT NULL,
    configuration_sha256 TEXT NOT NULL,
    sandbox_state_version INTEGER NOT NULL,
    worker_id TEXT NOT NULL,
    fencing_token_sha256 TEXT NOT NULL,
    started_at TEXT NOT NULL,
    last_heartbeat_at TEXT NOT NULL,
    lease_expires_at TEXT NOT NULL,
    status TEXT NOT NULL,
    stop_reason TEXT,
    session_version INTEGER NOT NULL,
    ended_at TEXT,
    FOREIGN KEY (configuration_id) REFERENCES isolated_paper_configurations(configuration_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_isolated_runtime_one_running_sandbox
ON isolated_paper_runtime_sessions(sandbox_id) WHERE status='RUNNING';

CREATE INDEX IF NOT EXISTS idx_isolated_runtime_sessions_time
ON isolated_paper_runtime_sessions(sandbox_id, started_at DESC, session_id DESC);

CREATE TABLE IF NOT EXISTS isolated_paper_runtime_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    sandbox_id TEXT NOT NULL,
    event_at TEXT NOT NULL,
    action TEXT NOT NULL,
    session_version INTEGER NOT NULL,
    reason TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES isolated_paper_runtime_sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_isolated_runtime_events_time
ON isolated_paper_runtime_events(session_id, session_version DESC, event_id DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_isolated_runtime_event_version
ON isolated_paper_runtime_events(session_id, session_version);
"""


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


class MarketStore:
    """Small auditable SQLite store for normalized market candles.

    Writes are idempotent on (symbol, timeframe, open_time). Re-ingesting the
    same candle updates its values rather than creating duplicate history.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(_SCHEMA)

    def upsert_candles(self, candles: Iterable[Candle], source: str) -> int:
        rows = list(candles)
        if not rows:
            return 0
        now = _iso(datetime.now(timezone.utc))
        payload = [
            (
                c.symbol.upper(),
                c.timeframe,
                _iso(c.open_time),
                c.open,
                c.high,
                c.low,
                c.close,
                c.volume,
                source,
                now,
            )
            for c in rows
        ]
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO candles(
                    symbol, timeframe, open_time, open, high, low, close, volume,
                    source, ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timeframe, open_time) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume,
                    source=excluded.source,
                    ingested_at=excluded.ingested_at
                """,
                payload,
            )
        return len(rows)

    def load_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Candle]:
        where = ["symbol = ?", "timeframe = ?"]
        params: list[object] = [symbol.upper(), timeframe]
        if start is not None:
            where.append("open_time >= ?")
            params.append(_iso(start))
        if end is not None:
            where.append("open_time <= ?")
            params.append(_iso(end))

        sql = f"""
            SELECT symbol, timeframe, open_time, open, high, low, close, volume
            FROM candles
            WHERE {' AND '.join(where)}
            ORDER BY open_time DESC
        """
        if limit is not None:
            if limit <= 0:
                raise ValueError("limit must be positive")
            sql += " LIMIT ?"
            params.append(limit)

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        rows = list(reversed(rows))
        return [
            Candle(
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                open_time=_parse(row["open_time"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for row in rows
        ]

    def latest_open_time(self, symbol: str, timeframe: str) -> datetime | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT MAX(open_time) AS latest FROM candles WHERE symbol=? AND timeframe=?",
                (symbol.upper(), timeframe),
            ).fetchone()
        if row is None or row["latest"] is None:
            return None
        return _parse(row["latest"])

    def is_fresh(
        self,
        symbol: str,
        timeframe: str,
        *,
        now: datetime | None = None,
        max_age: timedelta = timedelta(hours=2),
    ) -> bool:
        latest = self.latest_open_time(symbol, timeframe)
        if latest is None:
            return False
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        age = current.astimezone(timezone.utc) - latest
        return timedelta(0) <= age <= max_age

    def count_candles(self, symbol: str, timeframe: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM candles WHERE symbol=? AND timeframe=?",
                (symbol.upper(), timeframe),
            ).fetchone()
        return int(row["n"])

    def list_markets(self) -> list[dict[str, object]]:
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT symbol, timeframe, COUNT(*) AS bars, MAX(open_time) AS latest
                   FROM candles GROUP BY symbol, timeframe ORDER BY symbol, timeframe"""
            ).fetchall()
        return [
            {
                "symbol": row["symbol"],
                "timeframe": row["timeframe"],
                "bars": int(row["bars"]),
                "latest": row["latest"],
            }
            for row in rows
        ]

    def upsert_funding_rates(self, rates: Iterable[FundingRate], source: str) -> int:
        rows = list(rates)
        if not rows:
            return 0
        now = _iso(datetime.now(timezone.utc))
        payload = [
            (
                item.symbol.upper(),
                _iso(item.funding_time),
                item.funding_rate,
                item.mark_price,
                item.rate_type,
                source,
                now,
            )
            for item in rows
        ]
        with self.connect() as conn:
            conn.executemany(
                """INSERT INTO funding_rates(
                       symbol, funding_time, funding_rate, mark_price, rate_type, source, ingested_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(symbol, funding_time, rate_type) DO UPDATE SET
                       funding_rate=excluded.funding_rate,
                       mark_price=excluded.mark_price,
                       source=excluded.source,
                       ingested_at=excluded.ingested_at""",
                payload,
            )
        return len(rows)

    def load_funding_rates(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[FundingRate]:
        where = ["symbol = ?"]
        params: list[object] = [symbol.upper()]
        if start is not None:
            where.append("funding_time >= ?")
            params.append(_iso(start))
        if end is not None:
            where.append("funding_time <= ?")
            params.append(_iso(end))
        with self.connect() as conn:
            rows = conn.execute(
                f"""SELECT symbol, funding_time, funding_rate, mark_price, rate_type
                    FROM funding_rates WHERE {' AND '.join(where)}
                    ORDER BY funding_time, rate_type""",
                params,
            ).fetchall()
        return [
            FundingRate(
                symbol=row["symbol"],
                funding_time=_parse(row["funding_time"]),
                funding_rate=float(row["funding_rate"]),
                mark_price=float(row["mark_price"]) if row["mark_price"] is not None else None,
                rate_type=row["rate_type"],
            )
            for row in rows
        ]

    def count_funding_rates(self, symbol: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM funding_rates WHERE symbol=?", (symbol.upper(),)
            ).fetchone()
        return int(row["n"])

    def latest_funding_time(self, symbol: str) -> datetime | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT MAX(funding_time) AS latest FROM funding_rates WHERE symbol=?",
                (symbol.upper(),),
            ).fetchone()
        if row is None or row["latest"] is None:
            return None
        return _parse(row["latest"])

    def upsert_funding_cadence_observations(
        self,
        observations: Iterable[FundingCadenceObservation],
        source: str,
    ) -> int:
        rows = list(observations)
        if not rows:
            return 0
        now = _iso(datetime.now(timezone.utc))
        payload = [
            (
                item.symbol.upper(),
                _iso(item.observed_at),
                item.interval_hours,
                item.adjusted_rate_cap,
                item.adjusted_rate_floor,
                int(item.disclaimer),
                item.source_status,
                source,
                now,
            )
            for item in rows
        ]
        with self.connect() as conn:
            conn.executemany(
                """INSERT INTO funding_cadence_observations(
                       symbol, observed_at, interval_hours, adjusted_rate_cap,
                       adjusted_rate_floor, disclaimer, source_status, source, ingested_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(symbol, observed_at) DO UPDATE SET
                       interval_hours=excluded.interval_hours,
                       adjusted_rate_cap=excluded.adjusted_rate_cap,
                       adjusted_rate_floor=excluded.adjusted_rate_floor,
                       disclaimer=excluded.disclaimer,
                       source_status=excluded.source_status,
                       source=excluded.source,
                       ingested_at=excluded.ingested_at""",
                payload,
            )
        return len(rows)

    def load_funding_cadence_observations(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        *,
        include_previous: bool = False,
    ) -> list[FundingCadenceObservation]:
        where = ["symbol = ?"]
        params: list[object] = [symbol.upper()]
        if start is not None:
            where.append("observed_at >= ?")
            params.append(_iso(start))
        if end is not None:
            where.append("observed_at <= ?")
            params.append(_iso(end))
        with self.connect() as conn:
            rows = list(
                conn.execute(
                    f"""SELECT symbol, observed_at, interval_hours, adjusted_rate_cap,
                               adjusted_rate_floor, disclaimer, source_status
                        FROM funding_cadence_observations
                        WHERE {' AND '.join(where)} ORDER BY observed_at""",
                    params,
                ).fetchall()
            )
            if include_previous and start is not None:
                previous = conn.execute(
                    """SELECT symbol, observed_at, interval_hours, adjusted_rate_cap,
                              adjusted_rate_floor, disclaimer, source_status
                       FROM funding_cadence_observations
                       WHERE symbol=? AND observed_at < ?
                       ORDER BY observed_at DESC LIMIT 1""",
                    (symbol.upper(), _iso(start)),
                ).fetchone()
                if previous is not None:
                    rows.insert(0, previous)
        return [
            FundingCadenceObservation(
                symbol=row["symbol"],
                observed_at=_parse(row["observed_at"]),
                interval_hours=int(row["interval_hours"]),
                adjusted_rate_cap=(
                    float(row["adjusted_rate_cap"])
                    if row["adjusted_rate_cap"] is not None
                    else None
                ),
                adjusted_rate_floor=(
                    float(row["adjusted_rate_floor"])
                    if row["adjusted_rate_floor"] is not None
                    else None
                ),
                disclaimer=bool(row["disclaimer"]),
                source_status=row["source_status"],
            )
            for row in rows
        ]

    def record_ingestion_cycle(self, summary: dict[str, Any]) -> str:
        canonical = json.dumps(summary, sort_keys=True, separators=(",", ":"), allow_nan=False)
        cycle_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
        with self.connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO ingestion_cycles(
                       cycle_id, started_at, finished_at, status, execution_mode, summary_json
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cycle_id,
                    summary["started_at"],
                    summary["finished_at"],
                    summary["status"],
                    summary["execution_mode"],
                    canonical,
                ),
            )
        return cycle_id

    def list_ingestion_cycles(self, limit: int = 20) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT cycle_id, summary_json FROM ingestion_cycles
                   ORDER BY finished_at DESC, cycle_id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [{"cycle_id": row["cycle_id"], **json.loads(row["summary_json"])} for row in rows]

    def archive_latest_stable_view(
        self,
        payload: dict[str, Any],
        *,
        replay_window: str,
        created_at: datetime | None = None,
    ) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        identity_payload = dict(payload)
        identity_payload.pop("generated_at", None)
        identity = json.dumps(identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        view_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        market = payload["market"]
        stable = payload["latest_stable_view"]
        created = created_at or datetime.now(timezone.utc)
        with self.connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO latest_stable_views(
                       view_id, symbol, timeframe, replay_window, as_of, created_at,
                       schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    view_id,
                    market["symbol"],
                    market["timeframe"],
                    replay_window,
                    stable["as_of"],
                    _iso(created),
                    payload["schema_version"],
                    canonical,
                ),
            )
        return view_id

    def list_latest_stable_views(
        self, symbol: str | None = None, timeframe: str | None = None, limit: int = 20
    ) -> list[dict[str, object]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        where: list[str] = []
        params: list[object] = []
        if symbol:
            where.append("symbol = ?")
            params.append(symbol.upper())
        if timeframe:
            where.append("timeframe = ?")
            params.append(timeframe)
        sql = (
            "SELECT view_id, symbol, timeframe, replay_window, as_of, created_at, "
            "schema_version FROM latest_stable_views"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC, view_id DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_latest_stable_view(self, view_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM latest_stable_views WHERE view_id=?", (view_id,)
            ).fetchone()
        return json.loads(row["payload_json"]) if row is not None else None

    def archive_shadow_daily_snapshot(
        self,
        payload: dict[str, Any],
        *,
        created_at: datetime | None = None,
    ) -> str:
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("shadow snapshot must be PAPER_ONLY")
        if payload.get("review_gate", {}).get("live_execution_allowed") is not False:
            raise ValueError("shadow snapshot must explicitly disallow live execution")
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )

        def evidence(value: Any) -> Any:
            if isinstance(value, dict):
                return {
                    key: evidence(item)
                    for key, item in value.items()
                    if key != "generated_at"
                }
            if isinstance(value, list):
                return [evidence(item) for item in value]
            return value

        identity = json.dumps(
            evidence(payload), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        snapshot_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        created = created_at or datetime.now(timezone.utc)
        with self.connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO shadow_daily_snapshots(
                       snapshot_id, as_of, created_at, target_strategy,
                       symbols_json, schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot_id,
                    payload["as_of"],
                    _iso(created),
                    payload["configuration"]["validation_strategy"],
                    json.dumps(payload["symbols"], separators=(",", ":")),
                    payload["schema_version"],
                    canonical,
                ),
            )
        return snapshot_id

    def list_shadow_daily_snapshots(
        self,
        *,
        limit: int = 30,
        target_strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        where = ""
        params: list[object] = []
        if target_strategy:
            where = " WHERE target_strategy=?"
            params.append(target_strategy.upper())
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""SELECT snapshot_id, as_of, created_at, target_strategy,
                           symbols_json, schema_version, payload_json
                    FROM shadow_daily_snapshots{where}
                    ORDER BY created_at DESC, snapshot_id DESC LIMIT ?""",
                params,
            ).fetchall()
        result = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            result.append(
                {
                    "snapshot_id": row["snapshot_id"],
                    "as_of": row["as_of"],
                    "created_at": row["created_at"],
                    "target_strategy": row["target_strategy"],
                    "symbols": json.loads(row["symbols_json"]),
                    "schema_version": row["schema_version"],
                    "review_disposition": payload["review_gate"]["disposition"],
                    "portfolio_degraded": payload["portfolio"]["summary"]["degraded"],
                }
            )
        return result

    def get_shadow_daily_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM shadow_daily_snapshots WHERE snapshot_id=?",
                (snapshot_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row is not None else None

    def load_shadow_daily_snapshots(
        self,
        *,
        limit: int = 90,
        target_strategy: str | None = None,
    ) -> list[tuple[str, dict[str, Any]]]:
        metadata = self.list_shadow_daily_snapshots(
            limit=limit, target_strategy=target_strategy
        )
        snapshots = [
            (item["snapshot_id"], self.get_shadow_daily_snapshot(item["snapshot_id"]))
            for item in reversed(metadata)
        ]
        return [(snapshot_id, payload) for snapshot_id, payload in snapshots if payload]

    def archive_paper_configuration_proposal(
        self,
        payload: dict[str, Any],
        *,
        created_at: datetime | None = None,
    ) -> str:
        if payload.get("schema_version") != "mil3.paper-configuration-proposal.v1":
            raise ValueError("unsupported paper proposal schema")
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("paper proposal must be PAPER_ONLY")
        if payload.get("status") != "PENDING_HUMAN_REVIEW":
            raise ValueError("paper proposal must start pending human review")
        if payload.get("review_gate", {}).get("live_execution_allowed") is not False:
            raise ValueError("paper proposal review gate must disallow live execution")
        if payload.get("source_evidence", {}).get("governance_disposition") != (
            "PROMOTION_CANDIDATE"
        ):
            raise ValueError("paper proposal requires promotion-candidate evidence")
        if not payload.get("parameter_changes"):
            raise ValueError("paper proposal must contain a parameter change")
        authority = payload.get("authority", {})
        if authority.get("proposal_application_allowed") is not False:
            raise ValueError("paper proposal must explicitly disallow application")
        if authority.get("automatic_strategy_change_allowed") is not False:
            raise ValueError("paper proposal must lock automatic strategy changes")
        if authority.get("live_execution_allowed") is not False:
            raise ValueError("paper proposal must explicitly disallow live execution")

        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        identity_payload = dict(payload)
        identity_payload.pop("generated_at", None)
        identity = json.dumps(
            identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        proposal_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        created = created_at or datetime.now(timezone.utc)
        with self.connect() as conn:
            source = conn.execute(
                "SELECT payload_json FROM shadow_daily_snapshots WHERE snapshot_id=?",
                (payload["source_evidence"]["shadow_snapshot_id"],),
            ).fetchone()
            if source is None:
                raise ValueError("paper proposal source snapshot is not archived")
            source_payload = json.loads(source["payload_json"])
            if source_payload.get("execution_mode") != "PAPER_ONLY":
                raise ValueError("paper proposal source snapshot must be PAPER_ONLY")
            if source_payload.get("review_gate", {}).get(
                "live_execution_allowed"
            ) is not False:
                raise ValueError("paper proposal source must disallow live execution")
            if source_payload.get("configuration", {}).get(
                "validation_strategy"
            ) != payload.get("target_strategy"):
                raise ValueError("paper proposal target differs from its source snapshot")
            conn.execute(
                """INSERT OR IGNORE INTO paper_configuration_proposals(
                       proposal_id, created_at, target_strategy, source_snapshot_id,
                       schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    proposal_id,
                    _iso(created),
                    payload["target_strategy"],
                    payload["source_evidence"]["shadow_snapshot_id"],
                    payload["schema_version"],
                    canonical,
                ),
            )
        return proposal_id

    def archive_paper_proposal_review(
        self,
        payload: dict[str, Any],
    ) -> str:
        if payload.get("schema_version") != "mil3.paper-proposal-review.v1":
            raise ValueError("unsupported paper proposal review schema")
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("paper proposal review must be PAPER_ONLY")
        if payload.get("acknowledgement_applies_parameters") is not False:
            raise ValueError("paper proposal review must not apply parameters")
        if payload.get("automatic_strategy_change_allowed") is not False:
            raise ValueError("paper proposal review must lock automatic changes")
        if payload.get("live_execution_allowed") is not False:
            raise ValueError("paper proposal review must disallow live execution")
        if payload.get("disposition") not in {
            "ACKNOWLEDGED_FOR_PAPER_TRIAL",
            "DECLINED",
        }:
            raise ValueError("unsupported paper proposal review disposition")
        if not str(payload.get("reviewer", "")).strip() or not str(
            payload.get("note", "")
        ).strip():
            raise ValueError("paper proposal review requires reviewer and note")
        try:
            _parse(str(payload["reviewed_at"]))
        except (KeyError, ValueError):
            raise ValueError("paper proposal review requires a UTC review time") from None
        identity_payload = dict(payload)
        identity_payload.pop("reviewed_at", None)
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        identity = json.dumps(
            identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        review_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT review_id, payload_json FROM paper_proposal_reviews WHERE proposal_id=?",
                (payload["proposal_id"],),
            ).fetchone()
            if existing is not None:
                existing_payload = json.loads(existing["payload_json"])
                existing_identity = dict(existing_payload)
                existing_identity.pop("reviewed_at", None)
                if existing_identity != identity_payload:
                    raise ValueError("paper proposal already has a terminal review")
                return str(existing["review_id"])
            proposal = conn.execute(
                "SELECT payload_json FROM paper_configuration_proposals WHERE proposal_id=?",
                (payload["proposal_id"],),
            ).fetchone()
            if proposal is None:
                raise ValueError("paper proposal review target is not archived")
            proposal_payload = json.loads(proposal["payload_json"])
            if proposal_payload.get("target_strategy") != payload.get("target_strategy"):
                raise ValueError("paper proposal review target strategy mismatch")
            conn.execute(
                """INSERT INTO paper_proposal_reviews(
                       review_id, proposal_id, reviewed_at, disposition, reviewer,
                       schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    review_id,
                    payload["proposal_id"],
                    payload["reviewed_at"],
                    payload["disposition"],
                    payload["reviewer"],
                    payload["schema_version"],
                    canonical,
                ),
            )
        return review_id

    def list_paper_configuration_proposals(
        self,
        *,
        limit: int = 30,
        target_strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        where = ""
        params: list[object] = []
        if target_strategy:
            where = " WHERE p.target_strategy=?"
            params.append(target_strategy.upper())
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""SELECT p.proposal_id, p.created_at, p.target_strategy,
                           p.source_snapshot_id, p.schema_version,
                           r.review_id, r.reviewed_at, r.disposition, r.reviewer
                    FROM paper_configuration_proposals p
                    LEFT JOIN paper_proposal_reviews r ON r.proposal_id=p.proposal_id
                    {where}
                    ORDER BY p.created_at DESC, p.proposal_id DESC LIMIT ?""",
                params,
            ).fetchall()
        return [
            {
                "proposal_id": row["proposal_id"],
                "created_at": row["created_at"],
                "target_strategy": row["target_strategy"],
                "source_snapshot_id": row["source_snapshot_id"],
                "schema_version": row["schema_version"],
                "status": row["disposition"] or "PENDING_HUMAN_REVIEW",
                "review_id": row["review_id"],
                "reviewed_at": row["reviewed_at"],
                "reviewer": row["reviewer"],
            }
            for row in rows
        ]

    def get_paper_configuration_proposal(
        self, proposal_id: str
    ) -> dict[str, Any] | None:
        with self.connect() as conn:
            proposal = conn.execute(
                "SELECT payload_json FROM paper_configuration_proposals WHERE proposal_id=?",
                (proposal_id,),
            ).fetchone()
            review = conn.execute(
                "SELECT payload_json FROM paper_proposal_reviews WHERE proposal_id=?",
                (proposal_id,),
            ).fetchone()
        if proposal is None:
            return None
        proposal_payload = json.loads(proposal["payload_json"])
        review_payload = json.loads(review["payload_json"]) if review is not None else None
        return {
            "schema_version": "mil3.paper-configuration-proposal-envelope.v1",
            "execution_mode": "PAPER_ONLY",
            "proposal_id": proposal_id,
            "status": (
                review_payload["disposition"]
                if review_payload is not None
                else "PENDING_HUMAN_REVIEW"
            ),
            "proposal": proposal_payload,
            "review": review_payload,
            "read_only": True,
            "proposal_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def archive_paper_trial_result(self, payload: dict[str, Any]) -> str:
        if payload.get("schema_version") != "mil3.paper-trial-result.v1":
            raise ValueError("unsupported paper trial schema")
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("paper trial result must be PAPER_ONLY")
        if payload.get("lifecycle", {}).get("state") != "COMPLETED":
            raise ValueError("only completed paper trial results may be archived")
        authority = payload.get("authority", {})
        if authority.get("trial_application_allowed") is not False:
            raise ValueError("paper trial result must disallow application")
        if authority.get("automatic_strategy_change_allowed") is not False:
            raise ValueError("paper trial result must lock automatic changes")
        if authority.get("live_execution_allowed") is not False:
            raise ValueError("paper trial result must disallow live execution")
        gate = payload.get("review_gate", {})
        if gate.get("trial_application_allowed") is not False:
            raise ValueError("paper trial review gate must disallow application")
        if gate.get("automatic_strategy_change_allowed") is not False:
            raise ValueError("paper trial review gate must lock automatic changes")
        if gate.get("live_execution_allowed") is not False:
            raise ValueError("paper trial review gate must disallow live execution")
        if gate.get("disposition") not in {
            "STOP_TRIAL",
            "CONTINUE_BASELINE",
            "ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION",
        }:
            raise ValueError("unsupported paper trial disposition")
        input_evidence = payload.get("input_evidence", {})
        combined_hash = str(input_evidence.get("combined_sha256", ""))
        per_asset_hashes = input_evidence.get("per_asset_sha256", {})
        if len(combined_hash) != 64 or any(
            character not in "0123456789abcdef" for character in combined_hash
        ):
            raise ValueError("paper trial input evidence hash is required")
        if not isinstance(per_asset_hashes, dict) or not per_asset_hashes:
            raise ValueError("paper trial per-asset input hashes are required")
        if any(
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
            for value in per_asset_hashes.values()
        ):
            raise ValueError("paper trial per-asset input hash is invalid")
        expected_combined = hashlib.sha256(
            json.dumps(
                per_asset_hashes, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        if combined_hash != expected_combined:
            raise ValueError("paper trial combined input hash does not match assets")
        configured_symbols = payload.get("configuration", {}).get("symbols", [])
        result_symbols = [
            item.get("symbol") for item in payload.get("results", {}).get("per_asset", [])
            if isinstance(item, dict)
        ]
        if (
            not isinstance(configured_symbols, list)
            or any(not isinstance(symbol, str) for symbol in configured_symbols)
            or any(not isinstance(symbol, str) for symbol in result_symbols)
            or set(configured_symbols) != set(per_asset_hashes)
            or set(result_symbols) != set(per_asset_hashes)
        ):
            raise ValueError("paper trial asset evidence does not match configuration")
        stop_triggered = payload.get("stop_condition", {}).get("triggered")
        if (stop_triggered is True) != (gate.get("disposition") == "STOP_TRIAL"):
            raise ValueError("paper trial stop result and disposition disagree")

        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        identity_payload = json.loads(canonical)
        identity_payload.pop("generated_at", None)
        for event in identity_payload.get("lifecycle", {}).get("events", []):
            event.pop("at", None)
        identity = json.dumps(
            identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        trial_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        try:
            completed = _parse(str(payload["generated_at"]))
        except (KeyError, ValueError):
            raise ValueError("paper trial completion time is invalid") from None

        with self.connect() as conn:
            proposal = conn.execute(
                """SELECT p.payload_json, r.disposition
                   FROM paper_configuration_proposals p
                   LEFT JOIN paper_proposal_reviews r ON r.proposal_id=p.proposal_id
                   WHERE p.proposal_id=?""",
                (payload["proposal_id"],),
            ).fetchone()
            if proposal is None:
                raise ValueError("paper trial proposal is not archived")
            if proposal["disposition"] != "ACKNOWLEDGED_FOR_PAPER_TRIAL":
                raise ValueError("paper trial proposal is not acknowledged")
            proposal_payload = json.loads(proposal["payload_json"])
            if proposal_payload.get("target_strategy") != payload.get("target_strategy"):
                raise ValueError("paper trial strategy differs from proposal")
            if proposal_payload.get("source_evidence", {}).get(
                "shadow_snapshot_id"
            ) != payload.get("source_snapshot_id"):
                raise ValueError("paper trial source differs from proposal evidence")
            trial_configuration = payload.get("configuration", {})
            if trial_configuration.get("baseline") != proposal_payload.get(
                "baseline_parameters"
            ) or trial_configuration.get("proposed") != proposal_payload.get(
                "proposed_parameters"
            ):
                raise ValueError("paper trial parameters differ from proposal")
            existing = conn.execute(
                "SELECT trial_id, payload_json FROM paper_trial_results WHERE proposal_id=?",
                (payload["proposal_id"],),
            ).fetchone()
            if existing is not None:
                existing_identity = json.loads(existing["payload_json"])
                existing_identity.pop("generated_at", None)
                for event in existing_identity.get("lifecycle", {}).get("events", []):
                    event.pop("at", None)
                if existing_identity != identity_payload:
                    raise ValueError("paper proposal already has a different trial result")
                return str(existing["trial_id"])
            conn.execute(
                """INSERT INTO paper_trial_results(
                       trial_id, proposal_id, source_snapshot_id, completed_at,
                       target_strategy, disposition, schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trial_id,
                    payload["proposal_id"],
                    payload["source_snapshot_id"],
                    _iso(completed),
                    payload["target_strategy"],
                    gate["disposition"],
                    payload["schema_version"],
                    canonical,
                ),
            )
        return trial_id

    def list_paper_trial_results(
        self,
        *,
        limit: int = 30,
        target_strategy: str | None = None,
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        where = ""
        params: list[object] = []
        if target_strategy:
            where = " WHERE target_strategy=?"
            params.append(target_strategy.upper())
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""SELECT trial_id, proposal_id, source_snapshot_id, completed_at,
                           target_strategy, disposition, schema_version
                    FROM paper_trial_results{where}
                    ORDER BY completed_at DESC, trial_id DESC LIMIT ?""",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def get_paper_trial_result(self, trial_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM paper_trial_results WHERE trial_id=?",
                (trial_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "schema_version": "mil3.paper-trial-result-envelope.v1",
            "execution_mode": "PAPER_ONLY",
            "trial_id": trial_id,
            "trial": json.loads(row["payload_json"]),
            "read_only": True,
            "trial_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def archive_forward_observation(self, payload: dict[str, Any]) -> str:
        if payload.get("schema_version") != "mil3.forward-observation.v1":
            raise ValueError("unsupported forward observation schema")
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("forward observation must be PAPER_ONLY")
        authority = payload.get("authority", {})
        gate = payload.get("review_gate", {})
        for source in (authority, gate):
            if source.get("observation_application_allowed") is not False:
                raise ValueError("forward observation must disallow application")
            if source.get("automatic_strategy_change_allowed") is not False:
                raise ValueError("forward observation must lock automatic changes")
            if source.get("live_execution_allowed") is not False:
                raise ValueError("forward observation must disallow live execution")
        if gate.get("disposition") not in {
            "STOP_FORWARD_OBSERVATION",
            "CONTINUE_FORWARD_OBSERVATION",
            "PROPOSED_EDGE_CONFIRMED",
            "PROPOSED_EDGE_NOT_CONFIRMED",
        }:
            raise ValueError("unsupported forward observation disposition")
        if (payload.get("stop_condition", {}).get("triggered") is True) != (
            gate.get("disposition") == "STOP_FORWARD_OBSERVATION"
        ):
            raise ValueError("forward observation stop result and disposition disagree")
        evidence = payload.get("input_evidence", {})
        combined = str(evidence.get("combined_sha256", ""))
        hashes = evidence.get("per_asset_sha256", {})
        expected = hashlib.sha256(
            json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest() if isinstance(hashes, dict) and hashes else ""
        if len(combined) != 64 or combined != expected:
            raise ValueError("forward observation input hash does not match assets")
        symbols = payload.get("configuration", {}).get("symbols", [])
        assets = payload.get("results", {}).get("per_asset", [])
        if set(symbols) != set(hashes) or {item.get("symbol") for item in assets} != set(hashes):
            raise ValueError("forward observation assets do not match configuration")
        boundary = payload.get("boundary", {})
        if boundary.get("policy") != "STRICTLY_AFTER_TRIAL_EVIDENCE_END":
            raise ValueError("forward observation boundary policy is invalid")
        if boundary.get("historical_replay_included") is not False:
            raise ValueError("forward observation cannot include historical replay")
        observed_through = _parse(str(boundary["synchronized_forward_end"]))
        generated = _parse(str(payload["generated_at"]))

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        identity_payload = json.loads(canonical)
        identity_payload.pop("generated_at", None)
        identity = json.dumps(identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        observation_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        with self.connect() as conn:
            trial = conn.execute(
                "SELECT disposition, target_strategy, payload_json FROM paper_trial_results WHERE trial_id=?",
                (payload["trial_id"],),
            ).fetchone()
            if trial is None:
                raise ValueError("forward observation trial is not archived")
            if trial["disposition"] != "ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION":
                raise ValueError("forward observation trial is not eligible")
            trial_payload = json.loads(trial["payload_json"])
            trial_configuration = trial_payload.get("configuration", {})
            observation_configuration = payload.get("configuration", {})
            for key in ("symbols", "timeframe", "warmup_bars", "baseline", "proposed"):
                if observation_configuration.get(key) != trial_configuration.get(key):
                    raise ValueError("forward observation configuration differs from trial")
            if observation_configuration.get("trial_settings") != trial_configuration.get("settings"):
                raise ValueError("forward observation settings differ from trial")
            if payload.get("target_strategy") != trial["target_strategy"]:
                raise ValueError("forward observation strategy differs from trial")
            trial_anchors = {
                item.get("symbol"): item.get("evidence_end")
                for item in trial_payload.get("results", {}).get("per_asset", [])
                if isinstance(item, dict)
            }
            if boundary.get("trial_evidence_end_per_asset") != trial_anchors:
                raise ValueError("forward observation anchors differ from trial")
            for asset in assets:
                symbol = asset.get("symbol")
                try:
                    anchor = _parse(str(trial_anchors[symbol]))
                    forward_start = _parse(str(asset["forward_start"]))
                    forward_end = _parse(str(asset["forward_end"]))
                except (KeyError, TypeError, ValueError):
                    raise ValueError("forward observation asset boundary is invalid") from None
                if forward_start <= anchor or forward_end != observed_through:
                    raise ValueError("forward observation asset crosses trial boundary")
                if int(asset.get("forward_bars", 0)) <= 0:
                    raise ValueError("forward observation asset bars are invalid")
            existing = conn.execute(
                "SELECT observation_id, payload_json FROM forward_observations WHERE trial_id=? AND observed_through=?",
                (payload["trial_id"], _iso(observed_through)),
            ).fetchone()
            if existing is not None:
                existing_identity = json.loads(existing["payload_json"])
                existing_identity.pop("generated_at", None)
                if existing_identity != identity_payload:
                    raise ValueError("forward endpoint already has different observation evidence")
                return str(existing["observation_id"])
            latest = conn.execute(
                """SELECT observation_id, observed_through, input_sha256
                   FROM forward_observations WHERE trial_id=?
                   ORDER BY observed_through DESC LIMIT 1""",
                (payload["trial_id"],),
            ).fetchone()
            lineage = payload.get("lineage", {})
            if latest is None:
                if lineage.get("previous_observation_id") is not None or lineage.get("previous_input_sha256") is not None:
                    raise ValueError("first forward observation has invalid lineage")
            else:
                if observed_through < _parse(latest["observed_through"]):
                    raise ValueError("forward observation cannot move backward")
                if lineage.get("previous_observation_id") != latest["observation_id"] or lineage.get("previous_input_sha256") != latest["input_sha256"]:
                    raise ValueError("forward observation lineage does not match latest checkpoint")
            conn.execute(
                """INSERT INTO forward_observations(
                       observation_id, trial_id, observed_through, created_at,
                       target_strategy, disposition, input_sha256, schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    observation_id, payload["trial_id"], _iso(observed_through), _iso(generated),
                    payload["target_strategy"], gate["disposition"], combined,
                    payload["schema_version"], canonical,
                ),
            )
        return observation_id

    def list_forward_observations(
        self, *, limit: int = 30, target_strategy: str | None = None, trial_id: str | None = None
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        where: list[str] = []
        params: list[object] = []
        if target_strategy:
            where.append("target_strategy=?")
            params.append(target_strategy.upper())
        if trial_id:
            where.append("trial_id=?")
            params.append(trial_id)
        clause = f" WHERE {' AND '.join(where)}" if where else ""
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""SELECT observation_id, trial_id, observed_through, created_at,
                            target_strategy, disposition, input_sha256, schema_version
                     FROM forward_observations{clause}
                     ORDER BY observed_through DESC, observation_id DESC LIMIT ?""",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def latest_forward_observation_for_trial(self, trial_id: str) -> dict[str, Any] | None:
        rows = self.list_forward_observations(limit=1, trial_id=trial_id)
        return rows[0] if rows else None

    def load_forward_observations(
        self, trial_id: str, *, limit: int = 90
    ) -> list[tuple[str, dict[str, Any]]]:
        metadata = self.list_forward_observations(limit=limit, trial_id=trial_id)
        observations = []
        for item in reversed(metadata):
            envelope = self.get_forward_observation(item["observation_id"])
            if envelope is not None:
                observations.append(
                    (item["observation_id"], envelope["observation"])
                )
        return observations

    def get_forward_observation(self, observation_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM forward_observations WHERE observation_id=?",
                (observation_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "schema_version": "mil3.forward-observation-envelope.v1",
            "execution_mode": "PAPER_ONLY",
            "observation_id": observation_id,
            "observation": json.loads(row["payload_json"]),
            "read_only": True,
            "observation_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def archive_forward_candidate_review(self, payload: dict[str, Any]) -> str:
        from .forward_review import stability_evidence_hash, transition_state
        from .forward_stability import build_forward_stability

        if payload.get("schema_version") != "mil3.forward-candidate-review.v1":
            raise ValueError("unsupported forward candidate review schema")
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("forward candidate review must be PAPER_ONLY")
        if payload.get("review_action_applies_parameters") is not False:
            raise ValueError("forward candidate review must not apply parameters")
        if payload.get("automatic_strategy_change_allowed") is not False:
            raise ValueError("forward candidate review must lock automatic changes")
        if payload.get("live_execution_allowed") is not False:
            raise ValueError("forward candidate review must disallow live execution")
        if not str(payload.get("reviewer", "")).strip() or not str(payload.get("note", "")).strip():
            raise ValueError("forward candidate review requires reviewer and note")
        try:
            reviewed = _parse(str(payload["reviewed_at"]))
        except (KeyError, ValueError):
            raise ValueError("forward candidate review time is invalid") from None
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        identity_payload = json.loads(canonical)
        identity_payload.pop("reviewed_at", None)
        identity = json.dumps(
            identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        review_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]

        with self.connect() as conn:
            existing = conn.execute(
                "SELECT payload_json FROM forward_candidate_reviews WHERE review_id=?",
                (review_id,),
            ).fetchone()
            if existing is not None:
                existing_identity = json.loads(existing["payload_json"])
                existing_identity.pop("reviewed_at", None)
                if existing_identity != identity_payload:
                    raise ValueError("forward review identity collision")
                return review_id
            trial = conn.execute(
                "SELECT target_strategy FROM paper_trial_results WHERE trial_id=?",
                (payload["trial_id"],),
            ).fetchone()
            if trial is None:
                raise ValueError("forward candidate review trial is not archived")
            if payload.get("target_strategy") != trial["target_strategy"]:
                raise ValueError("forward candidate review strategy differs from trial")
            latest_review = conn.execute(
                """SELECT review_id, reviewed_at, resulting_state FROM forward_candidate_reviews
                   WHERE trial_id=? ORDER BY reviewed_at DESC, review_id DESC LIMIT 1""",
                (payload["trial_id"],),
            ).fetchone()
            current_state = latest_review["resulting_state"] if latest_review else "OBSERVING"
            expected_previous = latest_review["review_id"] if latest_review else None
            if payload.get("previous_review_id") != expected_previous:
                raise ValueError("forward candidate review lineage does not match latest review")
            if latest_review and reviewed <= _parse(latest_review["reviewed_at"]):
                raise ValueError("forward candidate review time must advance")
            source = payload.get("source_evidence", {})
            latest_observation = conn.execute(
                """SELECT observation_id, observed_through, input_sha256
                   FROM forward_observations WHERE trial_id=?
                   ORDER BY observed_through DESC, observation_id DESC LIMIT 1""",
                (payload["trial_id"],),
            ).fetchone()
            if latest_observation is None:
                raise ValueError("forward candidate review requires observation evidence")
            if (
                source.get("observation_id") != latest_observation["observation_id"]
                or source.get("observation_input_sha256") != latest_observation["input_sha256"]
                or source.get("observed_through") != latest_observation["observed_through"]
            ):
                raise ValueError("forward candidate review source is not latest evidence")

        observations = self.load_forward_observations(payload["trial_id"], limit=90)
        stability = build_forward_stability(observations)
        source = payload["source_evidence"]
        if source.get("stability_disposition") != stability["review_gate"]["disposition"]:
            raise ValueError("forward candidate review stability disposition is stale")
        if source.get("stability_sha256") != stability_evidence_hash(stability):
            raise ValueError("forward candidate review stability hash is stale")
        if source.get("available_checkpoints") != stability["summary"]["available_checkpoints"]:
            raise ValueError("forward candidate review checkpoint count is stale")
        if source.get("warning_codes") != stability["summary"]["warning_codes"]:
            raise ValueError("forward candidate review warning evidence is stale")
        expected_state = transition_state(
            str(current_state), str(payload.get("action", "")),
            str(source.get("stability_disposition", "")),
        )
        if payload.get("previous_state") != current_state or payload.get("resulting_state") != expected_state:
            raise ValueError("forward candidate review state transition is invalid")

        with self.connect() as conn:
            latest_review = conn.execute(
                """SELECT review_id, reviewed_at FROM forward_candidate_reviews WHERE trial_id=?
                   ORDER BY reviewed_at DESC, review_id DESC LIMIT 1""",
                (payload["trial_id"],),
            ).fetchone()
            expected_previous = latest_review["review_id"] if latest_review else None
            if payload.get("previous_review_id") != expected_previous:
                raise ValueError("forward candidate review lineage changed during archive")
            if latest_review and reviewed <= _parse(latest_review["reviewed_at"]):
                raise ValueError("forward candidate review time changed during archive")
            latest_observation = conn.execute(
                """SELECT observation_id, observed_through, input_sha256
                   FROM forward_observations WHERE trial_id=?
                   ORDER BY observed_through DESC, observation_id DESC LIMIT 1""",
                (payload["trial_id"],),
            ).fetchone()
            if latest_observation is None or (
                source.get("observation_id") != latest_observation["observation_id"]
                or source.get("observation_input_sha256") != latest_observation["input_sha256"]
                or source.get("observed_through") != latest_observation["observed_through"]
            ):
                raise ValueError("forward candidate review source changed during archive")
            conn.execute(
                """INSERT INTO forward_candidate_reviews(
                       review_id, trial_id, previous_review_id, reviewed_at, action,
                       resulting_state, reviewer, source_observation_id,
                       stability_sha256, schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    review_id, payload["trial_id"], payload.get("previous_review_id"),
                    _iso(reviewed), payload["action"], payload["resulting_state"],
                    payload["reviewer"], source["observation_id"],
                    source["stability_sha256"], payload["schema_version"], canonical,
                ),
            )
        return review_id

    def list_forward_candidate_reviews(
        self, trial_id: str, *, limit: int = 100
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT review_id, trial_id, previous_review_id, reviewed_at,
                          action, resulting_state, reviewer, source_observation_id,
                          stability_sha256, schema_version
                   FROM forward_candidate_reviews WHERE trial_id=?
                   ORDER BY reviewed_at DESC, review_id DESC LIMIT ?""",
                (trial_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_forward_candidate_review(self, review_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM forward_candidate_reviews WHERE review_id=?",
                (review_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row is not None else None

    def get_forward_candidate_lifecycle(self, trial_id: str) -> dict[str, Any] | None:
        trial = self.get_paper_trial_result(trial_id)
        if trial is None:
            return None
        reviews = self.list_forward_candidate_reviews(trial_id, limit=1000000)
        latest = reviews[0] if reviews else None
        return {
            "schema_version": "mil3.forward-candidate-lifecycle.v1",
            "execution_mode": "PAPER_ONLY",
            "trial_id": trial_id,
            "target_strategy": trial["trial"]["target_strategy"],
            "current_state": latest["resulting_state"] if latest else "OBSERVING",
            "latest_review": latest,
            "reviews": list(reversed(reviews)),
            "read_only": True,
            "review_action_applies_parameters": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def archive_isolated_activation_review(self, payload: dict[str, Any]) -> str:
        from .activation_approval import ALL_ACTIONS
        from .evidence_export import build_forward_evidence_bundle

        if payload.get("schema_version") != "mil3.isolated-paper-activation-review.v1":
            raise ValueError("unsupported isolated activation review schema")
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("isolated activation review must be PAPER_ONLY")
        action = str(payload.get("action", ""))
        if action not in ALL_ACTIONS:
            raise ValueError("unsupported isolated activation review action")
        authority = payload.get("authority", {})
        approved = payload.get("resulting_state") == "APPROVED"
        if authority.get("isolated_paper_activation_allowed") is not approved:
            raise ValueError("isolated activation authority differs from decision")
        for key in (
            "approval_applies_configuration",
            "shared_configuration_change_allowed",
            "automatic_strategy_change_allowed",
            "live_execution_allowed",
        ):
            if authority.get(key) is not False:
                raise ValueError("isolated activation review exceeds sandbox authority")
        if not str(payload.get("reviewer", "")).strip() or not str(
            payload.get("note", "")
        ).strip():
            raise ValueError("isolated activation review requires reviewer and note")
        try:
            reviewed = _parse(str(payload["reviewed_at"]))
        except (KeyError, ValueError):
            raise ValueError("isolated activation review time is invalid") from None
        valid_until = None
        if approved:
            try:
                valid_until = _parse(str(payload["valid_until"]))
            except (KeyError, ValueError):
                raise ValueError("isolated activation approval expiry is invalid") from None
            if valid_until <= reviewed or valid_until > reviewed + timedelta(hours=168):
                raise ValueError("isolated activation approval expiry exceeds policy")
        elif action != "REVOKE_ISOLATED_PAPER_ACTIVATION" and payload.get("valid_until") is not None:
            raise ValueError("rejected isolated activation must not have an expiry")
        source = payload.get("source_evidence", {})
        for key in (
            "bundle_combined_sha256",
            "bundle_file_sha256",
            "verification_receipt_sha256",
            "stability_sha256",
            "configuration_sha256",
        ):
            digest = str(source.get(key, ""))
            if len(digest) != 64 or not set(digest) <= set("0123456789abcdef"):
                raise ValueError(f"isolated activation source {key} is invalid")
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        review_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT payload_json FROM isolated_activation_reviews WHERE review_id=?",
                (review_id,),
            ).fetchone()
            if existing is not None:
                if existing["payload_json"] != canonical:
                    raise ValueError("isolated activation review identity collision")
                return review_id

        lifecycle = self.get_isolated_activation_lifecycle(
            str(payload["trial_id"]), now=reviewed
        )
        current_state = lifecycle["current_state"]
        latest = lifecycle.get("latest_event")
        expected_previous = latest["review_id"] if latest else None
        if payload.get("previous_review_id") != expected_previous:
            raise ValueError("isolated activation review lineage is stale")
        if action == "REVOKE_ISOLATED_PAPER_ACTIVATION":
            if current_state != "APPROVED" or payload.get("previous_state") != "APPROVED":
                raise ValueError("only a current isolated approval can be revoked")
            if payload.get("resulting_state") != "REVOKED":
                raise ValueError("isolated activation revocation state is invalid")
            previous_payload = self.get_isolated_activation_review(expected_previous)
            if previous_payload is None or any(
                payload.get(key) != previous_payload.get(key)
                for key in ("trial_id", "target_strategy", "sandbox_id", "valid_until")
            ):
                raise ValueError("isolated activation revocation target changed")
        else:
            if current_state != "PENDING_HUMAN_APPROVAL" or expected_previous is not None:
                raise ValueError("isolated activation trial already has a terminal decision")
            expected_state = (
                "APPROVED"
                if action == "APPROVE_ISOLATED_PAPER_ACTIVATION"
                else "REJECTED"
            )
            if (
                payload.get("previous_state") != "PENDING_HUMAN_APPROVAL"
                or payload.get("resulting_state") != expected_state
            ):
                raise ValueError("isolated activation decision state is invalid")
            rebuilt = build_forward_evidence_bundle(self, str(payload["trial_id"]))
            if rebuilt["manifest"]["combined_sha256"] != source["bundle_combined_sha256"]:
                raise ValueError("isolated activation evidence is stale")
            trial_configuration = rebuilt["evidence"]["trial"]["configuration"]
            configuration_hash = hashlib.sha256(
                json.dumps(
                    trial_configuration,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
            ).hexdigest()
            if (
                payload.get("target_strategy") != rebuilt["target_strategy"]
                or payload.get("configuration_snapshot") != trial_configuration
                or source["configuration_sha256"] != configuration_hash
                or source.get("latest_observation_id")
                != rebuilt["evidence"]["observations"][-1]["observation_id"]
                or source.get("stability_sha256")
                != rebuilt["manifest"]["component_sha256"]["stability"]
            ):
                raise ValueError("isolated activation source evidence changed")
            stability = rebuilt["evidence"]["stability"]
            if (
                source.get("stability_disposition")
                != stability["review_gate"]["disposition"]
                or source.get("warning_codes") != stability["summary"]["warning_codes"]
            ):
                raise ValueError("isolated activation stability evidence changed")
            if approved and (
                rebuilt["lifecycle_state"] != "OBSERVING_ACKNOWLEDGED"
                or source["stability_disposition"]
                != "EXTENDED_OBSERVATION_CONFIRMED"
                or source["warning_codes"]
            ):
                raise ValueError("isolated activation approval prerequisites are not satisfied")

        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            latest_row = conn.execute(
                """SELECT review_id, reviewed_at, resulting_state, valid_until
                   FROM isolated_activation_reviews WHERE trial_id=?
                   ORDER BY reviewed_at DESC, review_id DESC LIMIT 1""",
                (payload["trial_id"],),
            ).fetchone()
            actual_previous = latest_row["review_id"] if latest_row else None
            if actual_previous != payload.get("previous_review_id"):
                raise ValueError("isolated activation review lineage changed during archive")
            if latest_row and reviewed <= _parse(latest_row["reviewed_at"]):
                raise ValueError("isolated activation review time must advance")
            if action != "REVOKE_ISOLATED_PAPER_ACTIVATION":
                latest_observation = conn.execute(
                    """SELECT observation_id FROM forward_observations WHERE trial_id=?
                       ORDER BY observed_through DESC, observation_id DESC LIMIT 1""",
                    (payload["trial_id"],),
                ).fetchone()
                if (
                    latest_observation is None
                    or latest_observation["observation_id"]
                    != source.get("latest_observation_id")
                ):
                    raise ValueError("isolated activation evidence changed during archive")
            conn.execute(
                """INSERT INTO isolated_activation_reviews(
                       review_id, trial_id, previous_review_id, reviewed_at, action,
                       resulting_state, reviewer, sandbox_id, valid_until,
                       bundle_combined_sha256, schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    review_id, payload["trial_id"], payload.get("previous_review_id"),
                    _iso(reviewed), action, payload["resulting_state"],
                    payload["reviewer"], payload["sandbox_id"], payload.get("valid_until"),
                    source["bundle_combined_sha256"], payload["schema_version"], canonical,
                ),
            )
        return review_id

    def list_isolated_activation_reviews(
        self, trial_id: str, *, limit: int = 100
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT review_id, trial_id, previous_review_id, reviewed_at,
                          action, resulting_state, reviewer, sandbox_id, valid_until,
                          bundle_combined_sha256, schema_version
                   FROM isolated_activation_reviews WHERE trial_id=?
                   ORDER BY reviewed_at DESC, review_id DESC LIMIT ?""",
                (trial_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_isolated_activation_review(self, review_id: str | None) -> dict[str, Any] | None:
        if not review_id:
            return None
        with self.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM isolated_activation_reviews WHERE review_id=?",
                (review_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row is not None else None

    def get_isolated_activation_lifecycle(
        self, trial_id: str, *, now: datetime | None = None
    ) -> dict[str, Any]:
        trial = self.get_paper_trial_result(trial_id)
        if trial is None:
            raise ValueError("isolated activation trial is not archived")
        reviews = self.list_isolated_activation_reviews(trial_id, limit=1000000)
        latest = reviews[0] if reviews else None
        current_state = latest["resulting_state"] if latest else "PENDING_HUMAN_APPROVAL"
        expired = False
        if current_state == "APPROVED" and latest and latest["valid_until"]:
            expired = _parse(_iso(now or datetime.now(timezone.utc))) >= _parse(
                latest["valid_until"]
            )
            if expired:
                current_state = "EXPIRED"
        return {
            "schema_version": "mil3.isolated-paper-activation-lifecycle.v1",
            "execution_mode": "PAPER_ONLY",
            "trial_id": trial_id,
            "target_strategy": trial["trial"]["target_strategy"],
            "current_state": current_state,
            "expired": expired,
            "isolated_paper_activation_allowed": current_state == "APPROVED",
            "latest_event": latest,
            "events": list(reversed(reviews)),
            "read_only": True,
            "approval_applies_configuration": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def archive_isolated_paper_configuration(self, payload: dict[str, Any]) -> str:
        from .isolated_config import canonical_sha256

        if payload.get("schema_version") != "mil3.isolated-paper-configuration.v1":
            raise ValueError("unsupported isolated paper configuration schema")
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("isolated paper configuration must be PAPER_ONLY")
        authority = payload.get("authority", {})
        if (
            authority.get("registry_entry_inert") is not True
            or authority.get("atomic_sandbox_activation_allowed") is not True
        ):
            raise ValueError("isolated paper configuration is not an inert registry entry")
        for key in (
            "shared_configuration_change_allowed",
            "automatic_strategy_change_allowed",
            "live_execution_allowed",
        ):
            if authority.get(key) is not False:
                raise ValueError("isolated paper configuration exceeds registry authority")
        try:
            registered = _parse(str(payload["registered_at"]))
            valid_until = _parse(str(payload["valid_until"]))
        except (KeyError, ValueError):
            raise ValueError("isolated paper configuration time is invalid") from None
        if registered >= valid_until:
            raise ValueError("isolated paper configuration approval already expired")
        configuration = payload.get("configuration")
        configuration_sha256 = canonical_sha256(configuration)
        if payload.get("configuration_sha256") != configuration_sha256:
            raise ValueError("isolated paper configuration hash differs from payload")
        identity = {
            "trial_id": payload.get("trial_id"),
            "approval_review_id": payload.get("approval_review_id"),
            "sandbox_id": payload.get("sandbox_id"),
            "configuration_sha256": configuration_sha256,
        }
        configuration_id = canonical_sha256(identity)[:24]
        if payload.get("configuration_id") != configuration_id:
            raise ValueError("isolated paper configuration identity is invalid")
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT payload_json FROM isolated_paper_configurations WHERE configuration_id=?",
                (configuration_id,),
            ).fetchone()
            if existing is not None:
                existing_identity = json.loads(existing["payload_json"])
                incoming_identity = json.loads(canonical)
                existing_identity.pop("registered_at", None)
                incoming_identity.pop("registered_at", None)
                if existing_identity != incoming_identity:
                    raise ValueError("isolated paper configuration identity collision")
                return configuration_id
            consumed = conn.execute(
                "SELECT configuration_id FROM isolated_paper_configurations WHERE approval_review_id=?",
                (payload["approval_review_id"],),
            ).fetchone()
            if consumed is not None:
                raise ValueError("isolated activation approval was already consumed")
            approval_row = conn.execute(
                "SELECT payload_json FROM isolated_activation_reviews WHERE review_id=?",
                (payload["approval_review_id"],),
            ).fetchone()
            latest_approval = conn.execute(
                """SELECT review_id, resulting_state FROM isolated_activation_reviews
                   WHERE trial_id=? ORDER BY reviewed_at DESC, review_id DESC LIMIT 1""",
                (payload["trial_id"],),
            ).fetchone()
            if approval_row is None or latest_approval is None:
                raise ValueError("isolated paper configuration approval is unavailable")
            approval = json.loads(approval_row["payload_json"])
            if (
                latest_approval["review_id"] != payload["approval_review_id"]
                or latest_approval["resulting_state"] != "APPROVED"
                or approval.get("action") != "APPROVE_ISOLATED_PAPER_ACTIVATION"
                or approval.get("valid_until") != payload.get("valid_until")
                or approval.get("sandbox_id") != payload.get("sandbox_id")
                or approval.get("target_strategy") != payload.get("target_strategy")
                or approval.get("configuration_snapshot") != configuration
                or approval.get("source_evidence") != payload.get("source_evidence")
            ):
                raise ValueError("isolated paper configuration differs from current approval")
            if registered < _parse(approval["reviewed_at"]):
                raise ValueError("isolated paper configuration predates its approval")
            conn.execute(
                """INSERT INTO isolated_paper_configurations(
                       configuration_id, sandbox_id, trial_id, approval_review_id,
                       registered_at, valid_until, target_strategy,
                       configuration_sha256, schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    configuration_id, payload["sandbox_id"], payload["trial_id"],
                    payload["approval_review_id"], _iso(registered), _iso(valid_until),
                    payload["target_strategy"], configuration_sha256,
                    payload["schema_version"], canonical,
                ),
            )
        return configuration_id

    def list_isolated_paper_configurations(
        self, *, sandbox_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        where = " WHERE sandbox_id=?" if sandbox_id else ""
        params: list[Any] = [sandbox_id] if sandbox_id else []
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""SELECT configuration_id, sandbox_id, trial_id, approval_review_id,
                           registered_at, valid_until, target_strategy,
                           configuration_sha256, schema_version
                    FROM isolated_paper_configurations{where}
                    ORDER BY registered_at DESC, configuration_id DESC LIMIT ?""",
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def get_isolated_paper_configuration(
        self, configuration_id: str | None
    ) -> dict[str, Any] | None:
        if not configuration_id:
            return None
        with self.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM isolated_paper_configurations WHERE configuration_id=?",
                (configuration_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row is not None else None

    @staticmethod
    def _isolated_configuration_validity(
        conn: sqlite3.Connection,
        configuration_id: str | None,
        at: datetime,
    ) -> tuple[bool, str, sqlite3.Row | None]:
        if configuration_id is None:
            return True, "BASELINE_EMPTY", None
        config = conn.execute(
            """SELECT configuration_id, sandbox_id, trial_id, approval_review_id,
                      valid_until, payload_json
               FROM isolated_paper_configurations WHERE configuration_id=?""",
            (configuration_id,),
        ).fetchone()
        if config is None:
            return False, "CONFIGURATION_MISSING", None
        if at >= _parse(config["valid_until"]):
            return False, "APPROVAL_EXPIRED", config
        latest = conn.execute(
            """SELECT review_id, resulting_state FROM isolated_activation_reviews
               WHERE trial_id=? ORDER BY reviewed_at DESC, review_id DESC LIMIT 1""",
            (config["trial_id"],),
        ).fetchone()
        if latest is None or latest["review_id"] != config["approval_review_id"]:
            if latest is not None and latest["resulting_state"] == "REVOKED":
                return False, "APPROVAL_REVOKED", config
            return False, "APPROVAL_MISMATCH", config
        if latest["resulting_state"] != "APPROVED":
            return False, "APPROVAL_REVOKED", config
        return True, "CURRENT", config

    def resolve_isolated_paper_sandbox(
        self, sandbox_id: str, *, now: datetime | None = None
    ) -> dict[str, Any]:
        evaluated = _parse(_iso(now or datetime.now(timezone.utc)))
        with self.connect() as conn:
            sandbox = conn.execute(
                """SELECT sandbox_id, active_configuration_id, state_version, updated_at
                   FROM isolated_paper_sandboxes WHERE sandbox_id=?""",
                (sandbox_id,),
            ).fetchone()
            latest_event = conn.execute(
                """SELECT event_id, event_at, action, previous_configuration_id,
                          next_configuration_id, state_version, operator
                   FROM isolated_paper_sandbox_events WHERE sandbox_id=?
                   ORDER BY state_version DESC, event_id DESC LIMIT 1""",
                (sandbox_id,),
            ).fetchone()
            stored_id = sandbox["active_configuration_id"] if sandbox else None
            valid, reason, config_row = self._isolated_configuration_validity(
                conn, stored_id, evaluated
            )
            rollback = None
            if latest_event is not None and latest_event["action"] == "ACTIVATE":
                rolled_back = conn.execute(
                    "SELECT event_id FROM isolated_paper_sandbox_events WHERE rollback_of_event_id=?",
                    (latest_event["event_id"],),
                ).fetchone()
                if rolled_back is None and latest_event["next_configuration_id"] == stored_id:
                    target = latest_event["previous_configuration_id"]
                    target_valid, _, _ = self._isolated_configuration_validity(
                        conn, target, evaluated
                    )
                    rollback = {
                        "event_id": latest_event["event_id"],
                        "previous_configuration_id": target,
                        "safe_rollback_configuration_id": target if target_valid else None,
                        "target_fails_safe_to_empty": not target_valid,
                    }
        if stored_id is None:
            effective_state = "EMPTY"
            blocking_reason = "No isolated configuration is active."
            effective_id = None
        elif valid:
            effective_state = "ACTIVE"
            blocking_reason = "None; isolated PAPER_ONLY registry pointer is current."
            effective_id = stored_id
        else:
            effective_state = {
                "APPROVAL_EXPIRED": "EXPIRED_FAIL_SAFE",
                "APPROVAL_REVOKED": "REVOKED_FAIL_SAFE",
                "APPROVAL_MISMATCH": "APPROVAL_MISMATCH_FAIL_SAFE",
                "CONFIGURATION_MISSING": "CONFIGURATION_MISSING_FAIL_SAFE",
            }[reason]
            blocking_reason = (
                f"Stored pointer is ignored because {reason.replace('_', ' ').lower()}."
            )
            effective_id = None
        configuration = (
            json.loads(config_row["payload_json"]) if config_row is not None else None
        )
        return {
            "schema_version": "mil3.isolated-paper-sandbox-view.v1",
            "execution_mode": "PAPER_ONLY",
            "evaluated_at": evaluated.isoformat(),
            "sandbox_id": sandbox_id,
            "state_version": sandbox["state_version"] if sandbox else 0,
            "stored_configuration_id": stored_id,
            "effective_configuration_id": effective_id,
            "effective_state": effective_state,
            "blocking_reason": blocking_reason,
            "updated_at": sandbox["updated_at"] if sandbox else None,
            "latest_event_id": latest_event["event_id"] if latest_event else None,
            "latest_event": dict(latest_event) if latest_event else None,
            "stored_configuration": configuration,
            "effective_configuration": configuration if effective_id else None,
            "rollback_candidate": rollback,
            "read_only": True,
            "starts_strategy_process": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    def archive_isolated_paper_sandbox_event(self, payload: dict[str, Any]) -> str:
        from .isolated_config import canonical_sha256

        if payload.get("schema_version") != "mil3.isolated-paper-sandbox-event.v1":
            raise ValueError("unsupported isolated paper sandbox event schema")
        if payload.get("execution_mode") != "PAPER_ONLY":
            raise ValueError("isolated paper sandbox event must be PAPER_ONLY")
        action = str(payload.get("action", ""))
        allowed_actions = {
            "ACTIVATE", "ROLLBACK", "INVALIDATE_EXPIRED",
            "INVALIDATE_REVOKED", "INVALIDATE_APPROVAL_MISMATCH",
        }
        if action not in allowed_actions:
            raise ValueError("unsupported isolated paper sandbox action")
        authority = payload.get("authority", {})
        if (
            authority.get("isolated_registry_pointer_change_only") is not True
            or authority.get("starts_strategy_process") is not False
            or authority.get("shared_configuration_change_allowed") is not False
            or authority.get("automatic_strategy_change_allowed") is not False
            or authority.get("live_execution_allowed") is not False
        ):
            raise ValueError("isolated paper sandbox event exceeds pointer authority")
        if not str(payload.get("operator", "")).strip() or not str(
            payload.get("note", "")
        ).strip():
            raise ValueError("isolated paper sandbox event requires operator and note")
        try:
            event_at = _parse(str(payload["event_at"]))
            expected_version = int(payload["expected_state_version"])
        except (KeyError, ValueError, TypeError):
            raise ValueError("isolated paper sandbox event context is invalid") from None
        identity = dict(payload)
        supplied_event_id = str(identity.pop("event_id", ""))
        expected_event_id = canonical_sha256(identity)[:24]
        if supplied_event_id != expected_event_id:
            raise ValueError("isolated paper sandbox event identity is invalid")
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        sandbox_id = str(payload.get("sandbox_id", ""))
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT payload_json FROM isolated_paper_sandbox_events WHERE event_id=?",
                (supplied_event_id,),
            ).fetchone()
            if existing is not None:
                if existing["payload_json"] != canonical:
                    raise ValueError("isolated paper sandbox event identity collision")
                return supplied_event_id
            sandbox = conn.execute(
                """SELECT active_configuration_id, state_version FROM isolated_paper_sandboxes
                   WHERE sandbox_id=?""",
                (sandbox_id,),
            ).fetchone()
            if sandbox is None:
                if action != "ACTIVATE" or expected_version != 0:
                    raise ValueError("isolated paper sandbox is not initialized")
                conn.execute(
                    """INSERT INTO isolated_paper_sandboxes(
                           sandbox_id, active_configuration_id, state_version, updated_at
                       ) VALUES (?, NULL, 0, ?)""",
                    (sandbox_id, _iso(event_at)),
                )
                current_id = None
                current_version = 0
            else:
                current_id = sandbox["active_configuration_id"]
                current_version = int(sandbox["state_version"])
            latest = conn.execute(
                """SELECT event_id, event_at, action, previous_configuration_id,
                          next_configuration_id, state_version
                   FROM isolated_paper_sandbox_events WHERE sandbox_id=?
                   ORDER BY state_version DESC, event_id DESC LIMIT 1""",
                (sandbox_id,),
            ).fetchone()
            latest_id = latest["event_id"] if latest else None
            if latest is not None and event_at <= _parse(latest["event_at"]):
                raise ValueError("isolated paper sandbox event time must advance")
            if (
                current_version != expected_version
                or current_id != payload.get("previous_configuration_id")
                or latest_id != payload.get("previous_event_id")
            ):
                raise ValueError("isolated paper sandbox state changed before commit")
            next_id = payload.get("next_configuration_id")
            rollback_of = payload.get("rollback_of_event_id")
            if action == "ACTIVATE":
                valid, reason, config = self._isolated_configuration_validity(
                    conn, str(next_id) if next_id else None, event_at
                )
                if not valid or config is None:
                    raise ValueError(f"isolated configuration is not activatable: {reason}")
                if config["sandbox_id"] != sandbox_id:
                    raise ValueError("isolated configuration belongs to another sandbox")
                config_payload = json.loads(config["payload_json"])
                if event_at < _parse(config_payload["registered_at"]):
                    raise ValueError("isolated activation predates configuration registration")
                if next_id == current_id:
                    raise ValueError("isolated configuration is already the stored pointer")
                if rollback_of is not None:
                    raise ValueError("activation must not consume a rollback target")
            elif action == "ROLLBACK":
                if not rollback_of:
                    raise ValueError("rollback requires its source activation event")
                activation = conn.execute(
                    """SELECT action, previous_configuration_id, next_configuration_id
                       FROM isolated_paper_sandbox_events WHERE event_id=? AND sandbox_id=?""",
                    (rollback_of, sandbox_id),
                ).fetchone()
                already = conn.execute(
                    "SELECT event_id FROM isolated_paper_sandbox_events WHERE rollback_of_event_id=?",
                    (rollback_of,),
                ).fetchone()
                if (
                    activation is None or activation["action"] != "ACTIVATE"
                    or activation["next_configuration_id"] != current_id or already is not None
                ):
                    raise ValueError("rollback source is not the current unrolled activation")
                target = activation["previous_configuration_id"]
                target_valid, _, _ = self._isolated_configuration_validity(
                    conn, target, event_at
                )
                safe_target = target if target_valid else None
                if next_id != safe_target:
                    raise ValueError("rollback target changed before commit")
            else:
                valid, reason, _ = self._isolated_configuration_validity(
                    conn, current_id, event_at
                )
                expected_action = {
                    "APPROVAL_EXPIRED": "INVALIDATE_EXPIRED",
                    "APPROVAL_REVOKED": "INVALIDATE_REVOKED",
                    "APPROVAL_MISMATCH": "INVALIDATE_APPROVAL_MISMATCH",
                }.get(reason)
                if valid or expected_action != action or next_id is not None:
                    raise ValueError("fail-safe invalidation no longer matches current state")
                if rollback_of is not None:
                    raise ValueError("invalidation must not consume a rollback target")
            next_version = current_version + 1
            updated = conn.execute(
                """UPDATE isolated_paper_sandboxes
                   SET active_configuration_id=?, state_version=?, updated_at=?
                   WHERE sandbox_id=? AND state_version=?""",
                (next_id, next_version, _iso(event_at), sandbox_id, current_version),
            )
            if updated.rowcount != 1:
                raise ValueError("isolated paper sandbox pointer update lost its race")
            conn.execute(
                """INSERT INTO isolated_paper_sandbox_events(
                       event_id, sandbox_id, previous_event_id, event_at, action,
                       previous_configuration_id, next_configuration_id, state_version,
                       rollback_of_event_id, operator, schema_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    supplied_event_id, sandbox_id, payload.get("previous_event_id"),
                    _iso(event_at), action, current_id, next_id, next_version,
                    rollback_of, payload["operator"], payload["schema_version"], canonical,
                ),
            )
        return supplied_event_id

    def list_isolated_paper_sandbox_events(
        self, sandbox_id: str, *, limit: int = 100
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT event_id, sandbox_id, previous_event_id, event_at, action,
                          previous_configuration_id, next_configuration_id, state_version,
                          rollback_of_event_id, operator, schema_version
                   FROM isolated_paper_sandbox_events WHERE sandbox_id=?
                   ORDER BY state_version DESC, event_id DESC LIMIT ?""",
                (sandbox_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_isolated_paper_sandbox_event(self, event_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM isolated_paper_sandbox_events WHERE event_id=?",
                (event_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row is not None else None

    def reconcile_isolated_paper_sandboxes(
        self, *, now: datetime | None = None
    ) -> dict[str, Any]:
        from .isolated_config import build_fail_safe_invalidation_event

        evaluated = _parse(_iso(now or datetime.now(timezone.utc)))
        with self.connect() as conn:
            sandbox_ids = [
                row["sandbox_id"]
                for row in conn.execute(
                    "SELECT sandbox_id FROM isolated_paper_sandboxes ORDER BY sandbox_id"
                ).fetchall()
            ]
        records: list[dict[str, Any]] = []
        for sandbox_id in sandbox_ids:
            view = self.resolve_isolated_paper_sandbox(sandbox_id, now=evaluated)
            if view["effective_state"] not in {
                "EXPIRED_FAIL_SAFE", "REVOKED_FAIL_SAFE",
                "APPROVAL_MISMATCH_FAIL_SAFE",
            }:
                records.append({"sandbox_id": sandbox_id, "status": "NO_CHANGE"})
                continue
            try:
                event = build_fail_safe_invalidation_event(view, event_at=evaluated)
                event_id = self.archive_isolated_paper_sandbox_event(event)
                records.append({
                    "sandbox_id": sandbox_id,
                    "status": "INVALIDATED",
                    "event_id": event_id,
                    "reason": view["effective_state"],
                })
            except ValueError as exc:
                records.append({
                    "sandbox_id": sandbox_id,
                    "status": "DEGRADED",
                    "reason": str(exc),
                })
        return {
            "schema_version": "mil3.isolated-paper-reconciliation.v1",
            "execution_mode": "PAPER_ONLY",
            "evaluated_at": evaluated.isoformat(),
            "records": records,
            "configuration_process_started": False,
            "shared_configuration_change_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        }

    @staticmethod
    def _runtime_event_conn(
        conn: sqlite3.Connection,
        session: sqlite3.Row,
        *,
        action: str,
        event_at: datetime,
        version: int,
        reason: str,
        operator: str,
        note: str,
    ) -> str:
        from .isolated_config import canonical_sha256

        payload = {
            "schema_version": "mil3.isolated-paper-runtime-event.v1",
            "execution_mode": "PAPER_ONLY",
            "session_id": session["session_id"],
            "sandbox_id": session["sandbox_id"],
            "configuration_id": session["configuration_id"],
            "configuration_sha256": session["configuration_sha256"],
            "sandbox_state_version": int(session["sandbox_state_version"]),
            "worker_id": session["worker_id"],
            "event_at": _iso(event_at),
            "action": action,
            "session_version": version,
            "reason": reason,
            "operator": operator,
            "note": note,
            "authority": {
                "configuration_consumption_only": True,
                "replay_started": False,
                "order_path_present": False,
                "shared_configuration_change_allowed": False,
                "automatic_strategy_change_allowed": False,
                "live_execution_allowed": False,
            },
        }
        event_id = canonical_sha256(payload)[:24]
        payload["event_id"] = event_id
        conn.execute(
            """INSERT INTO isolated_paper_runtime_events(
                   event_id, session_id, sandbox_id, event_at, action,
                   session_version, reason, payload_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id, session["session_id"], session["sandbox_id"],
                _iso(event_at), action, version, reason,
                json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False),
            ),
        )
        return event_id

    @classmethod
    def _stop_runtime_conn(
        cls,
        conn: sqlite3.Connection,
        session: sqlite3.Row,
        *,
        stopped_at: datetime,
        reason: str,
        operator: str,
        note: str,
    ) -> str:
        if session["status"] != "RUNNING":
            raise ValueError("isolated paper runtime session is not running")
        version = int(session["session_version"]) + 1
        updated = conn.execute(
            """UPDATE isolated_paper_runtime_sessions
               SET status='STOPPED', stop_reason=?, session_version=?, ended_at=?
               WHERE session_id=? AND status='RUNNING' AND session_version=?""",
            (reason, version, _iso(stopped_at), session["session_id"], session["session_version"]),
        )
        if updated.rowcount != 1:
            raise ValueError("isolated paper runtime stop lost its race")
        return cls._runtime_event_conn(
            conn, session, action="STOP", event_at=stopped_at,
            version=version, reason=reason, operator=operator, note=note,
        )

    def isolated_paper_runtime_kill_switch(self, sandbox_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """SELECT sandbox_id, armed, state_version, changed_at, latest_event_id
                   FROM isolated_paper_runtime_kill_switches WHERE sandbox_id=?""",
                (sandbox_id,),
            ).fetchone()
        initialized = row is not None
        return {
            "schema_version": "mil3.isolated-paper-runtime-kill-switch.v1",
            "execution_mode": "PAPER_ONLY",
            "sandbox_id": sandbox_id,
            "initialized": initialized,
            "armed": bool(row["armed"]) if row else True,
            "effective_state": "ARMED" if row is None or row["armed"] else "CLEAR",
            "state_version": int(row["state_version"]) if row else 0,
            "changed_at": row["changed_at"] if row else None,
            "latest_event_id": row["latest_event_id"] if row else None,
            "blocking_reason": (
                "Kill switch is not initialized and therefore fails safe to ARMED."
                if row is None else
                "Kill switch is armed; runtime acquisition and renewal are blocked."
                if row["armed"] else
                "Kill switch is explicitly clear."
            ),
            "read_only": True,
            "browser_control_allowed": False,
            "live_execution_allowed": False,
        }

    def set_isolated_paper_runtime_kill_switch(
        self,
        sandbox_id: str,
        *,
        action: str,
        operator: str,
        note: str,
        now: datetime | None = None,
    ) -> str:
        from .isolated_config import canonical_sha256

        normalized_action = action.upper()
        if normalized_action not in {"ARM", "CLEAR"}:
            raise ValueError("runtime kill-switch action must be ARM or CLEAR")
        if not operator.strip() or not note.strip():
            raise ValueError("runtime kill-switch operator and note are required")
        event_at = _parse(_iso(now or datetime.now(timezone.utc)))
        desired = normalized_action == "ARM"
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """SELECT sandbox_id, armed, state_version, changed_at, latest_event_id
                   FROM isolated_paper_runtime_kill_switches WHERE sandbox_id=?""",
                (sandbox_id,),
            ).fetchone()
            current = bool(row["armed"]) if row else True
            version = int(row["state_version"]) if row else 0
            if current == desired and row is not None:
                raise ValueError("runtime kill switch is already in the requested state")
            if row is not None and event_at <= _parse(row["changed_at"]):
                raise ValueError("runtime kill-switch event time must advance")
            sessions = conn.execute(
                """SELECT * FROM isolated_paper_runtime_sessions
                   WHERE sandbox_id=? AND status='RUNNING'""",
                (sandbox_id,),
            ).fetchall()
            if desired and any(
                event_at < _parse(session["last_heartbeat_at"]) for session in sessions
            ):
                raise ValueError("runtime kill-switch event cannot predate a running heartbeat")
            payload = {
                "schema_version": "mil3.isolated-paper-runtime-kill-event.v1",
                "execution_mode": "PAPER_ONLY",
                "sandbox_id": sandbox_id,
                "action": normalized_action,
                "event_at": _iso(event_at),
                "operator": operator.strip(),
                "note": note.strip(),
                "previous_state": "ARMED" if current else "CLEAR",
                "resulting_state": "ARMED" if desired else "CLEAR",
                "state_version": version + 1,
                "authority": {
                    "stops_isolated_paper_runtime_only": True,
                    "starts_runtime": False,
                    "browser_control_allowed": False,
                    "live_execution_allowed": False,
                },
            }
            event_id = canonical_sha256(payload)[:24]
            payload["event_id"] = event_id
            if row is None:
                conn.execute(
                    """INSERT INTO isolated_paper_runtime_kill_switches(
                           sandbox_id, armed, state_version, changed_at, latest_event_id
                       ) VALUES (?, ?, ?, ?, ?)""",
                    (sandbox_id, int(desired), version + 1, _iso(event_at), event_id),
                )
            else:
                conn.execute(
                    """UPDATE isolated_paper_runtime_kill_switches
                       SET armed=?, state_version=?, changed_at=?, latest_event_id=?
                       WHERE sandbox_id=? AND state_version=?""",
                    (int(desired), version + 1, _iso(event_at), event_id, sandbox_id, version),
                )
            conn.execute(
                """INSERT INTO isolated_paper_runtime_kill_events(
                       event_id, sandbox_id, action, event_at, operator, note,
                       state_version, payload_json
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_id, sandbox_id, normalized_action, _iso(event_at),
                    operator.strip(), note.strip(), version + 1,
                    json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False),
                ),
            )
            if desired:
                for session in sessions:
                    self._stop_runtime_conn(
                        conn, session, stopped_at=event_at,
                        reason="KILL_SWITCH_ARMED", operator=operator.strip(),
                        note=note.strip(),
                    )
        return event_id

    def list_isolated_paper_runtime_kill_events(
        self, sandbox_id: str, *, limit: int = 100
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT payload_json FROM isolated_paper_runtime_kill_events
                   WHERE sandbox_id=? ORDER BY state_version DESC, event_id DESC LIMIT ?""",
                (sandbox_id, limit),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def acquire_isolated_paper_runtime(
        self,
        sandbox_id: str,
        *,
        worker_id: str,
        fencing_token_sha256: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        from .isolated_config import canonical_sha256

        if not worker_id.strip():
            raise ValueError("runtime worker_id is required")
        if len(fencing_token_sha256) != 64:
            raise ValueError("runtime fencing token hash is invalid")
        if not 5 <= lease_seconds <= 300:
            raise ValueError("runtime lease seconds must be between 5 and 300")
        started = _parse(_iso(now or datetime.now(timezone.utc)))
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            kill = conn.execute(
                "SELECT armed FROM isolated_paper_runtime_kill_switches WHERE sandbox_id=?",
                (sandbox_id,),
            ).fetchone()
            if kill is None or bool(kill["armed"]):
                raise ValueError("runtime kill switch is not explicitly clear")
            sandbox = conn.execute(
                """SELECT active_configuration_id, state_version
                   FROM isolated_paper_sandboxes WHERE sandbox_id=?""",
                (sandbox_id,),
            ).fetchone()
            if sandbox is None or sandbox["active_configuration_id"] is None:
                raise ValueError("runtime requires an effective isolated configuration")
            configuration_id = str(sandbox["active_configuration_id"])
            valid, reason, config = self._isolated_configuration_validity(
                conn, configuration_id, started
            )
            if not valid or config is None:
                raise ValueError(f"runtime configuration is not effective: {reason}")
            existing = conn.execute(
                """SELECT * FROM isolated_paper_runtime_sessions
                   WHERE sandbox_id=? AND status='RUNNING'""",
                (sandbox_id,),
            ).fetchone()
            if existing is not None:
                existing_state, existing_reason = self._runtime_effective_state_conn(
                    conn, existing, started
                )
                if existing_state != "RUNNING":
                    self._stop_runtime_conn(
                        conn, existing, stopped_at=started, reason=existing_reason,
                        operator="aars-runtime-acquirer",
                        note="Fence stale session before acquiring a new lease.",
                    )
                else:
                    raise ValueError("sandbox already has a running leased session")
            config_payload = json.loads(config["payload_json"])
            identity = {
                "sandbox_id": sandbox_id,
                "configuration_id": configuration_id,
                "configuration_sha256": config_payload["configuration_sha256"],
                "sandbox_state_version": int(sandbox["state_version"]),
                "worker_id": worker_id.strip(),
                "started_at": _iso(started),
                "fencing_token_sha256": fencing_token_sha256,
            }
            session_id = canonical_sha256(identity)[:24]
            lease_expires = min(
                started + timedelta(seconds=lease_seconds),
                _parse(config_payload["valid_until"]),
            )
            conn.execute(
                """INSERT INTO isolated_paper_runtime_sessions(
                       session_id, sandbox_id, configuration_id, configuration_sha256,
                       sandbox_state_version, worker_id, fencing_token_sha256,
                       started_at, last_heartbeat_at, lease_expires_at, status,
                       stop_reason, session_version, ended_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'RUNNING', NULL, 1, NULL)""",
                (
                    session_id, sandbox_id, configuration_id,
                    config_payload["configuration_sha256"], int(sandbox["state_version"]),
                    worker_id.strip(), fencing_token_sha256, _iso(started), _iso(started),
                    _iso(lease_expires),
                ),
            )
            session = conn.execute(
                "SELECT * FROM isolated_paper_runtime_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
            self._runtime_event_conn(
                conn, session, action="START", event_at=started,
                version=1, reason="EFFECTIVE_CONFIGURATION_LEASED",
                operator=worker_id.strip(), note="Acquire fenced PAPER_ONLY runtime lease.",
            )
        return {
            "schema_version": "mil3.isolated-paper-runtime-acquisition.v1",
            "execution_mode": "PAPER_ONLY",
            "session_id": session_id,
            "sandbox_id": sandbox_id,
            "configuration_id": configuration_id,
            "configuration_sha256": config_payload["configuration_sha256"],
            "sandbox_state_version": int(sandbox["state_version"]),
            "worker_id": worker_id.strip(),
            "lease_expires_at": _iso(lease_expires),
            "configuration_consumption_only": True,
            "replay_started": False,
            "order_path_present": False,
            "live_execution_allowed": False,
        }

    @staticmethod
    def _runtime_effective_state_conn(
        conn: sqlite3.Connection, session: sqlite3.Row, at: datetime
    ) -> tuple[str, str]:
        if session["status"] != "RUNNING":
            return str(session["status"]), str(session["stop_reason"] or "SESSION_STOPPED")
        kill = conn.execute(
            "SELECT armed FROM isolated_paper_runtime_kill_switches WHERE sandbox_id=?",
            (session["sandbox_id"],),
        ).fetchone()
        if kill is None or bool(kill["armed"]):
            return "KILL_SWITCH_FAIL_SAFE", "KILL_SWITCH_ARMED_OR_UNINITIALIZED"
        sandbox = conn.execute(
            """SELECT active_configuration_id, state_version FROM isolated_paper_sandboxes
               WHERE sandbox_id=?""",
            (session["sandbox_id"],),
        ).fetchone()
        if (
            sandbox is None
            or sandbox["active_configuration_id"] != session["configuration_id"]
            or int(sandbox["state_version"]) != int(session["sandbox_state_version"])
        ):
            return "POINTER_CHANGED_FAIL_SAFE", "SANDBOX_POINTER_OR_VERSION_CHANGED"
        valid, reason, config = MarketStore._isolated_configuration_validity(
            conn, session["configuration_id"], at
        )
        if not valid or config is None:
            return f"{reason}_FAIL_SAFE", reason
        config_payload = json.loads(config["payload_json"])
        if config_payload.get("configuration_sha256") != session["configuration_sha256"]:
            return "CONFIGURATION_HASH_FAIL_SAFE", "CONFIGURATION_HASH_CHANGED"
        if at >= _parse(session["lease_expires_at"]):
            return "LEASE_EXPIRED_FAIL_SAFE", "LEASE_EXPIRED"
        return "RUNNING", "LEASE_AND_CONFIGURATION_CURRENT"

    def resolve_isolated_paper_runtime_session(
        self, session_id: str, *, now: datetime | None = None
    ) -> dict[str, Any]:
        evaluated = _parse(_iso(now or datetime.now(timezone.utc)))
        with self.connect() as conn:
            session = conn.execute(
                "SELECT * FROM isolated_paper_runtime_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
            if session is None:
                raise KeyError(f"isolated paper runtime session not found: {session_id}")
            effective, reason = self._runtime_effective_state_conn(conn, session, evaluated)
        heartbeat_age = max(
            0.0, (evaluated - _parse(session["last_heartbeat_at"])).total_seconds()
        )
        return {
            "schema_version": "mil3.isolated-paper-runtime-session-view.v1",
            "execution_mode": "PAPER_ONLY",
            "evaluated_at": _iso(evaluated),
            "session_id": session_id,
            "sandbox_id": session["sandbox_id"],
            "configuration_id": session["configuration_id"],
            "configuration_sha256": session["configuration_sha256"],
            "sandbox_state_version": int(session["sandbox_state_version"]),
            "worker_id": session["worker_id"],
            "stored_status": session["status"],
            "effective_status": effective,
            "blocking_reason": reason,
            "started_at": session["started_at"],
            "last_heartbeat_at": session["last_heartbeat_at"],
            "heartbeat_age_seconds": heartbeat_age,
            "lease_expires_at": session["lease_expires_at"],
            "session_version": int(session["session_version"]),
            "ended_at": session["ended_at"],
            "read_only": True,
            "configuration_consumption_only": True,
            "replay_started": False,
            "order_path_present": False,
            "browser_control_allowed": False,
            "live_execution_allowed": False,
        }

    def list_isolated_paper_runtime_sessions(
        self, sandbox_id: str, *, limit: int = 100, now: datetime | None = None
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT session_id FROM isolated_paper_runtime_sessions
                   WHERE sandbox_id=? ORDER BY started_at DESC, session_id DESC LIMIT ?""",
                (sandbox_id, limit),
            ).fetchall()
        return [
            self.resolve_isolated_paper_runtime_session(row["session_id"], now=now)
            for row in rows
        ]

    def heartbeat_isolated_paper_runtime(
        self,
        session_id: str,
        *,
        fencing_token_sha256: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        import hmac

        if not 5 <= lease_seconds <= 300:
            raise ValueError("runtime lease seconds must be between 5 and 300")
        heartbeat = _parse(_iso(now or datetime.now(timezone.utc)))
        stopped = False
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            session = conn.execute(
                "SELECT * FROM isolated_paper_runtime_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
            if session is None:
                raise KeyError(f"isolated paper runtime session not found: {session_id}")
            if not hmac.compare_digest(
                str(session["fencing_token_sha256"]), fencing_token_sha256
            ):
                raise ValueError("runtime fencing token was rejected")
            if session["status"] != "RUNNING":
                raise ValueError("isolated paper runtime session is not running")
            if heartbeat < _parse(session["last_heartbeat_at"]):
                raise ValueError("runtime heartbeat cannot move backward")
            effective, reason = self._runtime_effective_state_conn(conn, session, heartbeat)
            if effective != "RUNNING":
                self._stop_runtime_conn(
                    conn, session, stopped_at=heartbeat, reason=reason,
                    operator=session["worker_id"],
                    note="Heartbeat detected a fail-safe stop condition.",
                )
                stopped = True
            else:
                config_row = conn.execute(
                    "SELECT payload_json FROM isolated_paper_configurations WHERE configuration_id=?",
                    (session["configuration_id"],),
                ).fetchone()
                if config_row is None:
                    raise ValueError("runtime configuration payload is unavailable")
                config = json.loads(config_row["payload_json"])
                version = int(session["session_version"]) + 1
                lease_expires = min(
                    heartbeat + timedelta(seconds=lease_seconds),
                    _parse(config["valid_until"]),
                )
                updated = conn.execute(
                    """UPDATE isolated_paper_runtime_sessions
                       SET last_heartbeat_at=?, lease_expires_at=?, session_version=?
                       WHERE session_id=? AND status='RUNNING' AND session_version=?""",
                    (
                        _iso(heartbeat), _iso(lease_expires), version,
                        session_id, session["session_version"],
                    ),
                )
                if updated.rowcount != 1:
                    raise ValueError("runtime heartbeat lost its fencing race")
                self._runtime_event_conn(
                    conn, session, action="HEARTBEAT", event_at=heartbeat,
                    version=version, reason="EFFECTIVE_CONFIGURATION_CONSUMED",
                    operator=session["worker_id"],
                    note="Renew fenced lease after effective configuration verification.",
                )
        view = self.resolve_isolated_paper_runtime_session(session_id, now=heartbeat)
        return {
            **view,
            "configuration_consumed": not stopped,
            "paper_calculation_performed": False,
        }

    def stop_isolated_paper_runtime(
        self,
        session_id: str,
        *,
        operator: str,
        note: str,
        reason: str = "MANUAL_STOP",
        now: datetime | None = None,
    ) -> str | None:
        if not operator.strip() or not note.strip():
            raise ValueError("runtime stop operator and note are required")
        stopped_at = _parse(_iso(now or datetime.now(timezone.utc)))
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            session = conn.execute(
                "SELECT * FROM isolated_paper_runtime_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
            if session is None:
                raise KeyError(f"isolated paper runtime session not found: {session_id}")
            if session["status"] != "RUNNING":
                return None
            if stopped_at < _parse(session["last_heartbeat_at"]):
                raise ValueError("runtime stop cannot predate the latest heartbeat")
            return self._stop_runtime_conn(
                conn, session, stopped_at=stopped_at, reason=reason,
                operator=operator.strip(), note=note.strip(),
            )

    def list_isolated_paper_runtime_events(
        self, session_id: str, *, limit: int = 100
    ) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT payload_json FROM isolated_paper_runtime_events
                   WHERE session_id=? ORDER BY session_version DESC, event_id DESC LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def reconcile_isolated_paper_runtime_sessions(
        self, *, now: datetime | None = None
    ) -> dict[str, Any]:
        evaluated = _parse(_iso(now or datetime.now(timezone.utc)))
        with self.connect() as conn:
            session_ids = [
                row["session_id"]
                for row in conn.execute(
                    "SELECT session_id FROM isolated_paper_runtime_sessions WHERE status='RUNNING'"
                ).fetchall()
            ]
        records = []
        for session_id in session_ids:
            view = self.resolve_isolated_paper_runtime_session(session_id, now=evaluated)
            if view["effective_status"] == "RUNNING":
                records.append({"session_id": session_id, "status": "NO_CHANGE"})
                continue
            event_id = self.stop_isolated_paper_runtime(
                session_id,
                operator="aars-runtime-reconciler",
                note="Persist derived fail-safe runtime stop.",
                reason=view["blocking_reason"],
                now=evaluated,
            )
            records.append({
                "session_id": session_id,
                "status": "STOPPED" if event_id else "ALREADY_STOPPED",
                "reason": view["effective_status"],
                "event_id": event_id,
            })
        return {
            "schema_version": "mil3.isolated-paper-runtime-reconciliation.v1",
            "execution_mode": "PAPER_ONLY",
            "evaluated_at": _iso(evaluated),
            "records": records,
            "replay_started": False,
            "order_path_present": False,
            "live_execution_allowed": False,
        }
