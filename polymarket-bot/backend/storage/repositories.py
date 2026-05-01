from __future__ import annotations

import json

from backend.models.calibration_memory import BacktestMemoryRecord
from backend.models.calibration_memory import BacktestMemoryStatus
from backend.models.calibration_memory import CalibrationMemoryBundle
from backend.models.calibration_memory import CalibrationMemorySummary
from backend.models.calibration_memory import CalibrationSample
from backend.models.calibration_memory import CalibrationSampleStatus
from backend.models.calibration_memory import HypotheticalAction
from backend.models.calibration_memory import SampleEligibility
from backend.models.activation_authorization_review import ActivationAuthorizationRecommendation
from backend.models.activation_authorization_review import ActivationAuthorizationReviewBundle
from backend.models.activation_authorization_review import ActivationAuthorizationReviewRecord
from backend.models.activation_authorization_review import ActivationAuthorizationReviewStatus
from backend.models.activation_authorization_review import ActivationAuthorizationReviewSummary
from backend.models.activation_readiness_review import ActivationReadinessRecommendation
from backend.models.activation_readiness_review import ActivationReadinessReviewBundle
from backend.models.activation_readiness_review import ActivationReadinessReviewRecord
from backend.models.activation_readiness_review import ActivationReadinessReviewStatus
from backend.models.activation_readiness_review import ActivationReadinessReviewSummary
from backend.models.approval_window_review import ApprovalWindowRecommendation
from backend.models.approval_window_review import ApprovalWindowReviewBundle
from backend.models.approval_window_review import ApprovalWindowReviewRecord
from backend.models.approval_window_review import ApprovalWindowReviewStatus
from backend.models.approval_window_review import ApprovalWindowReviewSummary
from backend.models.approval_window_review import ApprovalWindowState
from backend.models.command_review import CommandApprovalStatus
from backend.models.command_review import CommandGateStatus
from backend.models.command_review import CommandReviewBundle
from backend.models.command_review import CommandReviewRecommendation
from backend.models.command_review import CommandReviewRecord
from backend.models.command_review import CommandReviewStatus
from backend.models.command_review import CommandReviewSummary
from backend.models.core import AuditLogEvent
from backend.models.core import ExecutionDecision
from backend.models.core import MarketSnapshot
from backend.models.core import OpportunityCandidate
from backend.models.core import SimulationResult
from backend.models.core import StrategySignal
from backend.models.enums import ActionStatus
from backend.models.polymarket import PolymarketConnectorHealth
from backend.models.polymarket import PolymarketMarketRecord
from backend.models.snapshot_archive import MarketSnapshotArchiveRecord
from backend.models.snapshot_archive import MarketSnapshotSeries
from backend.models.snapshot_archive import SnapshotArchiveReason
from backend.models.snapshot_archive import SnapshotArchiveSummary
from backend.models.weather_archive import WeatherArchiveBundle
from backend.models.weather_archive import WeatherArchiveReason
from backend.models.weather_archive import WeatherArchiveSummary
from backend.models.weather_archive import WeatherEvidenceArchiveRecord
from backend.models.weather_archive import WeatherForecastArchiveRecord
from backend.models.weather_archive import WeatherForecastSourceType
from backend.models.weather_archive import WeatherViewArchiveRecord
from backend.models.probability_governance import CalibrationResult
from backend.models.probability_governance import EnginePromotionDecision
from backend.models.probability_governance import MarketOutcome
from backend.models.probability_governance import ProbabilityComparisonView
from backend.models.probability_governance import ProbabilityEngineConfig
from backend.models.probability_governance import ProbabilityEngineRun
from backend.models.outcome import MarketOutcomeRecord
from backend.models.outcome import OutcomeArchiveSummary
from backend.models.outcome import OutcomeBundle
from backend.models.outcome import OutcomeResolutionRecord
from backend.models.outcome import ResolutionStatus
from backend.models.outcome import WeatherActualRecord
from backend.models.deb_shadow import DebShadowDiagnosticRecord
from backend.models.deb_shadow import DebShadowMarketBundle
from backend.models.deb_shadow import DebShadowRunRecord
from backend.models.deb_shadow import DebShadowRunStatus
from backend.models.deb_shadow import DebShadowSummary
from backend.models.emos_shadow import EmosShadowDiagnosticRecord
from backend.models.emos_shadow import EmosShadowMarketBundle
from backend.models.emos_shadow import EmosShadowRunRecord
from backend.models.emos_shadow import EmosShadowRunStatus
from backend.models.emos_shadow import EmosShadowSummary
from backend.models.shadow_engine_evaluation import BestShadowEngine
from backend.models.shadow_engine_evaluation import ShadowEngineEvaluationBundle
from backend.models.shadow_engine_evaluation import ShadowEngineEvaluationRecord
from backend.models.shadow_engine_evaluation import ShadowEvaluationStatus
from backend.models.shadow_engine_evaluation import ShadowEngineEvaluationSummary
from backend.models.execution_decision_review import ExecutionApprovalStatus
from backend.models.execution_decision_review import ExecutionDecisionReviewBundle
from backend.models.execution_decision_review import ExecutionDecisionReviewRecommendation
from backend.models.execution_decision_review import ExecutionDecisionReviewRecord
from backend.models.execution_decision_review import ExecutionDecisionReviewStatus
from backend.models.execution_decision_review import ExecutionDecisionReviewSummary
from backend.models.execution_decision_review import ExecutionGateStatus
from backend.models.execution_queue_review import ExecutionQueueApprovalStatus
from backend.models.execution_queue_review import ExecutionQueueReviewBundle
from backend.models.execution_queue_review import ExecutionQueueReviewRecommendation
from backend.models.execution_queue_review import ExecutionQueueReviewRecord
from backend.models.execution_queue_review import ExecutionQueueReviewStatus
from backend.models.execution_queue_review import ExecutionQueueReviewSummary
from backend.models.execution_queue_review import ExecutionQueueGateStatus
from backend.models.weather import EvidencePack
from backend.models.weather import ProbabilityView
from backend.models.weather import WeatherMarketDescriptor
from backend.models.weather import WeatherSourceRecord
from backend.models.weather import WeatherView
from .db import get_connection


