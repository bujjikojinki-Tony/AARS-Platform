# MIL-4.1 Automated Evidence

MIL-4.1 removes the hand-authored evidence file.

SQLite -> DashboardService -> compact deterministic evidence -> Primary -> Challenger -> Evidence Gate.

Run evidence only:
```bash
python run_evidence_packet.py --db /data/mil3_market.sqlite --output evidence.json
```

Run the complete cognitive cycle:
```bash
python run_cognitive_cycle.py --db /data/mil3_market.sqlite --output cognitive_report.json
```

The source of truth remains the deterministic AARS service layer. The LLM receives derived evidence but cannot write market data, strategy parameters, credentials, positions, or orders. PAPER_ONLY remains invariant.
