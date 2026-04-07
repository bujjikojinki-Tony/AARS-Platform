import type { StableViewSummary } from "../../types/aars";

type LatestStableViewCardProps = {
  stableView?: StableViewSummary;
  latestStableView?: string;
  stableViewRationale?: string;
  safeContinuation?: string;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function LatestStableViewCard({
  stableView,
  latestStableView,
  stableViewRationale,
  safeContinuation,
}: LatestStableViewCardProps) {
  if (!stableView && latestStableView && stableViewRationale && safeContinuation) {
    return (
      <section className="card stable-card" aria-labelledby="stable-view-title">
        <div className="card-header">
          <div className="section-label">Latest Stable View Card</div>
          <h2 className="card-title" id="stable-view-title">
            Active continuation anchor
          </h2>
          <p className="card-copy">
            This block exists to show the last safe bounded state, why it is trusted,
            and what work can continue from it without reopening broader system definition.
          </p>
        </div>

        <div className="stability-grid">
          <div className="stability-column">
            <div className="mini-label">Latest stable view summary</div>
            <p className="card-copy">{latestStableView}</p>
          </div>
          <div className="stability-column">
            <div className="mini-label">Why this is the stable view</div>
            <p className="card-copy">{stableViewRationale}</p>
          </div>
          <div className="stability-column stability-column--wide">
            <div className="mini-label">What can safely continue</div>
            <p className="card-copy">{safeContinuation}</p>
          </div>
        </div>
      </section>
    );
  }

  if (!stableView) {
    return null;
  }

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
