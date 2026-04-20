from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


PROBABILITY_CONTRACT_VERSION = "probability_contract.v1"


class ProbabilityContract(BaseModel):
    contract_version: str = Field(default=PROBABILITY_CONTRACT_VERSION)
    probability_mode: str = "heuristic_not_calibrated"
    calibration_status: str = "not_calibrated"
    execution_constraint: str = "manual_advisory_only"
    model_id: str | None = None
    validation_ref: str | None = None
    approved_for_live: bool = False
    deployment_mode: str = "shadow"
    promotion_reason: str | None = None
    contract_source: str | None = None
    validation_report_generated_at: str | None = None


def build_probability_contract(payload: dict[str, Any] | None) -> dict[str, Any]:
    source = payload or {}
    contract = ProbabilityContract(
        probability_mode=str(source.get("probability_mode") or "heuristic_not_calibrated"),
        calibration_status=str(source.get("calibration_status") or "not_calibrated"),
        execution_constraint=str(source.get("execution_constraint") or "manual_advisory_only"),
        model_id=source.get("model_id"),
        validation_ref=source.get("validation_ref") or source.get("validation_report_generated_at"),
        approved_for_live=bool(source.get("approved_for_live", False)),
        deployment_mode=str(source.get("deployment_mode") or "shadow"),
        promotion_reason=source.get("promotion_reason"),
        contract_source=source.get("contract_source"),
        validation_report_generated_at=source.get("validation_report_generated_at"),
    )
    return contract.model_dump(mode="json", exclude_none=True)
