from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict

from .config import ConfigLoader
from .platform import build_runtime


def main() -> int:
    parser = argparse.ArgumentParser(description="AARS generic runtime platform")
    parser.add_argument("--config", help="JSON runtime configuration")
    parser.add_argument("--discover", action="store_true", help="Discover external plugins through entry points")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("plugins", help="List registered external plugins")
    subparsers.add_parser("health", help="Run runtime health checks")
    config_parser = subparsers.add_parser("config", help="Inspect resolved configuration")
    config_parser.add_argument("key", nargs="?")
    args = parser.parse_args()

    config = ConfigLoader({"core": {"api_version": "1"}}).load(args.config, os.environ)
    runtime = build_runtime(config)
    if args.discover:
        runtime.plugins.discover()

    if args.command == "plugins":
        print(json.dumps([asdict(status) for status in runtime.plugins.list_status()], sort_keys=True))
    elif args.command == "health":
        results = runtime.health.run()
        print(json.dumps({
            "status": runtime.health.overall_status(results),
            "checks": [asdict(result) for result in results],
        }, sort_keys=True))
    else:
        value = config.get(args.key) if args.key else config.values
        print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