class Repository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_shadow_engine_evaluation(self, item: ShadowEngineEvaluationRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO shadow_engine_evaluations
                (shadow_evaluation_id, market_id, calibration_sample_id, outcome_resolution_id,
                 primary_engine_id, deb_engine_id, emos_engine_id,
                 primary_probability, deb_probability, emos_probability, actual_outcome_value,
                 primary_brier_score, deb_brier_score, emos_brier_score,
                 primary_absolute_error, deb_absolute_error, emos_absolute_error,
                 best_engine, evaluation_status, created_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.shadow_evaluation_id,
                    item.market_id,
                    item.calibration_sample_id,
                    item.outcome_resolution_id,
                    item.primary_engine_id,
                    item.deb_engine_id,
                    item.emos_engine_id,
                    item.primary_probability,
                    item.deb_probability,
                    item.emos_probability,
                    item.actual_outcome_value,
                    item.primary_brier_score,
                    item.deb_brier_score,
                    item.emos_brier_score,
                    item.primary_absolute_error,
                    item.deb_absolute_error,
                    item.emos_absolute_error,
                    item.best_engine.value if hasattr(item.best_engine, "value") else str(item.best_engine),
                    item.evaluation_status.value
                    if hasattr(item.evaluation_status, "value")
                    else str(item.evaluation_status),
                    item.created_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_emos_shadow_run(self, item: EmosShadowRunRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO emos_shadow_runs
                (emos_shadow_run_id, market_id, calibration_sample_id, engine_id,
                 base_probability, emos_probability, location_adjustment, scale_adjustment,
                 sample_count, run_status, warnings_json, created_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.emos_shadow_run_id,
                    item.market_id,
                    item.calibration_sample_id,
                    item.engine_id,
                    item.base_probability,
                    item.emos_probability,
                    item.location_adjustment,
                    item.scale_adjustment,
                    item.sample_count,
                    item.run_status.value if hasattr(item.run_status, "value") else str(item.run_status),
                    json.dumps(item.warnings, ensure_ascii=False),
                    item.created_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_emos_shadow_diagnostic(self, item: EmosShadowDiagnosticRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO emos_shadow_diagnostics
                (emos_shadow_diagnostic_id, emos_shadow_run_id, market_id, calibration_sample_id,
                 sample_count, avg_model_brier_score, avg_market_brier_score, avg_probability_error,
                 avg_absolute_error, location_weight, scale_weight, notes, created_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.emos_shadow_diagnostic_id,
                    item.emos_shadow_run_id,
                    item.market_id,
                    item.calibration_sample_id,
                    item.sample_count,
                    item.avg_model_brier_score,
                    item.avg_market_brier_score,
                    item.avg_probability_error,
                    item.avg_absolute_error,
                    item.location_weight,
                    item.scale_weight,
                    item.notes,
                    item.created_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_deb_shadow_run(self, item: DebShadowRunRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO deb_shadow_runs
                (deb_shadow_run_id, market_id, calibration_sample_id, engine_id,
                 base_probability, deb_probability, bias_adjustment, calibration_gap,
                 sample_count, run_status, warnings_json, created_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.deb_shadow_run_id,
                    item.market_id,
                    item.calibration_sample_id,
                    item.engine_id,
                    item.base_probability,
                    item.deb_probability,
                    item.bias_adjustment,
                    item.calibration_gap,
                    item.sample_count,
                    item.run_status.value if hasattr(item.run_status, "value") else str(item.run_status),
                    json.dumps(item.warnings, ensure_ascii=False),
                    item.created_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_deb_shadow_diagnostic(self, item: DebShadowDiagnosticRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO deb_shadow_diagnostics
                (deb_shadow_diagnostic_id, deb_shadow_run_id, market_id, calibration_sample_id,
                 sample_count, avg_model_brier_score, avg_market_brier_score, avg_model_edge,
                 avg_probability_error, adjustment_weight, notes, created_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.deb_shadow_diagnostic_id,
                    item.deb_shadow_run_id,
                    item.market_id,
                    item.calibration_sample_id,
                    item.sample_count,
                    item.avg_model_brier_score,
                    item.avg_market_brier_score,
                    item.avg_model_edge,
                    item.avg_probability_error,
                    item.adjustment_weight,
                    item.notes,
                    item.created_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_calibration_sample(self, item: CalibrationSample) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO calibration_samples
                (calibration_sample_id, market_id, snapshot_archive_id, weather_view_archive_id,
                 weather_forecast_archive_id, probability_run_id, outcome_resolution_id, engine_id,
                 market_probability, model_probability, actual_outcome_value,
                 model_brier_score, market_brier_score, model_absolute_error,
                 market_absolute_error, model_beats_market, resolved_outcome,
                 sample_eligibility, sample_status, sampled_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.calibration_sample_id,
                    item.market_id,
                    item.snapshot_archive_id,
                    item.weather_view_archive_id,
                    item.weather_forecast_archive_id,
                    item.probability_run_id,
                    item.outcome_resolution_id,
                    item.engine_id,
                    item.market_probability,
                    item.model_probability,
                    item.actual_outcome_value,
                    item.model_brier_score,
                    item.market_brier_score,
                    item.model_absolute_error,
                    item.market_absolute_error,
                    None if item.model_beats_market is None else int(item.model_beats_market),
                    item.resolved_outcome.value
                    if hasattr(item.resolved_outcome, "value")
                    else str(item.resolved_outcome),
                    item.sample_eligibility.value
                    if hasattr(item.sample_eligibility, "value")
                    else str(item.sample_eligibility),
                    item.sample_status.value
                    if hasattr(item.sample_status, "value")
                    else str(item.sample_status),
                    item.sampled_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_backtest_memory_record(self, item: BacktestMemoryRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO backtest_memory_records
                (backtest_memory_id, market_id, snapshot_archive_id, weather_view_archive_id,
                 weather_forecast_archive_id, probability_run_id, outcome_resolution_id, engine_id,
                 market_probability, model_probability, actual_outcome_value, edge,
                 edge_threshold, hypothetical_action, hypothetical_result,
                 sample_eligibility, backtest_status, sampled_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.backtest_memory_id,
                    item.market_id,
                    item.snapshot_archive_id,
                    item.weather_view_archive_id,
                    item.weather_forecast_archive_id,
                    item.probability_run_id,
                    item.outcome_resolution_id,
                    item.engine_id,
                    item.market_probability,
                    item.model_probability,
                    item.actual_outcome_value,
                    item.edge,
                    item.edge_threshold,
                    item.hypothetical_action.value
                    if hasattr(item.hypothetical_action, "value")
                    else str(item.hypothetical_action),
                    item.hypothetical_result.value
                    if hasattr(item.hypothetical_result, "value")
                    else str(item.hypothetical_result),
                    item.sample_eligibility.value
                    if hasattr(item.sample_eligibility, "value")
                    else str(item.sample_eligibility),
                    item.backtest_status.value
                    if hasattr(item.backtest_status, "value")
                    else str(item.backtest_status),
                    item.sampled_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def list_calibration_samples(
        self,
        limit: int = 100,
        market_id: str | None = None,
        engine_id: str | None = None,
        sample_status: CalibrationSampleStatus | str | None = None,
        sample_eligibility: SampleEligibility | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if engine_id:
            clauses.append("engine_id = ?")
            params.append(engine_id)
        if sample_status:
            clauses.append("sample_status = ?")
            params.append(sample_status.value if hasattr(sample_status, "value") else str(sample_status))
        if sample_eligibility:
            clauses.append("sample_eligibility = ?")
            params.append(
                sample_eligibility.value
                if hasattr(sample_eligibility, "value")
                else str(sample_eligibility)
            )
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM calibration_samples
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_calibration_sample_row(row) for row in rows]

    def list_backtest_memory_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        engine_id: str | None = None,
        backtest_status: BacktestMemoryStatus | str | None = None,
        sample_eligibility: SampleEligibility | str | None = None,
        hypothetical_action: HypotheticalAction | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if engine_id:
            clauses.append("engine_id = ?")
            params.append(engine_id)
        if backtest_status:
            clauses.append("backtest_status = ?")
            params.append(
                backtest_status.value if hasattr(backtest_status, "value") else str(backtest_status)
            )
        if sample_eligibility:
            clauses.append("sample_eligibility = ?")
            params.append(
                sample_eligibility.value
                if hasattr(sample_eligibility, "value")
                else str(sample_eligibility)
            )
        if hypothetical_action:
            clauses.append("hypothetical_action = ?")
            params.append(
                hypothetical_action.value
                if hasattr(hypothetical_action, "value")
                else str(hypothetical_action)
            )
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM backtest_memory_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_backtest_memory_record_row(row) for row in rows]

    def get_calibration_sample_by_id(self, calibration_sample_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM calibration_samples
                WHERE calibration_sample_id = ?
                LIMIT 1
                """,
                (calibration_sample_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_calibration_sample_row(row)

    def get_backtest_memory_record_by_id(self, backtest_memory_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM backtest_memory_records
                WHERE backtest_memory_id = ?
                LIMIT 1
                """,
                (backtest_memory_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_backtest_memory_record_row(row)

    def get_calibration_memory_bundle(
        self,
        market_id: str,
        limit: int = 100,
    ) -> CalibrationMemoryBundle:
        return CalibrationMemoryBundle(
            market_id=market_id,
            calibration_samples=[
                CalibrationSample(**item)
                for item in self.list_calibration_samples(market_id=market_id, limit=limit)
            ],
            backtest_memory_records=[
                BacktestMemoryRecord(**item)
                for item in self.list_backtest_memory_records(market_id=market_id, limit=limit)
            ],
        )

    def get_latest_calibration_sample_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM calibration_samples
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_calibration_sample_row(row)

    def get_latest_backtest_memory_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM backtest_memory_records
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_backtest_memory_record_row(row)

    def get_calibration_memory_summary(self) -> CalibrationMemorySummary:
        with get_connection(self.db_path) as conn:
            sample_count = conn.execute(
                "SELECT COUNT(*) AS count FROM calibration_samples"
            ).fetchone()["count"]
            backtest_count = conn.execute(
                "SELECT COUNT(*) AS count FROM backtest_memory_records"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM calibration_samples
                UNION
                SELECT market_id FROM backtest_memory_records
                """
            ).fetchall()
            sample_status_rows = conn.execute(
                """
                SELECT sample_status, COUNT(*) AS count
                FROM calibration_samples
                GROUP BY sample_status
                """
            ).fetchall()
            backtest_status_rows = conn.execute(
                """
                SELECT backtest_status, COUNT(*) AS count
                FROM backtest_memory_records
                GROUP BY backtest_status
                """
            ).fetchall()
            eligibility_rows = conn.execute(
                """
                SELECT sample_eligibility, COUNT(*) AS count
                FROM calibration_samples
                GROUP BY sample_eligibility
                UNION ALL
                SELECT sample_eligibility, COUNT(*) AS count
                FROM backtest_memory_records
                GROUP BY sample_eligibility
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT sampled_at FROM calibration_samples
                UNION ALL
                SELECT sampled_at FROM backtest_memory_records
                ORDER BY sampled_at DESC
                LIMIT 1
                """
            ).fetchall()
        by_eligibility: dict[str, int] = {}
        for row in eligibility_rows:
            key = str(row["sample_eligibility"])
            by_eligibility[key] = by_eligibility.get(key, 0) + int(row["count"] or 0)
        return CalibrationMemorySummary(
            calibration_samples=int(sample_count or 0),
            backtest_memory_records=int(backtest_count or 0),
            unique_markets=len(unique_rows),
            by_sample_status={
                str(row["sample_status"]): int(row["count"] or 0) for row in sample_status_rows
            },
            by_backtest_status={
                str(row["backtest_status"]): int(row["count"] or 0) for row in backtest_status_rows
            },
            by_eligibility=by_eligibility,
            latest_sampled_at=latest_rows[0]["sampled_at"] if latest_rows else None,
        )

    def list_deb_shadow_runs(
        self,
        limit: int = 100,
        market_id: str | None = None,
        engine_id: str | None = None,
        run_status: DebShadowRunStatus | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if engine_id:
            clauses.append("engine_id = ?")
            params.append(engine_id)
        if run_status:
            clauses.append("run_status = ?")
            params.append(run_status.value if hasattr(run_status, "value") else str(run_status))
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM deb_shadow_runs
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_deb_shadow_run_row(row) for row in rows]

    def list_deb_shadow_diagnostics(
        self,
        limit: int = 100,
        market_id: str | None = None,
        deb_shadow_run_id: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if deb_shadow_run_id:
            clauses.append("deb_shadow_run_id = ?")
            params.append(deb_shadow_run_id)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM deb_shadow_diagnostics
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_deb_shadow_diagnostic_row(row) for row in rows]

    def get_deb_shadow_run_by_id(self, deb_shadow_run_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM deb_shadow_runs
                WHERE deb_shadow_run_id = ?
                LIMIT 1
                """,
                (deb_shadow_run_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_deb_shadow_run_row(row)

    def get_latest_deb_shadow_run_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM deb_shadow_runs
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_deb_shadow_run_row(row)

    def get_deb_shadow_market_bundle(
        self,
        market_id: str,
        limit: int = 100,
    ) -> DebShadowMarketBundle:
        return DebShadowMarketBundle(
            market_id=market_id,
            runs=[
                DebShadowRunRecord(**item)
                for item in self.list_deb_shadow_runs(market_id=market_id, limit=limit)
            ],
            diagnostics=[
                DebShadowDiagnosticRecord(**item)
                for item in self.list_deb_shadow_diagnostics(market_id=market_id, limit=limit)
            ],
        )

    def get_deb_shadow_summary(self) -> DebShadowSummary:
        with get_connection(self.db_path) as conn:
            total_runs = conn.execute(
                "SELECT COUNT(*) AS count FROM deb_shadow_runs"
            ).fetchone()["count"]
            total_diagnostics = conn.execute(
                "SELECT COUNT(*) AS count FROM deb_shadow_diagnostics"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM deb_shadow_runs
                UNION
                SELECT market_id FROM deb_shadow_diagnostics
                """
            ).fetchall()
            status_rows = conn.execute(
                """
                SELECT run_status, COUNT(*) AS count
                FROM deb_shadow_runs
                GROUP BY run_status
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT created_at FROM deb_shadow_runs
                UNION ALL
                SELECT created_at FROM deb_shadow_diagnostics
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchall()
        return DebShadowSummary(
            total_runs=int(total_runs or 0),
            total_diagnostics=int(total_diagnostics or 0),
            unique_markets=len(unique_rows),
            by_run_status={str(row["run_status"]): int(row["count"] or 0) for row in status_rows},
            latest_created_at=latest_rows[0]["created_at"] if latest_rows else None,
        )

    def list_emos_shadow_runs(
        self,
        limit: int = 100,
        market_id: str | None = None,
        engine_id: str | None = None,
        run_status: EmosShadowRunStatus | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if engine_id:
            clauses.append("engine_id = ?")
            params.append(engine_id)
        if run_status:
            clauses.append("run_status = ?")
            params.append(run_status.value if hasattr(run_status, "value") else str(run_status))
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM emos_shadow_runs
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_emos_shadow_run_row(row) for row in rows]

    def list_emos_shadow_diagnostics(
        self,
        limit: int = 100,
        market_id: str | None = None,
        emos_shadow_run_id: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if emos_shadow_run_id:
            clauses.append("emos_shadow_run_id = ?")
            params.append(emos_shadow_run_id)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM emos_shadow_diagnostics
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_emos_shadow_diagnostic_row(row) for row in rows]

    def get_emos_shadow_run_by_id(self, emos_shadow_run_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM emos_shadow_runs
                WHERE emos_shadow_run_id = ?
                LIMIT 1
                """,
                (emos_shadow_run_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_emos_shadow_run_row(row)

    def get_latest_emos_shadow_run_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM emos_shadow_runs
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_emos_shadow_run_row(row)

    def get_emos_shadow_market_bundle(
        self,
        market_id: str,
        limit: int = 100,
    ) -> EmosShadowMarketBundle:
        return EmosShadowMarketBundle(
            market_id=market_id,
            runs=[
                EmosShadowRunRecord(**item)
                for item in self.list_emos_shadow_runs(market_id=market_id, limit=limit)
            ],
            diagnostics=[
                EmosShadowDiagnosticRecord(**item)
                for item in self.list_emos_shadow_diagnostics(market_id=market_id, limit=limit)
            ],
        )

    def get_emos_shadow_summary(self) -> EmosShadowSummary:
        with get_connection(self.db_path) as conn:
            total_runs = conn.execute(
                "SELECT COUNT(*) AS count FROM emos_shadow_runs"
            ).fetchone()["count"]
            total_diagnostics = conn.execute(
                "SELECT COUNT(*) AS count FROM emos_shadow_diagnostics"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM emos_shadow_runs
                UNION
                SELECT market_id FROM emos_shadow_diagnostics
                """
            ).fetchall()
            status_rows = conn.execute(
                """
                SELECT run_status, COUNT(*) AS count
                FROM emos_shadow_runs
                GROUP BY run_status
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT created_at FROM emos_shadow_runs
                UNION ALL
                SELECT created_at FROM emos_shadow_diagnostics
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchall()
        return EmosShadowSummary(
            total_runs=int(total_runs or 0),
            total_diagnostics=int(total_diagnostics or 0),
            unique_markets=len(unique_rows),
            by_run_status={str(row["run_status"]): int(row["count"] or 0) for row in status_rows},
            latest_created_at=latest_rows[0]["created_at"] if latest_rows else None,
        )

    def list_shadow_engine_evaluations(
        self,
        limit: int = 100,
        market_id: str | None = None,
        evaluation_status: ShadowEvaluationStatus | str | None = None,
        best_engine: BestShadowEngine | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if evaluation_status:
            clauses.append("evaluation_status = ?")
            params.append(
                evaluation_status.value
                if hasattr(evaluation_status, "value")
                else str(evaluation_status)
            )
        if best_engine:
            clauses.append("best_engine = ?")
            params.append(best_engine.value if hasattr(best_engine, "value") else str(best_engine))
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM shadow_engine_evaluations
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_shadow_engine_evaluation_row(row) for row in rows]

    def get_shadow_engine_evaluation_by_id(self, shadow_evaluation_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM shadow_engine_evaluations
                WHERE shadow_evaluation_id = ?
                LIMIT 1
                """,
                (shadow_evaluation_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_shadow_engine_evaluation_row(row)

    def get_latest_shadow_engine_evaluation_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM shadow_engine_evaluations
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_shadow_engine_evaluation_row(row)

    def get_shadow_engine_evaluation_bundle(
        self,
        market_id: str,
        limit: int = 100,
    ) -> ShadowEngineEvaluationBundle:
        return ShadowEngineEvaluationBundle(
            market_id=market_id,
            evaluations=[
                ShadowEngineEvaluationRecord(**item)
                for item in self.list_shadow_engine_evaluations(market_id=market_id, limit=limit)
            ],
        )

    def get_shadow_engine_evaluation_summary(self) -> ShadowEngineEvaluationSummary:
        with get_connection(self.db_path) as conn:
            total_evaluations = conn.execute(
                "SELECT COUNT(*) AS count FROM shadow_engine_evaluations"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM shadow_engine_evaluations
                GROUP BY market_id
                """
            ).fetchall()
            status_rows = conn.execute(
                """
                SELECT evaluation_status, COUNT(*) AS count
                FROM shadow_engine_evaluations
                GROUP BY evaluation_status
                """
            ).fetchall()
            best_rows = conn.execute(
                """
                SELECT best_engine, COUNT(*) AS count
                FROM shadow_engine_evaluations
                GROUP BY best_engine
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT created_at
                FROM shadow_engine_evaluations
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchall()
        return ShadowEngineEvaluationSummary(
            total_evaluations=int(total_evaluations or 0),
            unique_markets=len(unique_rows),
            by_status={
                str(row["evaluation_status"]): int(row["count"] or 0) for row in status_rows
            },
            by_best_engine={
                str(row["best_engine"]): int(row["count"] or 0) for row in best_rows
            },
            latest_created_at=latest_rows[0]["created_at"] if latest_rows else None,
        )

    def save_command_review_record(self, item: CommandReviewRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO command_review_records
                (command_review_id, market_id, command_name, source_page, target_page,
                 command_path, review_status, approval_status, recommendation, gate_status,
                 active_engine_id, execution_mode, risk_status, approval_window_valid,
                 approval_valid_until, market_snapshot_archive_id, weather_view_archive_id,
                 weather_forecast_archive_id, probability_run_id, outcome_resolution_id,
                 calibration_sample_id, backtest_memory_id, deb_shadow_run_id,
                 emos_shadow_run_id, shadow_evaluation_id, reviewed_at,
                 raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.command_review_id,
                    item.market_id,
                    item.command_name,
                    item.source_page,
                    item.target_page,
                    item.command_path,
                    item.review_status.value if hasattr(item.review_status, "value") else str(item.review_status),
                    item.approval_status.value if hasattr(item.approval_status, "value") else str(item.approval_status),
                    item.recommendation.value if hasattr(item.recommendation, "value") else str(item.recommendation),
                    item.gate_status.value if hasattr(item.gate_status, "value") else str(item.gate_status),
                    item.active_engine_id,
                    item.execution_mode,
                    item.risk_status,
                    None if item.approval_window_valid is None else int(item.approval_window_valid),
                    item.approval_valid_until,
                    item.market_snapshot_archive_id,
                    item.weather_view_archive_id,
                    item.weather_forecast_archive_id,
                    item.probability_run_id,
                    item.outcome_resolution_id,
                    item.calibration_sample_id,
                    item.backtest_memory_id,
                    item.deb_shadow_run_id,
                    item.emos_shadow_run_id,
                    item.shadow_evaluation_id,
                    item.reviewed_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def list_command_review_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        gate_status: str | None = None,
    ) -> list[dict]:
        clauses = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if review_status:
            clauses.append("review_status = ?")
            params.append(review_status)
        if approval_status:
            clauses.append("approval_status = ?")
            params.append(approval_status)
        if gate_status:
            clauses.append("gate_status = ?")
            params.append(gate_status)
        where_sql = ""
        if clauses:
            where_sql = "WHERE " + " AND ".join(clauses)
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM command_review_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._parse_command_review_record_row(row) for row in rows]

    def get_latest_command_review_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM command_review_records
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_command_review_record_row(row)

    def get_command_review_bundle(self, market_id: str, limit: int = 100) -> CommandReviewBundle:
        return CommandReviewBundle(
            market_id=market_id,
            command_reviews=[
                CommandReviewRecord(**item)
                for item in self.list_command_review_records(market_id=market_id, limit=limit)
            ],
        )

    def get_command_review_summary(self) -> CommandReviewSummary:
        with get_connection(self.db_path) as conn:
            total_reviews = conn.execute(
                "SELECT COUNT(*) AS count FROM command_review_records"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM command_review_records
                GROUP BY market_id
                """
            ).fetchall()
            review_rows = conn.execute(
                """
                SELECT review_status, COUNT(*) AS count
                FROM command_review_records
                GROUP BY review_status
                """
            ).fetchall()
            approval_rows = conn.execute(
                """
                SELECT approval_status, COUNT(*) AS count
                FROM command_review_records
                GROUP BY approval_status
                """
            ).fetchall()
            gate_rows = conn.execute(
                """
                SELECT gate_status, COUNT(*) AS count
                FROM command_review_records
                GROUP BY gate_status
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT reviewed_at
                FROM command_review_records
                ORDER BY reviewed_at DESC
                LIMIT 1
                """
            ).fetchall()
        return CommandReviewSummary(
            command_reviews=int(total_reviews or 0),
            unique_markets=len(unique_rows),
            by_review_status={
                str(row["review_status"]): int(row["count"] or 0) for row in review_rows
            },
            by_approval_status={
                str(row["approval_status"]): int(row["count"] or 0) for row in approval_rows
            },
            by_gate_status={
                str(row["gate_status"]): int(row["count"] or 0) for row in gate_rows
            },
            latest_reviewed_at=latest_rows[0]["reviewed_at"] if latest_rows else None,
        )

    def save_execution_decision_review_record(self, item: ExecutionDecisionReviewRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO execution_decision_review_records
                (execution_decision_review_id, market_id, decision_id, candidate_id,
                 command_review_id, shadow_evaluation_id, execution_mode, action,
                 position_size, expected_cost, risk_status, execution_status,
                 review_status, approval_status, gate_status, recommendation,
                 approval_window_valid, approval_valid_until, reviewed_at,
                 raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.execution_decision_review_id,
                    item.market_id,
                    item.decision_id,
                    item.candidate_id,
                    item.command_review_id,
                    item.shadow_evaluation_id,
                    item.execution_mode,
                    item.action,
                    item.position_size,
                    item.expected_cost,
                    item.risk_status,
                    item.execution_status,
                    item.review_status.value if hasattr(item.review_status, "value") else str(item.review_status),
                    item.approval_status.value if hasattr(item.approval_status, "value") else str(item.approval_status),
                    item.gate_status.value if hasattr(item.gate_status, "value") else str(item.gate_status),
                    item.recommendation.value if hasattr(item.recommendation, "value") else str(item.recommendation),
                    None if item.approval_window_valid is None else int(item.approval_window_valid),
                    item.approval_valid_until,
                    item.reviewed_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def list_execution_decision_review_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        gate_status: str | None = None,
        execution_status: str | None = None,
        execution_mode: str | None = None,
    ) -> list[dict]:
        clauses = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if review_status:
            clauses.append("review_status = ?")
            params.append(review_status)
        if approval_status:
            clauses.append("approval_status = ?")
            params.append(approval_status)
        if gate_status:
            clauses.append("gate_status = ?")
            params.append(gate_status)
        if execution_status:
            clauses.append("execution_status = ?")
            params.append(execution_status)
        if execution_mode:
            clauses.append("execution_mode = ?")
            params.append(execution_mode)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM execution_decision_review_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._parse_execution_decision_review_row(row) for row in rows]

    def get_latest_execution_decision_review_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM execution_decision_review_records
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_execution_decision_review_row(row)

    def get_execution_decision_review_by_id(self, execution_decision_review_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM execution_decision_review_records
                WHERE execution_decision_review_id = ?
                LIMIT 1
                """,
                (execution_decision_review_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_execution_decision_review_row(row)

    def get_execution_decision_review_bundle(
        self,
        market_id: str,
        limit: int = 100,
    ) -> ExecutionDecisionReviewBundle:
        return ExecutionDecisionReviewBundle(
            market_id=market_id,
            execution_decision_reviews=[
                ExecutionDecisionReviewRecord(**item)
                for item in self.list_execution_decision_review_records(market_id=market_id, limit=limit)
            ],
        )

    def get_execution_decision_review_summary(self) -> ExecutionDecisionReviewSummary:
        with get_connection(self.db_path) as conn:
            total_reviews = conn.execute(
                "SELECT COUNT(*) AS count FROM execution_decision_review_records"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM execution_decision_review_records
                GROUP BY market_id
                """
            ).fetchall()
            review_rows = conn.execute(
                """
                SELECT review_status, COUNT(*) AS count
                FROM execution_decision_review_records
                GROUP BY review_status
                """
            ).fetchall()
            approval_rows = conn.execute(
                """
                SELECT approval_status, COUNT(*) AS count
                FROM execution_decision_review_records
                GROUP BY approval_status
                """
            ).fetchall()
            gate_rows = conn.execute(
                """
                SELECT gate_status, COUNT(*) AS count
                FROM execution_decision_review_records
                GROUP BY gate_status
                """
            ).fetchall()
            execution_status_rows = conn.execute(
                """
                SELECT execution_status, COUNT(*) AS count
                FROM execution_decision_review_records
                GROUP BY execution_status
                """
            ).fetchall()
            execution_mode_rows = conn.execute(
                """
                SELECT execution_mode, COUNT(*) AS count
                FROM execution_decision_review_records
                GROUP BY execution_mode
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT reviewed_at
                FROM execution_decision_review_records
                ORDER BY reviewed_at DESC
                LIMIT 1
                """
            ).fetchall()
        return ExecutionDecisionReviewSummary(
            execution_decision_reviews=int(total_reviews or 0),
            unique_markets=len(unique_rows),
            by_review_status={
                str(row["review_status"]): int(row["count"] or 0) for row in review_rows
            },
            by_approval_status={
                str(row["approval_status"]): int(row["count"] or 0) for row in approval_rows
            },
            by_gate_status={
                str(row["gate_status"]): int(row["count"] or 0) for row in gate_rows
            },
            by_execution_status={
                str(row["execution_status"]): int(row["count"] or 0)
                for row in execution_status_rows
            },
            by_execution_mode={
                str(row["execution_mode"]): int(row["count"] or 0)
                for row in execution_mode_rows
            },
            latest_reviewed_at=latest_rows[0]["reviewed_at"] if latest_rows else None,
        )

    def save_execution_queue_review_record(self, item: ExecutionQueueReviewRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO execution_queue_review_records
                (execution_queue_review_id, market_id, decision_id, candidate_id,
                 command_review_id, execution_decision_review_id, shadow_evaluation_id,
                 execution_mode, action, position_size, expected_cost, risk_status,
                 execution_status, review_status, approval_status, gate_status,
                 recommendation, approval_window_valid, approval_valid_until, reviewed_at,
                 raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.execution_queue_review_id,
                    item.market_id,
                    item.decision_id,
                    item.candidate_id,
                    item.command_review_id,
                    item.execution_decision_review_id,
                    item.shadow_evaluation_id,
                    item.execution_mode,
                    item.action,
                    item.position_size,
                    item.expected_cost,
                    item.risk_status,
                    item.execution_status,
                    item.review_status.value if hasattr(item.review_status, "value") else str(item.review_status),
                    item.approval_status.value if hasattr(item.approval_status, "value") else str(item.approval_status),
                    item.gate_status.value if hasattr(item.gate_status, "value") else str(item.gate_status),
                    item.recommendation.value if hasattr(item.recommendation, "value") else str(item.recommendation),
                    None if item.approval_window_valid is None else int(item.approval_window_valid),
                    item.approval_valid_until,
                    item.reviewed_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def list_execution_queue_review_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        gate_status: str | None = None,
        execution_status: str | None = None,
        execution_mode: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if review_status:
            clauses.append("review_status = ?")
            params.append(review_status)
        if approval_status:
            clauses.append("approval_status = ?")
            params.append(approval_status)
        if gate_status:
            clauses.append("gate_status = ?")
            params.append(gate_status)
        if execution_status:
            clauses.append("execution_status = ?")
            params.append(execution_status)
        if execution_mode:
            clauses.append("execution_mode = ?")
            params.append(execution_mode)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM execution_queue_review_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._parse_execution_queue_review_row(row) for row in rows]

    def get_latest_execution_queue_review_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM execution_queue_review_records
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_execution_queue_review_row(row)

    def get_execution_queue_review_by_id(self, execution_queue_review_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM execution_queue_review_records
                WHERE execution_queue_review_id = ?
                LIMIT 1
                """,
                (execution_queue_review_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_execution_queue_review_row(row)

    def get_execution_queue_review_bundle(self, market_id: str, limit: int = 100) -> ExecutionQueueReviewBundle:
        return ExecutionQueueReviewBundle(
            market_id=market_id,
            execution_queue_reviews=[
                ExecutionQueueReviewRecord(**item)
                for item in self.list_execution_queue_review_records(market_id=market_id, limit=limit)
            ],
        )

    def get_execution_queue_review_summary(self) -> ExecutionQueueReviewSummary:
        with get_connection(self.db_path) as conn:
            total_reviews = conn.execute(
                "SELECT COUNT(*) AS count FROM execution_queue_review_records"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM execution_queue_review_records
                GROUP BY market_id
                """
            ).fetchall()
            review_rows = conn.execute(
                """
                SELECT review_status, COUNT(*) AS count
                FROM execution_queue_review_records
                GROUP BY review_status
                """
            ).fetchall()
            approval_rows = conn.execute(
                """
                SELECT approval_status, COUNT(*) AS count
                FROM execution_queue_review_records
                GROUP BY approval_status
                """
            ).fetchall()
            gate_rows = conn.execute(
                """
                SELECT gate_status, COUNT(*) AS count
                FROM execution_queue_review_records
                GROUP BY gate_status
                """
            ).fetchall()
            execution_status_rows = conn.execute(
                """
                SELECT execution_status, COUNT(*) AS count
                FROM execution_queue_review_records
                GROUP BY execution_status
                """
            ).fetchall()
            execution_mode_rows = conn.execute(
                """
                SELECT execution_mode, COUNT(*) AS count
                FROM execution_queue_review_records
                GROUP BY execution_mode
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT reviewed_at
                FROM execution_queue_review_records
                ORDER BY reviewed_at DESC
                LIMIT 1
                """
            ).fetchall()
        return ExecutionQueueReviewSummary(
            execution_queue_reviews=int(total_reviews or 0),
            unique_markets=len(unique_rows),
            by_review_status={
                str(row["review_status"]): int(row["count"] or 0) for row in review_rows
            },
            by_approval_status={
                str(row["approval_status"]): int(row["count"] or 0) for row in approval_rows
            },
            by_gate_status={
                str(row["gate_status"]): int(row["count"] or 0) for row in gate_rows
            },
            by_execution_status={
                str(row["execution_status"]): int(row["count"] or 0)
                for row in execution_status_rows
            },
            by_execution_mode={
                str(row["execution_mode"]): int(row["count"] or 0)
                for row in execution_mode_rows
            },
            latest_reviewed_at=latest_rows[0]["reviewed_at"] if latest_rows else None,
        )

    def save_approval_window_review_record(self, item: ApprovalWindowReviewRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO approval_window_review_records
                (approval_window_review_id, market_id, decision_id, candidate_id,
                 command_review_id, execution_decision_review_id, execution_queue_review_id,
                 approval_status, approval_window_valid, approval_valid_until,
                 review_status, window_state, recommendation, reviewed_at,
                 raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.approval_window_review_id,
                    item.market_id,
                    item.decision_id,
                    item.candidate_id,
                    item.command_review_id,
                    item.execution_decision_review_id,
                    item.execution_queue_review_id,
                    item.approval_status,
                    None if item.approval_window_valid is None else int(item.approval_window_valid),
                    item.approval_valid_until,
                    item.review_status.value if hasattr(item.review_status, "value") else str(item.review_status),
                    item.window_state.value if hasattr(item.window_state, "value") else str(item.window_state),
                    item.recommendation.value if hasattr(item.recommendation, "value") else str(item.recommendation),
                    item.reviewed_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_activation_readiness_review_record(self, item: ActivationReadinessReviewRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO activation_readiness_review_records
                (activation_readiness_review_id, market_id, decision_id, candidate_id,
                 command_review_id, execution_decision_review_id, execution_queue_review_id,
                 approval_window_review_id, approval_status, window_state, review_status,
                 readiness_status, recommendation, reviewed_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.activation_readiness_review_id,
                    item.market_id,
                    item.decision_id,
                    item.candidate_id,
                    item.command_review_id,
                    item.execution_decision_review_id,
                    item.execution_queue_review_id,
                    item.approval_window_review_id,
                    item.approval_status,
                    item.window_state,
                    item.review_status,
                    item.readiness_status.value if hasattr(item.readiness_status, "value") else str(item.readiness_status),
                    item.recommendation.value if hasattr(item.recommendation, "value") else str(item.recommendation),
                    item.reviewed_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_activation_authorization_review_record(self, item: ActivationAuthorizationReviewRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO activation_authorization_review_records
                (activation_authorization_review_id, market_id, decision_id, candidate_id,
                 command_review_id, execution_decision_review_id, execution_queue_review_id,
                 approval_window_review_id, activation_readiness_review_id, approval_status,
                 window_state, readiness_status, authorization_status, recommendation,
                 reviewed_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.activation_authorization_review_id,
                    item.market_id,
                    item.decision_id,
                    item.candidate_id,
                    item.command_review_id,
                    item.execution_decision_review_id,
                    item.execution_queue_review_id,
                    item.approval_window_review_id,
                    item.activation_readiness_review_id,
                    item.approval_status,
                    item.window_state,
                    item.readiness_status,
                    item.authorization_status.value
                    if hasattr(item.authorization_status, "value")
                    else str(item.authorization_status),
                    item.recommendation.value if hasattr(item.recommendation, "value") else str(item.recommendation),
                    item.reviewed_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def list_approval_window_review_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        review_status: str | None = None,
        window_state: str | None = None,
        approval_status: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if review_status:
            clauses.append("review_status = ?")
            params.append(review_status)
        if window_state:
            clauses.append("window_state = ?")
            params.append(window_state)
        if approval_status:
            clauses.append("approval_status = ?")
            params.append(approval_status)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM approval_window_review_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._parse_approval_window_review_row(row) for row in rows]

    def list_activation_readiness_review_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        readiness_status: str | None = None,
        recommendation: str | None = None,
        approval_status: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if readiness_status:
            clauses.append("readiness_status = ?")
            params.append(readiness_status)
        if recommendation:
            clauses.append("recommendation = ?")
            params.append(recommendation)
        if approval_status:
            clauses.append("approval_status = ?")
            params.append(approval_status)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM activation_readiness_review_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._parse_activation_readiness_review_row(row) for row in rows]

    def list_activation_authorization_review_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        authorization_status: str | None = None,
        recommendation: str | None = None,
        approval_status: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if authorization_status:
            clauses.append("authorization_status = ?")
            params.append(authorization_status)
        if recommendation:
            clauses.append("recommendation = ?")
            params.append(recommendation)
        if approval_status:
            clauses.append("approval_status = ?")
            params.append(approval_status)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM activation_authorization_review_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._parse_activation_authorization_review_row(row) for row in rows]

    def get_latest_approval_window_review_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM approval_window_review_records
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_approval_window_review_row(row)

    def get_latest_activation_readiness_review_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM activation_readiness_review_records
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_activation_readiness_review_row(row)

    def get_latest_activation_authorization_review_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM activation_authorization_review_records
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_activation_authorization_review_row(row)

    def get_approval_window_review_by_id(self, approval_window_review_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM approval_window_review_records
                WHERE approval_window_review_id = ?
                LIMIT 1
                """,
                (approval_window_review_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_approval_window_review_row(row)

    def get_activation_readiness_review_by_id(self, activation_readiness_review_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM activation_readiness_review_records
                WHERE activation_readiness_review_id = ?
                LIMIT 1
                """,
                (activation_readiness_review_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_activation_readiness_review_row(row)

    def get_activation_authorization_review_by_id(self, activation_authorization_review_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM activation_authorization_review_records
                WHERE activation_authorization_review_id = ?
                LIMIT 1
                """,
                (activation_authorization_review_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_activation_authorization_review_row(row)

    def get_approval_window_review_bundle(self, market_id: str, limit: int = 100) -> ApprovalWindowReviewBundle:
        return ApprovalWindowReviewBundle(
            market_id=market_id,
            approval_window_reviews=[
                ApprovalWindowReviewRecord(**item)
                for item in self.list_approval_window_review_records(market_id=market_id, limit=limit)
            ],
        )

    def get_activation_readiness_review_bundle(
        self,
        market_id: str,
        limit: int = 100,
    ) -> ActivationReadinessReviewBundle:
        return ActivationReadinessReviewBundle(
            market_id=market_id,
            activation_readiness_reviews=[
                ActivationReadinessReviewRecord(**item)
                for item in self.list_activation_readiness_review_records(market_id=market_id, limit=limit)
            ],
        )

    def get_activation_authorization_review_bundle(
        self,
        market_id: str,
        limit: int = 100,
    ) -> ActivationAuthorizationReviewBundle:
        return ActivationAuthorizationReviewBundle(
            market_id=market_id,
            activation_authorization_reviews=[
                ActivationAuthorizationReviewRecord(**item)
                for item in self.list_activation_authorization_review_records(market_id=market_id, limit=limit)
            ],
        )

    def get_approval_window_review_summary(self) -> ApprovalWindowReviewSummary:
        with get_connection(self.db_path) as conn:
            total_reviews = conn.execute(
                "SELECT COUNT(*) AS count FROM approval_window_review_records"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM approval_window_review_records
                GROUP BY market_id
                """
            ).fetchall()
            review_rows = conn.execute(
                """
                SELECT review_status, COUNT(*) AS count
                FROM approval_window_review_records
                GROUP BY review_status
                """
            ).fetchall()
            window_rows = conn.execute(
                """
                SELECT window_state, COUNT(*) AS count
                FROM approval_window_review_records
                GROUP BY window_state
                """
            ).fetchall()
            approval_rows = conn.execute(
                """
                SELECT approval_status, COUNT(*) AS count
                FROM approval_window_review_records
                GROUP BY approval_status
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT reviewed_at
                FROM approval_window_review_records
                ORDER BY reviewed_at DESC
                LIMIT 1
                """
            ).fetchall()
        return ApprovalWindowReviewSummary(
            approval_window_reviews=int(total_reviews or 0),
            unique_markets=len(unique_rows),
            by_review_status={
                str(row["review_status"]): int(row["count"] or 0) for row in review_rows
            },
            by_window_state={
                str(row["window_state"]): int(row["count"] or 0) for row in window_rows
            },
            by_approval_status={
                str(row["approval_status"]): int(row["count"] or 0) for row in approval_rows
            },
            latest_reviewed_at=latest_rows[0]["reviewed_at"] if latest_rows else None,
        )

    def get_activation_readiness_review_summary(self) -> ActivationReadinessReviewSummary:
        with get_connection(self.db_path) as conn:
            total_reviews = conn.execute(
                "SELECT COUNT(*) AS count FROM activation_readiness_review_records"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM activation_readiness_review_records
                GROUP BY market_id
                """
            ).fetchall()
            readiness_rows = conn.execute(
                """
                SELECT readiness_status, COUNT(*) AS count
                FROM activation_readiness_review_records
                GROUP BY readiness_status
                """
            ).fetchall()
            recommendation_rows = conn.execute(
                """
                SELECT recommendation, COUNT(*) AS count
                FROM activation_readiness_review_records
                GROUP BY recommendation
                """
            ).fetchall()
            approval_rows = conn.execute(
                """
                SELECT approval_status, COUNT(*) AS count
                FROM activation_readiness_review_records
                GROUP BY approval_status
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT reviewed_at
                FROM activation_readiness_review_records
                ORDER BY reviewed_at DESC
                LIMIT 1
                """
            ).fetchall()
        return ActivationReadinessReviewSummary(
            activation_readiness_reviews=int(total_reviews or 0),
            unique_markets=len(unique_rows),
            by_readiness_status={
                str(row["readiness_status"]): int(row["count"] or 0) for row in readiness_rows
            },
            by_recommendation={
                str(row["recommendation"]): int(row["count"] or 0) for row in recommendation_rows
            },
            by_approval_status={
                str(row["approval_status"]): int(row["count"] or 0) for row in approval_rows
            },
            latest_reviewed_at=latest_rows[0]["reviewed_at"] if latest_rows else None,
        )

    def get_activation_authorization_review_summary(self) -> ActivationAuthorizationReviewSummary:
        with get_connection(self.db_path) as conn:
            total_reviews = conn.execute(
                "SELECT COUNT(*) AS count FROM activation_authorization_review_records"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM activation_authorization_review_records
                GROUP BY market_id
                """
            ).fetchall()
            authorization_rows = conn.execute(
                """
                SELECT authorization_status, COUNT(*) AS count
                FROM activation_authorization_review_records
                GROUP BY authorization_status
                """
            ).fetchall()
            recommendation_rows = conn.execute(
                """
                SELECT recommendation, COUNT(*) AS count
                FROM activation_authorization_review_records
                GROUP BY recommendation
                """
            ).fetchall()
            approval_rows = conn.execute(
                """
                SELECT approval_status, COUNT(*) AS count
                FROM activation_authorization_review_records
                GROUP BY approval_status
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT reviewed_at
                FROM activation_authorization_review_records
                ORDER BY reviewed_at DESC
                LIMIT 1
                """
            ).fetchall()
        return ActivationAuthorizationReviewSummary(
            activation_authorization_reviews=int(total_reviews or 0),
            unique_markets=len(unique_rows),
            by_authorization_status={
                str(row["authorization_status"]): int(row["count"] or 0) for row in authorization_rows
            },
            by_recommendation={
                str(row["recommendation"]): int(row["count"] or 0) for row in recommendation_rows
            },
            by_approval_status={
                str(row["approval_status"]): int(row["count"] or 0) for row in approval_rows
            },
            latest_reviewed_at=latest_rows[0]["reviewed_at"] if latest_rows else None,
        )

    def list_distinct_market_ids_for_calibration_memory(self) -> list[str]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT market_id FROM market_snapshot_archive
                UNION
                SELECT market_id FROM weather_view_archive
                UNION
                SELECT market_id FROM weather_forecast_archive
                UNION
                SELECT market_id FROM probability_engine_runs
                UNION
                SELECT market_id FROM outcome_resolution_records
                ORDER BY market_id ASC
                """
            ).fetchall()
        return [str(row["market_id"]) for row in rows if row["market_id"] is not None]

    def list_distinct_market_ids_for_execution_decision_review(self) -> list[str]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT market_id FROM opportunity_candidates
                UNION
                SELECT oc.market_id
                FROM execution_decisions ed
                INNER JOIN opportunity_candidates oc
                  ON oc.candidate_id = ed.candidate_id
                UNION
                SELECT market_id FROM command_review_records
                UNION
                SELECT market_id FROM market_snapshot_archive
                UNION
                SELECT market_id FROM weather_view_archive
                UNION
                SELECT market_id FROM weather_forecast_archive
                UNION
                SELECT market_id FROM probability_engine_runs
                UNION
                SELECT market_id FROM outcome_resolution_records
                UNION
                SELECT market_id FROM calibration_samples
                UNION
                SELECT market_id FROM backtest_memory_records
                UNION
                SELECT market_id FROM deb_shadow_runs
                UNION
                SELECT market_id FROM emos_shadow_runs
                UNION
                SELECT market_id FROM shadow_engine_evaluations
                ORDER BY market_id ASC
                """
            ).fetchall()
        return [str(row["market_id"]) for row in rows if row["market_id"] is not None]

    def list_distinct_market_ids_for_execution_queue_review(self) -> list[str]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT market_id FROM opportunity_candidates
                UNION
                SELECT oc.market_id
                FROM execution_decisions ed
                INNER JOIN opportunity_candidates oc
                  ON oc.candidate_id = ed.candidate_id
                UNION
                SELECT market_id FROM command_review_records
                UNION
                SELECT market_id FROM execution_decision_review_records
                UNION
                SELECT market_id FROM market_snapshot_archive
                UNION
                SELECT market_id FROM weather_view_archive
                UNION
                SELECT market_id FROM weather_forecast_archive
                UNION
                SELECT market_id FROM probability_engine_runs
                UNION
                SELECT market_id FROM outcome_resolution_records
                UNION
                SELECT market_id FROM calibration_samples
                UNION
                SELECT market_id FROM backtest_memory_records
                UNION
                SELECT market_id FROM deb_shadow_runs
                UNION
                SELECT market_id FROM emos_shadow_runs
                UNION
                SELECT market_id FROM shadow_engine_evaluations
                ORDER BY market_id ASC
                """
            ).fetchall()
        return [str(row["market_id"]) for row in rows if row["market_id"] is not None]

    def list_distinct_market_ids_for_approval_window_review(self) -> list[str]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT market_id FROM opportunity_candidates
                UNION
                SELECT oc.market_id
                FROM execution_decisions ed
                INNER JOIN opportunity_candidates oc
                  ON oc.candidate_id = ed.candidate_id
                UNION
                SELECT market_id FROM command_review_records
                UNION
                SELECT market_id FROM execution_decision_review_records
                UNION
                SELECT market_id FROM execution_queue_review_records
                UNION
                SELECT market_id FROM market_snapshot_archive
                UNION
                SELECT market_id FROM weather_view_archive
                UNION
                SELECT market_id FROM weather_forecast_archive
                UNION
                SELECT market_id FROM probability_engine_runs
                UNION
                SELECT market_id FROM outcome_resolution_records
                UNION
                SELECT market_id FROM calibration_samples
                UNION
                SELECT market_id FROM backtest_memory_records
                UNION
                SELECT market_id FROM deb_shadow_runs
                UNION
                SELECT market_id FROM emos_shadow_runs
                UNION
                SELECT market_id FROM shadow_engine_evaluations
                ORDER BY market_id ASC
                """
            ).fetchall()
        return [str(row["market_id"]) for row in rows if row["market_id"] is not None]

    def list_distinct_market_ids_for_activation_readiness_review(self) -> list[str]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT market_id FROM opportunity_candidates
                UNION
                SELECT oc.market_id
                FROM execution_decisions ed
                INNER JOIN opportunity_candidates oc
                  ON oc.candidate_id = ed.candidate_id
                UNION
                SELECT market_id FROM command_review_records
                UNION
                SELECT market_id FROM execution_decision_review_records
                UNION
                SELECT market_id FROM execution_queue_review_records
                UNION
                SELECT market_id FROM approval_window_review_records
                UNION
                SELECT market_id FROM market_snapshot_archive
                UNION
                SELECT market_id FROM weather_view_archive
                UNION
                SELECT market_id FROM weather_forecast_archive
                UNION
                SELECT market_id FROM probability_engine_runs
                UNION
                SELECT market_id FROM outcome_resolution_records
                UNION
                SELECT market_id FROM calibration_samples
                UNION
                SELECT market_id FROM backtest_memory_records
                UNION
                SELECT market_id FROM deb_shadow_runs
                UNION
                SELECT market_id FROM emos_shadow_runs
                UNION
                SELECT market_id FROM shadow_engine_evaluations
                ORDER BY market_id ASC
                """
            ).fetchall()
        return [str(row["market_id"]) for row in rows if row["market_id"] is not None]

    def list_distinct_market_ids_for_activation_authorization_review(self) -> list[str]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT market_id FROM opportunity_candidates
                UNION
                SELECT oc.market_id
                FROM execution_decisions ed
                INNER JOIN opportunity_candidates oc
                  ON oc.candidate_id = ed.candidate_id
                UNION
                SELECT market_id FROM command_review_records
                UNION
                SELECT market_id FROM execution_decision_review_records
                UNION
                SELECT market_id FROM execution_queue_review_records
                UNION
                SELECT market_id FROM approval_window_review_records
                UNION
                SELECT market_id FROM activation_readiness_review_records
                UNION
                SELECT market_id FROM market_snapshot_archive
                UNION
                SELECT market_id FROM weather_view_archive
                UNION
                SELECT market_id FROM weather_forecast_archive
                UNION
                SELECT market_id FROM probability_engine_runs
                UNION
                SELECT market_id FROM outcome_resolution_records
                UNION
                SELECT market_id FROM calibration_samples
                UNION
                SELECT market_id FROM backtest_memory_records
                UNION
                SELECT market_id FROM deb_shadow_runs
                UNION
                SELECT market_id FROM emos_shadow_runs
                UNION
                SELECT market_id FROM shadow_engine_evaluations
                ORDER BY market_id ASC
                """
            ).fetchall()
        return [str(row["market_id"]) for row in rows if row["market_id"] is not None]

    def get_latest_market_snapshot_archive_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM market_snapshot_archive
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_market_snapshot_archive_row(row)

    def get_latest_weather_view_archive_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM weather_view_archive
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_weather_view_archive_row(row)

    def get_latest_weather_forecast_archive_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM weather_forecast_archive
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_weather_forecast_archive_row(row)

    def get_latest_probability_engine_run_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM probability_engine_runs
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_probability_engine_run_row(row)

    def get_latest_outcome_resolution_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM outcome_resolution_records
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_outcome_resolution_record_row(row)

    def _parse_calibration_sample_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        value = item.get("model_beats_market")
        item["model_beats_market"] = None if value is None else bool(value)
        item["calibrationSampleId"] = item["calibration_sample_id"]
        item["marketId"] = item["market_id"]
        item["snapshotArchiveId"] = item["snapshot_archive_id"]
        item["weatherViewArchiveId"] = item["weather_view_archive_id"]
        item["weatherForecastArchiveId"] = item["weather_forecast_archive_id"]
        item["probabilityRunId"] = item["probability_run_id"]
        item["outcomeResolutionId"] = item["outcome_resolution_id"]
        item["engineId"] = item["engine_id"]
        item["marketProbability"] = item["market_probability"]
        item["modelProbability"] = item["model_probability"]
        item["actualOutcomeValue"] = item["actual_outcome_value"]
        item["modelBrierScore"] = item["model_brier_score"]
        item["marketBrierScore"] = item["market_brier_score"]
        item["modelAbsoluteError"] = item["model_absolute_error"]
        item["marketAbsoluteError"] = item["market_absolute_error"]
        item["modelBeatsMarket"] = item["model_beats_market"]
        item["resolvedOutcome"] = item["resolved_outcome"]
        item["sampleEligibility"] = item["sample_eligibility"]
        item["sampleStatus"] = item["sample_status"]
        item["sampledAt"] = item["sampled_at"]
        return item

    def _parse_backtest_memory_record_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["backtestMemoryId"] = item["backtest_memory_id"]
        item["marketId"] = item["market_id"]
        item["snapshotArchiveId"] = item["snapshot_archive_id"]
        item["weatherViewArchiveId"] = item["weather_view_archive_id"]
        item["weatherForecastArchiveId"] = item["weather_forecast_archive_id"]
        item["probabilityRunId"] = item["probability_run_id"]
        item["outcomeResolutionId"] = item["outcome_resolution_id"]
        item["engineId"] = item["engine_id"]
        item["marketProbability"] = item["market_probability"]
        item["modelProbability"] = item["model_probability"]
        item["actualOutcomeValue"] = item["actual_outcome_value"]
        item["edge"] = item["edge"]
        item["edgeThreshold"] = item["edge_threshold"]
        item["hypotheticalAction"] = item["hypothetical_action"]
        item["hypotheticalResult"] = item["hypothetical_result"]
        item["sampleEligibility"] = item["sample_eligibility"]
        item["backtestStatus"] = item["backtest_status"]
        item["sampledAt"] = item["sampled_at"]
        return item

    def _parse_deb_shadow_run_row(self, row) -> dict:
        item = dict(row)
        item["warnings"] = json.loads(item.get("warnings_json") or "[]")
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["debShadowRunId"] = item["deb_shadow_run_id"]
        item["marketId"] = item["market_id"]
        item["calibrationSampleId"] = item["calibration_sample_id"]
        item["engineId"] = item["engine_id"]
        item["baseProbability"] = item["base_probability"]
        item["debProbability"] = item["deb_probability"]
        item["biasAdjustment"] = item["bias_adjustment"]
        item["calibrationGap"] = item["calibration_gap"]
        item["sampleCount"] = item["sample_count"]
        item["runStatus"] = item["run_status"]
        return item

    def _parse_deb_shadow_diagnostic_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["debShadowDiagnosticId"] = item["deb_shadow_diagnostic_id"]
        item["debShadowRunId"] = item["deb_shadow_run_id"]
        item["marketId"] = item["market_id"]
        item["calibrationSampleId"] = item["calibration_sample_id"]
        item["sampleCount"] = item["sample_count"]
        item["avgModelBrierScore"] = item["avg_model_brier_score"]
        item["avgMarketBrierScore"] = item["avg_market_brier_score"]
        item["avgModelEdge"] = item["avg_model_edge"]
        item["avgProbabilityError"] = item["avg_probability_error"]
        item["adjustmentWeight"] = item["adjustment_weight"]
        return item

    def _parse_emos_shadow_run_row(self, row) -> dict:
        item = dict(row)
        item["warnings"] = json.loads(item.get("warnings_json") or "[]")
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["emosShadowRunId"] = item["emos_shadow_run_id"]
        item["marketId"] = item["market_id"]
        item["calibrationSampleId"] = item["calibration_sample_id"]
        item["engineId"] = item["engine_id"]
        item["baseProbability"] = item["base_probability"]
        item["emosProbability"] = item["emos_probability"]
        item["locationAdjustment"] = item["location_adjustment"]
        item["scaleAdjustment"] = item["scale_adjustment"]
        item["sampleCount"] = item["sample_count"]
        item["runStatus"] = item["run_status"]
        return item

    def _parse_emos_shadow_diagnostic_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["emosShadowDiagnosticId"] = item["emos_shadow_diagnostic_id"]
        item["emosShadowRunId"] = item["emos_shadow_run_id"]
        item["marketId"] = item["market_id"]
        item["calibrationSampleId"] = item["calibration_sample_id"]
        item["sampleCount"] = item["sample_count"]
        item["avgModelBrierScore"] = item["avg_model_brier_score"]
        item["avgMarketBrierScore"] = item["avg_market_brier_score"]
        item["avgProbabilityError"] = item["avg_probability_error"]
        item["avgAbsoluteError"] = item["avg_absolute_error"]
        item["locationWeight"] = item["location_weight"]
        item["scaleWeight"] = item["scale_weight"]
        return item

    def _parse_shadow_engine_evaluation_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["shadowEvaluationId"] = item["shadow_evaluation_id"]
        item["marketId"] = item["market_id"]
        item["calibrationSampleId"] = item["calibration_sample_id"]
        item["outcomeResolutionId"] = item["outcome_resolution_id"]
        item["primaryEngineId"] = item["primary_engine_id"]
        item["debEngineId"] = item["deb_engine_id"]
        item["emosEngineId"] = item["emos_engine_id"]
        item["primaryProbability"] = item["primary_probability"]
        item["debProbability"] = item["deb_probability"]
        item["emosProbability"] = item["emos_probability"]
        item["actualOutcomeValue"] = item["actual_outcome_value"]
        item["primaryBrierScore"] = item["primary_brier_score"]
        item["debBrierScore"] = item["deb_brier_score"]
        item["emosBrierScore"] = item["emos_brier_score"]
        item["primaryAbsoluteError"] = item["primary_absolute_error"]
        item["debAbsoluteError"] = item["deb_absolute_error"]
        item["emosAbsoluteError"] = item["emos_absolute_error"]
        item["bestEngine"] = item["best_engine"]
        item["evaluationStatus"] = item["evaluation_status"]
        return item

    def _parse_command_review_record_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        value = item.get("approval_window_valid")
        item["approval_window_valid"] = None if value is None else bool(value)
        item["commandReviewId"] = item["command_review_id"]
        item["marketId"] = item["market_id"]
        item["commandName"] = item["command_name"]
        item["sourcePage"] = item["source_page"]
        item["targetPage"] = item["target_page"]
        item["commandPath"] = item["command_path"]
        item["reviewStatus"] = item["review_status"]
        item["approvalStatus"] = item["approval_status"]
        item["recommendation"] = item["recommendation"]
        item["gateStatus"] = item["gate_status"]
        item["activeEngineId"] = item["active_engine_id"]
        item["executionMode"] = item["execution_mode"]
        item["riskStatus"] = item["risk_status"]
        item["approvalWindowValid"] = item["approval_window_valid"]
        item["approvalValidUntil"] = item["approval_valid_until"]
        item["marketSnapshotArchiveId"] = item["market_snapshot_archive_id"]
        item["weatherViewArchiveId"] = item["weather_view_archive_id"]
        item["weatherForecastArchiveId"] = item["weather_forecast_archive_id"]
        item["probabilityRunId"] = item["probability_run_id"]
        item["outcomeResolutionId"] = item["outcome_resolution_id"]
        item["calibrationSampleId"] = item["calibration_sample_id"]
        item["backtestMemoryId"] = item["backtest_memory_id"]
        item["debShadowRunId"] = item["deb_shadow_run_id"]
        item["emosShadowRunId"] = item["emos_shadow_run_id"]
        item["shadowEvaluationId"] = item["shadow_evaluation_id"]
        item["reviewedAt"] = item["reviewed_at"]
        return item

    def save_market_outcome_record(self, item: MarketOutcomeRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO market_outcome_records
                (market_outcome_id, market_id, question, source, resolved_outcome,
                 resolution_status, resolved_value, resolved_at, notes, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.market_outcome_id,
                    item.market_id,
                    item.question,
                    item.source.value if hasattr(item.source, "value") else str(item.source),
                    item.resolved_outcome.value
                    if hasattr(item.resolved_outcome, "value")
                    else str(item.resolved_outcome),
                    item.resolution_status.value
                    if hasattr(item.resolution_status, "value")
                    else str(item.resolution_status),
                    item.resolved_value,
                    item.resolved_at,
                    item.notes,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_weather_actual_record(self, item: WeatherActualRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO weather_actual_records
                (weather_actual_id, market_id, city, target_date, source, metric,
                 unit, actual_value, observed_at, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.weather_actual_id,
                    item.market_id,
                    item.city,
                    item.target_date,
                    item.source.value if hasattr(item.source, "value") else str(item.source),
                    item.metric.value if hasattr(item.metric, "value") else str(item.metric),
                    item.unit.value if hasattr(item.unit, "value") else str(item.unit),
                    item.actual_value,
                    item.observed_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def save_outcome_resolution_record(self, item: OutcomeResolutionRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO outcome_resolution_records
                (outcome_resolution_id, market_id, market_outcome_id, weather_actual_id,
                 weather_view_id, threshold, direction, actual_value, resolved_outcome,
                 resolution_status, resolution_source, resolved_at, notes, raw_payload_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.outcome_resolution_id,
                    item.market_id,
                    item.market_outcome_id,
                    item.weather_actual_id,
                    item.weather_view_id,
                    item.threshold,
                    item.direction.value if hasattr(item.direction, "value") else str(item.direction),
                    item.actual_value,
                    item.resolved_outcome.value
                    if hasattr(item.resolved_outcome, "value")
                    else str(item.resolved_outcome),
                    item.resolution_status.value
                    if hasattr(item.resolution_status, "value")
                    else str(item.resolution_status),
                    item.resolution_source.value
                    if hasattr(item.resolution_source, "value")
                    else str(item.resolution_source),
                    item.resolved_at,
                    item.notes,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                ),
            )

    def list_market_outcome_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        resolution_status: str | ResolutionStatus | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if resolution_status:
            clauses.append("resolution_status = ?")
            params.append(
                resolution_status.value
                if hasattr(resolution_status, "value")
                else str(resolution_status)
            )
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM market_outcome_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_market_outcome_record_row(row) for row in rows]

    def list_weather_actual_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        source: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if source:
            clauses.append("source = ?")
            params.append(source)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM weather_actual_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_weather_actual_record_row(row) for row in rows]

    def list_outcome_resolution_records(
        self,
        limit: int = 100,
        market_id: str | None = None,
        resolution_status: str | ResolutionStatus | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if market_id:
            clauses.append("market_id = ?")
            params.append(market_id)
        if resolution_status:
            clauses.append("resolution_status = ?")
            params.append(
                resolution_status.value
                if hasattr(resolution_status, "value")
                else str(resolution_status)
            )
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM outcome_resolution_records
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_outcome_resolution_record_row(row) for row in rows]

    def get_weather_actual_record_by_id(self, weather_actual_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM weather_actual_records
                WHERE weather_actual_id = ?
                LIMIT 1
                """,
                (weather_actual_id,),
            ).fetchone()
        if not row:
            return None
        return self._parse_weather_actual_record_row(row)

    def get_outcome_bundle(self, market_id: str, limit: int = 100) -> OutcomeBundle:
        return OutcomeBundle(
            market_id=market_id,
            markets=[
                MarketOutcomeRecord(**item)
                for item in self.list_market_outcome_records(market_id=market_id, limit=limit)
            ],
            weather_actuals=[
                WeatherActualRecord(**item)
                for item in self.list_weather_actual_records(market_id=market_id, limit=limit)
            ],
            resolutions=[
                OutcomeResolutionRecord(**item)
                for item in self.list_outcome_resolution_records(market_id=market_id, limit=limit)
            ],
        )

    def get_outcome_archive_summary(self) -> OutcomeArchiveSummary:
        with get_connection(self.db_path) as conn:
            outcome_count = conn.execute(
                "SELECT COUNT(*) AS count FROM market_outcome_records"
            ).fetchone()["count"]
            actual_count = conn.execute(
                "SELECT COUNT(*) AS count FROM weather_actual_records"
            ).fetchone()["count"]
            resolution_count = conn.execute(
                "SELECT COUNT(*) AS count FROM outcome_resolution_records"
            ).fetchone()["count"]
            unique_rows = conn.execute(
                """
                SELECT market_id FROM market_outcome_records
                UNION
                SELECT market_id FROM weather_actual_records
                UNION
                SELECT market_id FROM outcome_resolution_records
                """
            ).fetchall()
            status_rows = conn.execute(
                """
                SELECT resolution_status, COUNT(*) AS count
                FROM outcome_resolution_records
                GROUP BY resolution_status
                """
            ).fetchall()
            resolved_rows = conn.execute(
                """
                SELECT resolved_outcome, COUNT(*) AS count
                FROM outcome_resolution_records
                GROUP BY resolved_outcome
                """
            ).fetchall()
            latest_rows = conn.execute(
                """
                SELECT resolved_at FROM market_outcome_records
                UNION ALL
                SELECT observed_at AS resolved_at FROM weather_actual_records
                UNION ALL
                SELECT resolved_at FROM outcome_resolution_records
                ORDER BY resolved_at DESC
                LIMIT 1
                """
            ).fetchall()
        return OutcomeArchiveSummary(
            market_outcome_records=int(outcome_count or 0),
            weather_actual_records=int(actual_count or 0),
            outcome_resolution_records=int(resolution_count or 0),
            unique_markets=len(unique_rows),
            by_resolution_status={
                str(item["resolution_status"]): int(item["count"] or 0) for item in status_rows
            },
            by_resolved_outcome={
                str(item["resolved_outcome"]): int(item["count"] or 0) for item in resolved_rows
            },
            latest_resolved_at=latest_rows[0]["resolved_at"] if latest_rows else None,
        )

    def _parse_market_outcome_record_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["marketOutcomeId"] = item["market_outcome_id"]
        item["marketId"] = item["market_id"]
        item["resolvedOutcome"] = item["resolved_outcome"]
        item["resolutionStatus"] = item["resolution_status"]
        item["resolvedValue"] = item["resolved_value"]
        item["resolvedAt"] = item["resolved_at"]
        return item

    def _parse_weather_actual_record_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["weatherActualId"] = item["weather_actual_id"]
        item["marketId"] = item["market_id"]
        item["targetDate"] = item["target_date"]
        item["actualValue"] = item["actual_value"]
        item["observedAt"] = item["observed_at"]
        return item

    def _parse_outcome_resolution_record_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["outcomeResolutionId"] = item["outcome_resolution_id"]
        item["marketId"] = item["market_id"]
        item["marketOutcomeId"] = item["market_outcome_id"]
        item["weatherActualId"] = item["weather_actual_id"]
        item["weatherViewId"] = item["weather_view_id"]
        item["actualValue"] = item["actual_value"]
        item["resolvedOutcome"] = item["resolved_outcome"]
        item["resolutionStatus"] = item["resolution_status"]
        item["resolutionSource"] = item["resolution_source"]
        item["resolvedAt"] = item["resolved_at"]
        return item

    def save_market_snapshot_archive_record(self, item: MarketSnapshotArchiveRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO market_snapshot_archive
                (snapshot_archive_id, market_id, source, question, yes_price, no_price,
                 liquidity, spread, fetched_at, archived_at, market_source_mode,
                 raw_ref, metadata_json, archive_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.snapshot_archive_id,
                    item.market_id,
                    item.source,
                    item.question,
                    item.yes_price,
                    item.no_price,
                    item.liquidity,
                    item.spread,
                    item.fetched_at,
                    item.archived_at,
                    item.market_source_mode.value
                    if hasattr(item.market_source_mode, "value")
                    else str(item.market_source_mode),
                    item.raw_ref,
                    json.dumps(item.metadata, ensure_ascii=False),
                    item.archive_reason.value
                    if hasattr(item.archive_reason, "value")
                    else str(item.archive_reason),
                ),
            )

    def save_market_snapshot_archive_records(
        self,
        items: list[MarketSnapshotArchiveRecord],
    ) -> None:
        for item in items:
            self.save_market_snapshot_archive_record(item)

    def list_market_snapshot_archive(
        self,
        limit: int = 100,
        source: str | None = None,
        archive_reason: SnapshotArchiveReason | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if source:
            clauses.append("source = ?")
            params.append(source)
        if archive_reason:
            clauses.append("archive_reason = ?")
            params.append(
                archive_reason.value if hasattr(archive_reason, "value") else str(archive_reason)
            )
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM market_snapshot_archive
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_market_snapshot_archive_row(row) for row in rows]

    def get_market_snapshot_series(
        self,
        market_id: str,
        limit: int = 500,
    ) -> MarketSnapshotSeries:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM market_snapshot_archive
                WHERE market_id = ?
                ORDER BY archived_at ASC, id ASC
                LIMIT ?
                """,
                (market_id, limit),
            ).fetchall()
        snapshots = [
            MarketSnapshotArchiveRecord(**self._parse_market_snapshot_archive_row(row))
            for row in rows
        ]
        return MarketSnapshotSeries(
            market_id=market_id,
            count=len(snapshots),
            first_archived_at=snapshots[0].archived_at if snapshots else None,
            last_archived_at=snapshots[-1].archived_at if snapshots else None,
            snapshots=snapshots,
        )

    def get_market_snapshot_archive_summary(self) -> SnapshotArchiveSummary:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                  COUNT(*) AS total_snapshots,
                  COUNT(DISTINCT market_id) AS unique_markets,
                  MAX(archived_at) AS latest_archived_at
                FROM market_snapshot_archive
                """
            ).fetchone()
            source_rows = conn.execute(
                """
                SELECT source, COUNT(*) AS count
                FROM market_snapshot_archive
                GROUP BY source
                """
            ).fetchall()
            reason_rows = conn.execute(
                """
                SELECT archive_reason, COUNT(*) AS count
                FROM market_snapshot_archive
                GROUP BY archive_reason
                """
            ).fetchall()
        return SnapshotArchiveSummary(
            total_snapshots=int(row["total_snapshots"] or 0),
            unique_markets=int(row["unique_markets"] or 0),
            by_source={str(item["source"]): int(item["count"]) for item in source_rows},
            by_archive_reason={
                str(item["archive_reason"]): int(item["count"]) for item in reason_rows
            },
            latest_archived_at=row["latest_archived_at"],
        )

    def save_market_snapshot(self, item: MarketSnapshot) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO market_snapshots
                (market_id, question, yes_price, no_price, liquidity, spread, source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.market_id,
                    item.question,
                    item.yes_price,
                    item.no_price,
                    item.liquidity,
                    item.spread,
                    item.source,
                    item.fetched_at,
                ),
            )

    def save_strategy_signal(self, item: StrategySignal) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO strategy_signals
                (signal_id, market_id, strategy_id, side, model_probability, market_probability,
                 edge_percent, z_score, confidence, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.signal_id,
                    item.market_id,
                    item.strategy_id,
                    item.side.value,
                    item.model_probability,
                    item.market_probability,
                    item.edge_percent,
                    item.z_score,
                    item.confidence,
                    item.reason,
                    item.created_at,
                ),
            )

    def save_opportunity_candidate(self, item: OpportunityCandidate) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO opportunity_candidates
                (candidate_id, signal_id, market_id, question, side, market_probability,
                 model_probability, edge_percent, z_score, liquidity, spread,
                 confidence_tier, risk_status, action_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.candidate_id,
                    item.signal_id,
                    item.market_id,
                    item.question,
                    item.side.value,
                    item.market_probability,
                    item.model_probability,
                    item.edge_percent,
                    item.z_score,
                    item.liquidity,
                    item.spread,
                    item.confidence_tier,
                    item.risk_status.value,
                    item.action_status.value,
                    item.created_at,
                ),
            )

    def save_execution_decision(self, item: ExecutionDecision) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO execution_decisions
                (decision_id, candidate_id, mode, action, position_size, expected_cost,
                 risk_status, execution_status, created_at, executed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.decision_id,
                    item.candidate_id,
                    item.mode.value,
                    item.action,
                    item.position_size,
                    item.expected_cost,
                    item.risk_status.value,
                    item.execution_status.value,
                    item.created_at,
                    item.executed_at,
                ),
            )

    def save_simulation_result(self, item: SimulationResult) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO simulation_results
                (simulation_id, decision_id, candidate_id, side, entry_price, position_size,
                 simulated_cost, expected_probability, expected_value, max_loss, max_gain,
                 result_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.simulation_id,
                    item.decision_id,
                    item.candidate_id,
                    item.side.value,
                    item.entry_price,
                    item.position_size,
                    item.simulated_cost,
                    item.expected_probability,
                    item.expected_value,
                    item.max_loss,
                    item.max_gain,
                    item.result_status,
                    item.created_at,
                ),
            )

    def save_audit_log(self, item: AuditLogEvent) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_logs
                (event_id, event_type, object_type, object_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item.event_id,
                    item.event_type,
                    item.object_type,
                    item.object_id,
                    json.dumps(item.payload, ensure_ascii=False),
                    item.created_at,
                ),
            )

    def save_weather_descriptor(self, item: WeatherMarketDescriptor) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO weather_descriptors
                (market_id, question, city, region, country, target_date, metric,
                 threshold, upper_threshold, unit, direction, confidence,
                 parse_warnings_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.market_id,
                    item.question,
                    item.city,
                    item.region,
                    item.country,
                    item.target_date,
                    item.metric.value,
                    item.threshold,
                    item.upper_threshold,
                    item.unit.value,
                    item.direction.value,
                    item.confidence.value,
                    json.dumps(item.parse_warnings, ensure_ascii=False),
                    item.created_at,
                ),
            )

    def save_weather_source(self, item: WeatherSourceRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO weather_sources
                (source_id, market_id, source_name, source_type, city, target_date,
                 fetched_at, valid_time, raw_payload_json, normalized_value, unit,
                 freshness_status, trust_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.source_id,
                    item.market_id,
                    item.source_name,
                    item.source_type.value,
                    item.city,
                    item.target_date,
                    item.fetched_at,
                    item.valid_time,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    item.normalized_value,
                    item.unit.value,
                    item.freshness_status.value,
                    item.trust_level.value,
                ),
            )

    def save_evidence_pack(self, item: EvidencePack) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO evidence_packs
                (evidence_pack_id, market_id, descriptor_json, sources_json,
                 evidence_freshness, evidence_conflict_level, raw_refs_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.evidence_pack_id,
                    item.market_id,
                    item.descriptor.model_dump_json(),
                    json.dumps(
                        [s.model_dump(mode="json") for s in item.sources],
                        ensure_ascii=False,
                    ),
                    item.evidence_freshness.value,
                    item.evidence_conflict_level.value,
                    json.dumps(item.raw_refs, ensure_ascii=False),
                    item.created_at,
                ),
            )

    def save_weather_view(self, item: WeatherView) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO weather_views
                (weather_view_id, evidence_pack_id, market_id, city, target_date,
                 expected_value, expected_range_low, expected_range_high, sigma,
                 threshold, direction, unit, confidence, evidence_summary_json,
                 invalidation_rules_json, confirmation_rules_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.weather_view_id,
                    item.evidence_pack_id,
                    item.market_id,
                    item.city,
                    item.target_date,
                    item.expected_value,
                    item.expected_range_low,
                    item.expected_range_high,
                    item.sigma,
                    item.threshold,
                    item.direction.value,
                    item.unit.value,
                    item.confidence.value,
                    json.dumps(item.evidence_summary, ensure_ascii=False),
                    json.dumps(item.invalidation_rules, ensure_ascii=False),
                    json.dumps(item.confirmation_rules, ensure_ascii=False),
                    item.created_at,
                ),
            )

    def save_probability_view(self, item: ProbabilityView) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO probability_views
                (probability_view_id, weather_view_id, market_id, engine_id,
                 model_probability, threshold, expected_value, sigma, direction,
                 confidence, warnings_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.probability_view_id,
                    item.weather_view_id,
                    item.market_id,
                    item.engine_id,
                    item.model_probability,
                    item.threshold,
                    item.expected_value,
                    item.sigma,
                    item.direction.value,
                    item.confidence.value,
                    json.dumps(item.warnings, ensure_ascii=False),
                    item.created_at,
                ),
            )

    def save_weather_forecast_archive_record(self, item: WeatherForecastArchiveRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO weather_forecast_archive
                (forecast_archive_id, market_id, weather_view_id, evidence_pack_id,
                 city, target_date, source_id, source_type, metric, unit,
                 expected_value, expected_range_low, expected_range_high, sigma,
                 fetched_at, archived_at, raw_payload_json, metadata_json, archive_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.forecast_archive_id,
                    item.market_id,
                    item.weather_view_id,
                    item.evidence_pack_id,
                    item.city,
                    item.target_date,
                    item.source_id,
                    item.source_type.value if hasattr(item.source_type, "value") else str(item.source_type),
                    item.metric.value if hasattr(item.metric, "value") else str(item.metric),
                    item.unit.value if hasattr(item.unit, "value") else str(item.unit),
                    item.expected_value,
                    item.expected_range_low,
                    item.expected_range_high,
                    item.sigma,
                    item.fetched_at,
                    item.archived_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                    item.archive_reason.value if hasattr(item.archive_reason, "value") else str(item.archive_reason),
                ),
            )

    def save_weather_evidence_archive_record(self, item: WeatherEvidenceArchiveRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO weather_evidence_archive
                (evidence_archive_id, market_id, evidence_pack_id, source_ids_json,
                 evidence_summary_json, invalidation_rules_json, confirmation_rules_json,
                 archived_at, raw_payload_json, metadata_json, archive_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.evidence_archive_id,
                    item.market_id,
                    item.evidence_pack_id,
                    json.dumps(item.source_ids, ensure_ascii=False),
                    json.dumps(item.evidence_summary, ensure_ascii=False),
                    json.dumps(item.invalidation_rules, ensure_ascii=False),
                    json.dumps(item.confirmation_rules, ensure_ascii=False),
                    item.archived_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                    item.archive_reason.value if hasattr(item.archive_reason, "value") else str(item.archive_reason),
                ),
            )

    def save_weather_view_archive_record(self, item: WeatherViewArchiveRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO weather_view_archive
                (weather_view_archive_id, market_id, weather_view_id, evidence_pack_id,
                 city, target_date, expected_value, expected_range_low, expected_range_high,
                 sigma, threshold, direction, unit, confidence, archived_at,
                 raw_payload_json, metadata_json, archive_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.weather_view_archive_id,
                    item.market_id,
                    item.weather_view_id,
                    item.evidence_pack_id,
                    item.city,
                    item.target_date,
                    item.expected_value,
                    item.expected_range_low,
                    item.expected_range_high,
                    item.sigma,
                    item.threshold,
                    item.direction,
                    item.unit,
                    item.confidence,
                    item.archived_at,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    json.dumps(item.metadata, ensure_ascii=False),
                    item.archive_reason.value if hasattr(item.archive_reason, "value") else str(item.archive_reason),
                ),
            )

    def list_weather_forecast_archive(
        self,
        limit: int = 100,
        source_type: WeatherForecastSourceType | str | None = None,
        archive_reason: WeatherArchiveReason | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if source_type:
            clauses.append("source_type = ?")
            params.append(source_type.value if hasattr(source_type, "value") else str(source_type))
        if archive_reason:
            clauses.append("archive_reason = ?")
            params.append(archive_reason.value if hasattr(archive_reason, "value") else str(archive_reason))
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM weather_forecast_archive
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_weather_forecast_archive_row(row) for row in rows]

    def list_weather_evidence_archive(
        self,
        limit: int = 100,
        archive_reason: WeatherArchiveReason | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if archive_reason:
            clauses.append("archive_reason = ?")
            params.append(archive_reason.value if hasattr(archive_reason, "value") else str(archive_reason))
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM weather_evidence_archive
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_weather_evidence_archive_row(row) for row in rows]

    def list_weather_view_archive(
        self,
        limit: int = 100,
        archive_reason: WeatherArchiveReason | str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        if archive_reason:
            clauses.append("archive_reason = ?")
            params.append(archive_reason.value if hasattr(archive_reason, "value") else str(archive_reason))
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM weather_view_archive
                {where_sql}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_weather_view_archive_row(row) for row in rows]

    def get_weather_archive_bundle(self, market_id: str, limit: int = 100) -> WeatherArchiveBundle:
        with get_connection(self.db_path) as conn:
            forecast_rows = conn.execute(
                """
                SELECT * FROM weather_forecast_archive
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (market_id, limit),
            ).fetchall()
            evidence_rows = conn.execute(
                """
                SELECT * FROM weather_evidence_archive
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (market_id, limit),
            ).fetchall()
            view_rows = conn.execute(
                """
                SELECT * FROM weather_view_archive
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (market_id, limit),
            ).fetchall()
        return WeatherArchiveBundle(
            market_id=market_id,
            forecasts=[WeatherForecastArchiveRecord(**self._parse_weather_forecast_archive_row(row)) for row in forecast_rows],
            evidence=[WeatherEvidenceArchiveRecord(**self._parse_weather_evidence_archive_row(row)) for row in evidence_rows],
            weather_views=[WeatherViewArchiveRecord(**self._parse_weather_view_archive_row(row)) for row in view_rows],
        )

    def get_weather_archive_summary(self) -> WeatherArchiveSummary:
        with get_connection(self.db_path) as conn:
            forecast_row = conn.execute(
                "SELECT COUNT(*) AS count, MAX(archived_at) AS latest FROM weather_forecast_archive"
            ).fetchone()
            evidence_row = conn.execute(
                "SELECT COUNT(*) AS count, MAX(archived_at) AS latest FROM weather_evidence_archive"
            ).fetchone()
            view_row = conn.execute(
                "SELECT COUNT(*) AS count, MAX(archived_at) AS latest FROM weather_view_archive"
            ).fetchone()
            market_rows = conn.execute(
                """
                SELECT market_id FROM weather_forecast_archive
                UNION
                SELECT market_id FROM weather_evidence_archive
                UNION
                SELECT market_id FROM weather_view_archive
                """
            ).fetchall()
            source_rows = conn.execute(
                """
                SELECT source_type, COUNT(*) AS count
                FROM weather_forecast_archive
                GROUP BY source_type
                """
            ).fetchall()
            reason_rows = conn.execute(
                """
                SELECT archive_reason, COUNT(*) AS count FROM (
                  SELECT archive_reason FROM weather_forecast_archive
                  UNION ALL
                  SELECT archive_reason FROM weather_evidence_archive
                  UNION ALL
                  SELECT archive_reason FROM weather_view_archive
                )
                GROUP BY archive_reason
                """
            ).fetchall()
        latest_archived_at = max(
            (
                value
                for value in [
                    forecast_row["latest"],
                    evidence_row["latest"],
                    view_row["latest"],
                ]
                if value
            ),
            default=None,
        )
        return WeatherArchiveSummary(
            forecast_records=int(forecast_row["count"] or 0),
            evidence_records=int(evidence_row["count"] or 0),
            weather_view_records=int(view_row["count"] or 0),
            unique_markets=len(market_rows),
            by_source_type={str(row["source_type"]): int(row["count"]) for row in source_rows},
            by_archive_reason={str(row["archive_reason"]): int(row["count"]) for row in reason_rows},
            latest_archived_at=latest_archived_at,
        )

    def save_polymarket_market_record(self, item: PolymarketMarketRecord) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO polymarket_market_cache
                (polymarket_market_id, condition_id, question, slug, category,
                 active, closed, archived, end_date, resolution_source,
                 outcomes_json, outcome_prices_json, clob_token_ids_json,
                 liquidity, volume, raw_payload_json, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.polymarket_market_id,
                    item.condition_id,
                    item.question,
                    item.slug,
                    item.category,
                    None if item.active is None else int(item.active),
                    None if item.closed is None else int(item.closed),
                    None if item.archived is None else int(item.archived),
                    item.end_date,
                    item.resolution_source,
                    json.dumps(item.outcomes, ensure_ascii=False),
                    json.dumps(item.outcome_prices, ensure_ascii=False),
                    json.dumps(item.clob_token_ids, ensure_ascii=False),
                    item.liquidity,
                    item.volume,
                    json.dumps(item.raw_payload, ensure_ascii=False),
                    item.fetched_at,
                ),
            )

    def list_polymarket_market_cache(self, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM polymarket_market_cache
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._parse_polymarket_market_cache_row(row) for row in rows]

    def list_polymarket_weather_market_cache(self, limit: int = 100) -> list[dict]:
        weather_terms = [
            "%weather%",
            "%temperature%",
            "%temp%",
            "%rain%",
            "%rainfall%",
            "%precipitation%",
            "%snow%",
            "%hurricane%",
            "%storm%",
            "%wind%",
            "%heat%",
            "%cold%",
        ]
        term_clause = "(LOWER(question) LIKE LOWER(?) OR LOWER(slug) LIKE LOWER(?) OR LOWER(category) LIKE LOWER(?))"
        clauses = " OR ".join([term_clause] * len(weather_terms))
        params: list[object] = []
        for term in weather_terms:
            params.extend([term, term, term])
        params.append(limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM polymarket_market_cache
                WHERE {clauses}
                ORDER BY id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._parse_polymarket_market_cache_row(row) for row in rows]

    def _parse_polymarket_market_cache_row(self, row) -> dict:
        item = dict(row)
        item["active"] = None if item.get("active") is None else bool(item["active"])
        item["closed"] = None if item.get("closed") is None else bool(item["closed"])
        item["archived"] = None if item.get("archived") is None else bool(item["archived"])
        item["outcomes"] = json.loads(item.get("outcomes_json") or "[]")
        item["outcome_prices"] = json.loads(item.get("outcome_prices_json") or "[]")
        item["clob_token_ids"] = json.loads(item.get("clob_token_ids_json") or "[]")
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        return item

    def _parse_market_snapshot_archive_row(self, row) -> dict:
        item = dict(row)
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        return item

    def _parse_weather_forecast_archive_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        return item

    def _parse_weather_evidence_archive_row(self, row) -> dict:
        item = dict(row)
        item["source_ids"] = json.loads(item.get("source_ids_json") or "[]")
        item["evidence_summary"] = json.loads(item.get("evidence_summary_json") or "[]")
        item["invalidation_rules"] = json.loads(item.get("invalidation_rules_json") or "[]")
        item["confirmation_rules"] = json.loads(item.get("confirmation_rules_json") or "[]")
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        return item

    def _parse_weather_view_archive_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        return item

    def save_polymarket_connector_health(self, item: PolymarketConnectorHealth) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO polymarket_connector_health
                (connector_id, gamma_reachable, clob_reachable, last_gamma_status,
                 last_clob_status, mode, warnings_json, last_checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.connector_id,
                    1 if item.gamma_reachable else 0,
                    1 if item.clob_reachable else 0,
                    item.last_gamma_status,
                    item.last_clob_status,
                    item.mode.value if hasattr(item.mode, "value") else str(item.mode),
                    json.dumps(item.warnings, ensure_ascii=False),
                    item.last_checked_at,
                ),
            )

    def get_latest_polymarket_connector_health(self) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM polymarket_connector_health
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["gamma_reachable"] = bool(item["gamma_reachable"])
        item["clob_reachable"] = bool(item["clob_reachable"])
        item["warnings"] = json.loads(item.get("warnings_json") or "[]")
        return item

    def list_polymarket_connector_health(self, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM polymarket_connector_health
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["gamma_reachable"] = bool(item["gamma_reachable"])
            item["clob_reachable"] = bool(item["clob_reachable"])
            item["warnings"] = json.loads(item.get("warnings_json") or "[]")
            items.append(item)
        return items

    def save_probability_engine_config(self, item: ProbabilityEngineConfig) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO probability_engine_configs
                (engine_id, engine_name, engine_type, version, enabled, can_be_primary,
                 description, default_params_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.engine_id,
                    item.engine_name,
                    item.engine_type.value,
                    item.version,
                    1 if item.enabled else 0,
                    1 if item.can_be_primary else 0,
                    item.description,
                    json.dumps(item.default_params, ensure_ascii=False),
                    item.created_at,
                    item.updated_at,
                ),
            )

    def list_probability_engine_configs(self) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM probability_engine_configs ORDER BY id ASC"
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["enabled"] = bool(item["enabled"])
            item["can_be_primary"] = bool(item["can_be_primary"])
            item["default_params"] = json.loads(item.get("default_params_json") or "{}")
            items.append(item)
        return items

    def get_probability_engine_config(self, engine_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM probability_engine_configs
                WHERE engine_id = ?
                LIMIT 1
                """,
                (engine_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["enabled"] = bool(item["enabled"])
        item["can_be_primary"] = bool(item["can_be_primary"])
        item["default_params"] = json.loads(item.get("default_params_json") or "{}")
        return item

    def save_probability_engine_run(self, item: ProbabilityEngineRun) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO probability_engine_runs
                (run_id, market_id, weather_view_id, engine_id, engine_type,
                 model_probability, expected_value, sigma, threshold, direction,
                 params_json, warnings_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.run_id,
                    item.market_id,
                    item.weather_view_id,
                    item.engine_id,
                    item.engine_type.value,
                    item.model_probability,
                    item.expected_value,
                    item.sigma,
                    item.threshold,
                    item.direction,
                    json.dumps(item.params, ensure_ascii=False),
                    json.dumps(item.warnings, ensure_ascii=False),
                    item.created_at,
                ),
            )

    def _parse_probability_engine_run_row(self, row) -> dict:
        item = dict(row)
        item["params"] = json.loads(item.get("params_json") or "{}")
        item["warnings"] = json.loads(item.get("warnings_json") or "[]")
        return item

    def list_probability_engine_runs_for_market(self, market_id: str, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM probability_engine_runs
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (market_id, limit),
            ).fetchall()
        return [self._parse_probability_engine_run_row(row) for row in rows]

    def list_probability_engine_runs_for_engine(self, engine_id: str, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM probability_engine_runs
                WHERE engine_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (engine_id, limit),
            ).fetchall()
        return [self._parse_probability_engine_run_row(row) for row in rows]

    def save_probability_comparison(self, item: ProbabilityComparisonView) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO probability_comparisons
                (comparison_id, market_id, weather_view_id, active_engine_id,
                 active_probability, engine_runs_json, spread_between_engines,
                 disagreement_level, selection_reason, warnings_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.comparison_id,
                    item.market_id,
                    item.weather_view_id,
                    item.active_engine_id,
                    item.active_probability,
                    json.dumps([r.model_dump(mode="json") for r in item.engine_runs], ensure_ascii=False),
                    item.spread_between_engines,
                    item.disagreement_level.value,
                    item.selection_reason,
                    json.dumps(item.warnings, ensure_ascii=False),
                    item.created_at,
                ),
            )

    def get_latest_probability_comparison(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM probability_comparisons
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["engine_runs"] = json.loads(item.get("engine_runs_json") or "[]")
        item["warnings"] = json.loads(item.get("warnings_json") or "[]")
        return item

    def save_market_outcome(self, item: MarketOutcome) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO market_outcomes
                (outcome_id, market_id, resolved_value, resolved_direction_hit,
                 official_source, resolved_at, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.outcome_id,
                    item.market_id,
                    item.resolved_value,
                    None if item.resolved_direction_hit is None else int(item.resolved_direction_hit),
                    item.official_source,
                    item.resolved_at,
                    item.status.value,
                    item.notes,
                ),
            )

    def get_latest_market_outcome(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM market_outcomes
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        value = item.get("resolved_direction_hit")
        item["resolved_direction_hit"] = None if value is None else bool(value)
        return item

    def save_calibration_result(self, item: CalibrationResult) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO calibration_results
                (calibration_id, market_id, engine_id, run_id, outcome_id,
                 predicted_probability, actual_outcome, brier_score,
                 absolute_error, bucket, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.calibration_id,
                    item.market_id,
                    item.engine_id,
                    item.run_id,
                    item.outcome_id,
                    item.predicted_probability,
                    item.actual_outcome,
                    item.brier_score,
                    item.absolute_error,
                    item.bucket,
                    item.created_at,
                ),
            )

    def list_calibration_results_for_engine(self, engine_id: str, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM calibration_results
                WHERE engine_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (engine_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_calibration_results_for_market(self, market_id: str, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM calibration_results
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (market_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_engine_promotion_decision(self, item: EnginePromotionDecision) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO engine_promotion_decisions
                (decision_id, engine_id, current_type, proposed_type, eligible,
                 decision, evidence_count, avg_brier_score, avg_absolute_error,
                 reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.decision_id,
                    item.engine_id,
                    item.current_type.value,
                    item.proposed_type.value,
                    1 if item.eligible else 0,
                    item.decision.value,
                    item.evidence_count,
                    item.avg_brier_score,
                    item.avg_absolute_error,
                    item.reason,
                    item.created_at,
                ),
            )

    def get_latest_engine_promotion_decision(self, engine_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM engine_promotion_decisions
                WHERE engine_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (engine_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["eligible"] = bool(item["eligible"])
        return item

    def list_opportunity_candidates(self, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM opportunity_candidates ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_weather_descriptors(self, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM weather_descriptors ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_evidence_packs(self, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM evidence_packs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_latest_evidence_pack(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM evidence_packs
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["descriptor"] = json.loads(item.get("descriptor_json") or "{}")
        item["sources"] = json.loads(item.get("sources_json") or "[]")
        item["raw_refs"] = json.loads(item.get("raw_refs_json") or "[]")
        return item

    def get_latest_weather_view(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM weather_views
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["evidence_summary"] = json.loads(item.get("evidence_summary_json") or "[]")
        item["invalidation_rules"] = json.loads(item.get("invalidation_rules_json") or "[]")
        item["confirmation_rules"] = json.loads(item.get("confirmation_rules_json") or "[]")
        return item

    def get_latest_probability_view(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM probability_views
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["warnings"] = json.loads(item.get("warnings_json") or "[]")
        return item

    def get_latest_weather_descriptor(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM weather_descriptors
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["parse_warnings"] = json.loads(item.get("parse_warnings_json") or "[]")
        return item

    def list_weather_sources_for_market(self, market_id: str, limit: int = 100) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM weather_sources
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (market_id, limit),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
            items.append(item)
        return items

    def get_latest_candidate_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM opportunity_candidates
                WHERE market_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_latest_execution_decision_for_market(self, market_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT ed.*
                FROM execution_decisions ed
                INNER JOIN opportunity_candidates oc
                  ON oc.candidate_id = ed.candidate_id
                WHERE oc.market_id = ?
                ORDER BY ed.id DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_candidate(self, candidate_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM opportunity_candidates WHERE candidate_id = ? ORDER BY id DESC LIMIT 1",
                (candidate_id,),
            ).fetchone()
            return dict(row) if row else None

    def update_candidate_action_status(self, candidate_id: str, status: ActionStatus) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE opportunity_candidates SET action_status = ? WHERE candidate_id = ?",
                (status.value, candidate_id),
            )

    def list_table(self, table: str, limit: int = 100) -> list[dict]:
        allowed = {
            "strategy_signals",
            "opportunity_candidates",
            "simulation_results",
            "audit_logs",
            "market_snapshots",
            "execution_decision_review_records",
            "execution_queue_review_records",
            "approval_window_review_records",
            "activation_readiness_review_records",
            "activation_authorization_review_records",
        }
        if table not in allowed:
            raise ValueError(f"Unsupported table: {table}")
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        result = [dict(row) for row in rows]
        if table == "audit_logs":
            for row in result:
                row["payload"] = json.loads(row.get("payload_json") or "{}")
        return result

    def _parse_execution_decision_review_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        approval_window_valid = item.get("approval_window_valid")
        item["approval_window_valid"] = None if approval_window_valid is None else bool(approval_window_valid)
        item["executionDecisionReviewId"] = item["execution_decision_review_id"]
        item["marketId"] = item["market_id"]
        item["decisionId"] = item["decision_id"]
        item["candidateId"] = item["candidate_id"]
        item["commandReviewId"] = item["command_review_id"]
        item["shadowEvaluationId"] = item["shadow_evaluation_id"]
        item["executionMode"] = item["execution_mode"]
        item["positionSize"] = item["position_size"]
        item["expectedCost"] = item["expected_cost"]
        item["reviewStatus"] = item["review_status"]
        item["approvalStatus"] = item["approval_status"]
        item["gateStatus"] = item["gate_status"]
        item["recommendation"] = item["recommendation"]
        item["approvalWindowValid"] = item["approval_window_valid"]
        item["approvalValidUntil"] = item["approval_valid_until"]
        item["reviewedAt"] = item["reviewed_at"]
        return item

    def _parse_execution_queue_review_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        approval_window_valid = item.get("approval_window_valid")
        item["approval_window_valid"] = None if approval_window_valid is None else bool(approval_window_valid)
        item["executionQueueReviewId"] = item["execution_queue_review_id"]
        item["marketId"] = item["market_id"]
        item["decisionId"] = item["decision_id"]
        item["candidateId"] = item["candidate_id"]
        item["commandReviewId"] = item["command_review_id"]
        item["executionDecisionReviewId"] = item["execution_decision_review_id"]
        item["shadowEvaluationId"] = item["shadow_evaluation_id"]
        item["executionMode"] = item["execution_mode"]
        item["positionSize"] = item["position_size"]
        item["expectedCost"] = item["expected_cost"]
        item["reviewStatus"] = item["review_status"]
        item["approvalStatus"] = item["approval_status"]
        item["gateStatus"] = item["gate_status"]
        item["recommendation"] = item["recommendation"]
        item["approvalWindowValid"] = item["approval_window_valid"]
        item["approvalValidUntil"] = item["approval_valid_until"]
        item["reviewedAt"] = item["reviewed_at"]
        return item

    def _parse_approval_window_review_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        approval_window_valid = item.get("approval_window_valid")
        item["approval_window_valid"] = None if approval_window_valid is None else bool(approval_window_valid)
        item["approvalWindowReviewId"] = item["approval_window_review_id"]
        item["marketId"] = item["market_id"]
        item["decisionId"] = item["decision_id"]
        item["candidateId"] = item["candidate_id"]
        item["commandReviewId"] = item["command_review_id"]
        item["executionDecisionReviewId"] = item["execution_decision_review_id"]
        item["executionQueueReviewId"] = item["execution_queue_review_id"]
        item["approvalStatus"] = item["approval_status"]
        item["approvalWindowValid"] = item["approval_window_valid"]
        item["approvalValidUntil"] = item["approval_valid_until"]
        item["reviewStatus"] = item["review_status"]
        item["windowState"] = item["window_state"]
        item["recommendation"] = item["recommendation"]
        item["reviewedAt"] = item["reviewed_at"]
        return item

    def _parse_activation_readiness_review_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["activationReadinessReviewId"] = item["activation_readiness_review_id"]
        item["marketId"] = item["market_id"]
        item["decisionId"] = item["decision_id"]
        item["candidateId"] = item["candidate_id"]
        item["commandReviewId"] = item["command_review_id"]
        item["executionDecisionReviewId"] = item["execution_decision_review_id"]
        item["executionQueueReviewId"] = item["execution_queue_review_id"]
        item["approvalWindowReviewId"] = item["approval_window_review_id"]
        item["approvalStatus"] = item["approval_status"]
        item["windowState"] = item["window_state"]
        item["reviewStatus"] = item["review_status"]
        item["readinessStatus"] = item["readiness_status"]
        item["recommendation"] = item["recommendation"]
        item["reviewedAt"] = item["reviewed_at"]
        return item

    def _parse_activation_authorization_review_row(self, row) -> dict:
        item = dict(row)
        item["raw_payload"] = json.loads(item.get("raw_payload_json") or "{}")
        item["metadata"] = json.loads(item.get("metadata_json") or "{}")
        item["activationAuthorizationReviewId"] = item["activation_authorization_review_id"]
        item["marketId"] = item["market_id"]
        item["decisionId"] = item["decision_id"]
        item["candidateId"] = item["candidate_id"]
        item["commandReviewId"] = item["command_review_id"]
        item["executionDecisionReviewId"] = item["execution_decision_review_id"]
        item["executionQueueReviewId"] = item["execution_queue_review_id"]
        item["approvalWindowReviewId"] = item["approval_window_review_id"]
        item["activationReadinessReviewId"] = item["activation_readiness_review_id"]
        item["approvalStatus"] = item["approval_status"]
        item["windowState"] = item["window_state"]
        item["readinessStatus"] = item["readiness_status"]
        item["authorizationStatus"] = item["authorization_status"]
        item["recommendation"] = item["recommendation"]
        item["reviewedAt"] = item["reviewed_at"]
        return item

    def get_rules(self) -> dict:
        with get_connection(self.db_path) as conn:
            rows = conn.execute("SELECT key, value FROM rule_configs").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def set_rule(self, key: str, value: str) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO rule_configs (key, value) VALUES (?, ?)",
                (key, value),
            )

    def get_mode(self) -> str:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT value FROM system_state WHERE key = 'execution_mode'"
            ).fetchone()
        return row["value"] if row else "OBSERVE_ONLY"

    def set_mode(self, mode: str) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)",
                ("execution_mode", mode),
            )
