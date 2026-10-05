from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
from typing import Any
from .calibrated_research import review_calibrated

def _forecast_id(packet_id:str,symbol:str,horizon:int)->str:
 return sha256(f"{packet_id}:{symbol}:{horizon}".encode()).hexdigest()[:20]

def forecast_asset(packet_id:str,symbol:str,asset_evidence:dict[str,Any],horizon:int,*,primary_model=None,challenger_model=None)->dict[str,Any]:
 base={"packet_id":packet_id,"symbol":symbol,"horizon_hours":horizon,"asset_evidence":asset_evidence}
 primary=review_calibrated({"role":"PRIMARY","forecast":base},model=primary_model)
 challenger=review_calibrated({"role":"CHALLENGER","instruction":"Independently challenge this asset forecast.","forecast":base,"primary":asdict(primary)},model=challenger_model)
 return {"forecast_id":_forecast_id(packet_id,symbol,horizon),"packet_id":packet_id,"symbol":symbol,"horizon_hours":horizon,
         "primary":asdict(primary),"challenger":asdict(challenger),"authority":"RESEARCH_ONLY","execution_authority":"NONE"}
