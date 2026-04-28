from __future__ import annotations


def convert_to_canonical(
    value: float,
    *,
    raw_unit: str | None,
    canonical_unit: str | None,
) -> float:
    raw = str(raw_unit or "").strip().lower()
    canonical = str(canonical_unit or "").strip().lower()
    if not raw or raw == canonical:
        return value

    if canonical == "celsius":
        if raw == "fahrenheit":
            return (value - 32.0) * (5.0 / 9.0)
        return value
    if canonical == "kt":
        if raw == "mph":
            return value * 0.868976
        if raw in {"m/s", "ms"}:
            return value * 1.943844
        if raw == "km/h":
            return value * 0.539957
        return value
    if canonical == "mm":
        if raw == "inch":
            return value * 25.4
        if raw == "cm":
            return value * 10.0
        return value
    return value
