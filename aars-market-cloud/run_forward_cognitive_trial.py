import argparse,json
from aars_market.forward_cognitive_trial import run_cycle
p=argparse.ArgumentParser();p.add_argument("--db",default="/data/mil3_market.sqlite");p.add_argument("--memory-db",default="/data/cognitive_memory.sqlite");p.add_argument("--state-file",default="/data/cognitive_trial_state.json");p.add_argument("--scorecard",default="/data/cognitive_scorecard.json");p.add_argument("--days",type=int,default=30);p.add_argument("--forecast-every-hours",type=int,default=4);a=p.parse_args()
print(json.dumps(run_cycle(".",a.db,a.memory_db,a.state_file,a.scorecard,a.days,a.forecast_every_hours),ensure_ascii=False,indent=2))
