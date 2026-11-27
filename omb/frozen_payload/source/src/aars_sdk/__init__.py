"""Stable SDK facade for creating AARS reference objects."""

from .client import AARSClient
from .errors import SDKConformanceError, SDKRelationshipError, SDKValidationError

SDK_API_VERSION = "1.0"

__all__ = [
    "AARSClient",
    "SDK_API_VERSION",
    "SDKConformanceError",
    "SDKRelationshipError",
    "SDKValidationError",
]
