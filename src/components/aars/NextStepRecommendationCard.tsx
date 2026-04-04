import type {
  CurrentStepSummary,
  NextStepControl,
  ProjectSummary,
  ReviewSummary,
  StableViewSummary,
} from "../../types/aars";

type NextStepRecommendationCardProps =
  | {
      nextStepControl: NextStepControl;
      currentStep: CurrentStepSummary;
      project?: never;
      review?: never;
      stableView?: never;
    }
  | {
      project: ProjectSummary;
      review: ReviewSummary;
      stableView: StableViewSummary;
      nextStepControl?: never;
      currentStep?: never;
    };

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function NextStepRecommendationCard(props: NextStepRecommendationCardProps) {
  if ("nextStepControl" in props && props.nextStepControl) {
    const { nextStepControl, currentStep } = props;

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

  const { project, review, stableView } = props;
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
        <p className="action-rationale">
          Stable-view support: {stableView.recommendedNextStep}
        </p>
      </div>
    </section>
  );
}
