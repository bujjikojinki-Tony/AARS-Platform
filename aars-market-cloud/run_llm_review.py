from __future__ import annotations
import argparse, json
from pathlib import Path
from aars_market.llm_research import review, to_dict

def main():
    p=argparse.ArgumentParser(description="AARS RESEARCH_ONLY LLM reviewer")
    p.add_argument("--input",required=True,help="JSON evidence payload")
    p.add_argument("--output",default="")
    p.add_argument("--model",default=None)
    a=p.parse_args()
    payload=json.loads(Path(a.input).read_text(encoding="utf-8"))
    result=to_dict(review(payload,model=a.model))
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if a.output: Path(a.output).write_text(text+"\n",encoding="utf-8")
    print(text)
if __name__=="__main__": main()
