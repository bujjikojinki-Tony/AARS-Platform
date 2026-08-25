from pathlib import Path
import re


UI_ROOT = Path(__file__).parents[1] / "ui"


def test_continuous_shadow_workspace_exposes_task_and_safety_hierarchy():
    html = (UI_ROOT / "index.html").read_text(encoding="utf-8")

    assert "AARS // 03.15" in html
    assert 'id="shadow-state-banner"' in html
    assert 'id="shadow-review-gate"' in html
    assert 'id="shadow-history-trust"' in html
    assert 'id="shadow-trend"' in html
    assert 'id="shadow-warning-list"' in html
    assert 'id="shadow-timeline"' in html
    assert 'id="shadow-detail"' in html
    assert "LATEST STABLE SNAPSHOT" in html
    assert "LIVE EXECUTION DISALLOWED" in html
    assert "Created By Deerflow" in html


def test_continuous_shadow_client_uses_only_read_only_mil312_routes():
    javascript = (UI_ROOT / "app.js").read_text(encoding="utf-8")

    assert "/api/v1/shadow-snapshots?limit=90" in javascript
    assert "/api/v1/shadow-stability?limit=90" in javascript
    assert "/api/v1/shadow-snapshots/${encodeURIComponent(snapshotId)}" in javascript
    assert 'payload.execution_mode !== "PAPER_ONLY"' in javascript
    assert 'payload.review_gate?.live_execution_allowed !== false' in javascript
    assert "No sample daily evidence is fabricated" in javascript
    assert "method: \"POST\"" not in javascript
    assert "method: \"PUT\"" not in javascript
    assert "method: \"PATCH\"" not in javascript
    assert "method: \"DELETE\"" not in javascript


def test_continuous_shadow_layout_has_responsive_and_degraded_states():
    css = (UI_ROOT / "styles.css").read_text(encoding="utf-8")

    assert '.shadow-state-banner[data-status="DEGRADED"]' in css
    assert ".shadow-grid" in css
    assert ".shadow-asset-grid" in css
    assert "@media (max-width: 900px)" in css
    assert "@media (max-width: 620px)" in css
    assert "prefers-reduced-motion" in css


def test_mil313_dom_ids_remain_unique():
    html = (UI_ROOT / "index.html").read_text(encoding="utf-8")
    ids = re.findall(r'\bid="([^"]+)"', html)

    assert len(ids) == len(set(ids))
