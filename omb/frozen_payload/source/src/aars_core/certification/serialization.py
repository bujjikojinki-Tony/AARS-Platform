from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from aars_core.domain.common import ObjectStatus, ObjectType, Provenance
from aars_core.domain.objects import Claim, Decision, Evidence, Knowledge, Lesson, Memory, Observation, Outcome, Policy


OBJECT_CLASSES = {
    ObjectType.OBSERVATION: Observation, ObjectType.EVIDENCE: Evidence,
    ObjectType.CLAIM: Claim, ObjectType.DECISION: Decision,
    ObjectType.OUTCOME: Outcome, ObjectType.LESSON: Lesson,
    ObjectType.MEMORY: Memory, ObjectType.KNOWLEDGE: Knowledge,
    ObjectType.POLICY: Policy,
}

REFERENCE_FIELDS = {
    "observation_ids", "evidence_ids", "claim_ids", "decision_ids",
    "outcome_ids", "lesson_ids", "knowledge_ids", "codes",
}


def load_graph(path: str | Path) -> tuple[object, ...]:
    source = Path(path)
    documents = [_load_json(item) for item in sorted(source.glob("*.json"))] if source.is_dir() else [_load_json(source)]
    if not documents:
        raise ValueError("input directory contains no JSON files")
    records: list[Mapping[str, Any]] = []
    for document in documents:
        if isinstance(document, dict) and "objects" in document:
            document = document["objects"]
        elif isinstance(document, dict) and "type" in document:
            document = [document]
        if not isinstance(document, list):
            raise ValueError("input must contain a domain object, an object array, or an 'objects' array")
        records.extend(document)
    return tuple(object_from_dict(record) for record in records)


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def object_from_dict(record: Mapping[str, Any]) -> object:
    if not isinstance(record, Mapping):
        raise TypeError("each graph object must be a JSON object")
    data = dict(record)
    object_type = ObjectType(data["type"])
    provenance_data = dict(data["provenance"])
    provenance_data["collected_at"] = _datetime(provenance_data["collected_at"])
    provenance_data["parent_ids"] = tuple(provenance_data.get("parent_ids", ()))
    data["provenance"] = Provenance(**provenance_data)
    data["type"] = object_type
    data["status"] = ObjectStatus(data["status"])
    data["created_at"] = _datetime(data["created_at"])
    for field in REFERENCE_FIELDS & data.keys():
        data[field] = tuple(data[field])
    for field in ("observed_at", "measured_at"):
        if field in data:
            data[field] = _datetime(data[field])
    return OBJECT_CLASSES[object_type](**data)


def _datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise TypeError("datetime fields must use ISO-8601 text")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
