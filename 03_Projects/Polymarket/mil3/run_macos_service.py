from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aars_market.macos_deployment import (
    MacOSDeploymentConfig,
    install_launch_agents,
    launch_agent_status,
    render_forward_bot_launch_agent,
    uninstall_launch_agents,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3.10 Mac mini launchd manager")
    parser.add_argument(
        "command",
        choices=("install", "render", "render-forward-bots", "status", "uninstall"),
    )
    parser.add_argument("--runtime-root", default="~/AARS-MIL3")
    parser.add_argument("--project-root", default=str(Path(__file__).parent))
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--agents-dir", default="~/Library/LaunchAgents")
    parser.add_argument("--api-port", type=int, default=8765)
    parser.add_argument("--poll-seconds", type=int, default=3600)
    parser.add_argument("--health-seconds", type=int, default=300)
    parser.add_argument("--sandbox-id", default="aars-paper-sandbox")
    parser.add_argument("--forward-poll-seconds", type=int, default=60)
    parser.add_argument("--forward-lease-seconds", type=int, default=120)
    args = parser.parse_args()

    if args.command == "status":
        payload = launch_agent_status()
    elif args.command == "uninstall":
        payload = uninstall_launch_agents(args.agents_dir)
    else:
        config = MacOSDeploymentConfig(
            project_root=Path(args.project_root),
            python_executable=Path(args.python),
            runtime_root=Path(args.runtime_root),
            api_port=args.api_port,
            poll_seconds=args.poll_seconds,
            health_seconds=args.health_seconds,
        )
        if args.command == "render-forward-bots":
            path = render_forward_bot_launch_agent(
                config,
                args.agents_dir,
                sandbox_id=args.sandbox_id,
                interval_seconds=args.forward_poll_seconds,
                lease_seconds=args.forward_lease_seconds,
            )
            payload = {
                "execution_mode": "PAPER_ONLY",
                "rendered": str(path),
                "loaded": False,
                "separate_from_default_install": True,
                "live_execution_allowed": False,
            }
        else:
            payload = install_launch_agents(
                config,
                args.agents_dir,
                load=args.command == "install",
            )
    print(json.dumps(payload, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
