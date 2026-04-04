import type { CurrentStepSummary, NextStepControl } from "../../types/aars";

type NextStepRecommendationCardProps = {
  nextStepControl: NextStepControl;
  currentStep: CurrentStepSummary;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function NextStepRecommendationCard({
  nextStepControl,
  currentStep,
}: NextStepRecommendationCardProps) {
  return (
    <section className="card next-step-card" aria-labelledby="step-next-title">
      <div className="card-header">
        <div className="section-label">Next Step Recommendation Card</div>
        <h2 className="card-title" id="step-next-title">
          Immediate recommended move
        </h2>
      </div>
      <div className="decision-block">
        <div className="decision-title">
          <p className="decision-name">{labelize(nextStepControl.decision)}</p>
          <span className="status-pill status-pill--warning">step-aware</span>
        </div>
        <p>{nextStepControl.immediateNextStep}</p>
        <p className="action-rationale">
          Current step support: {currentStep.immediateNextStep}
        </p>
      </div>
    </section>
  );
}
