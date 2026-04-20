from __future__ import annotations

import json

from weather_execution_gateway.execution.intent_loader import IntentLoader


def test_intent_loader_lists_loads_and_marks_consumed(tmp_path) -> None:
    pending_dir = tmp_path / "pending_intents"
    pending_dir.mkdir()
    intent_path = pending_dir / "intent_1.json"
    intent_path.write_text(
        json.dumps(
            {
                "intent_id": "intent_1",
                "market_id": "sample_market_001",
                "signal_id": "sig_1",
                "side": "buy",
                "price": 0.42,
                "size": 10,
                "post_only": True,
                "max_slippage_pct": 0.02,
                "approved": True,
            }
        ),
        encoding="utf-8",
    )

    loader = IntentLoader(pending_dir=str(pending_dir))
    files = loader.list_pending_files()
    assert files == [intent_path]

    intent = loader.load_first_pending()
    assert intent is not None
    assert intent.intent_id == "intent_1"

    consumed_path = loader.mark_consumed(intent_path)
    assert consumed_path.exists()
    assert consumed_path.parent.name == "consumed_intents"
    assert not intent_path.exists()
