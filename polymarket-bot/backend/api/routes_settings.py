from __future__ import annotations

from fastapi import APIRouter


def create_settings_router(rule_registry) -> APIRouter:
    router = APIRouter(prefix="/api/settings", tags=["settings"])

    @router.get("/rules")
    def get_rules():
        return rule_registry.get_rules()

    @router.post("/rules")
    def update_rules(payload: dict):
        return rule_registry.update_rules(payload)

    @router.get("/mode")
    def get_mode():
        return {"mode": rule_registry.get_mode()}

    @router.post("/mode")
    def set_mode(payload: dict):
        try:
            mode = rule_registry.set_mode(payload.get("mode"))
            return {"status": "ok", "mode": mode}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    return router
