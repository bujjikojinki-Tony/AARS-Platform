import type { StableViewSummary } from "../../types/aars";

type LatestStableViewCardProps = {
  stableView: StableViewSummary;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function LatestStableViewCard({ stableView }: LatestStableViewCardProps) {
  return (
    <section className="card stable-card" aria-labelledby="stable-view-title">
      <div className="card-header">
        <div className="section-label">Latest Stable View Card</div>
        <h2 className="card-title" id="stable-view-title">
          Current continuity anchor
        </h2>
        <p className="card-copy">
          The Latest Stable View is the continuity spine for safe continuation. It should
          be stronger than raw activity logs and clearer than a generic status summary.
        </p>
      </div>

      <div className="stability-grid">
        <div className="stability-column">
          <div className="metric-row">
            <span className="chip chip--accent">
              <strong>Stable View ID:</strong> {stableView.stableViewId}
            </span>
            <span className="chip chip--accent">
              <strong>Scope:</strong> {stableView.scope}
            </span>
            <span className="chip chip--ok">
              <strong>Maturity:</strong> {labelize(stableView.maturity)}
            </span>
          </div>

          <div className="section-block">
            <div>
              <div className="mini-label">Stable state summary</div>
              <p className="card-copy">{stableView.summary}</p>
            </div>
            <div>
              <div className="mini-label">Recommended next step</div>
              <p className="card-copy">{stableView.recommendedNextStep}</p>
            </div>
          </div>
        </div>

        <div className="stability-column">
          <div className="mini-label">Completed elements</div>
          <div className="list-column">
            {stableView.completedElements.map((item) => (
              <div className="tag" key={item}>
                <strong>Done</strong> {item}
              </div>
            ))}
          </div>

          <div className="mini-label">Unresolved but tolerable</div>
          <div className="list-column">
            {stableView.unresolvedButTolerable.map((item) => (
              <div className="tag" key={item}>
                <strong>Tolerate</strong> {item}
              </div>
            ))}
          </div>

          <div className="mini-label">Continuation conditions</div>
          <div className="list-column">
            {stableView.continuationConditions.map((item) => (
              <div className="tag" key={item}>
                <strong>Require</strong> {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
