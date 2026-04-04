import type { ProjectSummary, ReviewSummary, StableViewSummary } from "../../types/aars";

type DecisionBannerProps = {
  project: ProjectSummary;
  review: ReviewSummary;
  stableView: StableViewSummary;
};

const decisionOptions = [
  "review_required",
  "continue_with_caution",
  "closure_allowed",
  "freeze_recommended",
  "recover_before_continue",
] as const;

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function DecisionBanner({
  project,
  review,
  stableView,
}: DecisionBannerProps) {
  const nextStep = project.nextStep ?? stableView.recommendedNextStep;

  return (
    <section className="card decision-summary-card" aria-labelledby="decision-banner-title">
      <div className="card-header">
        <div className="section-label">Decision Banner</div>
        <h2 className="card-title" id="decision-banner-title">
          {labelize(review.decision)}
        </h2>
      </div>

      <div className="decision-block">
        <div className="decision-options">
          {decisionOptions.map((option) => (
            <span
              className={`decision-option${option === review.decision ? " decision-option--active" : ""}`}
              key={option}
            >
              {labelize(option)}
            </span>
          ))}
        </div>
        <p className="action-rationale">Current reviewed condition: {review.currentState}</p>
        <p className="action-rationale">Bounded next step: {nextStep}</p>
      </div>
    </section>
  );
}
