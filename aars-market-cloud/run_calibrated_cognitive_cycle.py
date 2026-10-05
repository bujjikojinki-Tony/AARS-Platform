from __future__ import annotations
import argparse,json,os
from aars_market.cognitive_memory import CognitiveMemory
from aars_market.cognitive_v2 import run_calibrated_review
from aars_market.evidence_packet import build_from_sqlite
from aars_market.service import DEFAULT_SYMBOLS
def main():
 p=argparse.ArgumentParser(description="MIL-4.4 calibrated cognitive cycle")
 p.add_argument("--db",default="mil3_market.sqlite"); p.add_argument("--memory-db",default="cognitive_memory.sqlite")
 p.add_argument("--symbols",nargs="+",default=list(DEFAULT_SYMBOLS)); p.add_argument("--timeframe",default="1h"); p.add_argument("--window",default="90d"); p.add_argument("--horizon",type=int,default=24)
 a=p.parse_args(); evidence=build_from_sqlite(a.db,symbols=tuple(a.symbols),timeframe=a.timeframe,replay_window=a.window)
 report=run_calibrated_review(evidence,horizon_hours=a.horizon,primary_model=os.getenv("AARS_LLM_PRIMARY_MODEL") or None,challenger_model=os.getenv("AARS_LLM_CHALLENGER_MODEL") or None)
 CognitiveMemory(a.memory_db).save(report["packet_id"],evidence,report); print(json.dumps({"packet_id":report["packet_id"],"horizon_hours":a.horizon,"gate":report["gate"]},ensure_ascii=False))
if __name__=="__main__": main()
