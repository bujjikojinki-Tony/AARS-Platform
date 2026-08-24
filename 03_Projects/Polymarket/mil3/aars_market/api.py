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
        server_version = "AARS-MIL3-ReadOnly/0.3"

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
