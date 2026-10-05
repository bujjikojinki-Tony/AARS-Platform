import argparse,json
from aars_market.forecast_outcomes import evaluate_pending
p=argparse.ArgumentParser();p.add_argument("--db",default="mil3_market.sqlite");p.add_argument("--memory-db",default="cognitive_memory.sqlite");a=p.parse_args()
print(json.dumps(evaluate_pending(a.memory_db,a.db),ensure_ascii=False,indent=2))
