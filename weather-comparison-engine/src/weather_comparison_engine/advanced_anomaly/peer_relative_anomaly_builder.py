from __future__ import annotations


def build_peer_relative_anomaly(*, market_row: dict, peer_rows: list[dict]) -> dict:
    metric = _to_float(market_row.get("edge_dislocation"))
    if metric == 0.0:
        metric = _to_float(market_row.get("anomaly_score"))

    peer_values = []
    for row in peer_rows:
        value = _to_float(row.get("edge_dislocation"))
        if value == 0.0:
            value = _to_float(row.get("anomaly_score"))
        peer_values.append(value)

    if not peer_values:
        return {"peer_rank": 0, "peer_zscore": 0.0, "peer_outlier_flag": False, "peer_relative_anomaly_score": 0.0}

    peer_values = sorted(peer_values)
    rank = 1 + sum(1 for value in peer_values if value < metric)
    mean = sum(peer_values) / len(peer_values)
    variance = sum((value - mean) ** 2 for value in peer_values) / len(peer_values)
    std = variance ** 0.5 if variance > 0 else 0.0
    zscore = 0.0 if std == 0 else (metric - mean) / std
    score = min(1.0, abs(zscore) / 3.0)
    return {
        "peer_rank": rank,
        "peer_zscore": round(zscore, 4),
        "peer_outlier_flag": abs(zscore) >= 2.0,
        "peer_relative_anomaly_score": round(score, 4),
    }


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
