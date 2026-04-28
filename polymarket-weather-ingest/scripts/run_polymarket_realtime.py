from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from polymarket_weather_ingest.discovery.weather_filter import WeatherFilter
from polymarket_weather_ingest.ingest.gamma_client import GammaClient
from polymarket_weather_ingest.ingest.market_snapshot_builder import MarketSnapshotBuilder
from polymarket_weather_ingest.ingest.market_state_reducer import MarketStateReducer
from polymarket_weather_ingest.ingest.market_band_scheme import derive_market_band_spec
from polymarket_weather_ingest.ingest.realtime_registry import RealtimeRegistry
from polymarket_weather_ingest.ingest.ws_market_stream import PolymarketMarketStream


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "outputs"
SNAPSHOT_PATH = OUTPUT_DIR / "market_realtime_snapshot.json"
SIMPLE_PATH = OUTPUT_DIR / "market_realtime_simple.json"
REGISTRY_PATH = OUTPUT_DIR / "weather_asset_registry.json"
WEATHER_BUNDLES_PATH = OUTPUT_DIR / "weather_realtime_bundles.json"
DISCOVERY_PAGE_SIZE = 100
DISCOVERY_MAX_OFFSET = 1000
PINNED_MARKET_ID = os.getenv("PINNED_MARKET_ID") or None
PINNED_MARKET_FAMILY = os.getenv("PINNED_MARKET_FAMILY") or None
if PINNED_MARKET_FAMILY == "all":
    PINNED_MARKET_FAMILY = None
USE_DISCOVERY_CACHE_FALLBACK = os.getenv("USE_DISCOVERY_CACHE_FALLBACK", "1") != "0"


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def read_json(path: Path) -> object | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def extract_asset_ids(registry_rows: list[dict]) -> list[str]:
    asset_ids: list[str] = []
    for row in registry_rows:
        yes_asset_id = row.get("yes_asset_id")
        no_asset_id = row.get("no_asset_id")

        if yes_asset_id:
            asset_ids.append(str(yes_asset_id))
        if no_asset_id:
            asset_ids.append(str(no_asset_id))

    # dedupe but keep order
    seen = set()
    result = []
    for a in asset_ids:
        if a not in seen:
            seen.add(a)
            result.append(a)
    return result


def family_simple_path(market_family: str) -> Path:
    safe_family = market_family or "unknown"
    return OUTPUT_DIR / f"market_realtime_simple_{safe_family}.json"


def has_price_payload(row: dict) -> bool:
    return any(
        row.get(field) is not None
        for field in ("market_probability", "yes_price", "no_price")
    )


def select_preferred_market(
    rows: list[dict],
    pinned_market_id: str | None = None,
    pinned_family: str | None = None,
) -> dict | None:
    if not rows:
        return None

    priced_rows = [row for row in rows if has_price_payload(row)]
    selected_pool = priced_rows or rows

    if pinned_market_id:
        pinned_rows = [row for row in selected_pool if str(row.get("market_id")) == pinned_market_id]
        if pinned_rows:
            return sorted(pinned_rows, key=market_priority)[0]

    if pinned_family:
        family_rows = [row for row in selected_pool if row.get("market_family") == pinned_family]
        if family_rows:
            return sorted(family_rows, key=market_priority)[0]

    weather_rows = [row for row in selected_pool if is_likely_weather_market(row)]
    selected_pool = weather_rows if weather_rows else selected_pool
    return sorted(selected_pool, key=market_priority)[0]


def write_family_simple_snapshots(rows: list[dict]) -> dict[str, dict]:
    selected_by_family: dict[str, dict] = {}
    grouped: dict[str, list[dict]] = {}

    for row in rows:
        family = row.get("market_family") or "unknown"
        grouped.setdefault(family, []).append(row)

    for family, family_rows in grouped.items():
        selected = select_preferred_market(
            family_rows,
            pinned_market_id=PINNED_MARKET_ID,
            pinned_family=PINNED_MARKET_FAMILY,
        )
        if selected is None:
            continue
        selected_by_family[family] = selected
        write_json(family_simple_path(family), selected)

    return selected_by_family


