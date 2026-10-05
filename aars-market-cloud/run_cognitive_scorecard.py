from __future__ import annotations
import argparse,json
from aars_market.cognitive_scorecard import write_scorecard
def main():
 p=argparse.ArgumentParser(description="MIL-4.3 cognitive model scorecard")
 p.add_argument("--memory-db",default="cognitive_memory.sqlite"); p.add_argument("--output",default="cognitive_scorecard.json")
 p.add_argument("--min-samples",type=int,default=10); a=p.parse_args()
 result=write_scorecard(a.memory_db,a.output,a.min_samples)
 print(json.dumps({"output":a.output,"evaluated_outcomes":result["evaluated_outcomes"],"groups":len(result["groups"])},ensure_ascii=False))
if __name__=="__main__": main()
