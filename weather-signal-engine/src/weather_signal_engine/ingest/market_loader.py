import json
from pathlib import Path

from weather_signal_engine.models.market_snapshot import MarketSnapshot


class MarketLoader:
    def load_stub(self, market_id: str, market_question: str) -> MarketSnapshot:
        return MarketSnapshot(
            market_id=market_id,
            market_question=market_question,
            observed_at="UNKNOWN",
            favored_band=None,
            implied_temperature_value=None,
            market_price_context=None,
            notes="stub market snapshot",
        )

    def load_from_file(self, path: str | Path) -> MarketSnapshot:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return MarketSnapshot(**payload)
