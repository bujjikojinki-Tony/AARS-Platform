from __future__ import annotations

import math

from weather_rules_research.models import BiasReportRow, BiasSummary, JoinedRecord


def evaluate_bias(
    joined_records: list[JoinedRecord],
    band_c: float = 2.0,
) -> list[BiasReportRow]:
    rows: list[BiasReportRow] = []
    for record in joined_records:
        error_c = round(float(record.predicted_temperature_c) - float(record.settled_temperature_c), 3)
        abs_error_c = round(abs(error_c), 3)
        squared_error_c = round(error_c * error_c, 3)
        rows.append(
            BiasReportRow(
                market_id=record.market_id,
                station_id=record.station_id,
                market_type=record.market_type,
                settlement_date=record.settlement_date,
                predicted_temperature_c=float(record.predicted_temperature_c),
                settled_temperature_c=float(record.settled_temperature_c),
                error_c=error_c,
                abs_error_c=abs_error_c,
                squared_error_c=squared_error_c,
                forecast_source=record.forecast_source,
                band_hit=abs_error_c <= band_c,
            )
        )

    return rows


def summarize_bias_metrics(rows: list[BiasReportRow], band_c: float = 2.0) -> BiasSummary:
    if not rows:
        return BiasSummary(
            sample_size=0,
            mean_error_c=0.0,
            mae_c=0.0,
            rmse_c=0.0,
            band_c=band_c,
            band_hit_rate=0.0,
        )

    sample_size = len(rows)
    mean_error_c = round(sum(row.error_c for row in rows) / sample_size, 3)
    mae_c = round(sum(row.abs_error_c for row in rows) / sample_size, 3)
    rmse_c = round(math.sqrt(sum(row.squared_error_c for row in rows) / sample_size), 3)
    band_hit_rate = round(sum(1 for row in rows if row.band_hit) / sample_size, 3)

    return BiasSummary(
        sample_size=sample_size,
        mean_error_c=mean_error_c,
        mae_c=mae_c,
        rmse_c=rmse_c,
        band_c=band_c,
        band_hit_rate=band_hit_rate,
    )
