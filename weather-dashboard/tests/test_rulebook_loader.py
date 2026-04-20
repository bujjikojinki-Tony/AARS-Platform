import json

from weather_dashboard.loaders.rulebook_loader import RulebookLoader


def test_rulebook_loader(tmp_path):
    path = tmp_path / "rulebook.json"
    path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "rules": [{"market_id": "m1"}],
            }
        ),
        encoding="utf-8",
    )

    loader = RulebookLoader()
    payload = loader.load(path)

    assert payload["version"] == "0.1"
    assert payload["rules"][0]["market_id"] == "m1"
