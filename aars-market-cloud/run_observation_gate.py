import argparse,json
from aars_market.observation_gate import assess
p=argparse.ArgumentParser();p.add_argument("--data-dir",default="/data");p.add_argument("--min-hours",type=int,default=72);a=p.parse_args();r=assess(a.data_dir,a.min_hours);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(2 if r["status"]=="FAIL" else 0)
