from __future__ import annotations

from backend.app_factory import create_app as _create_app
from backend.models.polymarket import MarketSourceMode
from backend.storage.db import DEFAULT_DB_PATH


app = _create_app(
    DEFAULT_DB_PATH,
    allow_network=False,
    allow_polymarket_network=False,
    market_source_mode=MarketSourceMode.MOCK_ONLY,
)
