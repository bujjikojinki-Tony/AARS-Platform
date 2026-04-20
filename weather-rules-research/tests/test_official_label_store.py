from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.outputs.official_label_store import (
    OfficialLabelStoreBuilder,
    StationOfficialRecordBuilder,
)


def test_official_label_store_builds_global_and_sea_ice_records():
    builder = OfficialLabelStoreBuilder()

    records = builder.build_records(
        resolver_report={
            "rules": [
                {
                    "market_id": "678686",
                    "market_question": "Will 2026 be the hottest year on record?",
                    "market_family": "global_temperature_index",
                    "resolver_status": "matched",
                    "expected_band": "top_1",
                },
                {
                    "market_id": "693870",
                    "market_question": "Will the minimum Arctic sea ice extent this summer be between 4.0m & 4.2m square kilometers?",
                    "market_family": "sea_ice_extent",
                    "resolver_status": "matched",
                    "expected_band": "in_range",
                    "threshold_lower": 4.0,
                    "threshold_upper": 4.2,
                },
            ]
        },
        global_temperature_index_snapshot={
            "timestamp": "2026-04-13T12:00:00+00:00",
            "year": 2026,
            "ordinal_rank": 3,
            "band": "top_3",
            "source": "sample.global_temperature_index",
        },
        sea_ice_extent_snapshot={
            "timestamp": "2026-04-17T00:00:00+00:00",
            "season_year": 2026,
            "minimum_extent": 4.1,
            "unit": "million_sq_km",
            "source": "sample.nsidc_sea_ice_extent",
        },
    )

    assert len(records) == 2

    global_record = next(record for record in records if record["market_id"] == "678686")
    sea_ice_record = next(record for record in records if record["market_id"] == "693870")

    assert global_record["official_value"] == 3.0
    assert global_record["resolved_band"] == "top_3"
    assert global_record["label_type"] == "snapshot_grade"

    assert sea_ice_record["official_value"] == 4.1
    assert sea_ice_record["resolved_band"] == "in_range"
    assert sea_ice_record["label_type"] == "snapshot_grade"


def test_official_label_store_summary_counts_families():
    builder = OfficialLabelStoreBuilder()

    summary = builder.build_summary(
        [
            {"market_id": "678686", "market_family": "global_temperature_index", "source": "sample.global"},
            {"market_id": "693870", "market_family": "sea_ice_extent", "source": "sample.nsidc"},
        ]
    )

    assert summary["record_count"] == 2
    assert summary["market_family_counts"]["global_temperature_index"] == 1
    assert summary["market_family_counts"]["sea_ice_extent"] == 1


def test_official_label_store_writes_history_jsonl(tmp_path):
    builder = OfficialLabelStoreBuilder()
    out = tmp_path / "official_history.jsonl"

    builder.write_history_jsonl(
        [
            {"market_id": "m1", "official_value": 1.0},
            {"market_id": "m2", "official_value": 2.0},
        ],
        out,
    )

    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert '"market_id": "m1"' in lines[0]


def test_official_label_store_appends_history_without_duplicates(tmp_path):
    builder = OfficialLabelStoreBuilder()
    out = tmp_path / "official_history.jsonl"

    path, appended_first = builder.append_history_jsonl(
        [
            {
                "market_id": "m1",
                "target_date": "2026-04-12",
                "variable_name": "daily_max_temperature",
                "resolved_band": "28",
                "official_value": 28.0,
            }
        ],
        out,
    )
    _, appended_second = builder.append_history_jsonl(
        [
            {
                "market_id": "m1",
                "target_date": "2026-04-12",
                "variable_name": "daily_max_temperature",
                "resolved_band": "28",
                "official_value": 28.0,
            },
            {
                "market_id": "m2",
                "target_date": "2026-04-13",
                "variable_name": "daily_max_temperature",
                "resolved_band": "27",
                "official_value": 27.0,
            },
        ],
        out,
    )

    loaded = builder.load_history_jsonl(path)
    assert appended_first == 1
    assert appended_second == 1
    assert len(loaded) == 2
    assert loaded[0]["market_id"] == "m1"
    assert loaded[1]["market_id"] == "m2"


def test_station_official_record_builder_builds_temperature_records():
    builder = StationOfficialRecordBuilder()

    records = builder.build_records(
        rules=[
            MarketRule(
                market_id="sample_market_001",
                market_question="Highest temperature in Central Park on Apr 12?",
                market_type="daily_high_temperature",
                location_name="Central Park",
                target_date="Apr 12",
                station_name="New York City Central Park",
                nws_station_id="KNYC",
                cdo_station_id="GHCND:USW00094728",
                variable_name="daily_max_temperature",
                timezone="America/New_York",
                source_name="market_rules",
                raw_rules_text="Resolves using official station data from Central Park in New York time for the daily high.",
                parse_confidence=0.92,
                needs_review=False,
            )
        ],
        scenarios=[
            {
                "market_id": "sample_market_001",
                "target_date": "2026-04-12",
                "official_value": 28.0,
                "expected_band": "28",
                "source": "sample.station_settlement",
            }
        ],
    )

    assert len(records) == 1
    record = records[0]
    assert record["market_id"] == "sample_market_001"
    assert record["station_id"] == "KNYC"
    assert record["official_value"] == 28.0
    assert record["resolved_band"] == "28"
    assert record["label_type"] == "settlement_grade"
