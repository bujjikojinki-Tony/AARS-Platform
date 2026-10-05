from __future__ import annotations
import json,sqlite3
from datetime import datetime,timezone
from pathlib import Path
def assess(data_dir="/data",min_hours=72):
 d=Path(data_dir);sf=d/"cognitive_trial_state.json";mem=d/"cognitive_memory.sqlite";score=d/"cognitive_scorecard.json";checks=[]
 if not sf.exists():return {"status":"FAIL","checks":[{"id":"TRIAL_STATE","status":"FAIL","detail":"missing"}],"authority":"OBSERVATION_ONLY"}
 s=json.loads(sf.read_text());age=(datetime.now(timezone.utc)-datetime.fromisoformat(s["started_at"])).total_seconds()/3600
 checks.append({"id":"TRIAL_AGE","status":"PASS" if age>=min_hours else "WARN","detail":str(round(age,1))+"h"})
 checks.append({"id":"SCORECARD","status":"PASS" if score.exists() else "WARN"})
 f=o=0
 if mem.exists():
  with sqlite3.connect(mem) as c:
   try:f=c.execute("SELECT COUNT(*) FROM cognitive_forecasts").fetchone()[0]
   except sqlite3.Error:pass
   try:o=c.execute("SELECT COUNT(*) FROM forecast_outcomes").fetchone()[0]
   except sqlite3.Error:pass
 checks.append({"id":"FORECASTS","status":"PASS" if f>0 else "FAIL","detail":f})
 checks.append({"id":"OUTCOMES","status":"PASS" if o>0 else ("WARN" if age<24 else "FAIL"),"detail":o})
 status="FAIL" if any(x["status"]=="FAIL" for x in checks) else "WARN" if any(x["status"]=="WARN" for x in checks) else "PASS"
 return {"status":status,"observed_hours":age,"forecast_count":f,"outcome_count":o,"checks":checks,"execution_mode":"PAPER_ONLY","authority":"OBSERVATION_ONLY","automatic_changes":False}
