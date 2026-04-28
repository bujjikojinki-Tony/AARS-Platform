from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_weather_realtime import startup_self_check_and_sync


async def main() -> None:
    bootstrap = await startup_self_check_and_sync()
    snapshot = bootstrap.get("snapshot") or {}
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
