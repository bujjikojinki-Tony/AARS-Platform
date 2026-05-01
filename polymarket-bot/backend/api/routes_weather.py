from __future__ import annotations

from fastapi import APIRouter

from backend.models.core import MarketSnapshot
from backend.probability.weather_probability_provider import WeatherProbabilityProvider
from backend.weather.market_question_parser import MarketQuestionParser
from backend.weather.weather_market_resolver import WeatherMarketResolver


def create_weather_router(
    repository,
    default_year: int = 2026,
    allow_network: bool = False,
    default_sigma: float = 2.5,
    archive_weather_on_probability_build: bool = False,
) -> APIRouter:
    router = APIRouter(prefix="/api/weather", tags=["weather"])
    parser = MarketQuestionParser(default_year=default_year)
    resolver = WeatherMarketResolver()
    provider = WeatherProbabilityProvider(
        repository=repository,
        default_year=default_year,
        allow_network=allow_network,
        default_sigma=default_sigma,
        archive_weather_on_probability_build=archive_weather_on_probability_build,
    )

    @router.post("/resolve")
    def resolve_weather_market(payload: dict):
        market_id = payload.get("market_id") or "adhoc_weather_market"
        question = payload.get("question")
        if not question:
            return {"status": "error", "message": "question is required"}
        descriptor = parser.parse(market_id=market_id, question=question)
        descriptor = resolver.resolve(descriptor)
        repository.save_weather_descriptor(descriptor)
        return {"status": "ok", "descriptor": descriptor.model_dump(mode="json")}

    @router.post("/probability")
    def build_weather_probability(payload: dict):
        market_id = payload.get("market_id") or "adhoc_weather_market"
        question = payload.get("question")
        if not question:
            return {"status": "error", "message": "question is required"}
        yes_price = float(payload.get("yes_price", 0.5))
        no_price = float(payload.get("no_price", 1 - yes_price))
        liquidity = float(payload.get("liquidity", 1000))
        spread = float(payload.get("spread", 0.03))
        market = MarketSnapshot(
            market_id=market_id,
            question=question,
            yes_price=yes_price,
            no_price=no_price,
            liquidity=liquidity,
            spread=spread,
            source="adhoc",
        )
        probability_view = provider.build_probability_view(market)
        return {
            "status": "ok",
            "probability": probability_view.model_dump(mode="json"),
            "latest_evidence_pack": repository.get_latest_evidence_pack(market_id),
            "latest_weather_view": repository.get_latest_weather_view(market_id),
        }

    @router.get("/descriptor/{market_id}")
    def get_descriptor(market_id: str):
        item = repository.get_latest_weather_descriptor(market_id)
        if not item:
            return {"status": "error", "message": "descriptor not found"}
        return {"status": "ok", "descriptor": item}

    @router.get("/sources/{market_id}")
    def get_sources(market_id: str, limit: int = 100):
        return {
            "status": "ok",
            "sources": repository.list_weather_sources_for_market(market_id, limit),
        }

    @router.get("/evidence/{market_id}")
    def get_evidence(market_id: str):
        item = repository.get_latest_evidence_pack(market_id)
        if not item:
            return {"status": "error", "message": "evidence pack not found"}
        return {
            "status": "ok",
            "evidence_pack": item,
            "sources": repository.list_weather_sources_for_market(market_id),
        }

    @router.get("/view/{market_id}")
    def get_weather_view(market_id: str):
        item = repository.get_latest_weather_view(market_id)
        if not item:
            return {"status": "error", "message": "weather view not found"}
        return {"status": "ok", "weather_view": item}

    @router.get("/probability/{market_id}")
    def get_probability(market_id: str):
        item = repository.get_latest_probability_view(market_id)
        if not item:
            return {"status": "error", "message": "probability view not found"}
        return {"status": "ok", "probability_view": item}

    return router
