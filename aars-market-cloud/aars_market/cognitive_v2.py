from __future__ import annotations
from dataclasses import asdict
from typing import Any
from .calibrated_research import review_calibrated
from .cognitive import build_evidence_packet

def run_calibrated_review(payload:dict[str,Any],*,horizon_hours:int=24,primary_model=None,challenger_model=None)->dict[str,Any]:
 packet=build_evidence_packet(payload)
 primary=review_calibrated({"role":"PRIMARY","horizon_hours":horizon_hours,"evidence_packet":asdict(packet)},model=primary_model)
 challenger=review_calibrated({"role":"CHALLENGER","horizon_hours":horizon_hours,"instruction":"Independently challenge the primary interpretation and produce your own probabilities.","evidence_packet":asdict(packet),"primary":asdict(primary)},model=challenger_model)
 return {"schema_version":"mil4.calibrated-review.v1","packet_id":packet.packet_id,"horizon_hours":horizon_hours,
  "primary":asdict(primary),"challenger":asdict(challenger),
  "gate":{"status":"ACCEPTED_FOR_RESEARCH" if (primary.counter_evidence or challenger.counter_evidence) and (primary.risks or challenger.risks) else "INSUFFICIENT_EVIDENCE",
          "execution_authority":"NONE","execution_mode":"PAPER_ONLY"},"authority":"RESEARCH_ONLY"}
