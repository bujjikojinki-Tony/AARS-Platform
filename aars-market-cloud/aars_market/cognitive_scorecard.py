from __future__ import annotations
import json, sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

CLASSES=("BULL","BASE","BEAR")

def _norm(p:dict[str,Any])->dict[str,float]:
 vals={k:max(0.0,float(p.get(k.lower(),p.get(k,0.0)) or 0.0)) for k in CLASSES}
 s=sum(vals.values())
 return {k:(vals[k]/s if s else 1/3) for k in CLASSES}

def brier(probs:dict[str,float],actual:str)->float:
 p=_norm(probs); return sum((p[k]-(1.0 if k==actual else 0.0))**2 for k in CLASSES)/3.0

def _llm_probs(review:dict[str,Any],quant:dict[str,float])->dict[str,float]:
 # LLM v1 is qualitative. Until it emits calibrated class probabilities, score it
 # conservatively as the quant prior rather than fabricating probabilities.
 return _norm(quant)

def build_scorecard(memory_db:str|Path,min_samples:int=10)->dict[str,Any]:
 con=sqlite3.connect(Path(memory_db)); con.row_factory=sqlite3.Row
 reviews={r["packet_id"]:r for r in con.execute("SELECT * FROM cognitive_reviews")}
 outcomes=list(con.execute("SELECT * FROM cognitive_outcomes ORDER BY evaluated_at"))
 buckets=defaultdict(lambda:{"n":0,"quant_brier":0.0,"primary_brier":0.0,"challenger_brier":0.0})
 rows=[]
 for o in outcomes:
  r=reviews.get(o["packet_id"])
  if not r: continue
  evidence=json.loads(r["evidence_json"]); report=json.loads(r["report_json"])
  asset=evidence.get("assets",{}).get(o["symbol"],{})
  stable=asset.get("latest_stable_view") or {}
  probs=stable.get("probabilities") or asset.get("probabilities") or {}
  if not probs: continue
  state=str(stable.get("market_state") or stable.get("state") or "UNKNOWN")
  q=_norm(probs); primary=_llm_probs(report.get("primary",{}),q); challenger=_llm_probs(report.get("challenger",{}),q)
  qb=brier(q,o["realized_class"]); pb=brier(primary,o["realized_class"]); cb=brier(challenger,o["realized_class"])
  row={"packet_id":o["packet_id"],"symbol":o["symbol"],"horizon_hours":o["horizon_hours"],"market_state":state,
       "actual":o["realized_class"],"quant_brier":qb,"primary_brier":pb,"challenger_brier":cb}
  rows.append(row)
  for key in (("ALL","ALL","ALL"),(o["symbol"],"ALL","ALL"),("ALL",state,"ALL"),("ALL","ALL",str(o["horizon_hours"])),
              (o["symbol"],state,str(o["horizon_hours"]))):
   b=buckets[key]; b["n"]+=1; b["quant_brier"]+=qb; b["primary_brier"]+=pb; b["challenger_brier"]+=cb
 groups=[]
 for (symbol,state,horizon),v in sorted(buckets.items()):
  n=v["n"]; groups.append({"symbol":symbol,"market_state":state,"horizon_hours":horizon,"samples":n,
   "status":"MEASURED" if n>=min_samples else "INSUFFICIENT_SAMPLE",
   "quant_brier":v["quant_brier"]/n,"primary_brier":v["primary_brier"]/n,"challenger_brier":v["challenger_brier"]/n,
   "llm_incremental_value":"NOT_YET_MEASURABLE"})
 return {"schema_version":"mil4.cognitive-scorecard.v1","authority":"ANALYTICS_ONLY",
         "note":"LLM v1 is qualitative; no probability uplift is claimed until calibrated LLM class probabilities are stored.",
         "min_samples":min_samples,"evaluated_outcomes":len(rows),"groups":groups}

def write_scorecard(memory_db:str|Path,output:str|Path,min_samples:int=10):
 payload=build_scorecard(memory_db,min_samples); Path(output).write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); return payload
