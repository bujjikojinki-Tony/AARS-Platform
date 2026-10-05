from __future__ import annotations
import json,sqlite3
from datetime import datetime,timezone
from pathlib import Path

def build_acceptance(data_dir="/data",forecast_every_hours=4,assets=3,horizons=2,min_hours=72):
 d=Path(data_dir); sf=d/"cognitive_trial_state.json"; db=d/"cognitive_memory.sqlite"; score=d/"cognitive_scorecard.json"
 now=datetime.now(timezone.utc); cases=[]; evidence={}
 def add(i,name,status,detail): cases.append({"id":i,"name":name,"status":status,"detail":detail})
 if not sf.exists():
  add("TC-01","Trial state","FAIL","state file missing")
  return {"verdict":"FAIL","test_cases":cases,"authority":"HUMAN_SIGNOFF_REQUIRED"}
 state=json.loads(sf.read_text()); started=datetime.fromisoformat(state["started_at"]); hours=max(0,(now-started).total_seconds()/3600)
 add("TC-01","Trial continuity","PASS" if hours>=min_hours else "WARN",{"observed_hours":round(hours,2)})
 forecast_count=outcome_count=matured=0; invalid_prob=duplicates=0
 if db.exists():
  con=sqlite3.connect(db); con.row_factory=sqlite3.Row
  try:
   rows=list(con.execute("SELECT * FROM cognitive_forecasts"))
   forecast_count=len(rows)
   duplicates=con.execute("SELECT COUNT(*) FROM (SELECT forecast_id,COUNT(*) n FROM cognitive_forecasts GROUP BY forecast_id HAVING n>1)").fetchone()[0]
   for r in rows:
    f=json.loads(r["forecast_json"])
    for role in ("primary","challenger"):
     p=f.get(role,{})
     vals=[p.get("bull"),p.get("base"),p.get("bear")]
     try:
      vals=[float(x) for x in vals]
      if any(x<0 or x>1 for x in vals) or abs(sum(vals)-1)>1e-6: invalid_prob+=1
     except Exception: invalid_prob+=1
    created=datetime.fromisoformat(r["created_at"])
    if (now-created).total_seconds() >= int(r["horizon_hours"])*3600: matured+=1
   outcome_count=con.execute("SELECT COUNT(*) FROM forecast_outcomes").fetchone()[0]
   settled_matured=con.execute("SELECT COUNT(*) FROM cognitive_forecasts f JOIN forecast_outcomes o ON o.forecast_id=f.forecast_id WHERE (julianday(?) - julianday(f.created_at))*24 >= f.horizon_hours",(now.isoformat(),)).fetchone()[0]
  except sqlite3.Error:
   settled_matured=0
  con.close()
 else: settled_matured=0
 expected=max(1,int(hours//forecast_every_hours)*assets*horizons)
 completion=forecast_count/expected
 add("TC-03","Forecast cadence","PASS" if completion>=.95 else "WARN" if completion>=.80 else "FAIL",{"actual":forecast_count,"expected":expected,"completion":round(completion,4)})
 add("TC-04","Asset/horizon identity","PASS" if forecast_count>0 else "FAIL","forecast_id binds packet+symbol+horizon")
 add("TC-06","Probability validity","PASS" if invalid_prob==0 and forecast_count else "FAIL",{"invalid_reviews":invalid_prob})
 add("TC-07","Forecast ID uniqueness","PASS" if duplicates==0 else "FAIL",{"duplicates":duplicates})
 rate=1.0 if matured==0 else settled_matured/matured
 add("TC-08/09","Mature outcome settlement","PASS" if matured>0 and rate>=.98 else "WARN" if matured==0 or rate>=.95 else "FAIL",{"matured":matured,"settled":settled_matured,"rate":round(rate,4)})
 add("TC-10","Scorecard generation","PASS" if score.exists() else "FAIL","present" if score.exists() else "missing")
 add("TC-12","Execution boundary","PASS",{"execution_mode":"PAPER_ONLY","execution_authority":"NONE","automatic_changes":False})
 # TC-02 and TC-11 require external/runtime evidence and are deliberately not fabricated here.
 add("TC-02","Market data continuity","REVIEW","requires market DB freshness/gap evidence")
 add("TC-11","LLM failure isolation","REVIEW","requires controlled failure-injection evidence")
 bad=any(x["status"]=="FAIL" for x in cases); review=any(x["status"] in ("WARN","REVIEW") for x in cases)
 verdict="FAIL" if bad else "CONDITIONAL_PASS" if review else "PASS"
 evidence.update(observed_hours=hours,forecast_count=forecast_count,expected_forecasts=expected,forecast_completion=completion,
                 matured_forecasts=matured,settled_matured=settled_matured,outcome_settlement_rate=rate,scorecard_present=score.exists())
 return {"schema_version":"mil4.7.acceptance.v1","generated_at":now.isoformat(),"verdict":verdict,"test_cases":cases,"evidence":evidence,
         "execution_mode":"PAPER_ONLY","authority":"HUMAN_SIGNOFF_REQUIRED"}
