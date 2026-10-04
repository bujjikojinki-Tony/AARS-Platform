from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA="""
CREATE TABLE IF NOT EXISTS cognitive_reviews(
 packet_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, evidence_json TEXT NOT NULL,
 report_json TEXT NOT NULL, authority TEXT NOT NULL DEFAULT 'RESEARCH_ONLY');
CREATE TABLE IF NOT EXISTS cognitive_outcomes(
 packet_id TEXT NOT NULL, symbol TEXT NOT NULL, horizon_hours INTEGER NOT NULL,
 evaluated_at TEXT NOT NULL, start_price REAL NOT NULL, end_price REAL NOT NULL,
 realized_return REAL NOT NULL, realized_class TEXT NOT NULL,
 PRIMARY KEY(packet_id,symbol,horizon_hours));
"""

class CognitiveMemory:
 def __init__(self,path:str|Path): self.path=Path(path)
 def _db(self): return sqlite3.connect(self.path)
 def init(self):
  with self._db() as db: db.executescript(SCHEMA)
 def save(self,packet_id:str,evidence:dict[str,Any],report:dict[str,Any]):
  self.init()
  with self._db() as db:
   db.execute("INSERT OR IGNORE INTO cognitive_reviews VALUES(?,?,?,?,?)",
    (packet_id,datetime.now(timezone.utc).isoformat(),json.dumps(evidence,sort_keys=True,default=str),
     json.dumps(report,sort_keys=True,default=str),"RESEARCH_ONLY"))
 def review(self,packet_id:str)->dict[str,Any]|None:
  self.init()
  with self._db() as db: row=db.execute("SELECT created_at,evidence_json,report_json,authority FROM cognitive_reviews WHERE packet_id=?",(packet_id,)).fetchone()
  return None if row is None else {"packet_id":packet_id,"created_at":row[0],"evidence":json.loads(row[1]),"report":json.loads(row[2]),"authority":row[3]}
 def save_outcome(self,packet_id:str,symbol:str,horizon:int,start:float,end:float,realized_class:str):
  self.init()
  with self._db() as db:
   db.execute("INSERT OR REPLACE INTO cognitive_outcomes VALUES(?,?,?,?,?,?,?,?)",
    (packet_id,symbol,horizon,datetime.now(timezone.utc).isoformat(),start,end,end/start-1.0,realized_class))