def build_initial_simple_from_bundles(bundles: list[dict]) -> dict | None:
    if not bundles:
        return None

    selected = select_preferred_bundle(bundles)
    market = selected.get("market") or {}
    question = market.get("market_question")

    return {
        "market_id": market.get("market_id"),
        "market_question": question,
        "location_name": extract_location_name(question),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "favored_side": None,
        "market_probability": None,
        "market_family": classify_market_family(question),
        "market_band": derive_market_band_spec(question, None).band,
        "market_band_scheme": derive_market_band_spec(question, None).scheme,
        "yes_price": None,
        "no_price": None,
    }


def build_initial_family_snapshots(bundles: list[dict]) -> dict[str, dict]:
    snapshots: dict[str, dict] = {}
    grouped: dict[str, list[dict]] = {}

    for bundle in bundles:
        market = bundle.get("market") or {}
        question = market.get("market_question")
        family = classify_market_family(question)
        grouped.setdefault(family, []).append(bundle)

    for family, family_bundles in grouped.items():
        selected = select_preferred_bundle(family_bundles)
        market = selected.get("market") or {}
        question = market.get("market_question")
        snapshots[family] = {
            "market_id": market.get("market_id"),
            "market_question": question,
            "location_name": extract_location_name(question),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "favored_side": None,
            "market_probability": None,
            "market_family": classify_market_family(question),
            "market_band": derive_market_band_spec(question, None).band,
            "market_band_scheme": derive_market_band_spec(question, None).scheme,
            "yes_price": None,
            "no_price": None,
        }

    return snapshots


def load_existing_simple_snapshots(output_dir: Path) -> list[dict]:
    snapshots: list[dict] = []
    for path in sorted(output_dir.glob("market_realtime_simple*.json")):
        payload = read_json(path)
        if isinstance(payload, dict):
            snapshots.append(payload)
    return snapshots


def select_startup_simple_snapshot(
    initial_family_snapshots: dict[str, dict],
    output_dir: Path,
    pinned_market_id: str | None = None,
    pinned_family: str | None = None,
) -> dict | None:
    startup_candidates = list(initial_family_snapshots.values())
    startup_candidates.extend(load_existing_simple_snapshots(output_dir))
    selected = select_preferred_market(
        startup_candidates,
        pinned_market_id=pinned_market_id,
        pinned_family=pinned_family,
    )
    if selected is not None and has_price_payload(selected):
        return selected
    return None


def select_preferred_bundle(bundles: list[dict]) -> dict:
    def sort_key(bundle: dict) -> tuple[float, int]:
        market = bundle.get("market") or {}
        question = market.get("market_question")
        updated_at = market.get("updated_at") or bundle.get("price_state", {}).get("observed_at") or ""
        try:
            updated_at_ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).timestamp() if updated_at else 0.0
        except ValueError:
            updated_at_ts = 0.0
        family = classify_market_family(question)
        family_priority = {
            "global_temperature_index": 0,
            "station_temperature": 1,
            "sea_ice_extent": 2,
            "weather_metric": 3,
            "unknown": 9,
        }.get(family, 9)
        return -updated_at_ts, family_priority

    return sorted(bundles, key=sort_key)[0]


def build_market_lookup(registry_rows: list[dict]) -> dict[str, dict]:
    """
    Build asset_id -> market info lookup.
    """
    lookup: dict[str, dict] = {}

    for row in registry_rows:
        yes_asset_id = row.get("yes_asset_id")
        no_asset_id = row.get("no_asset_id")

        if yes_asset_id:
            lookup[str(yes_asset_id)] = {
                "market_id": row.get("market_id"),
                "market_question": row.get("market_question"),
                "event_title": row.get("event_title"),
                "side": "yes",
            }

        if no_asset_id:
            lookup[str(no_asset_id)] = {
                "market_id": row.get("market_id"),
                "market_question": row.get("market_question"),
                "event_title": row.get("event_title"),
                "side": "no",
            }

    return lookup


def extract_location_name(question: str | None) -> str:
    if not question:
        return "UNKNOWN"

    lower = question.lower()
    if " in " in lower and " on " in lower:
        try:
            start = lower.index(" in ") + 4
            end = lower.index(" on ")
            return question[start:end].strip()
        except ValueError:
            return "UNKNOWN"

    return "UNKNOWN"


