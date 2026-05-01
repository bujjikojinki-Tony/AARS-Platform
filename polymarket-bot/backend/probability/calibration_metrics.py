from __future__ import annotations


def _validate_probability(predicted_probability: float) -> None:
    if predicted_probability < 0 or predicted_probability > 1:
        raise ValueError("predicted_probability must be in [0, 1]")


def _validate_actual_outcome(actual_outcome: int) -> None:
    if actual_outcome not in {0, 1}:
        raise ValueError("actual_outcome must be 0 or 1")


def brier_score(predicted_probability: float, actual_outcome: int) -> float:
    _validate_probability(predicted_probability)
    _validate_actual_outcome(actual_outcome)
    return (predicted_probability - actual_outcome) ** 2


def absolute_error(predicted_probability: float, actual_outcome: int) -> float:
    _validate_probability(predicted_probability)
    _validate_actual_outcome(actual_outcome)
    return abs(predicted_probability - actual_outcome)


def probability_bucket(predicted_probability: float) -> str:
    _validate_probability(predicted_probability)
    if predicted_probability < 0.2:
        return "0.0-0.2"
    if predicted_probability < 0.4:
        return "0.2-0.4"
    if predicted_probability < 0.6:
        return "0.4-0.6"
    if predicted_probability < 0.8:
        return "0.6-0.8"
    return "0.8-1.0"
