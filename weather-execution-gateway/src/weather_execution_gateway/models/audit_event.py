from pydantic import BaseModel


class AuditEvent(BaseModel):
    event_id: str
    intent_id: str
    event_type: str
    payload_json: str
