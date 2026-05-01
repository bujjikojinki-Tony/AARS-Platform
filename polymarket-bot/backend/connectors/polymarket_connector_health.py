from __future__ import annotations

from backend.connectors.polymarket_clob_read_client import PolymarketClobReadClient
from backend.connectors.polymarket_config import PolymarketConnectorConfig
from backend.connectors.polymarket_errors import ReadOnlyConnectorNetworkDisabled
from backend.connectors.polymarket_errors import ReadOnlyConnectorRequestError
from backend.connectors.polymarket_gamma_client import PolymarketGammaClient
from backend.models.polymarket import PolymarketConnectorHealth
from backend.models.polymarket import PolymarketConnectorMode


class PolymarketConnectorHealthChecker:
    """
    Read-only connector health checker.
    Safety boundary:
    - Does not call network when allow_polymarket_network=False.
    - Does not call trading endpoints.
    - Does not use auth.
    """

    def __init__(self, config: PolymarketConnectorConfig):
        self.config = config
        self.gamma_client = PolymarketGammaClient(config)
        self.clob_client = PolymarketClobReadClient(config)

    def check(self) -> PolymarketConnectorHealth:
        warnings: list[str] = []
        mode = self.config.market_source_mode or self.config.mode
        if not self.config.allow_polymarket_network:
            warnings.append("Polymarket network access disabled by config.")
            if mode == PolymarketConnectorMode.HYBRID:
                status = "HYBRID_FALLBACK"
                warnings.append("HYBRID mode falls back to mock markets when network is disabled.")
            elif mode == PolymarketConnectorMode.POLYMARKET_ONLY:
                status = "BLOCKED"
                warnings.append("POLYMARKET_ONLY requires allow_polymarket_network=True.")
            else:
                status = "MOCK_ONLY"
                warnings.append("MOCK_ONLY mode uses mock markets only.")
            return PolymarketConnectorHealth(
                gamma_reachable=False,
                clob_reachable=False,
                last_gamma_status=None,
                last_clob_status=None,
                mode=mode,
                warnings=warnings,
                allow_polymarket_network=False,
                read_only=True,
                status=status,
            )

        gamma_reachable = False
        clob_reachable = False
        last_gamma_status = None
        last_clob_status = None

        try:
            self.gamma_client.fetch_markets(limit=1)
            gamma_reachable = True
            last_gamma_status = 200
        except ReadOnlyConnectorNetworkDisabled:
            warnings.append("Gamma network disabled.")
        except ReadOnlyConnectorRequestError as exc:
            warnings.append(f"Gamma health check failed: {exc}")
        except Exception as exc:
            warnings.append(f"Gamma health check failed: {exc}")

        try:
            self.clob_client.get_midpoint("health_check_token")
            clob_reachable = True
            last_clob_status = 200
        except ReadOnlyConnectorNetworkDisabled:
            warnings.append("CLOB network disabled.")
        except ReadOnlyConnectorRequestError as exc:
            warnings.append(f"CLOB read endpoint not confirmed: {exc}")
        except Exception as exc:
            warnings.append(f"CLOB health check failed: {exc}")

        return PolymarketConnectorHealth(
            gamma_reachable=gamma_reachable,
            clob_reachable=clob_reachable,
            last_gamma_status=last_gamma_status,
            last_clob_status=last_clob_status,
            mode=mode,
            warnings=warnings,
            allow_polymarket_network=self.config.allow_polymarket_network,
            read_only=True,
            status="READ_ONLY" if self.config.allow_polymarket_network else "MOCK_ONLY",
        )


def build_polymarket_connector_health(
    config: PolymarketConnectorConfig,
    *,
    weather_market_count: int = 0,
) -> PolymarketConnectorHealth:
    health = PolymarketConnectorHealthChecker(config).check()
    warnings = list(health.warnings)
    if weather_market_count == 0:
        warnings.append("No weather markets were synced yet.")
    return health.model_copy(update={"warnings": warnings})
