from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from aars_core.domain import (
    AARSObject,
    EP01_SPEC_VERSION,
    ObjectStatus,
    ObjectType,
    Provenance,
)

from .errors import SDKRelationshipError, SDKValidationError


DEFAULT_SOURCE_ID = "aars-sdk"
DEFAULT_SOURCE_TYPE = "sdk"
DEFAULT_SOURCE_VERSION = "1.0.0"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_id(object_type: ObjectType, value: str | None = None) -> str:
    if value is not None:
        if not isinstance(value, str) or not value.strip():
            raise SDKValidationError("id must be non-empty text when provided")
        return value
    return f"{object_type.value}.{uuid4().hex}"


def build_provenance(
    *,
    provenance: Provenance | None,
    created_at: datetime,
    source_id: str | None,
    source_type: str | None,
    source_version: str | None,
    content_hash: str | None,
    source_uri: str | None,
    parent_ids: tuple[str, ...],
) -> Provenance:
    if provenance is not None:
        if not isinstance(provenance, Provenance):
            raise SDKValidationError("provenance must be a Provenance instance")
        return provenance
    return Provenance(
        source_id=source_id or DEFAULT_SOURCE_ID,
        source_type=source_type or DEFAULT_SOURCE_TYPE,
        source_version=source_version or DEFAULT_SOURCE_VERSION,
        collected_at=created_at,
        content_hash=content_hash or "sha256:unavailable",
        source_uri=source_uri,
        parent_ids=parent_ids,
    )


def common_fields(
    *,
    object_type: ObjectType,
    status: ObjectStatus,
    id: str | None = None,
    created_at: datetime | None = None,
    spec_version: str = EP01_SPEC_VERSION,
    provenance: Provenance | None = None,
    semantic_type: str = "aars.any",
    source_id: str | None = None,
    source_type: str | None = None,
    source_version: str | None = None,
    content_hash: str | None = None,
    source_uri: str | None = None,
    parent_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    created = created_at or utc_now()
    return {
        "id": build_id(object_type, id),
        "type": object_type,
        "created_at": created,
        "spec_version": spec_version,
        "provenance": build_provenance(
            provenance=provenance,
            created_at=created,
            source_id=source_id,
            source_type=source_type,
            source_version=source_version,
            content_hash=content_hash,
            source_uri=source_uri,
            parent_ids=parent_ids,
        ),
        "status": status,
        "semantic_type": semantic_type,
    }


def require_objects(name: str, values: tuple[object, ...], expected: type[AARSObject]) -> tuple[AARSObject, ...]:
    if not isinstance(values, tuple):
        raise SDKValidationError(f"{name} must be provided as a tuple")
    if not values:
        raise SDKRelationshipError(f"{name} must contain at least one {expected.__name__}")
    for value in values:
        if not isinstance(value, expected):
            actual = value.__class__.__name__
            raise SDKRelationshipError(f"{name} must contain {expected.__name__} objects, not {actual}")
    return values  # type: ignore[return-value]


def require_optional_objects(
    name: str, values: tuple[object, ...], expected: type[AARSObject],
) -> tuple[AARSObject, ...]:
    if not isinstance(values, tuple):
        raise SDKValidationError(f"{name} must be provided as a tuple")
    for value in values:
        if not isinstance(value, expected):
            actual = value.__class__.__name__
            raise SDKRelationshipError(f"{name} must contain {expected.__name__} objects, not {actual}")
    return values  # type: ignore[return-value]


def ids(values: tuple[AARSObject, ...]) -> tuple[str, ...]:
    return tuple(value.id for value in values)
