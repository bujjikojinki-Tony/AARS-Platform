from __future__ import annotations
import json,subprocess
from dataclasses import asdict,dataclass
from datetime import datetime,timedelta,timezone
from pathlib import Path
@dataclass
class TrialState:
 started_at:str; ends_at:str; last_forecast_at:str|None=None; last_scorecard_at:str|None=None; forecast_cycles:int=0; outcome_cycles:int=0; status:str="RUNNING"
def _load(p,days):
 if Path(p).exists(): return TrialState(**json.loads(Path(p).read_text()))
 n=datetime.now(timezone.utc); return TrialState(n.isoformat(),(n+timedelta(days=days)).isoformat())
def _due(last,hours,now): return last is None or now-datetime.fromisoformat(last)>=timedelta(hours=hours)
def run_cycle(root=".",db="/data/mil3_market.sqlite",memory_db="/data/cognitive_memory.sqlite",state_file="/data/cognitive_trial_state.json",scorecard="/data/cognitive_scorecard.json",days=30,forecast_every_hours=4):
 s=_load(state_file,days);now=datetime.now(timezone.utc);actions=[]
 if now>=datetime.fromisoformat(s.ends_at): s.status="COMPLETE"
 subprocess.run(["python",str(Path(root)/"run_forecast_outcomes.py"),"--db",db,"--memory-db",memory_db],check=True);s.outcome_cycles+=1;actions.append("OUTCOMES_CHECKED")
 if s.status=="RUNNING" and _due(s.last_forecast_at,forecast_every_hours,now):
  subprocess.run(["python",str(Path(root)/"run_asset_forecasts.py"),"--db",db,"--memory-db",memory_db],check=True);s.last_forecast_at=now.isoformat();s.forecast_cycles+=1;actions.append("FORECASTS_CREATED")
 if _due(s.last_scorecard_at,24,now):
  subprocess.run(["python",str(Path(root)/"run_cognitive_scorecard.py"),"--memory-db",memory_db,"--output",scorecard],check=True);s.last_scorecard_at=now.isoformat();actions.append("SCORECARD_WRITTEN")
 Path(state_file).write_text(json.dumps(asdict(s),indent=2)+"\n")
 return {"trial":asdict(s),"actions":actions,"execution_mode":"PAPER_ONLY","adaptation":"DISABLED"}
