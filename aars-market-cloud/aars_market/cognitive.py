from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from .llm_research import ResearchReview, review, to_dict

@dataclass(frozen=True)
class EvidencePacket:
    packet_id: str
    generated_at: str
    execution_mode: str
    payload: dict[str, Any]

@dataclass(frozen=True)
class CognitiveReport:
    packet_id: str
    primary: dict[str, Any]
    challenger: dict[str, Any]
    gate: dict[str, Any]
    authority: str = "RESEARCH_ONLY"

def build_evidence_packet(payload: dict[str, Any]) -> EvidencePacket:
    canonical=json.dumps(payload,sort_keys=True,default=str,separators=(",",":"))
    return EvidencePacket(
        packet_id=sha256(canonical.encode()).hexdigest()[:16],
        generated_at=datetime.now(timezone.utc).isoformat(),
        execution_mode="PAPER_ONLY",
        payload=payload,
    )

def _challenger_payload(packet: EvidencePacket, primary: ResearchReview)->dict[str,Any]:
    return {
        "role":"CHALLENGER",
        "instruction":"Try to falsify the primary interpretation. Identify unsupported inference, missing evidence, regime alternatives and risk blind spots. Do not recommend trades.",
        "evidence_packet":asdict(packet),
        "primary_review":to_dict(primary),
    }

def evidence_gate(primary: ResearchReview, challenger: ResearchReview)->dict[str,Any]:
    p=float(primary.confidence); c=float(challenger.confidence)
    has_counter=bool(primary.counter_evidence or challenger.counter_evidence)
    has_risk=bool(primary.risks or challenger.risks)
    accepted=p >= 0.55 and has_counter and has_risk
    return {
        "status":"ACCEPTED_FOR_RESEARCH" if accepted else "INSUFFICIENT_EVIDENCE",
        "primary_confidence":p,
        "challenger_confidence":c,
        "counter_evidence_present":has_counter,
        "risk_evidence_present":has_risk,
        "execution_authority":"NONE",
        "execution_mode":"PAPER_ONLY",
    }

def run_cognitive_review(payload: dict[str,Any], *, primary_model: str|None=None, challenger_model: str|None=None)->CognitiveReport:
    packet=build_evidence_packet(payload)
    primary=review({"role":"PRIMARY_RESEARCHER","evidence_packet":asdict(packet)},model=primary_model)
    challenger=review(_challenger_payload(packet,primary),model=challenger_model)
    gate=evidence_gate(primary,challenger)
    return CognitiveReport(packet.packet_id,to_dict(primary),to_dict(challenger),gate)
