from __future__ import annotations

from uuid import uuid4

from backend.models.weather import EvidenceConflictLevel
from backend.models.weather import EvidenceFreshness
from backend.models.weather import EvidencePack
from backend.models.weather import FreshnessStatus
from backend.models.weather import ProbabilityView
from backend.models.weather import SourceType
from backend.models.weather import TrustLevel
from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherMarketDescriptor
from backend.models.weather import WeatherMetric
from backend.models.weather import WeatherSourceRecord
from backend.models.weather import WeatherUnit
from backend.models.weather import WeatherView
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def test_weather_storage_round_trip(tmp_path) -> None:
    db_path = str(tmp_path / "weather_storage.sqlite")
    init_db(db_path)
    repo = Repository(db_path)

    descriptor = WeatherMarketDescriptor(
        market_id="mock_weather_strong_yes",
        question="Will Tokyo high temperature exceed 30C on June 1?",
        city="Tokyo",
        country="JP",
        target_date="2026-06-01",
        metric=WeatherMetric.DAILY_HIGH,
        threshold=30,
        unit=WeatherUnit.C,
        direction=WeatherDirection.ABOVE,
    )
    source = WeatherSourceRecord(
        source_id=f"src_{uuid4().hex[:8]}",
        market_id=descriptor.market_id,
        source_name="open_meteo_mock",
        source_type=SourceType.FORECAST,
        city="Tokyo",
        target_date="2026-06-01",
        raw_payload={"daily": {"temperature_2m_max": [31.2]}},
        normalized_value=31.2,
        unit=WeatherUnit.C,
        freshness_status=FreshnessStatus.FRESH,
        trust_level=TrustLevel.PRIMARY,
    )
    pack = EvidencePack(
        evidence_pack_id=f"evp_{uuid4().hex[:8]}",
        market_id=descriptor.market_id,
        descriptor=descriptor,
        sources=[source],
        evidence_freshness=EvidenceFreshness.FRESH,
        evidence_conflict_level=EvidenceConflictLevel.NONE,
        raw_refs=[source.source_id],
    )
    view = WeatherView(
        weather_view_id=f"wv_{uuid4().hex[:8]}",
        evidence_pack_id=pack.evidence_pack_id,
        market_id=descriptor.market_id,
        city="Tokyo",
        target_date="2026-06-01",
        expected_value=31.2,
        expected_range_low=28.7,
        expected_range_high=33.7,
        sigma=2.5,
        threshold=30,
        direction=WeatherDirection.ABOVE,
        unit=WeatherUnit.C,
        evidence_summary=["Open-Meteo mock forecast daily high = 31.2C"],
    )
    probability = ProbabilityView(
        probability_view_id=f"pv_{uuid4().hex[:8]}",
        weather_view_id=view.weather_view_id,
        market_id=descriptor.market_id,
        model_probability=0.684,
        threshold=30,
        expected_value=31.2,
        sigma=2.5,
        direction=WeatherDirection.ABOVE,
    )

    repo.save_weather_descriptor(descriptor)
    repo.save_weather_source(source)
    repo.save_evidence_pack(pack)
    repo.save_weather_view(view)
    repo.save_probability_view(probability)

    assert repo.list_weather_descriptors()[0]["market_id"] == descriptor.market_id
    assert repo.get_latest_evidence_pack(descriptor.market_id)["market_id"] == descriptor.market_id
    assert repo.get_latest_weather_view(descriptor.market_id)["market_id"] == descriptor.market_id
    assert repo.get_latest_probability_view(descriptor.market_id)["market_id"] == descriptor.market_id
