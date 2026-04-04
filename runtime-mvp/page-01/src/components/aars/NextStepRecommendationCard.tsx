import type { ProjectSummary, ReviewSummary, StableViewSummary } from "../../types/aars";

type NextStepRecommendationCardProps = {
  project: ProjectSummary;
  review: ReviewSummary;
  stableView: StableViewSummary;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function NextStepRecommendationCard({
  project,
  review,
  stableView,
}: NextStepRecommendationCardProps) {
  const nextStep = project.nextStep ?? stableView.recommendedNextStep;

  return (
    <section className="card next-step-card" aria-labelledby="next-step-title">
      <div className="card-header">
        <div className="section-label">Next Step Recommendation Card</div>
        <h2 className="card-title" id="next-step-title">
          Recommended next move
        </h2>
      </div>

      <div className="decision-block">
        <div className="decision-title">
          <p className="decision-name">{labelize(review.decision)}</p>
          <span className="status-pill status-pill--warning">Decision-aware</span>
        </div>
        <p>{nextStep}</p>
        <p className="action-rationale">Stable-view support: {stableView.recommendedNextStep}</p>
      </div>
    </section>
  );
}
