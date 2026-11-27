from __future__ import annotations


class SDKValidationError(ValueError):
    """Base SDK error for invalid facade input."""


class SDKRelationshipError(SDKValidationError):
    """Raised when an SDK relationship points at an illegal object type."""


class SDKConformanceError(SDKValidationError):
    """Raised when SDK-created objects fail AARS graph conformance."""
