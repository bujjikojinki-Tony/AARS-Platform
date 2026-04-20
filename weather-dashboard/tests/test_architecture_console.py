from weather_dashboard.ui.architecture_console import find_resolver_rule


def test_find_resolver_rule_requires_exact_market_match():
    report = {
        "rules": [
            {"market_id": "A", "resolver_status": "matched"},
            {"market_id": "B", "resolver_status": "matched"},
        ]
    }

    assert find_resolver_rule(report, "B") == {"market_id": "B", "resolver_status": "matched"}
    assert find_resolver_rule(report, "missing") is None
