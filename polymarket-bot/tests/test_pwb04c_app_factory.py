from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app_factory import create_app


def test_create_app_uses_isolated_databases(tmp_path):
    db_one = tmp_path / "pwb04c_one.sqlite"
    db_two = tmp_path / "pwb04c_two.sqlite"

    app_one = create_app(str(db_one), allow_network=False)
    app_two = create_app(str(db_two), allow_network=False)

    client_one = TestClient(app_one)
    client_two = TestClient(app_two)

    assert client_one.get("/healthz").json()["status"] == "ok"
    assert client_two.get("/healthz").json()["status"] == "ok"

    assert client_one.get("/api/settings/mode").json()["mode"] == "OBSERVE_ONLY"
    assert client_two.get("/api/settings/mode").json()["mode"] == "OBSERVE_ONLY"

    response = client_one.post("/api/settings/mode", json={"mode": "SIMULATION"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["mode"] == "SIMULATION"

    assert client_one.get("/api/settings/mode").json()["mode"] == "SIMULATION"
    assert client_two.get("/api/settings/mode").json()["mode"] == "OBSERVE_ONLY"
