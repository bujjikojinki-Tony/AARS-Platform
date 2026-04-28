from weather_comparison_engine.features import HistoricalFeatureStoreBuilder, load_optional_json_records


def test_feature_store_builds_labeled_precipitation_sample():
    builder = HistoricalFeatureStoreBuilder()

    samples = builder.build_samples(
        comparison_rows=[
            {
                "timestamp": "2026-04-18T00:00:00+00:00",
                "market_id": "rain_001",
                "market_probability": 0.60,
                "yes_price": 0.60,
                "no_price": 0.40,
                "model_value": 12.0,
                "model_band": "in_range",
                "market_band": "in_range",
                "confidence_score": 0.90,
                "confidence_adjusted_gap": 0.0,
                "comparison_status": "aligned",
                "action_hint": "watch",
                "source_policy_ref": "source_policy_registry.v1",
                "precision_policy_ref": "precision_policy.weather_metric.precipitation.v1",
                "rounding_policy_ref": "rounding_policy.weather_metric.precipitation.v1",
                "band_mapping_policy_ref": "band_mapping.precipitation_mm_threshold.v1",
                "normalization_version": "measurement_normalization.v1",
                "top_parameter_view": {
                    "forecast": {
                        "raw_value": 12.0,
                        "raw_unit": "mm",
                        "canonical_value": 12.0,
                        "canonical_unit": "mm",
                        "display_value": 12.0,
                        "display_unit": "mm",
                        "conversion_rule": "identity",
                        "conversion_applied": False,
                        "normalization_version": "measurement_normalization.v1",
                    },
                    "weather": {
                        "raw_value": 11.0,
                        "raw_unit": "mm",
                        "canonical_value": 11.0,
                        "canonical_unit": "mm",
                        "display_value": 11.0,
                        "display_unit": "mm",
                        "conversion_rule": "identity",
                        "conversion_applied": False,
                        "normalization_version": "measurement_normalization.v1",
                    },
                    "source_contract": {
                        "source_policy_ref": "source_policy_registry.v1",
                    },
                    "normalization": {
                        "source_policy_ref": "source_policy_registry.v1",
                        "precision_policy_ref": "precision_policy.weather_metric.precipitation.v1",
                        "rounding_policy_ref": "rounding_policy.weather_metric.precipitation.v1",
                        "band_mapping_policy_ref": "band_mapping.precipitation_mm_threshold.v1",
                        "normalization_version": "measurement_normalization.v1",
                    },
                },
            }
        ],
        resolver_report={
            "rules": [
                {
                    "market_id": "rain_001",
                    "market_question": "Will rainfall in Shanghai on Apr 18 be between 10mm and 20mm?",
                    "resolver_status": "matched",
                    "resolver_reason": "matched_by_market_id",
                    "resolver_confidence": 0.88,
                    "market_family": "weather_metric",
                    "required_data_source": "wunderground_zspd",
                    "band_scheme": "precipitation_range_3way",
                    "station_id": "ZSPD",
                    "target_date": "2026-04-18",
                    "variable_name": "daily_precipitation_sum",
                    "expected_band": "in_range",
                    "threshold_lower": 10.0,
                    "threshold_upper": 20.0,
                }
            ]
        },
        official_records=[
            {
                "station_id": "ZSPD",
                "target_date": "2026-04-18",
                "variable_name": "daily_precipitation_sum",
                "official_value": 11.0,
                "source": "ncei_cdo_daily",
            }
        ],
    )

    assert len(samples) == 1
    sample = samples[0]
    assert sample.market_id == "rain_001"
    assert sample.is_labeled is True
    assert sample.official_value == 11.0
    assert sample.resolved_band == "in_range"
    assert sample.outcome == "YES"
    assert sample.model_probability == 0.72
    assert sample.edge == 0.12
    assert sample.schema_version == "training_sample.v2"
    assert sample.source_policy_ref == "source_policy_registry.v1"
    assert sample.normalization_version == "measurement_normalization.v1"
    assert sample.forecast_canonical_value == 12.0
    assert sample.observation_canonical_value == 11.0


