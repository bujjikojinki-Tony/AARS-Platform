from __future__ import annotations
import argparse,json
from aars_market.outcome_feedback import evaluate
def main():
 p=argparse.ArgumentParser(description="MIL-4.2 24h/72h outcome evaluator")
 p.add_argument("packet_id"); p.add_argument("--db",default="mil3_market.sqlite"); p.add_argument("--memory-db",default="cognitive_memory.sqlite")
 a=p.parse_args(); print(json.dumps(evaluate(a.memory_db,a.db,a.packet_id),ensure_ascii=False,indent=2))
if __name__=="__main__": main()
