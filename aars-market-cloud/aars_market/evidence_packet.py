from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .service import DEFAULT_SYMBOLS, DashboardRequest, DashboardService, PortfolioRequest
from .storage import MarketStore

def _compact_dashboard(p: dict[str,Any])->dict[str,Any]:
    stable=p.get("latest_stable_view",{})
    return {
        "selection":p.get("selection"),
        "market":p.get("market"),
        "latest_stable_view":stable,
        "risk":p.get("risk"),
        "alerts":p.get("alerts",[]),
        "funding_coverage":p.get("funding_coverage"),
        "strategies":[{"id":s.get("id"),"summary":s.get("summary")} for s in p.get("strategies",[])],
        "review_gate":p.get("review_gate"),
    }

def build_from_sqlite(db: str|Path, *, symbols=DEFAULT_SYMBOLS, timeframe="1h", replay_window="90d")->dict[str,Any]:
    store=MarketStore(Path(db)); store.init_db()
    service=DashboardService(store)
    now=datetime.now(timezone.utc)
    assets={}
    for symbol in symbols:
        payload=service.build(DashboardRequest(symbol=symbol,timeframe=timeframe,replay_window=replay_window),
                              now=now,archive=False,max_trace_points=1)
        assets[symbol]=_compact_dashboard(payload)
    portfolio=service.build_portfolio(PortfolioRequest(symbols=tuple(symbols),timeframe=timeframe,replay_window=replay_window),now=now)
    return {
        "schema_version":"mil4.evidence-packet.v1",
        "generated_at":now.isoformat(),
        "execution_mode":"PAPER_ONLY",
        "authority":"EVIDENCE_ONLY",
        "assets":assets,
        "portfolio":portfolio,
        "prohibitions":["NO_LIVE_ORDERS","NO_PARAMETER_MUTATION","NO_LEVERAGE_MUTATION","NO_CREDENTIAL_ACCESS"],
    }
