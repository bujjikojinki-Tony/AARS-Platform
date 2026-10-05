import argparse,json
from pathlib import Path
from aars_market.acceptance import build_acceptance
p=argparse.ArgumentParser();p.add_argument("--data-dir",default="/data");p.add_argument("--output",default="/data/mil4_7_acceptance.json");a=p.parse_args()
r=build_acceptance(a.data_dir);Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n");print(json.dumps(r,ensure_ascii=False,indent=2))
