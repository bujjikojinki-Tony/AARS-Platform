from __future__ import annotations

from statistics import mean
from uuid import uuid4

from backend.models.probability_governance import EnginePromotionDecision
from backend.models.probability_governance import ProbabilityEngineType
from backend.models.probability_governance import PromotionDecisionType


class ModelPromotionGate:
    def __init__(
        self,
        repository,
        minimum_evidence_count: int = 30,
        max_avg_brier_score: float = 0.20,
        max_avg_absolute_error: float = 0.35,
    ):
        self.repository = repository
        self.minimum_evidence_count = minimum_evidence_count
        self.max_avg_brier_score = max_avg_brier_score
        self.max_avg_absolute_error = max_avg_absolute_error

    def evaluate(self, engine_id: str) -> EnginePromotionDecision:
        config = self.repository.get_probability_engine_config(engine_id)
        if not config:
            raise ValueError("engine config not found")

        current_type = ProbabilityEngineType(config["engine_type"])
        if current_type == ProbabilityEngineType.PRIMARY:
            decision = EnginePromotionDecision(
                decision_id=f"pd_{uuid4().hex[:10]}",
                engine_id=engine_id,
                current_type=current_type,
                proposed_type=current_type,
                eligible=True,
                decision=PromotionDecisionType.KEEP_PRIMARY,
                evidence_count=0,
                reason="engine is already PRIMARY",
            )
            self.repository.save_engine_promotion_decision(decision)
            return decision

        results = self.repository.list_calibration_results_for_engine(
            engine_id=engine_id,
            limit=10_000,
        )
        evidence_count = len(results)
        avg_brier = mean([r["brier_score"] for r in results]) if results else None
        avg_abs = mean([r["absolute_error"] for r in results]) if results else None

        if evidence_count < self.minimum_evidence_count:
            decision = EnginePromotionDecision(
                decision_id=f"pd_{uuid4().hex[:10]}",
                engine_id=engine_id,
                current_type=current_type,
                proposed_type=current_type,
                eligible=False,
                decision=PromotionDecisionType.NEEDS_MORE_DATA,
                evidence_count=evidence_count,
                avg_brier_score=avg_brier,
                avg_absolute_error=avg_abs,
                reason=(
                    f"insufficient evidence: {evidence_count} < "
                    f"{self.minimum_evidence_count}"
                ),
            )
            self.repository.save_engine_promotion_decision(decision)
            return decision

        if config.get("can_be_primary") is not True:
            decision = EnginePromotionDecision(
                decision_id=f"pd_{uuid4().hex[:10]}",
                engine_id=engine_id,
                current_type=current_type,
                proposed_type=current_type,
                eligible=False,
                decision=PromotionDecisionType.KEEP_SHADOW,
                evidence_count=evidence_count,
                avg_brier_score=avg_brier,
                avg_absolute_error=avg_abs,
                reason="engine config can_be_primary=false",
            )
            self.repository.save_engine_promotion_decision(decision)
            return decision

        if avg_brier is not None and avg_brier > self.max_avg_brier_score:
            decision = EnginePromotionDecision(
                decision_id=f"pd_{uuid4().hex[:10]}",
                engine_id=engine_id,
                current_type=current_type,
                proposed_type=current_type,
                eligible=False,
                decision=PromotionDecisionType.KEEP_SHADOW,
                evidence_count=evidence_count,
                avg_brier_score=avg_brier,
                avg_absolute_error=avg_abs,
                reason=(
                    f"avg brier score {avg_brier:.4f} exceeds "
                    f"{self.max_avg_brier_score:.4f}"
                ),
            )
            self.repository.save_engine_promotion_decision(decision)
            return decision

        if avg_abs is not None and avg_abs > self.max_avg_absolute_error:
            decision = EnginePromotionDecision(
                decision_id=f"pd_{uuid4().hex[:10]}",
                engine_id=engine_id,
                current_type=current_type,
                proposed_type=current_type,
                eligible=False,
                decision=PromotionDecisionType.KEEP_SHADOW,
                evidence_count=evidence_count,
                avg_brier_score=avg_brier,
                avg_absolute_error=avg_abs,
                reason=(
                    f"avg absolute error {avg_abs:.4f} exceeds "
                    f"{self.max_avg_absolute_error:.4f}"
                ),
            )
            self.repository.save_engine_promotion_decision(decision)
            return decision

        decision = EnginePromotionDecision(
            decision_id=f"pd_{uuid4().hex[:10]}",
            engine_id=engine_id,
            current_type=current_type,
            proposed_type=ProbabilityEngineType.PRIMARY,
            eligible=True,
            decision=PromotionDecisionType.PROMOTE,
            evidence_count=evidence_count,
            avg_brier_score=avg_brier,
            avg_absolute_error=avg_abs,
            reason="engine passed promotion thresholds",
        )
        self.repository.save_engine_promotion_decision(decision)
        return decision
