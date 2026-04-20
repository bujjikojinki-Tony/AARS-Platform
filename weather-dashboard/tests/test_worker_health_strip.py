from weather_dashboard.ui.worker_health_strip import build_worker_health_strip_items


def test_worker_health_strip_items_empty_without_report():
    assert build_worker_health_strip_items(None) == []


def test_worker_health_strip_items_formats_freshness():
    items = build_worker_health_strip_items(
        {
            "workers": [
                {"label": "Market", "status": "healthy", "freshness_seconds": 12.7},
                {"label": "Forecast", "status": "stale", "freshness_seconds": None},
            ]
        }
    )

    assert items[0]["label"] == "Market"
    assert items[0]["freshness"] == "12s"
    assert items[1]["status"] == "stale"
    assert items[1]["freshness"] == "-"