def classify_market_family(question: str | None) -> str:
    q = (question or "").lower()

    if "hottest year" in q or "rank among the hottest years" in q:
        return "global_temperature_index"
    if "sea ice" in q and "extent" in q:
        return "sea_ice_extent"
    if any(keyword in q for keyword in ("temperature", "highest temperature", "lowest temperature")):
        return "station_temperature"
    if any(keyword in q for keyword in ("precipitation", "rainfall", "snowfall", "wind", "humidity")):
        return "weather_metric"
    return "unknown"


def market_priority(row: dict) -> tuple[int, float, int]:
    updated_at = str(row.get("updated_at") or "")
    try:
        updated_at_ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).timestamp() if updated_at else 0.0
    except ValueError:
        updated_at_ts = 0.0
    family = row.get("market_family") or "unknown"
    family_priority = {
        "global_temperature_index": 0,
        "station_temperature": 1,
        "sea_ice_extent": 2,
        "weather_metric": 3,
        "unknown": 9,
    }
    price_priority = 0 if has_price_payload(row) else 1
    return price_priority, -updated_at_ts, family_priority.get(family, 9)


def aggregate_market_simple(
    reducer_snapshot: list[dict],
    asset_lookup: dict[str, dict],
) -> list[dict]:
    """
    Convert asset-level state into market-level simplified state.

    Logic:
    - group yes/no assets by market_id
    - use last_trade_price if available, otherwise midpoint(best_bid, best_ask)
    - favored side = higher current price
    - market_probability = favored side price
    - market_band = derived placeholder band from probability
    """
    grouped: dict[str, dict] = {}

    for asset_state in reducer_snapshot:
        asset_id = str(asset_state.get("asset_id"))
        meta = asset_lookup.get(asset_id)
        if meta is None:
            continue

        market_id = str(meta["market_id"])
        market_question = meta["market_question"]
        side = meta["side"]

        current_price = asset_state.get("last_trade_price")
        if current_price is None:
            best_bid = asset_state.get("best_bid")
            best_ask = asset_state.get("best_ask")
            if best_bid is not None and best_ask is not None:
                try:
                    current_price = (float(best_bid) + float(best_ask)) / 2
                except Exception:
                    current_price = None

        grouped.setdefault(
            market_id,
            {
                "market_id": market_id,
                "market_question": market_question,
                "location_name": extract_location_name(market_question),
                "updated_at": asset_state.get("updated_at"),
                "yes_price": None,
                "no_price": None,
            },
        )

        if side == "yes":
            grouped[market_id]["yes_price"] = current_price
        elif side == "no":
            grouped[market_id]["no_price"] = current_price

        grouped[market_id]["updated_at"] = asset_state.get("updated_at")

    simplified: list[dict] = []

    for market_id, row in grouped.items():
        yes_price = row.get("yes_price")
        no_price = row.get("no_price")

        favored_side = None
        market_probability = None

        if yes_price is not None and no_price is not None:
            try:
                yes_price = float(yes_price)
                no_price = float(no_price)
                if yes_price >= no_price:
                    favored_side = "yes"
                    market_probability = yes_price
                else:
                    favored_side = "no"
                    market_probability = no_price
            except Exception:
                favored_side = None
                market_probability = None
        elif yes_price is not None:
            favored_side = "yes"
            market_probability = float(yes_price)
        elif no_price is not None:
            favored_side = "no"
            market_probability = float(no_price)

        spec = derive_market_band_spec(row.get("market_question"), market_probability)

        simplified.append(
            {
                "market_id": row["market_id"],
                "market_question": row["market_question"],
                "location_name": row["location_name"],
                "updated_at": row["updated_at"],
                "favored_side": favored_side,
                "market_probability": market_probability,
                "market_family": classify_market_family(row.get("market_question")),
                "market_band": spec.band,
                "market_band_scheme": spec.scheme,
                "market_band_label": spec.label,
                "market_band_lower": spec.lower_threshold,
                "market_band_upper": spec.upper_threshold,
                "market_band_unit": spec.unit,
                "yes_price": yes_price,
                "no_price": no_price,
            }
        )

    return simplified


def is_likely_weather_market(row: dict) -> bool:
    question = (row.get("market_question") or "").lower()
    location_name = row.get("location_name") or "UNKNOWN"

    if location_name == "UNKNOWN":
        return False

    keywords = [
        "temperature",
        "weather",
        "rain",
        "snow",
        "wind",
        "hurricane",
        "storm",
    ]
    return any(keyword in question for keyword in keywords)


