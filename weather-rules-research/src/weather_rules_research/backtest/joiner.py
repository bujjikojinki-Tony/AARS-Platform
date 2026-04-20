from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from weather_rules_research.models import ForecastSnapshot, JoinedRecord, SettlementRecord
from weather_rules_research.models.forecast_snapshot import ForecastSnapshot as SampleForecastSnapshot


@dataclass
class JoinedForecastSettlement:
    target_date: str
    variable_name: str
    forecast_value: float
    official_value: float
    error: float


class ForecastSettlementJoiner:
    def join(
        self,
        forecast_snapshot: SampleForecastSnapshot,
        settlement_record: SettlementRecord,
    ) -> JoinedForecastSettlement:
        official_value = float(settlement_record.official_value or 0.0)
        forecast_value = float(forecast_snapshot.value)
        return JoinedForecastSettlement(
            target_date=forecast_snapshot.target_date,
            variable_name=forecast_snapshot.variable_name,
            forecast_value=forecast_value,
            official_value=official_value,
            error=round(forecast_value - official_value, 4),
        )


def join_forecasts_to_settlements(
    forecasts: list[ForecastSnapshot],
    settlements: list[SettlementRecord],
) -> list[JoinedRecord]:
    settlements_by_key = {
        (settlement.station_id, settlement.target_date): settlement for settlement in settlements
    }

    joined: list[JoinedRecord] = []
    for forecast in forecasts:
        settlement = settlements_by_key.get((forecast.station_id, forecast.target_date.isoformat()))
        if settlement is None:
            continue
        joined.append(
            JoinedRecord(
                market_id=forecast.market_id,
                station_id=forecast.station_id,
                market_type=forecast.market_type,
                settlement_date=date.fromisoformat(settlement.target_date),
                predicted_temperature_c=forecast.predicted_temperature_c,
                settled_temperature_c=float(settlement.official_value or 0.0),
                forecast_issued_at=forecast.issued_at,
                forecast_source=forecast.source,
                settlement_source=settlement.source,
                settlement_unit=settlement.unit,
                settlement_source_url=settlement.source_url,
                settlement_raw_payload_ref=settlement.raw_payload_ref,
            )
        )

    return joined
