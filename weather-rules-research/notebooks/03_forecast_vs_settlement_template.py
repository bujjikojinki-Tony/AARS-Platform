# %% [markdown]
# # 03 Forecast vs Settlement
#
# Goal:
# Compare forecast values with official settlement records for one market family.
#
# Steps:
# 1. Load normalized rules
# 2. Load station mapping
# 3. Load forecast data
# 4. Load official observation data
# 5. Join forecast vs settlement
# 6. Evaluate bias / band hit / drift / stability
# 7. Export reports

# %%
from pathlib import Path

import pandas as pd

from weather_rules_research.backtest.band_eval import BandEvaluator, TemperatureBand
from weather_rules_research.backtest.bias_eval import BiasEvaluator
from weather_rules_research.backtest.drift_eval import DriftEvaluator, ForecastDriftRow
from weather_rules_research.backtest.joiner import JoinedForecastSettlement
from weather_rules_research.backtest.stability_eval import StabilityEvaluator, StabilityRow
from weather_rules_research.outputs.export_bias_report import BiasReportExporter

# %%
BASE = Path("data")
PROCESSED = BASE / "processed"
OUTPUTS = BASE / "outputs"

print("Processed dir:", PROCESSED)
print("Outputs dir:", OUTPUTS)

# %% [markdown]
# ## 1. Load Example Datasets
#
# Replace these stubs with real generated artifacts later.

# %%
joined_rows = [
    JoinedForecastSettlement(
        target_date="2026-04-12",
        variable_name="daily_max_temperature",
        forecast_value=27.3,
        official_value=27.0,
        error=0.3,
    ),
    JoinedForecastSettlement(
        target_date="2026-04-13",
        variable_name="daily_max_temperature",
        forecast_value=28.2,
        official_value=28.0,
        error=0.2,
    ),
    JoinedForecastSettlement(
        target_date="2026-04-14",
        variable_name="daily_max_temperature",
        forecast_value=26.1,
        official_value=27.0,
        error=-0.9,
    ),
]

drift_rows = [
    ForecastDriftRow(
        forecast_issued_date="2026-04-07",
        target_date="2026-04-12",
        lead_days=5,
        forecast_value=28.0,
        official_value=27.0,
    ),
    ForecastDriftRow(
        forecast_issued_date="2026-04-09",
        target_date="2026-04-12",
        lead_days=3,
        forecast_value=27.5,
        official_value=27.0,
    ),
    ForecastDriftRow(
        forecast_issued_date="2026-04-11",
        target_date="2026-04-12",
        lead_days=1,
        forecast_value=27.2,
        official_value=27.0,
    ),
]

stability_rows = [
    StabilityRow(group_key="CentralPark-Apr", forecast_value=27.3, official_value=27.0),
    StabilityRow(group_key="CentralPark-Apr", forecast_value=28.2, official_value=28.0),
    StabilityRow(group_key="CentralPark-Apr", forecast_value=26.1, official_value=27.0),
]

# %% [markdown]
# ## 2. Basic Bias Metrics

# %%
bias_eval = BiasEvaluator()

mean_error = bias_eval.mean_error(joined_rows)
mae = bias_eval.mean_absolute_error(joined_rows)
rmse = (sum((row.error ** 2) for row in joined_rows) / len(joined_rows)) ** 0.5

pd.DataFrame(
    [
        {"metric": "mean_error", "value": mean_error},
        {"metric": "mae", "value": mae},
        {"metric": "rmse", "value": rmse},
    ]
)

# %% [markdown]
# ## 3. Band Evaluation

# %%
band_eval = BandEvaluator(
    [
        TemperatureBand(label="26_or_below", upper=26.0),
        TemperatureBand(label="27", lower=26.0, upper=27.0, lower_inclusive=False),
        TemperatureBand(label="28", lower=27.0, upper=28.0, lower_inclusive=False),
        TemperatureBand(label="29_plus", lower=28.0, lower_inclusive=False, upper=None),
    ]
)

band_rows = []
for row in joined_rows:
    band_rows.append(
        {
            "target_date": row.target_date,
            "forecast_value": row.forecast_value,
            "official_value": row.official_value,
            "forecast_band": band_eval.classify(row.forecast_value),
            "official_band": band_eval.classify(row.official_value),
            "hit": band_eval.hit(row.forecast_value, row.official_value),
            "adjacent_hit": band_eval.adjacent_hit(row.forecast_value, row.official_value),
            "extreme_miss": band_eval.extreme_miss(row.forecast_value, row.official_value),
        }
    )

pd.DataFrame(band_rows)

# %% [markdown]
# ## 4. Drift Evaluation

# %%
drift_eval = DriftEvaluator()

pd.DataFrame(
    [
        {
            "lead_days": lead,
            "mean_error": drift_eval.mean_error_by_lead(drift_rows).get(lead),
            "mae": drift_eval.mae_by_lead(drift_rows).get(lead),
            "rmse": drift_eval.rmse_by_lead(drift_rows).get(lead),
        }
        for lead in sorted(drift_eval.group_by_lead_days(drift_rows).keys())
    ]
)

# %% [markdown]
# ## 5. Stability Evaluation

# %%
stability_eval = StabilityEvaluator()

pd.DataFrame(
    [
        {
            "group_key": group,
            "mean_error": stability_eval.mean_error_by_group(stability_rows).get(group),
            "mae": stability_eval.mae_by_group(stability_rows).get(group),
            "error_range": stability_eval.error_range_by_group(stability_rows).get(group),
        }
        for group in sorted(stability_eval.group_rows(stability_rows).keys())
    ]
)

# %% [markdown]
# ## 6. Export Summary Report

# %%
exporter = BiasReportExporter(
    band_evaluator=band_eval,
)

summary_path = OUTPUTS / "forecast_bias_summary.csv"
drift_path = OUTPUTS / "forecast_drift_detail.csv"
stability_path = OUTPUTS / "forecast_stability_detail.csv"

OUTPUTS.mkdir(parents=True, exist_ok=True)

exporter.export_summary_report(
    path=summary_path,
    joined_rows=joined_rows,
    drift_rows=drift_rows,
    stability_rows=stability_rows,
)

exporter.export_drift_detail_report(
    path=drift_path,
    drift_rows=drift_rows,
)

exporter.export_stability_detail_report(
    path=stability_path,
    stability_rows=stability_rows,
)

print("Exported:")
print(summary_path)
print(drift_path)
print(stability_path)

# %% [markdown]
# ## 7. Next Step
#
# Replace stub rows with:
# - parsed rulebook
# - station map
# - Open-Meteo forecast snapshots
# - official settlement records