async def discover_weather_registry() -> tuple[list[dict], list[dict]]:
    gamma = GammaClient()
    weather_filter = WeatherFilter()
    registry_builder = RealtimeRegistry()
    snapshot_builder = MarketSnapshotBuilder()

    events: list[dict] = []
    try:
        for offset in range(0, DISCOVERY_MAX_OFFSET, DISCOVERY_PAGE_SIZE):
            page = gamma.fetch_active_events_sync(limit=DISCOVERY_PAGE_SIZE, offset=offset)
            if not page:
                break
            events.extend(page)
    except Exception as exc:
        if not USE_DISCOVERY_CACHE_FALLBACK:
            raise
        cached_registry = read_json(REGISTRY_PATH)
        cached_bundles = read_json(WEATHER_BUNDLES_PATH)
        if isinstance(cached_registry, list) and isinstance(cached_bundles, list):
            print(f"[discovery] Gamma failed; using cache fallback: {exc}")
            return cached_registry, cached_bundles
        raise RuntimeError(
            "Gamma discovery failed and no cached discovery files were available"
        ) from exc

    weather_events = [event for event in events if weather_filter.is_weather_event(event)]
    registry_rows = registry_builder.build_asset_registry(weather_events)
    bundles = [snapshot_builder.build_from_event(event).model_dump() for event in weather_events]

    write_json(REGISTRY_PATH, registry_rows)
    write_json(WEATHER_BUNDLES_PATH, bundles)

    return registry_rows, bundles


async def run_market_stream(asset_ids: list[str], asset_lookup: dict[str, dict]) -> None:
    reducer = MarketStateReducer()

    async def on_event(event: dict) -> None:
        await reducer.on_event(event)

        reducer_snapshot = reducer.snapshot()

        snapshot_payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "asset_count": len(reducer.state_by_asset),
            "states": reducer_snapshot,
        }
        write_json(SNAPSHOT_PATH, snapshot_payload)

        simplified = aggregate_market_simple(
            reducer_snapshot=reducer_snapshot,
            asset_lookup=asset_lookup,
        )

        if simplified:
            write_family_simple_snapshots(simplified)
            selected = select_preferred_market(
                simplified,
                pinned_market_id=PINNED_MARKET_ID,
                pinned_family=PINNED_MARKET_FAMILY,
            )
            if selected is None:
                return
            write_json(SIMPLE_PATH, selected)

    stream = PolymarketMarketStream(asset_ids=asset_ids)
    await stream.run(on_event)


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    registry_rows, bundles = await discover_weather_registry()

    print("=" * 80)
    print("DISCOVERY COMPLETE")
    print(f"Weather events bundled : {len(bundles)}")
    print(f"Registry rows          : {len(registry_rows)}")
    print(f"Registry output        : {REGISTRY_PATH}")
    print(f"Bundle output          : {WEATHER_BUNDLES_PATH}")
    print("=" * 80)

    initial_family_snapshots = build_initial_family_snapshots(bundles)
    if initial_family_snapshots:
        for family, snapshot in initial_family_snapshots.items():
            existing_family_snapshot = read_json(family_simple_path(family))
            if isinstance(existing_family_snapshot, dict) and has_price_payload(existing_family_snapshot):
                selected_family_snapshot = existing_family_snapshot
            else:
                selected_family_snapshot = snapshot
            if selected_family_snapshot is not None:
                write_json(family_simple_path(family), selected_family_snapshot)

        initial_simple = select_startup_simple_snapshot(
            initial_family_snapshots=initial_family_snapshots,
            output_dir=OUTPUT_DIR,
            pinned_market_id=PINNED_MARKET_ID,
            pinned_family=PINNED_MARKET_FAMILY,
        )
        if initial_simple is not None:
            write_json(SIMPLE_PATH, initial_simple)

    asset_ids = extract_asset_ids(registry_rows)
    asset_lookup = build_market_lookup(registry_rows)

    if not asset_ids:
        raise RuntimeError("No asset_ids found for weather markets")

    print("STARTING MARKET STREAM")
    print(f"Subscribed asset_ids : {len(asset_ids)}")
    print(f"Full snapshot output : {SNAPSHOT_PATH}")
    print(f"Simple state output  : {SIMPLE_PATH}")
    print("=" * 80)

    await run_market_stream(asset_ids, asset_lookup)


if __name__ == "__main__":
    asyncio.run(main())
