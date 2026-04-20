from __future__ import annotations

VALID_FAIL_ON_SIGNALS = {"red", "amber", "never"}
EXIT_CODE_MATRIX = {
    "never": {"green": 0, "amber": 0, "red": 0},
    "red": {"green": 0, "amber": 0, "red": 2},
    "amber": {"green": 0, "amber": 2, "red": 2},
}


def build_exit_code_matrix() -> dict[str, dict[str, int]]:
    return {mode: dict(mapping) for mode, mapping in EXIT_CODE_MATRIX.items()}


def resolve_exit_code(summary: dict, *, fail_on_signal: str) -> int:
    mode = str(fail_on_signal or "").strip().lower()
    if mode not in VALID_FAIL_ON_SIGNALS:
        raise ValueError(f"Unsupported fail_on_signal: {fail_on_signal}")

    signal = str(summary.get("automation_signal") or "").strip().lower()
    return int(EXIT_CODE_MATRIX[mode].get(signal, 0))
