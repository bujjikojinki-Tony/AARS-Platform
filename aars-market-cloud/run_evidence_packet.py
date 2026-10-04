from __future__ import annotations
import argparse,json
from pathlib import Path
from aars_market.evidence_packet import build_from_sqlite
from aars_market.service import DEFAULT_SYMBOLS

def main():
    p=argparse.ArgumentParser(description="Build MIL-4.1 evidence directly from AARS SQLite")
    p.add_argument("--db",default="mil3_market.sqlite")
    p.add_argument("--symbols",nargs="+",default=list(DEFAULT_SYMBOLS))
    p.add_argument("--timeframe",default="1h")
    p.add_argument("--window",default="90d")
    p.add_argument("--output",default="evidence.json")
    a=p.parse_args()
    payload=build_from_sqlite(a.db,symbols=tuple(a.symbols),timeframe=a.timeframe,replay_window=a.window)
    Path(a.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    print(a.output)
if __name__=="__main__": main()
