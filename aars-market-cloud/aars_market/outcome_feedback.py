from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
from typing import Any
from .cognitive_memory import CognitiveMemory
from .storage import MarketStore

def _classify(r:float,threshold:float=0.01)->str:
 return "BULL" if r>=threshold else "BEAR" if r<=-threshold else "BASE"

def evaluate(memory_db:str|Path, market_db:str|Path, packet_id:str, horizons=(24,72))->dict[str,Any]:
 mem=CognitiveMemory(memory_db); item=mem.review(packet_id)
 if item is None: raise ValueError(f"unknown packet_id: {packet_id}")
 store=MarketStore(Path(market_db))
 results=[]
 for symbol,asset in item["evidence"].get("assets",{}).items():
  market=asset.get("market") or {}
  raw=market.get("latest_candle_at")
  if not raw: continue
  start_time=datetime.fromisoformat(raw.replace("Z","+00:00")).astimezone(timezone.utc)
  start_rows=store.load_candles(symbol,market.get("timeframe","1h"),start=start_time,end=start_time)
  if not start_rows: continue
  start=float(start_rows[-1].close)
  for h in horizons:
   target=start_time+timedelta(hours=h)
   rows=store.load_candles(symbol,market.get("timeframe","1h"),start=target,end=target)
   if not rows: continue
   end=float(rows[-1].close); cls=_classify(end/start-1.0)
   mem.save_outcome(packet_id,symbol,h,start,end,cls)
   results.append({"symbol":symbol,"horizon_hours":h,"start_price":start,"end_price":end,"realized_return":end/start-1.0,"realized_class":cls})
 return {"packet_id":packet_id,"evaluation_mode":"OBSERVATION_ONLY","outcomes":results}
