from __future__ import annotations

import sqlite3
from dataclasses import fields
from typing import Generic
from typing import TypeVar

from weather_comparison_engine.polymarket_bot.models import AuditLog
from weather_comparison_engine.polymarket_bot.models import ExecutionDecision
from weather_comparison_engine.polymarket_bot.models import MarketSnapshot
from weather_comparison_engine.polymarket_bot.models import OpportunityCandidate
from weather_comparison_engine.polymarket_bot.models import SimulationResult
from weather_comparison_engine.polymarket_bot.models import StrategySignal

T = TypeVar("T")


class BaseRepository(Generic[T]):
    table_name: str
    model_cls: type[T]
    order_by: str = "created_at DESC"
    bool_columns: tuple[str, ...] = ()
    id_column: str | None = None

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.columns = [field.name for field in fields(self.model_cls)]

    def save(self, item: T) -> None:
        placeholders = ", ".join("?" for _ in self.columns)
        column_sql = ", ".join(self.columns)
        sql = f"INSERT OR REPLACE INTO {self.table_name} ({column_sql}) VALUES ({placeholders})"
        values = []
        for column in self.columns:
            value = getattr(item, column)
            if column in self.bool_columns and value is not None:
                value = int(value)
            values.append(value)
        self.conn.execute(sql, values)
        self.conn.commit()

    def list_all(self) -> list[T]:
        rows = self.conn.execute(
            f"SELECT {', '.join(self.columns)} FROM {self.table_name} ORDER BY {self.order_by}"
        ).fetchall()
        items: list[T] = []
        for row in rows:
            payload = dict(row)
            for column in self.bool_columns:
                if column in payload and payload[column] is not None:
                    payload[column] = bool(payload[column])
            items.append(self.model_cls(**payload))
        return items

    def get_by_id(self, object_id: str) -> T | None:
        if self.id_column is None:
            raise ValueError(f"{self.__class__.__name__} does not define id_column")
        row = self.conn.execute(
            f"SELECT {', '.join(self.columns)} FROM {self.table_name} WHERE {self.id_column} = ?",
            (object_id,),
        ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        for column in self.bool_columns:
            if column in payload and payload[column] is not None:
                payload[column] = bool(payload[column])
        return self.model_cls(**payload)


class MarketSnapshotRepository(BaseRepository[MarketSnapshot]):
    table_name = "market_snapshots"
    model_cls = MarketSnapshot
    order_by = "fetched_at DESC, market_id ASC"
    id_column = "market_id"


class StrategySignalRepository(BaseRepository[StrategySignal]):
    table_name = "strategy_signals"
    model_cls = StrategySignal
    id_column = "signal_id"


class OpportunityCandidateRepository(BaseRepository[OpportunityCandidate]):
    table_name = "opportunity_candidates"
    model_cls = OpportunityCandidate
    id_column = "candidate_id"


class ExecutionDecisionRepository(BaseRepository[ExecutionDecision]):
    table_name = "execution_decisions"
    model_cls = ExecutionDecision
    bool_columns = ("approval_required",)
    id_column = "decision_id"


class SimulationResultRepository(BaseRepository[SimulationResult]):
    table_name = "simulation_results"
    model_cls = SimulationResult
    id_column = "simulation_id"


class AuditLogRepository(BaseRepository[AuditLog]):
    table_name = "audit_logs"
    model_cls = AuditLog
    id_column = "event_id"


class PolymarketBotRepositories:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.market_snapshots = MarketSnapshotRepository(conn)
        self.strategy_signals = StrategySignalRepository(conn)
        self.opportunity_candidates = OpportunityCandidateRepository(conn)
        self.execution_decisions = ExecutionDecisionRepository(conn)
        self.simulation_results = SimulationResultRepository(conn)
        self.audit_logs = AuditLogRepository(conn)
