from __future__ import annotations
import json, os
from dataclasses import dataclass, asdict
from typing import Any
from urllib.request import Request,urlopen

@dataclass(frozen=True)
class CalibratedReview:
 model:str; summary:str; bull:float; base:float; bear:float
 supporting_evidence:tuple[str,...]; counter_evidence:tuple[str,...]; risks:tuple[str,...]; hypotheses:tuple[str,...]
 authority:str="RESEARCH_ONLY"

SYSTEM="""You are an AARS probabilistic research reviewer. Use only supplied evidence.
Return JSON only: summary,bull,base,bear,supporting_evidence,counter_evidence,risks,hypotheses.
bull/base/bear are probabilities for the requested horizon, each 0..1 and must sum to 1.
Do not recommend orders, position size, leverage, exposure, or parameter changes. RESEARCH_ONLY."""

def _normalized(d:dict[str,Any])->tuple[float,float,float]:
 vals=[max(0.0,float(d.get(k,0.0))) for k in ("bull","base","bear")]; s=sum(vals)
 if s<=0: raise ValueError("LLM probability mass must be positive")
 vals=[v/s for v in vals]
 if abs(sum(vals)-1)>1e-9: raise ValueError("probability normalization failed")
 return tuple(vals)

def review_calibrated(payload:dict[str,Any],*,model:str|None=None,timeout:float=45)->CalibratedReview:
 key=os.getenv("OPENAI_API_KEY")
 if not key: raise RuntimeError("OPENAI_API_KEY is not configured")
 model=model or os.getenv("AARS_LLM_MODEL","gpt-6-luna")
 body={"model":model,"instructions":SYSTEM,"input":json.dumps(payload,default=str,separators=(",",":")),"text":{"format":{"type":"json_object"}}}
 req=Request("https://api.openai.com/v1/responses",data=json.dumps(body).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},method="POST")
 with urlopen(req,timeout=timeout) as resp: raw=json.load(resp)
 text=raw.get("output_text","")
 if not text:
  text="".join(c.get("text","") for i in raw.get("output",[]) for c in i.get("content",[]) if c.get("type")=="output_text")
 d=json.loads(text); bull,base,bear=_normalized(d)
 return CalibratedReview(model,str(d.get("summary","")),bull,base,bear,
  tuple(map(str,d.get("supporting_evidence",[]))),tuple(map(str,d.get("counter_evidence",[]))),
  tuple(map(str,d.get("risks",[]))),tuple(map(str,d.get("hypotheses",[]))))
