from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .service import DashboardRequest, DashboardService, PortfolioRequest


READ_ONLY_METHODS = "GET, HEAD, OPTIONS"


def make_handler(service: DashboardService, ui_root: str | Path) -> type[SimpleHTTPRequestHandler]:
    root = str(Path(ui_root).resolve())

    class ReadOnlyHandler(SimpleHTTPRequestHandler):
        server_version = "AARS-MIL3-ReadOnly/0.13"

        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=root, **kwargs)

        def _json(self, status: int, payload: Any, *, body: bool = True) -> None:
            encoded = json.dumps(payload, sort_keys=True, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-AARS-Execution-Mode", "PAPER_ONLY")
            self.send_header("Allow", READ_ONLY_METHODS)
            self.end_headers()
            if body:
                self.wfile.write(encoded)

        def _api_payload(self) -> tuple[int, Any]:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path == "/api/v1/health":
                return HTTPStatus.OK, {
                    "status": "ok",
                    "execution_mode": "PAPER_ONLY",
                    "read_only": True,
                }
            if parsed.path == "/api/v1/markets":
                return HTTPStatus.OK, {"markets": service.markets()}
            if parsed.path == "/api/v1/funding-cadence":
                symbol = query.get("symbol", ["SOLUSDT"])[0]
                return HTTPStatus.OK, service.funding_cadence(symbol)
            if parsed.path == "/api/v1/ingestion-cycles":
                limit = int(query.get("limit", ["20"])[0])
                return HTTPStatus.OK, {
                    "ingestion_cycles": service.store.list_ingestion_cycles(limit)
                }
            if parsed.path == "/api/v1/dashboard":
                request = DashboardRequest(
                    symbol=query.get("symbol", ["SOLUSDT"])[0],
                    timeframe=query.get("interval", ["1h"])[0],
                    replay_window=query.get("window", ["90d"])[0],
                )
                return HTTPStatus.OK, service.build(request, archive=False)
            if parsed.path == "/api/v1/portfolio":
                symbols = tuple(
                    item.strip().upper()
                    for item in query.get("symbols", ["BTCUSDT,ETHUSDT,SOLUSDT"])[0].split(",")
                    if item.strip()
                )
                request = PortfolioRequest(
                    symbols=symbols,
                    timeframe=query.get("interval", ["1h"])[0],
                    replay_window=query.get("window", ["90d"])[0],
                    strategy=query.get("strategy", ["AARS_DYNAMIC"])[0],
                )
                return HTTPStatus.OK, service.build_portfolio(request)
            if parsed.path == "/api/v1/stable-view-diff":
                before = query.get("before", [""])[0]
                after = query.get("after", [""])[0]
                if not before or not after:
                    raise ValueError("before and after view ids are required")
                return HTTPStatus.OK, service.compare_views(before, after)
            if parsed.path == "/api/v1/stable-views":
                limit = int(query.get("limit", ["20"])[0])
                views = service.store.list_latest_stable_views(
                    query.get("symbol", [None])[0], query.get("interval", [None])[0], limit
                )
                return HTTPStatus.OK, {"stable_views": views}
            if parsed.path == "/api/v1/shadow-snapshots":
                limit = int(query.get("limit", ["30"])[0])
                return HTTPStatus.OK, service.list_shadow_snapshots(
                    limit=limit,
                    target_strategy=query.get("strategy", [None])[0],
                )
            if parsed.path == "/api/v1/shadow-stability":
                limit = int(query.get("limit", ["90"])[0])
                return HTTPStatus.OK, service.shadow_stability(
                    limit=limit,
                    target_strategy=query.get("strategy", [None])[0],
                )
            if parsed.path == "/api/v1/strategy-diagnostics":
                return HTTPStatus.OK, service.strategy_diagnostics(
                    snapshot_id=query.get("snapshot_id", [None])[0]
                )
            if parsed.path == "/api/v1/low-turnover-challenger":
                return HTTPStatus.OK, service.low_turnover_challenger(
                    snapshot_id=query.get("snapshot_id", [None])[0]
                )
            if parsed.path == "/api/v1/frozen-challenger-robustness":
                return HTTPStatus.OK, service.frozen_challenger_robustness(
                    snapshot_id=query.get("snapshot_id", [None])[0]
                )
            if parsed.path == "/api/v1/promotion-governance":
                limit = int(query.get("limit", ["90"])[0])
                return HTTPStatus.OK, service.promotion_governance(
                    limit=limit,
                    target_strategy=query.get("strategy", [None])[0],
                )
            if parsed.path == "/api/v1/paper-proposals":
                limit = int(query.get("limit", ["30"])[0])
                return HTTPStatus.OK, service.list_paper_proposals(
                    limit=limit,
                    target_strategy=query.get("strategy", [None])[0],
                )
            if parsed.path == "/api/v1/paper-trials":
                limit = int(query.get("limit", ["30"])[0])
                return HTTPStatus.OK, service.list_paper_trials(
                    limit=limit,
                    target_strategy=query.get("strategy", [None])[0],
                )
            if parsed.path == "/api/v1/forward-observations":
                limit = int(query.get("limit", ["30"])[0])
                return HTTPStatus.OK, service.list_forward_observations(
                    limit=limit,
                    target_strategy=query.get("strategy", [None])[0],
                    trial_id=query.get("trial_id", [None])[0],
                )
            if parsed.path == "/api/v1/forward-stability":
                trial_id = query.get("trial_id", [""])[0]
                if not trial_id:
                    raise ValueError("trial_id is required")
                return HTTPStatus.OK, service.forward_stability(
                    trial_id, limit=int(query.get("limit", ["90"])[0])
                )
            if parsed.path == "/api/v1/forward-lifecycle":
                trial_id = query.get("trial_id", [""])[0]
                if not trial_id:
                    raise ValueError("trial_id is required")
                return HTTPStatus.OK, service.forward_candidate_lifecycle(trial_id)
            if parsed.path == "/api/v1/forward-evidence-manifest":
                trial_id = query.get("trial_id", [""])[0]
                if not trial_id:
                    raise ValueError("trial_id is required")
                return HTTPStatus.OK, service.forward_evidence_manifest(trial_id)
            if parsed.path == "/api/v1/evidence-governance-policy":
                return HTTPStatus.OK, service.evidence_governance_policy()
            if parsed.path == "/api/v1/isolated-activation":
                trial_id = query.get("trial_id", [""])[0]
                if not trial_id:
                    raise ValueError("trial_id is required")
                return HTTPStatus.OK, service.isolated_activation_lifecycle(trial_id)
            if parsed.path == "/api/v1/isolated-configurations":
                return HTTPStatus.OK, service.list_isolated_configurations(
                    sandbox_id=query.get("sandbox_id", [None])[0],
                    limit=int(query.get("limit", ["100"])[0]),
                )
            if parsed.path == "/api/v1/isolated-sandbox":
                sandbox_id = query.get("sandbox_id", [""])[0]
                if not sandbox_id:
                    raise ValueError("sandbox_id is required")
                return HTTPStatus.OK, service.isolated_sandbox(sandbox_id)
            if parsed.path == "/api/v1/isolated-sandbox-events":
                sandbox_id = query.get("sandbox_id", [""])[0]
                if not sandbox_id:
                    raise ValueError("sandbox_id is required")
                return HTTPStatus.OK, service.list_isolated_sandbox_events(
                    sandbox_id, limit=int(query.get("limit", ["100"])[0])
                )
            if parsed.path == "/api/v1/isolated-runtime":
                sandbox_id = query.get("sandbox_id", [""])[0]
                if not sandbox_id:
                    raise ValueError("sandbox_id is required")
                return HTTPStatus.OK, service.isolated_runtime(
                    sandbox_id, limit=int(query.get("limit", ["100"])[0])
                )
            if parsed.path == "/api/v1/isolated-runtime-events":
                session_id = query.get("session_id", [""])[0]
                if not session_id:
                    raise ValueError("session_id is required")
                return HTTPStatus.OK, service.isolated_runtime_events(
                    session_id, limit=int(query.get("limit", ["100"])[0])
                )
            if parsed.path == "/api/v1/isolated-runtime-kill-events":
                sandbox_id = query.get("sandbox_id", [""])[0]
                if not sandbox_id:
                    raise ValueError("sandbox_id is required")
                return HTTPStatus.OK, service.isolated_runtime_kill_events(
                    sandbox_id, limit=int(query.get("limit", ["100"])[0])
                )
            if parsed.path == "/api/v1/isolated-runtime-cycles":
                sandbox_id = query.get("sandbox_id", [""])[0]
                if not sandbox_id:
                    raise ValueError("sandbox_id is required")
                return HTTPStatus.OK, service.isolated_runtime_cycles(
                    sandbox_id, limit=int(query.get("limit", ["100"])[0])
                )
            if parsed.path == "/api/v1/forward-bot-operations":
                sandbox_id = query.get("sandbox_id", [""])[0]
                if not sandbox_id:
                    raise ValueError("sandbox_id is required")
                return HTTPStatus.OK, service.forward_bot_operations(sandbox_id)
            if parsed.path == "/api/v1/isolated-runtime-cycle-events":
                cycle_id = query.get("cycle_id", [""])[0]
                if not cycle_id:
                    raise ValueError("cycle_id is required")
                return HTTPStatus.OK, service.isolated_runtime_cycle_events(
                    cycle_id, limit=int(query.get("limit", ["100"])[0])
                )
            cycle_prefix = "/api/v1/isolated-runtime-cycles/"
            if parsed.path.startswith(cycle_prefix):
                cycle_id = parsed.path[len(cycle_prefix):]
                try:
                    return HTTPStatus.OK, service.isolated_runtime_cycle(cycle_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "isolated runtime cycle not found"}
            ledger_prefix = "/api/v1/isolated-paper-ledger-results/"
            if parsed.path.startswith(ledger_prefix):
                result_id = parsed.path[len(ledger_prefix):]
                try:
                    return HTTPStatus.OK, service.isolated_paper_ledger_result(result_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "isolated paper ledger result not found"}
            runtime_session_prefix = "/api/v1/isolated-runtime-sessions/"
            if parsed.path.startswith(runtime_session_prefix):
                session_id = parsed.path[len(runtime_session_prefix):]
                try:
                    return HTTPStatus.OK, service.isolated_runtime_session(session_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "isolated runtime session not found"}
            sandbox_event_prefix = "/api/v1/isolated-sandbox-events/"
            if parsed.path.startswith(sandbox_event_prefix):
                event_id = parsed.path[len(sandbox_event_prefix):]
                try:
                    return HTTPStatus.OK, service.isolated_sandbox_event(event_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "isolated sandbox event not found"}
            configuration_prefix = "/api/v1/isolated-configurations/"
            if parsed.path.startswith(configuration_prefix):
                configuration_id = parsed.path[len(configuration_prefix):]
                try:
                    return HTTPStatus.OK, service.isolated_configuration(configuration_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "isolated configuration not found"}
            activation_review_prefix = "/api/v1/isolated-activation-reviews/"
            if parsed.path.startswith(activation_review_prefix):
                review_id = parsed.path[len(activation_review_prefix):]
                try:
                    return HTTPStatus.OK, service.isolated_activation_review(review_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "isolated activation review not found"}
            review_prefix = "/api/v1/forward-reviews/"
            if parsed.path.startswith(review_prefix):
                review_id = parsed.path[len(review_prefix):]
                try:
                    return HTTPStatus.OK, service.forward_candidate_review(review_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "forward candidate review not found"}
            forward_prefix = "/api/v1/forward-observations/"
            if parsed.path.startswith(forward_prefix):
                observation_id = parsed.path[len(forward_prefix):]
                try:
                    return HTTPStatus.OK, service.forward_observation(observation_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "forward observation not found"}
            trial_prefix = "/api/v1/paper-trials/"
            if parsed.path.startswith(trial_prefix):
                trial_id = parsed.path[len(trial_prefix):]
                try:
                    return HTTPStatus.OK, service.paper_trial(trial_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "paper trial not found"}
            proposal_prefix = "/api/v1/paper-proposals/"
            if parsed.path.startswith(proposal_prefix):
                proposal_id = parsed.path[len(proposal_prefix):]
                try:
                    return HTTPStatus.OK, service.paper_proposal(proposal_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "paper proposal not found"}
            shadow_prefix = "/api/v1/shadow-snapshots/"
            if parsed.path.startswith(shadow_prefix):
                snapshot_id = parsed.path[len(shadow_prefix):]
                try:
                    return HTTPStatus.OK, service.shadow_snapshot(snapshot_id)
                except KeyError:
                    return HTTPStatus.NOT_FOUND, {"error": "shadow snapshot not found"}
            prefix = "/api/v1/stable-views/"
            if parsed.path.startswith(prefix):
                view = service.store.get_latest_stable_view(parsed.path[len(prefix):])
                return (
                    (HTTPStatus.OK, view)
                    if view is not None
                    else (HTTPStatus.NOT_FOUND, {"error": "stable view not found"})
                )
            return HTTPStatus.NOT_FOUND, {"error": "API route not found"}

        def _dispatch_api(self, *, body: bool) -> None:
            try:
                status, payload = self._api_payload()
            except (ValueError, KeyError) as exc:
                status, payload = HTTPStatus.BAD_REQUEST, {"error": str(exc)}
            except Exception:
                status, payload = HTTPStatus.INTERNAL_SERVER_ERROR, {
                    "error": "dashboard service failed"
                }
            self._json(status, payload, body=body)

        def do_GET(self) -> None:  # noqa: N802
            if urlparse(self.path).path.startswith("/api/"):
                self._dispatch_api(body=True)
            else:
                super().do_GET()

        def do_HEAD(self) -> None:  # noqa: N802
            if urlparse(self.path).path.startswith("/api/"):
                self._dispatch_api(body=False)
            else:
                super().do_HEAD()

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Allow", READ_ONLY_METHODS)
            self.send_header("Access-Control-Allow-Methods", READ_ONLY_METHODS)
            self.end_headers()

        def _method_not_allowed(self) -> None:
            self._json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "read-only API"})

        do_POST = _method_not_allowed
        do_PUT = _method_not_allowed
        do_PATCH = _method_not_allowed
        do_DELETE = _method_not_allowed

    return ReadOnlyHandler


def create_server(
    service: DashboardService,
    ui_root: str | Path,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(service, ui_root))
