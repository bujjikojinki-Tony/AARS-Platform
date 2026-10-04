from __future__ import annotations
import argparse,json,os
from dataclasses import asdict
from pathlib import Path
from aars_market.cognitive import run_cognitive_review
from aars_market.cognitive_memory import CognitiveMemory
from aars_market.evidence_packet import build_from_sqlite
from aars_market.service import DEFAULT_SYMBOLS

def main():
 p=argparse.ArgumentParser(description="MIL-4.2 cognitive cycle with immutable research memory")
 p.add_argument("--db",default="mil3_market.sqlite"); p.add_argument("--memory-db",default="cognitive_memory.sqlite")
 p.add_argument("--symbols",nargs="+",default=list(DEFAULT_SYMBOLS)); p.add_argument("--timeframe",default="1h"); p.add_argument("--window",default="90d")
 a=p.parse_args()
 evidence=build_from_sqlite(a.db,symbols=tuple(a.symbols),timeframe=a.timeframe,replay_window=a.window)
 report=run_cognitive_review(evidence,primary_model=os.getenv("AARS_LLM_PRIMARY_MODEL") or None,challenger_model=os.getenv("AARS_LLM_CHALLENGER_MODEL") or None)
 rd=asdict(report); CognitiveMemory(a.memory_db).save(report.packet_id,evidence,rd)
 print(json.dumps({"packet_id":report.packet_id,"gate":report.gate,"memory_db":a.memory_db,"authority":"RESEARCH_ONLY"},ensure_ascii=False))
if __name__=="__main__": main()
