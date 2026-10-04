from __future__ import annotations
import argparse,json
from dataclasses import asdict
from pathlib import Path
from aars_market.cognitive import run_cognitive_review

def main():
    p=argparse.ArgumentParser(description="AARS MIL-4 cognitive research review")
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="")
    p.add_argument("--primary-model",default=None)
    p.add_argument("--challenger-model",default=None)
    a=p.parse_args()
    payload=json.loads(Path(a.input).read_text(encoding="utf-8"))
    report=asdict(run_cognitive_review(payload,primary_model=a.primary_model,challenger_model=a.challenger_model))
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if a.output: Path(a.output).write_text(text+"\n",encoding="utf-8")
    print(text)
if __name__=="__main__": main()
