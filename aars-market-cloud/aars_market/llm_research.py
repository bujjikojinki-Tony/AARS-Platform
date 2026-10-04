from __future__ import annotations
import json, os
from dataclasses import asdict, dataclass
from typing import Any
from urllib.request import Request, urlopen

@dataclass(frozen=True)
class ResearchReview:
    model: str
    summary: str
    supporting_evidence: tuple[str, ...]
    counter_evidence: tuple[str, ...]
    risks: tuple[str, ...]
    hypotheses: tuple[str, ...]
    confidence: float
    authority: str = "RESEARCH_ONLY"

SYSTEM = """You are the AARS research reviewer. Analyze only the supplied structured evidence.
Never issue orders, position sizes, leverage changes, or parameter changes.
Separate evidence from inference. Actively seek counter-evidence.
Return JSON only with keys: summary, supporting_evidence, counter_evidence, risks, hypotheses, confidence.
confidence must be 0..1. This output is RESEARCH_ONLY and cannot alter PAPER_ONLY execution."""

def review(payload: dict[str, Any], *, model: str | None=None, timeout: float=45.0) -> ResearchReview:
    key=os.getenv("OPENAI_API_KEY")
    if not key: raise RuntimeError("OPENAI_API_KEY is not configured")
    model=model or os.getenv("AARS_LLM_MODEL","gpt-6-luna")
    body={"model":model,"instructions":SYSTEM,"input":json.dumps(payload,default=str,separators=(",",":")),
          "text":{"format":{"type":"json_object"}}}
    req=Request("https://api.openai.com/v1/responses",data=json.dumps(body).encode(),
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","User-Agent":"AARS-Research/1.0"},method="POST")
    with urlopen(req,timeout=timeout) as resp: raw=json.load(resp)
    text=raw.get("output_text")
    if not text:
        parts=[]
        for item in raw.get("output",[]):
            for c in item.get("content",[]):
                if c.get("type")=="output_text": parts.append(c.get("text",""))
        text="".join(parts)
    data=json.loads(text)
    confidence=max(0.0,min(1.0,float(data.get("confidence",0.0))))
    return ResearchReview(model=model,summary=str(data.get("summary","")),
        supporting_evidence=tuple(map(str,data.get("supporting_evidence",[]))),
        counter_evidence=tuple(map(str,data.get("counter_evidence",[]))),
        risks=tuple(map(str,data.get("risks",[]))),hypotheses=tuple(map(str,data.get("hypotheses",[]))),
        confidence=confidence)

def to_dict(value: ResearchReview)->dict[str,Any]: return asdict(value)
