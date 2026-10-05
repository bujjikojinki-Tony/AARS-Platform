from __future__ import annotations
import json,sqlite3
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
SCHEMA="""
CREATE TABLE IF NOT EXISTS cognitive_forecasts(
 forecast_id TEXT PRIMARY KEY, packet_id TEXT NOT NULL, symbol TEXT NOT NULL, horizon_hours INTEGER NOT NULL,
 created_at TEXT NOT NULL, evidence_json TEXT NOT NULL, forecast_json TEXT NOT NULL, authority TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS forecast_outcomes(
 forecast_id TEXT PRIMARY KEY, evaluated_at TEXT NOT NULL, start_price REAL NOT NULL, end_price REAL NOT NULL,
 realized_return REAL NOT NULL, realized_class TEXT NOT NULL);
"""
class ForecastMemory:
 def __init__(self,path:str|Path): self.path=Path(path)
 def _db(self): return sqlite3.connect(self.path)
 def init(self):
  with self._db() as db: db.executescript(SCHEMA)
 def save(self,evidence:dict[str,Any],forecast:dict[str,Any]):
  self.init()
  with self._db() as db: db.execute("INSERT OR IGNORE INTO cognitive_forecasts VALUES(?,?,?,?,?,?,?,?)",
   (forecast["forecast_id"],forecast["packet_id"],forecast["symbol"],forecast["horizon_hours"],datetime.now(timezone.utc).isoformat(),
    json.dumps(evidence,sort_keys=True,default=str),json.dumps(forecast,sort_keys=True,default=str),"RESEARCH_ONLY"))
 def pending(self):
  self.init()
  with self._db() as db:
   rows=db.execute("SELECT f.* FROM cognitive_forecasts f LEFT JOIN forecast_outcomes o ON f.forecast_id=o.forecast_id WHERE o.forecast_id IS NULL").fetchall()
  return rows
 def save_outcome(self,fid,start,end,cls):
  self.init()
  with self._db() as db: db.execute("INSERT OR REPLACE INTO forecast_outcomes VALUES(?,?,?,?,?,?)",
   (fid,datetime.now(timezone.utc).isoformat(),start,end,end/start-1,cls))
