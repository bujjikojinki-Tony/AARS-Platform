from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationSummary(BaseModel):
    schema_version: str = "validation_summary.v1"
    generated_at: str
    scope_type: str
    scope_id: str
    validation_status: str
    validation_age: str | None = None
    label_coverage: float | None = None
    source_coverage: float | None = None
    normalization_consistency: float | None = None
    family_support_level: str | None = None
    promotion_readiness: str
    reasons: list[str] = Field(default_factory=list)
    policy_refs: dict = Field(default_factory=dict)
    upstream_refs: dict = Field(default_factory=dict)


class CoverageSummary(BaseModel):
    schema_version: str = "coverage_summary.v1"
    generated_at: str
    scope_type: str
    scope_id: str
    label_coverage: float
    official_label_coverage: float | None = None
    source_coverage: float
    forecast_coverage: float | None = None
    observation_coverage: float | None = None
    freshness_reliability: float | None = None
    source_precision_reliability: float | None = None
    coverage_components: dict = Field(default_factory=dict)
    upstream_refs: dict = Field(default_factory=dict)


class PromotionDecisionSupport(BaseModel):
    schema_version: str = "promotion_decision_support.v1"
    generated_at: str
    scope_type: str
    scope_id: str
    current_probability_mode: str
    promotion_readiness: str
    promotion_reason: str | None = None
    demotion_reason: str | None = None
    blocking_factors: list[str] = Field(default_factory=list)
    validation_summary_ref: str
    policy_refs: dict = Field(default_factory=dict)


class ModelValidationCompare(BaseModel):
    schema_version: str = "model_validation_compare.v1"
    generated_at: str
    scope_type: str
    scope_id: str
    candidate_models: list[str]
    candidate_source_stacks: list[list[str]]
    validation_scores: dict = Field(default_factory=dict)
    coverage_scores: dict = Field(default_factory=dict)
    freshness_reliability_scores: dict = Field(default_factory=dict)
    selected_best_model: str | None = None
    selected_best_source_stack: list[str] = Field(default_factory=list)
    selected_best_model_reason: str | None = None
    policy_refs: dict = Field(default_factory=dict)
