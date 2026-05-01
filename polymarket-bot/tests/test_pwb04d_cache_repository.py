from backend.models.polymarket import MarketSourceMode
from backend.models.polymarket import PolymarketConnectorHealth
from backend.models.polymarket import PolymarketMarketRecord
from backend.storage.db import init_db
from backend.storage.repositories import Repository


def test_polymarket_market_cache_save_and_list(tmp_path):
    db_path = str(tmp_path / "pwb04d_cache.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    record = PolymarketMarketRecord(
        polymarket_market_id="pm_weather_1",
        condition_id="cond_weather_1",
        question="Will Tokyo high temperature exceed 30C on June 1?",
        slug="tokyo-high-temperature-june-1",
        category="weather",
        active=True,
        closed=False,
        archived=False,
        outcomes=["Yes", "No"],
        outcome_prices=[0.52, 0.49],
        clob_token_ids=["token_yes", "token_no"],
        liquidity=1000,
        volume=5000,
        raw_payload={"mock": True},
    )
    repo.save_polymarket_market_record(record)

    rows = repo.list_polymarket_market_cache()

    assert len(rows) == 1
    row = rows[0]
    assert row["polymarket_market_id"] == "pm_weather_1"
    assert row["condition_id"] == "cond_weather_1"
    assert row["question"] == record.question
    assert row["active"] is True
    assert row["closed"] is False
    assert row["archived"] is False
    assert row["outcomes"] == ["Yes", "No"]
    assert row["outcome_prices"] == [0.52, 0.49]
    assert row["clob_token_ids"] == ["token_yes", "token_no"]
    assert row["raw_payload"] == {"mock": True}


def test_polymarket_weather_market_cache_query(tmp_path):
    db_path = str(tmp_path / "pwb04d_weather_cache.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    weather = PolymarketMarketRecord(
        polymarket_market_id="pm_weather_1",
        condition_id="cond_weather_1",
        question="Will Tokyo high temperature exceed 30C on June 1?",
        slug="tokyo-high-temperature-june-1",
        category="weather",
        outcomes=["Yes", "No"],
        outcome_prices=[0.52, 0.49],
    )
    election = PolymarketMarketRecord(
        polymarket_market_id="pm_election_1",
        condition_id="cond_election_1",
        question="Will candidate X win the election?",
        slug="candidate-x-election",
        category="politics",
        outcomes=["Yes", "No"],
        outcome_prices=[0.55, 0.46],
    )
    repo.save_polymarket_market_record(weather)
    repo.save_polymarket_market_record(election)

    weather_rows = repo.list_polymarket_weather_market_cache()

    assert len(weather_rows) == 1
    assert weather_rows[0]["polymarket_market_id"] == "pm_weather_1"


def test_polymarket_connector_health_save_and_latest(tmp_path):
    db_path = str(tmp_path / "pwb04d_health.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    health = PolymarketConnectorHealth(
        gamma_reachable=False,
        clob_reachable=False,
        mode=MarketSourceMode.MOCK_ONLY,
        warnings=["Polymarket network access disabled by config."],
    )
    repo.save_polymarket_connector_health(health)

    latest = repo.get_latest_polymarket_connector_health()

    assert latest is not None
    assert latest["connector_id"] == "polymarket_read_only_v0"
    assert latest["gamma_reachable"] is False
    assert latest["clob_reachable"] is False
    assert latest["mode"] == "MOCK_ONLY"
    assert "network access disabled" in latest["warnings"][0]


def test_polymarket_connector_health_history(tmp_path):
    db_path = str(tmp_path / "pwb04d_health_history.sqlite")
    init_db(db_path)
    repo = Repository(db_path)
    repo.save_polymarket_connector_health(
        PolymarketConnectorHealth(
            gamma_reachable=False,
            clob_reachable=False,
            mode=MarketSourceMode.MOCK_ONLY,
            warnings=["first"],
        )
    )
    repo.save_polymarket_connector_health(
        PolymarketConnectorHealth(
            gamma_reachable=False,
            clob_reachable=False,
            mode=MarketSourceMode.HYBRID,
            warnings=["second"],
        )
    )

    rows = repo.list_polymarket_connector_health()

    assert len(rows) == 2
    assert rows[0]["mode"] == "HYBRID"
    assert rows[0]["warnings"] == ["second"]
    assert rows[1]["mode"] == "MOCK_ONLY"
    assert rows[1]["warnings"] == ["first"]
