from weather_comparison_engine.status.gate_stack_consumer import consume_gate_stack_payload


def test_consumer_prefers_exact_market_view() -> None:
    result = consume_gate_stack_payload(
        {
            "schema_version": "gate_stack_api.v1",
            "generated_at": "2026-04-19T10:00:00+00:00",
            "market_id": "m-default",
            "gate_source": "api",
            "market_gate_views": [
                {"market_id": "m-1", "gate_source": "unified_fallback", "can_execute": False},
                {"market_id": "m-2", "gate_source": "api", "can_execute": True},
            ],
        },
        market_id="m-2",
    )

    assert result.gate_source == "api"
    assert result.schema_version_checked == "gate_stack_api.v1"
    assert result.generated_at == "2026-04-19T10:00:00+00:00"
    assert result.payload["market_id"] == "m-2"
    assert result.market_view == {"market_id": "m-2", "gate_source": "api", "can_execute": True}


def test_consumer_normalizes_unknown_gate_source_to_api() -> None:
    result = consume_gate_stack_payload(
        {
            "schema_version": "gate_stack_api.v1",
            "generated_at": "2026-04-19T10:00:00+00:00",
            "gate_source": "unexpected",
            "market_id": "m-default",
        }
    )

    assert result.gate_source == "api"
    assert result.schema_version_checked == "gate_stack_api.v1"
