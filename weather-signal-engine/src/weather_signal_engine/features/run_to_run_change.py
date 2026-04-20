def compute_run_to_run_change(previous_value: float | None, current_value: float) -> float | None:
    if previous_value is None:
        return None
    return round(current_value - previous_value, 4)
