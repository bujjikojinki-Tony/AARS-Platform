import type { ProjectSummary, ReviewSummary, StableViewSummary } from "../../types/aars";

type ActionCommandBarProps = {
  project: ProjectSummary;
  review: ReviewSummary;
  stableView: StableViewSummary;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function ActionCommandBar({
  project,
  review,
  stableView,
}: ActionCommandBarProps) {
  const nextStep = project.nextStep ?? stableView.recommendedNextStep;

  return (
    <section className="action-bar" aria-labelledby="action-command-title">
      <div className="action-bar-header">
        <div>
          <div className="action-context">Action Command Bar</div>
          <h2 className="card-title" id="action-command-title">
            Admissible actions only
          </h2>
        </div>
        <span className="status-pill status-pill--warning">{labelize(review.decision)}</span>
      </div>

      <div className="action-grid">
        <div className="action-list">
          <div className="action-item">
            <div>
              <strong>Promote current stable anchor</strong>
              <span>Use {stableView.stableViewId} as the live continuation spine.</span>
            </div>
            <span className="action-pill action-pill--ok">admissible</span>
          </div>

          <div className="action-item">
            <div>
              <strong>Write project validation conclusion</strong>
              <span>{nextStep}</span>
            </div>
            <span className="action-pill action-pill--warning">next</span>
          </div>

          <div className="action-item">
            <div>
              <strong>Defer new branches</strong>
              <span>Do not widen into full platform scope before synthesis is complete.</span>
            </div>
            <span className="action-pill action-pill--accent">guardrail</span>
          </div>
        </div>

        <div className="admissibility-panel">
          <div className="mini-label">Decision rationale</div>
          {review.rationale.map((item) => (
            <p className="action-rationale" key={item}>
              {item}
            </p>
          ))}
          <div className="mini-label">Why these are bounded</div>
          <p className="action-rationale">
            The page only surfaces actions supported by review logic and the latest stable
            view. Closure, freeze, and expansion remain intentionally unavailable.
          </p>
        </div>
      </div>
    </section>
  );
}
