from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.api import create_server
from aars_market.service import DashboardService
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3.7 PAPER_ONLY read-only local API")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    service = DashboardService(store)
    ui_root = Path(__file__).parent / "ui"
    server = create_server(service, ui_root, args.host, args.port)
    print("execution_mode=PAPER_ONLY")
    print("api_mode=READ_ONLY")
    print(f"open=http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
