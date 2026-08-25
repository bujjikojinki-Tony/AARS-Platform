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
