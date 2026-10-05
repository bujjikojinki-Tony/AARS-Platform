from __future__ import annotations
import json,sqlite3
from datetime import datetime,timedelta,timezone
from pathlib import Path
from .forecast_memory import ForecastMemory
from .storage import MarketStore
def evaluate_pending(memory_db,market_db):
 mem=ForecastMemory(memory_db);mem.init();store=MarketStore(Path(market_db));results=[]
 with sqlite3.connect(Path(memory_db)) as db:
  db.row_factory=sqlite3.Row
  rows=db.execute("SELECT f.* FROM cognitive_forecasts f LEFT JOIN forecast_outcomes o ON f.forecast_id=o.forecast_id WHERE o.forecast_id IS NULL").fetchall()
 for r in rows:
  ev=json.loads(r["evidence_json"]);market=ev.get("market") or {};raw=market.get("latest_candle_at")
  if not raw:continue
  t=datetime.fromisoformat(raw.replace("Z","+00:00")).astimezone(timezone.utc);tf=market.get("timeframe","1h")
  a=store.load_candles(r["symbol"],tf,start=t,end=t);target=t+timedelta(hours=r["horizon_hours"]);b=store.load_candles(r["symbol"],tf,start=target,end=target)
  if not a or not b:continue
  start=float(a[-1].close);end=float(b[-1].close);ret=end/start-1;cls="BULL" if ret>=.01 else "BEAR" if ret<=-.01 else "BASE"
  mem.save_outcome(r["forecast_id"],start,end,cls);results.append({"forecast_id":r["forecast_id"],"symbol":r["symbol"],"horizon_hours":r["horizon_hours"],"realized_return":ret,"realized_class":cls})
 return {"evaluation_mode":"OBSERVATION_ONLY","evaluated":results}
