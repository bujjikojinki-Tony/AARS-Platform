from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = DATA_DIR / "outputs"

for path in [CACHE_DIR, OUTPUT_DIR]:
    path.mkdir(parents=True, exist_ok=True)
