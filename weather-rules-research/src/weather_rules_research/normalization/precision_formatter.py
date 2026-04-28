from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def format_display_value(value: float, *, precision: int | None, rounding_rule: str) -> float:
    if precision is None or rounding_rule == "exact_no_rounding":
        return value
    quantize = Decimal("1").scaleb(-precision)
    decimal_value = Decimal(str(value))
    return float(decimal_value.quantize(quantize, rounding=ROUND_HALF_UP))
