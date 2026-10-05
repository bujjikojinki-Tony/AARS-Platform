from __future__ import annotations
import argparse,json,os
from aars_market.asset_forecast import forecast_asset
from aars_market.cognitive import build_evidence_packet
from aars_market.evidence_packet import build_from_sqlite
from aars_market.forecast_memory import ForecastMemory
from aars_market.service import DEFAULT_SYMBOLS
def main():
 p=argparse.ArgumentParser(description="MIL-4.5 per-asset per-horizon cognitive forecasts")
 p.add_argument("--db",default="mil3_market.sqlite");p.add_argument("--memory-db",default="cognitive_memory.sqlite")
 p.add_argument("--symbols",nargs="+",default=list(DEFAULT_SYMBOLS));p.add_argument("--horizons",nargs="+",type=int,default=[24,72]);p.add_argument("--window",default="90d")
 a=p.parse_args();e=build_from_sqlite(a.db,symbols=tuple(a.symbols),replay_window=a.window);packet=build_evidence_packet(e);mem=ForecastMemory(a.memory_db);out=[]
 for s in a.symbols:
  for h in a.horizons:
   f=forecast_asset(packet.packet_id,s,e["assets"][s],h,primary_model=os.getenv("AARS_LLM_PRIMARY_MODEL") or None,challenger_model=os.getenv("AARS_LLM_CHALLENGER_MODEL") or None)
   mem.save(e["assets"][s],f);out.append({"forecast_id":f["forecast_id"],"symbol":s,"horizon_hours":h})
 print(json.dumps({"packet_id":packet.packet_id,"forecasts":out,"execution_mode":"PAPER_ONLY"},ensure_ascii=False))
if __name__=="__main__":main()