def test_feature_store_summary_counts_labeled_and_unlabeled_rows():
    builder = HistoricalFeatureStoreBuilder()

    samples = builder.build_samples(
        comparison_rows=[
            {
                "timestamp": "2026-04-18T00:00:00+00:00",
                "market_id": "rain_001",
                "market_probability": 0.60,
                "yes_price": 0.60,
                "no_price": 0.40,
                "model_band": "in_range",
                "market_band": "in_range",
                "confidence_score": 0.90,
                "comparison_status": "aligned",
                "source_policy_ref": "source_policy_registry.v1",
                "precision_policy_ref": "precision_policy.weather_metric.precipitation.v1",
                "rounding_policy_ref": "rounding_policy.weather_metric.precipitation.v1",
                "band_mapping_policy_ref": "band_mapping.precipitation_mm_threshold.v1",
                "normalization_version": "measurement_normalization.v1",
                "top_parameter_view": {
                    "forecast": {
                        "canonical_value": 12.0,
                        "canonical_unit": "mm",
                        "normalization_version": "measurement_normalization.v1",
                    },
                    "weather": {
                        "canonical_value": 11.0,
                        "canonical_unit": "mm",
                        "normalization_version": "measurement_normalization.v1",
                    },
                    "normalization": {
                        "source_policy_ref": "source_policy_registry.v1",
                        "precision_policy_ref": "precision_policy.weather_metric.precipitation.v1",
                        "rounding_policy_ref": "rounding_policy.weather_metric.precipitation.v1",
                        "band_mapping_policy_ref": "band_mapping.precipitation_mm_threshold.v1",
                        "normalization_version": "measurement_normalization.v1",
                    },
                },
            },
            {
                "timestamp": "2026-04-18T01:00:00+00:00",
                "market_id": "678686",
                "market_probability": 0.67,
                "yes_price": 0.67,
                "no_price": 0.65,
                "model_band": "top_3",
                "market_band": "top_3",
                "confidence_score": 1.0,
                "comparison_status": "aligned",
            },
        ],
        resolver_report={
            "rules": [
                {
                    "market_id": "rain_001",
                    "market_question": "Will rainfall in Shanghai on Apr 18 be between 10mm and 20mm?",
                    "resolver_status": "matched",
                    "resolver_reason": "matched_by_market_id",
                    "resolver_confidence": 0.88,
                    "market_family": "weather_metric",
                    "required_data_source": "wunderground_zspd",
                    "band_scheme": "precipitation_range_3way",
                    "station_id": "ZSPD",
                    "target_date": "2026-04-18",
                    "variable_name": "daily_precipitation_sum",
                    "expected_band": "in_range",
                    "threshold_lower": 10.0,
                    "threshold_upper": 20.0,
                },
                {
                    "market_id": "678686",
                    "market_question": "Will 2026 be the hottest year on record?",
                    "resolver_status": "matched",
                    "resolver_reason": "global_temperature_index_snapshot_expected",
                    "resolver_confidence": 1.0,
                    "market_family": "global_temperature_index",
                    "required_data_source": "global_temperature_index_snapshot",
                    "band_scheme": "global_temperature_index_ordinal",
                    "expected_band": "top_1",
                },
            ]
        },
        official_records=[
            {
                "station_id": "ZSPD",
                "target_date": "2026-04-18",
                "variable_name": "daily_precipitation_sum",
                "official_value": 11.0,
                "source": "ncei_cdo_daily",
            }
        ],
    )

    summary = builder.build_summary(samples)

    assert summary["tracked_rows"] == 2
    assert summary["tracked_markets"] == 2
    assert summary["labeled_rows"] == 1
    assert summary["unlabeled_rows"] == 1
    assert summary["market_family_counts"]["weather_metric"] == 1
    assert summary["market_family_counts"]["global_temperature_index"] == 1
    assert summary["label_counts"]["YES"] == 1
    assert summary["label_counts"]["unlabeled"] == 1
    assert summary["schema_version"] == "feature_store_summary.v2"
    assert summary["canonical_rows"] >= 1
    assert summary["canonical_ratio"] is not None
    assert summary["source_policy_ref_counts"]["unknown"] >= 1


def test_feature_store_uses_market_level_official_record_without_resolver_rule():
    builder = HistoricalFeatureStoreBuilder()

    samples = builder.build_samples(
        comparison_rows=[
            {
                "timestamp": "2026-04-18T02:00:00+00:00",
                "market_id": "sample_market_001",
                "market_probability": 0.58,
                "yes_price": 0.58,
                "no_price": 0.42,
                "model_band": "28",
                "market_band": "28",
                "confidence_score": 0.91,
                "comparison_status": "aligned",
                "top_parameter_view": {
                    "forecast": {
                        "canonical_value": 28.0,
                        "canonical_unit": "celsius",
                        "normalization_version": "measurement_normalization.v1",
                    },
                    "weather": {
                        "canonical_value": 28.0,
                        "canonical_unit": "celsius",
                        "normalization_version": "measurement_normalization.v1",
                    },
                    "normalization": {
                        "source_policy_ref": "source_policy_registry.v1",
                        "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
                        "rounding_policy_ref": "rounding_policy.temperature_daily_max.v1",
                        "band_mapping_policy_ref": "band_mapping.temperature_celsius_integer.v1",
                        "normalization_version": "measurement_normalization.v1",
                    },
                },
            }
        ],
        resolver_report={"rules": []},
        official_records=[
            {
                "market_id": "sample_market_001",
                "market_family": "station_temperature",
                "target_date": "2026-04-12",
                "variable_name": "daily_max_temperature",
                "station_id": "KNYC",
                "official_value": 28.0,
                "resolved_band": "28",
                "expected_band": "28",
                "source": "sample.station_settlement",
            }
        ],
    )

    assert len(samples) == 1
    sample = samples[0]
    assert sample.market_id == "sample_market_001"
    assert sample.resolved_band == "28"
    assert sample.outcome == "YES"
    assert sample.is_labeled is True
    assert sample.label_source == "sample.station_settlement"


def test_load_optional_json_records_supports_jsonl(tmp_path):
    path = tmp_path / "official_history.jsonl"
    path.write_text(
        '\n'.join(
            [
                '{"market_id":"m1","resolved_band":"28"}',
                '{"market_id":"m2","resolved_band":"top_3"}',
            ]
        )
        + '\n',
        encoding="utf-8",
    )

    records = load_optional_json_records(path)

    assert len(records) == 2
    assert records[0]["market_id"] == "m1"
    assert records[1]["resolved_band"] == "top_3"
