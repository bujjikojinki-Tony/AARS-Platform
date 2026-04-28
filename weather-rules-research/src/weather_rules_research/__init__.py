"""Weather rules research package."""

from .normalization import (
    convert_to_canonical,
    format_display_value,
    get_band_mapping_policy,
    get_canonical_value,
    get_display_value,
    normalize_measurement,
)

__all__ = [
    "convert_to_canonical",
    "format_display_value",
    "get_band_mapping_policy",
    "get_canonical_value",
    "get_display_value",
    "normalize_measurement",
]

__all__ = ["__version__"]

__version__ = "0.1.0"
