from pydantic import BaseModel


class Confidence(BaseModel):
    score: float
    level: str
    reasons: list[str] = []
