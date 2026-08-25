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
