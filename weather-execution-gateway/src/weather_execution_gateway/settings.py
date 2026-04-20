from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"

for path in [CONFIG_DIR, DATA_DIR, OUTPUT_DIR]:
    path.mkdir(parents=True, exist_ok=True)
