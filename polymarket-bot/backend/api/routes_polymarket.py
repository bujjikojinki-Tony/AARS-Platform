from __future__ import annotations

from fastapi import APIRouter

from backend.archive.market_snapshot_archive_service import MarketSnapshotArchiveService
from backend.connectors.polymarket_connector_health import PolymarketConnectorHealthChecker
from backend.connectors.polymarket_read_only_market_source import PolymarketReadOnlyMarketSource
from backend.models.polymarket import MarketSourceMode
from backend.models.snapshot_archive import SnapshotArchiveReason


def create_polymarket_router(services) -> APIRouter:
    router = APIRouter(prefix="/api/polymarket", tags=["polymarket-read-only"])
    archive_service = MarketSnapshotArchiveService(services.repository)

    def _source() -> PolymarketReadOnlyMarketSource:
        return PolymarketReadOnlyMarketSource(
            config=services.polymarket_config,
            mock_source=services.mock_market_source,
        )

    @router.get("/health")
    def get_polymarket_health():
        checker = PolymarketConnectorHealthChecker(services.polymarket_config)
        health = checker.check()
        services.repository.save_polymarket_connector_health(health)
        return {
            "status": "ok",
            "health": health.model_dump(mode="json"),
            "config": services.polymarket_config.model_dump_safe(),
        }

    @router.get("/markets")
    def get_polymarket_markets(limit: int = 50):
        items = services.repository.list_polymarket_market_cache(limit=limit)
        return {
            "status": "ok",
            "mode": services.polymarket_config.market_source_mode.value,
            "allow_polymarket_network": services.polymarket_config.allow_polymarket_network,
            "items": items,
        }

    @router.get("/weather-markets")
    def get_polymarket_weather_markets(limit: int = 50):
        cached = services.repository.list_polymarket_weather_market_cache(limit=limit)
        preview_snapshots = []
        warnings: list[str] = []
        if not cached:
            try:
                source = _source()
                snapshots = source.fetch_markets()
                preview_snapshots = [snapshot.model_dump(mode="json") for snapshot in snapshots]
                warnings.extend(source.last_warnings)
            except Exception as exc:
                warnings.append(f"weather market preview failed: {exc}")
        return {
            "status": "ok",
            "mode": services.polymarket_config.market_source_mode.value,
            "allow_polymarket_network": services.polymarket_config.allow_polymarket_network,
            "cached_items": cached,
            "preview_snapshots": preview_snapshots,
            "warnings": warnings,
        }

    @router.post("/sync-weather-markets")
    def sync_weather_markets(payload: dict | None = None):
        payload = payload or {}
        limit = int(payload.get("limit") or services.polymarket_config.max_markets)
        archive_requested = bool(payload.get("archive", False))
        source = _source()
        warnings: list[str] = []
        saved_count = 0
        archive_saved_count = 0
        records = []
        snapshots_to_archive = []

        try:
            if services.polymarket_config.market_source_mode == MarketSourceMode.MOCK_ONLY:
                if archive_requested:
                    try:
                        archive_records = archive_service.archive_snapshots(
                            snapshots=services.mock_market_source.fetch_markets(),
                            market_source_mode=services.market_source_mode,
                            archive_reason=SnapshotArchiveReason.SYNC_CAPTURE,
                            metadata={"capture_source": "sync-weather-markets", "mode": "MOCK_ONLY"},
                        )
                        archive_saved_count = len(archive_records)
                    except Exception as exc:
                        warnings.append(f"sync archive failed safely: {exc}")
                warnings.append("MOCK_ONLY mode: sync skipped; Polymarket network not used.")
                health = PolymarketConnectorHealthChecker(services.polymarket_config).check()
                services.repository.save_polymarket_connector_health(health)
                return {
                    "status": "ok",
                    "saved_count": 0,
                    "archive_saved_count": archive_saved_count,
                    "records": [],
                    "warnings": warnings + health.warnings,
                }

            weather_records = source.fetch_weather_records(limit=limit)
            for record in weather_records:
                try:
                    snapshots_to_archive.append(record.to_market_snapshot())
                except Exception as exc:
                    warnings.append(
                        f"snapshot conversion failed for archive {record.polymarket_market_id}: {exc}"
                    )
                if record.source != "polymarket":
                    warnings.append(
                        f"skipped non-polymarket fallback record: {record.polymarket_market_id}"
                    )
                    continue
                services.repository.save_polymarket_market_record(record)
                records.append(record.model_dump(mode="json"))
                saved_count += 1
            warnings.extend(source.last_warnings)
            if archive_requested and snapshots_to_archive:
                try:
                    archive_records = archive_service.archive_snapshots(
                        snapshots=snapshots_to_archive,
                        market_source_mode=services.market_source_mode,
                        archive_reason=SnapshotArchiveReason.SYNC_CAPTURE,
                        metadata={"capture_source": "sync-weather-markets"},
                    )
                    archive_saved_count = len(archive_records)
                except Exception as exc:
                    warnings.append(f"sync archive failed safely: {exc}")
        except Exception as exc:
            warnings.append(f"sync-weather-markets failed safely: {exc}")

        health = PolymarketConnectorHealthChecker(services.polymarket_config).check()
        services.repository.save_polymarket_connector_health(health)
        return {
            "status": "ok",
            "saved_count": saved_count,
            "archive_saved_count": archive_saved_count,
            "records": records,
            "warnings": warnings + health.warnings,
        }

    @router.get("/source-mode")
    def get_source_mode():
        return {
            "status": "ok",
            "market_source_mode": services.polymarket_config.market_source_mode.value,
            "allow_polymarket_network": services.polymarket_config.allow_polymarket_network,
            "config": services.polymarket_config.model_dump_safe(),
        }

    @router.post("/source-mode")
    def set_source_mode(payload: dict):
        mode_raw = payload.get("market_source_mode")
        allow_network_raw = payload.get("allow_polymarket_network")
        if mode_raw is None:
            return {
                "status": "error",
                "message": "market_source_mode is required",
            }
        try:
            mode = MarketSourceMode(str(mode_raw))
        except Exception:
            return {
                "status": "error",
                "message": f"unsupported market_source_mode: {mode_raw}",
            }

        services.polymarket_config.market_source_mode = mode
        services.market_source_mode = mode
        if allow_network_raw is not None:
            services.polymarket_config.allow_polymarket_network = bool(allow_network_raw)
            services.allow_polymarket_network = bool(allow_network_raw)
        services.polymarket_config.validate_safe_defaults()

        services.market_source = (
            services.mock_market_source
            if mode == MarketSourceMode.MOCK_ONLY
            else PolymarketReadOnlyMarketSource(
                config=services.polymarket_config,
                mock_source=services.mock_market_source,
            )
        )
        services.strategy_runner.market_source = services.market_source
        return {
            "status": "ok",
            "market_source_mode": services.polymarket_config.market_source_mode.value,
            "allow_polymarket_network": services.polymarket_config.allow_polymarket_network,
            "live_execution": False,
            "message": "source mode updated for runtime only; trading remains disabled.",
        }

    return router
