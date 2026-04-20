def choose_action_hint(edge_strength: float, confidence_score: float) -> str:
    if confidence_score < 0.5:
        return "ignore"
    if edge_strength <= 0.0:
        return "watch"
    if confidence_score >= 0.8:
        return "approve_small"
    return "watch"
