from __future__ import annotations

from weather_rules_research.models.settlement_record import SettlementRecord


class OfficialObservationReconciler:
    def to_settlement_record(self, payload: dict) -> SettlementRecord:
        return SettlementRecord(
            station_id=payload["station_id"],
            target_date=payload["target_date"],
            variable_name=payload["variable_name"],
            official_value=payload.get("official_value"),
            unit=payload.get("unit"),
            source=payload["source"],
            source_url=payload.get("source_url"),
            raw_payload_ref=payload.get("raw_payload_ref"),
            quality_flag=payload.get("quality_flag"),
            notes=payload.get("notes"),
        )

    def validate_for_backtest(self, record: SettlementRecord) -> list[str]:
        issues: list[str] = []

        if not record.station_id:
            issues.append("missing station_id")

        if not record.target_date:
            issues.append("missing target_date")

        if not record.variable_name:
            issues.append("missing variable_name")

        if record.official_value is None:
            issues.append("missing official_value")

        if not record.source:
            issues.append("missing source")

        return issues

    def is_settlement_grade(self, record: SettlementRecord) -> bool:
        """
        Conservative MVP definition:
        only daily official sources count as settlement-grade.
        """
        return record.source in {
            "ncei_cdo_daily",
        }
