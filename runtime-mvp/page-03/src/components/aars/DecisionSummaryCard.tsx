import type {
  ProjectSummary,
  ReviewSummary,
  StableViewSummary,
} from "../../../page-02/src/types/aars";

type DecisionSummaryCardProps = {
  review: ReviewSummary;
  project: ProjectSummary;
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

export function DecisionSummaryCard({
  review,
  project,
  stableView,
}: DecisionSummaryCardProps) {
  const nextStep = project.nextStep ?? stableView.recommendedNextStep;

  return (
    <section className="card decision-summary-card" aria-labelledby="decision-summary-title">
      <div className="card-header">
        <div className="section-label">Decision Summary Panel</div>
        <h2 className="card-title" id="decision-summary-title">
          Current decision
        </h2>
      </div>

      <div className="decision-block">
        <div className="decision-title">
          <p className="decision-name">{labelize(review.decision)}</p>
          <span className="status-pill status-pill--warning">governance gate</span>
        </div>

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

        <div className="rationale-list">
          {review.rationale.map((item, index) => (
            <div className="rationale-item" key={item}>
              <strong>Why {String(index + 1).padStart(2, "0")}</strong>
              <span>{item}</span>
            </div>
          ))}
        </div>

        <p className="action-rationale">Bounded next step: {nextStep}</p>
      </div>
    </section>
  );
}
