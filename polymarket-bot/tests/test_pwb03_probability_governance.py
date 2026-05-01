from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app_factory import create_app
from backend.storage.db import init_db
from backend.models.weather import ParseConfidence, WeatherDirection, WeatherUnit, WeatherView
from backend.probability.gaussian_probability_engine import GaussianProbabilityEngine
from backend.probability.probability_view_builder import ProbabilityViewBuilder


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs" / "implementation"


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "pwb03_api_test.sqlite"
    init_db(str(db_path))
    return str(db_path)


@pytest.fixture
def app(test_db):
    return create_app(test_db, allow_network=False)


@pytest.fixture
def client(app):
    return TestClient(app)


def _build_tokyo_view() -> WeatherView:
    return WeatherView(
        weather_view_id="wv_test",
        evidence_pack_id="evp_test",
        market_id="mkt_test",
        city="Tokyo",
        target_date="2026-06-01",
        expected_value=31.2,
        expected_range_low=28.7,
        expected_range_high=33.7,
        sigma=2.5,
        threshold=30,
        direction=WeatherDirection.ABOVE,
        unit=WeatherUnit.C,
        confidence=ParseConfidence.MEDIUM,
    )


def test_gaussian_v0_remains_active_primary_probability_baseline():
    view = _build_tokyo_view()
    probability_view = ProbabilityViewBuilder().build(view)

    assert probability_view.engine_id == "gaussian_v0"
    assert 0.67 < probability_view.model_probability < 0.70

    probability, warnings = GaussianProbabilityEngine().compute(view)
    assert probability == probability_view.model_probability
    assert warnings == []


def test_live_execution_remains_disabled(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["live_execution"] is False
    assert body["status"] == "ok"


def test_pwb03_freeze_docs_state_shadow_placeholders_only():
    status_note = (DOCS_DIR / "round-pwb-03-status-note.md").read_text(encoding="utf-8")
    accepted_inventory = (DOCS_DIR / "round-pwb-03-accepted-path-inventory.md").read_text(encoding="utf-8")
    freeze_note = (DOCS_DIR / "round-pwb-03-baseline-freeze.md").read_text(encoding="utf-8")

    for text in (status_note, accepted_inventory, freeze_note):
        assert "gaussian_v0" in text
        assert "shadow placeholder" in text.lower()
        assert "live execution remains disabled" in text.lower() or "live execution" in text.lower()

    assert "DEB" in freeze_note
    assert "EMOS" in freeze_note
    assert "shadow placeholder only" in freeze_note.lower()
    assert "no live trading" in freeze_note.lower()
