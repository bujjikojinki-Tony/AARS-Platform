from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = PACKAGE_ROOT.parent
DATA_DIR = PACKAGE_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "outputs"
REGISTRIES_DIR = DATA_DIR / "registries"
MEASUREMENT_REGISTRY_DIR = REGISTRIES_DIR / "measurement_registry"

for path in [DATA_DIR, RAW_DIR, OUTPUT_DIR, REGISTRIES_DIR, MEASUREMENT_REGISTRY_DIR]:
    path.mkdir(parents=True, exist_ok=True)

REALTIME_MARKET_JSON = Path(
    __import__("os").getenv(
        "REALTIME_MARKET_JSON",
        str(WORKSPACE_ROOT / "polymarket-weather-ingest" / "data" / "outputs" / "market_realtime_simple.json"),
    )
)

REALTIME_MARKET_SNAPSHOTS_GLOB = __import__("os").getenv(
    "REALTIME_MARKET_SNAPSHOTS_GLOB",
    str(WORKSPACE_ROOT / "polymarket-weather-ingest" / "data" / "outputs" / "market_realtime_simple_*.json"),
)

SOURCE_POLICY_REGISTRY_JSON = Path(
    __import__("os").getenv(
        "SOURCE_POLICY_REGISTRY_JSON",
        str(REGISTRIES_DIR / "source_policy_registry.json"),
    )
)
UNIT_REGISTRY_JSON = Path(
    __import__("os").getenv(
        "UNIT_REGISTRY_JSON",
        str(MEASUREMENT_REGISTRY_DIR / "unit_registry.json"),
    )
)
PRECISION_POLICY_REGISTRY_JSON = Path(
    __import__("os").getenv(
        "PRECISION_POLICY_REGISTRY_JSON",
        str(MEASUREMENT_REGISTRY_DIR / "precision_policy_registry.json"),
    )
)
ROUNDING_POLICY_REGISTRY_JSON = Path(
    __import__("os").getenv(
        "ROUNDING_POLICY_REGISTRY_JSON",
        str(MEASUREMENT_REGISTRY_DIR / "rounding_policy_registry.json"),
    )
)
BAND_MAPPING_POLICY_REGISTRY_JSON = Path(
    __import__("os").getenv(
        "BAND_MAPPING_POLICY_REGISTRY_JSON",
        str(MEASUREMENT_REGISTRY_DIR / "band_mapping_policy_registry.json"),
    )
)

RULEBOOK_JSON = Path(
    __import__("os").getenv(
        "RULEBOOK_JSON",
        str(OUTPUT_DIR / "sample_rulebook.json"),
    )
)

STATION_MAP_JSON = Path(
    __import__("os").getenv(
        "STATION_MAP_JSON",
        str(DATA_DIR / "processed" / "station_maps" / "manual_station_map.json"),
    )
)

RESOLVED_MARKET_RULES_DIR = Path(
    __import__("os").getenv(
        "RESOLVED_MARKET_RULES_DIR",
        str(OUTPUT_DIR / "resolved_market_rules"),
    )
)

RESOLVER_REPORT_JSON = Path(
    __import__("os").getenv(
        "RESOLVER_REPORT_JSON",
        str(OUTPUT_DIR / "resolver_report.json"),
    )
)

GLOBAL_TEMPERATURE_INDEX_JSON = Path(
    __import__("os").getenv(
        "GLOBAL_TEMPERATURE_INDEX_JSON",
        str(OUTPUT_DIR / "global_temperature_index_snapshot.json"),
    )
)

SEA_ICE_EXTENT_JSON = Path(
    __import__("os").getenv(
        "SEA_ICE_EXTENT_JSON",
        str(OUTPUT_DIR / "sea_ice_extent_snapshot.json"),
    )
)

OFFICIAL_RECORDS_DIR = Path(
    __import__("os").getenv(
        "OFFICIAL_RECORDS_DIR",
        str(OUTPUT_DIR / "official_records"),
    )
)

OFFICIAL_LABEL_SUMMARY_JSON = Path(
    __import__("os").getenv(
        "OFFICIAL_LABEL_SUMMARY_JSON",
        str(OUTPUT_DIR / "official_label_summary.json"),
    )
)

OFFICIAL_HISTORY_JSONL = Path(
    __import__("os").getenv(
        "OFFICIAL_HISTORY_JSONL",
        str(OUTPUT_DIR / "official_history.jsonl"),
    )
)

STATION_OFFICIAL_SCENARIOS_JSON = Path(
    __import__("os").getenv(
        "STATION_OFFICIAL_SCENARIOS_JSON",
        str(OUTPUT_DIR / "sample_station_official_records.json"),
    )
)

STATION_SETTLEMENT_RECORDS_JSON = Path(
    __import__("os").getenv(
        "STATION_SETTLEMENT_RECORDS_JSON",
        str(OUTPUT_DIR / "station_settlement_records.json"),
    )
)

STATION_SETTLEMENT_SUMMARY_JSON = Path(
    __import__("os").getenv(
        "STATION_SETTLEMENT_SUMMARY_JSON",
        str(OUTPUT_DIR / "station_settlement_summary.json"),
    )
)

OFFICIAL_STATION_FETCH_ENABLED = (
    __import__("os").getenv("OFFICIAL_STATION_FETCH_ENABLED", "0") == "1"
)

STATION_SETTLEMENT_REFRESH_INTERVAL_SECONDS = int(
    __import__("os").getenv("STATION_SETTLEMENT_REFRESH_INTERVAL_SECONDS", "900")
)

STATION_SETTLEMENT_MAX_CYCLES = int(
    __import__("os").getenv("STATION_SETTLEMENT_MAX_CYCLES", "0")
)

OFFICIAL_LABEL_REFRESH_INTERVAL_SECONDS = int(
    __import__("os").getenv("OFFICIAL_LABEL_REFRESH_INTERVAL_SECONDS", "1800")
)

OFFICIAL_LABEL_MAX_CYCLES = int(
    __import__("os").getenv("OFFICIAL_LABEL_MAX_CYCLES", "0")
)
