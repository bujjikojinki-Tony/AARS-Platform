from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes_activation_authorization_review import create_activation_authorization_review_router
from backend.api.routes_activation_readiness_review import create_activation_readiness_review_router
from backend.api.routes_command import create_command_router
from backend.api.routes_approval_window_review import create_approval_window_review_router
from backend.api.routes_calibration_memory import create_calibration_memory_router
from backend.api.routes_command_review import create_command_review_router
from backend.api.routes_execution_decision_review import create_execution_decision_review_router
from backend.api.routes_execution_queue_review import create_execution_queue_review_router
from backend.api.routes_deb_shadow import create_deb_shadow_router
from backend.api.routes_emos_shadow import create_emos_shadow_router
from backend.api.routes_evidence import create_evidence_router
from backend.api.routes_history import create_history_router
from backend.api.routes_opportunities import create_opportunities_router
from backend.api.routes_outcomes import create_outcomes_router
from backend.api.routes_polymarket import create_polymarket_router
from backend.api.routes_probability_governance import create_probability_governance_router
from backend.api.routes_settings import create_settings_router
from backend.api.routes_snapshot_archive import create_snapshot_archive_router
from backend.api.routes_shadow_engine_evaluation import create_shadow_engine_evaluation_router
from backend.api.routes_weather_archive import create_weather_archive_router
from backend.api.routes_weather import create_weather_router
from backend.api.routes_workstation import create_workstation_router
from backend.models.polymarket import MarketSourceMode
from backend.services import AppServices
from backend.services import create_services
from backend.storage.db import DEFAULT_DB_PATH


def create_app(
    db_path: str = DEFAULT_DB_PATH,
    allow_network: bool = False,
    allow_polymarket_network: bool = False,
    market_source_mode: MarketSourceMode | str = MarketSourceMode.MOCK_ONLY,
    default_year: int = 2026,
    default_sigma: float = 2.5,
    archive_weather_on_probability_build: bool = False,
) -> FastAPI:
    services: AppServices = create_services(
        db_path,
        allow_network=allow_network,
        allow_polymarket_network=allow_polymarket_network,
        market_source_mode=market_source_mode,
        default_year=default_year,
        default_sigma=default_sigma,
        archive_weather_on_probability_build=archive_weather_on_probability_build,
    )

    app = FastAPI(title="Polymarket Bot PWB-01/PWB-02/PWB-03/PWB-04D/PWB-04E/PWB-04F/PWB-04G/PWB-05/PWB-05A/PWB-05B/PWB-05C/PWB-06/PWB-07/PWB-08/PWB-09/PWB-10/PWB-11")
    app.state.db_path = services.db_path
    app.state.repository = services.repository
    app.state.allow_network = services.allow_network
    app.state.allow_polymarket_network = services.allow_polymarket_network
    app.state.market_source_mode = services.market_source_mode
    app.state.default_year = services.default_year
    app.state.default_sigma = services.default_sigma
    app.state.polymarket_config = services.polymarket_config
    app.state.services = services

    @app.get("/healthz")
    def healthz():
        return {
            "status": "ok",
            "mode": services.repository.get_mode(),
            "db_path": services.db_path,
            "allow_network": services.allow_network,
            "allow_polymarket_network": services.allow_polymarket_network,
            "market_source_mode": services.market_source_mode.value,
            "live_execution": False,
            "archive_weather_on_probability_build": services.archive_weather_on_probability_build,
            "rounds": [
                "PWB-01",
                "PWB-02",
                "PWB-03",
                "PWB-04C",
                "PWB-04D",
                "PWB-04E",
                "PWB-04F",
                "PWB-04G",
                "PWB-05",
                "PWB-05A",
                "PWB-05B",
                "PWB-05C",
                "PWB-06",
                "PWB-07",
                "PWB-08",
                "PWB-09",
                "PWB-10",
                "PWB-11",
            ],
        }

    app.include_router(
        create_opportunities_router(
            services.repository,
            services.strategy_runner,
            services.market_source_mode,
        )
    )
    app.include_router(
        create_command_router(
            services.repository,
            services.strategy_runner,
            services.simulator,
            services.rule_registry,
        )
    )
    app.include_router(create_history_router(services.repository))
    app.include_router(create_settings_router(services.rule_registry))
    app.include_router(
        create_weather_router(
            repository=services.repository,
            default_year=services.default_year,
            allow_network=services.allow_network,
            default_sigma=services.default_sigma,
            archive_weather_on_probability_build=services.archive_weather_on_probability_build,
        )
    )
    app.include_router(create_evidence_router(services.repository))
    app.include_router(create_workstation_router(services.repository))
    app.include_router(create_probability_governance_router(services.repository))
    app.include_router(create_polymarket_router(services))
    app.include_router(create_snapshot_archive_router(services))
    app.include_router(create_weather_archive_router(services))
    app.include_router(create_outcomes_router(services))
    app.include_router(create_calibration_memory_router(services.repository))
    app.include_router(create_deb_shadow_router(services.repository))
    app.include_router(create_emos_shadow_router(services.repository))
    app.include_router(create_shadow_engine_evaluation_router(services.repository))
    app.include_router(create_command_review_router(services.repository))
    app.include_router(create_execution_decision_review_router(services.repository))
    app.include_router(create_execution_queue_review_router(services.repository))
    app.include_router(create_approval_window_review_router(services.repository))
    app.include_router(create_activation_readiness_review_router(services.repository))
    app.include_router(create_activation_authorization_review_router(services.repository))
    return app
