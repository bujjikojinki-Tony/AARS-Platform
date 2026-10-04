# MIL-4 Cognitive Research Layer

Pipeline:

Quant/market evidence -> EvidencePacket -> Primary Researcher -> Challenger -> Evidence Gate -> CognitiveReport.

Invariants:
- execution_mode is always PAPER_ONLY.
- LLM authority is RESEARCH_ONLY.
- Evidence Gate has zero order authority.
- No model may change leverage, exposure, strategy parameters, credentials or execution state.
- Challenger is deliberately given the primary result and asked to falsify it.
- Gate requires counter-evidence and risk evidence; otherwise the report is INSUFFICIENT_EVIDENCE.

Recommended deployment:
- primary: gpt-6-sol for deeper scheduled reviews, or gpt-6-luna for frequent low-cost reviews.
- challenger: independently configured model via AARS_LLM_CHALLENGER_MODEL.
- keep API keys only in local/cloud secret storage, never Git.
