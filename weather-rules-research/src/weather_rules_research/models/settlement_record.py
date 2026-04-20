from __future__ import annotations

from pydantic import BaseModel


class SettlementRecord(BaseModel):
    station_id: str
    target_date: str
    variable_name: str
    official_value: float | None
    unit: str | None = None
    source: str
    source_url: str | None = None
    raw_payload_ref: str | None = None
    quality_flag: str | None = None
    notes: str | None = None
