from __future__ import annotations
import json,sqlite3
from pathlib import Path
def observation_payload(data_dir="/data"):
 d=Path(data_dir);state=d/"cognitive_trial_state.json";score=d/"cognitive_scorecard.json";db=d/"cognitive_memory.sqlite"
 p={"schema_version":"mil4.observation.v1","execution_mode":"PAPER_ONLY","authority":"READ_ONLY","trial":json.loads(state.read_text()) if state.exists() else {"status":"NOT_STARTED"},"scorecard":json.loads(score.read_text()) if score.exists() else {"status":"PENDING"}}
 if db.exists():
  with sqlite3.connect(db) as con:
   for table,key in [("cognitive_forecasts","forecast_count"),("forecast_outcomes","outcome_count")]:
    try:p[key]=con.execute("SELECT COUNT(*) FROM "+table).fetchone()[0]
    except sqlite3.Error:p[key]=0
 else:p.update(forecast_count=0,outcome_count=0)
 return p
