from __future__ import annotations

from weather_comparison_engine.status.gate_stack_consumer import consume_gate_stack_payload


def build_gate_stack_contract_consistency_report(
    gate_stack_api: dict | None,
    automation_summary: dict | None,
    *,
    market_id: str | None = None,
    telegram_runtime_snapshot: dict | None = None,
    gateway_runtime_snapshot: dict | None = None,
) -> dict:
    api = gate_stack_api if isinstance(gate_stack_api, dict) else {}
    summary = automation_summary if isinstance(automation_summary, dict) else {}
    telegram = telegram_runtime_snapshot if isinstance(telegram_runtime_snapshot, dict) else {}
    gateway = gateway_runtime_snapshot if isinstance(gateway_runtime_snapshot, dict) else {}
    selected_market_id = str(market_id or summary.get("market_id") or api.get("market_id") or "")
    consumer = consume_gate_stack_payload(api, market_id=selected_market_id)

    checks: list[dict[str, object]] = []
    checks.append(
        _check_equal(
            "source_schema_alignment",
            str(summary.get("source_schema_version") or ""),
            str(api.get("schema_version") or ""),
        )
    )
    checks.append(
        _check_equal(
            "market_id_alignment",
            str(summary.get("market_id") or ""),
            selected_market_id,
        )
    )

    source_payload = consumer.market_view if isinstance(consumer.market_view, dict) else _resolve_api_source_payload(api, market_id=selected_market_id)
    checks.append(
        _check_equal(
            "can_execute_alignment",
            bool(summary.get("can_execute", False)),
            bool(source_payload.get("can_execute", api.get("can_execute", False))),
        )
    )
    checks.append(
        _check_equal(
            "severity_alignment",
            str(summary.get("severity") or ""),
            str(source_payload.get("severity") or api.get("severity") or ""),
        )
    )
    checks.append(
        _check_equal(
            "primary_block_reason_alignment",
            str(summary.get("primary_block_reason") or ""),
            str(
                source_payload.get("primary_block_reason")
                or api.get("primary_block_reason")
                or ""
            ),
        )
    )
    checks.append(
        _check_equal(
            "recommended_action_alignment",
            str(summary.get("recommended_operator_action") or ""),
            str(
                source_payload.get("recommended_operator_action")
                or api.get("recommended_operator_action")
                or ""
            ),
        )
    )

    summary_block_reasons = [str(item) for item in summary.get("block_reasons") or []]
    source_block_reasons = [
        str(item) for item in source_payload.get("block_reasons") or api.get("block_reasons") or []
    ]
    checks.append(
        _check_equal(
            "block_reasons_alignment",
            summary_block_reasons,
            source_block_reasons,
        )
    )

    gate_source = str(summary.get("gate_source") or consumer.gate_source or "api")
    checks.append(
        {
            "name": "gate_source_enum",
            "passed": gate_source in {"api", "unified_fallback", "local_fallback"},
            "actual": gate_source,
            "expected": "api|unified_fallback|local_fallback",
        }
    )
    expected_block_reasons = [str(item) for item in summary.get("block_reasons") or []]
    if telegram:
        checks.extend(
            _surface_checks(
                "telegram",
                telegram,
                selected_market_id=selected_market_id,
                expected_gate_source=gate_source,
                expected_block_reasons=expected_block_reasons,
            )
        )
    if gateway:
        checks.extend(
            _surface_checks(
                "gateway",
                gateway,
                selected_market_id=selected_market_id,
                expected_gate_source=gate_source,
                expected_block_reasons=expected_block_reasons,
            )
        )

    passed = all(bool(item.get("passed")) for item in checks)
    mismatches = [item for item in checks if not bool(item.get("passed"))]
    mismatch_buckets = _mismatch_buckets(mismatches)
    schema_health = _schema_health(api=api, summary=summary, telegram=telegram, gateway=gateway)
    fallback_stats = _fallback_stats(summary=summary, telegram=telegram, gateway=gateway)
    return {
        "schema_version": "gate_stack_contract_consistency.v1",
        "market_id": selected_market_id or None,
        "passed": passed,
        "schema_health": schema_health,
        "fallback_stats": fallback_stats,
        "mismatch_buckets": mismatch_buckets,
        "checks": checks,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def _resolve_api_source_payload(payload: dict, *, market_id: str) -> dict:
    if market_id:
        views = payload.get("market_gate_views")
        if isinstance(views, list):
            for view in views:
                if not isinstance(view, dict):
                    continue
                if str(view.get("market_id") or "") == market_id:
                    return view
    return payload


def _check_equal(name: str, actual: object, expected: object) -> dict[str, object]:
    return {
        "name": name,
        "passed": actual == expected,
        "actual": actual,
        "expected": expected,
    }


def _surface_checks(
    surface: str,
    payload: dict,
    *,
    selected_market_id: str,
    expected_gate_source: str,
    expected_block_reasons: list[str],
) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    checks.append(
        _check_equal(
            f"{surface}_market_id_alignment",
            str(payload.get("market_id") or ""),
            selected_market_id,
        )
    )
    checks.append(
        _check_equal(
            f"{surface}_gate_source_alignment",
            str(payload.get("gate_source") or ""),
            expected_gate_source,
        )
    )
    checks.append(
        _check_equal(
            f"{surface}_block_reasons_alignment",
            [str(item) for item in payload.get("block_reasons") or []],
            expected_block_reasons,
        )
    )
    return checks


def _schema_health(*, api: dict, summary: dict, telegram: dict, gateway: dict) -> dict:
    issues: list[dict[str, object]] = []
    surfaces = {
        "gate_stack_api": api,
        "automation_summary": summary,
        "telegram_runtime": telegram,
        "gateway_runtime": gateway,
    }
    for name, payload in surfaces.items():
        if not payload:
            continue
        if not str(payload.get("schema_version") or "").strip():
            issues.append({"surface": name, "field": "schema_version", "level": "critical"})
        if not str(payload.get("generated_at") or "").strip():
            issues.append({"surface": name, "field": "generated_at", "level": "warning"})
        if name == "automation_summary" and not str(payload.get("gate_source") or "").strip():
            issues.append({"surface": name, "field": "gate_source", "level": "warning"})

    level = "ok"
    if any(item.get("level") == "critical" for item in issues):
        level = "critical"
    elif issues:
        level = "warning"
    return {
        "level": level,
        "issue_count": len(issues),
        "issues": issues,
    }


def _fallback_stats(*, summary: dict, telegram: dict, gateway: dict) -> dict:
    counts = {
        "api": 0,
        "unified_fallback": 0,
        "local_fallback": 0,
        "unknown": 0,
    }
    for payload in (summary, telegram, gateway):
        if not payload:
            continue
        source = str(payload.get("gate_source") or "").strip().lower()
        if source in counts:
            counts[source] += 1
        else:
            counts["unknown"] += 1
    return counts


def _mismatch_buckets(mismatches: list[dict]) -> dict:
    bucket_names = ("schema_drift", "source_drift", "reason_drift", "other_drift")
    counts = {name: 0 for name in bucket_names}
    details = {name: [] for name in bucket_names}
    for mismatch in mismatches:
        name = str(mismatch.get("name") or "")
        bucket = _bucket_for_check_name(name)
        counts[bucket] += 1
        details[bucket].append(name)
    return {
        "counts": counts,
        "details": details,
    }


def _bucket_for_check_name(name: str) -> str:
    token = name.lower()
    if "schema" in token or "generated_at" in token:
        return "schema_drift"
    if "gate_source" in token or "market_id" in token:
        return "source_drift"
    if "reason" in token or "action" in token:
        return "reason_drift"
    return "other_drift"
