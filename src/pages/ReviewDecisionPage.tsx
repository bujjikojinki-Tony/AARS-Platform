import { LatestStableViewCard } from "../components/aars/LatestStableViewCard";
import { StatusBadge } from "../components/aars/StatusBadge";
import { mockReviewDecisionPayload } from "../data/mock/reviewDecisionMock";

type ReviewDecisionPageProps = {
  onReturnCurrentStep?: () => void;
};

export function ReviewDecisionPage({
  onReturnCurrentStep,
}: ReviewDecisionPageProps) {
  const payload = mockReviewDecisionPayload;

  function handleActionClick(actionId: string) {
    if (actionId === "return-current-step") {
      onReturnCurrentStep?.();
      return;
    }

    console.log(`[AARS Page 03] ${actionId}`);
  }

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Review decision page header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Page 03 / Review Decision Surface</div>
          <div className="governance-chip-row">
            <StatusBadge label="Review Target" value={payload.reviewTarget} />
            <StatusBadge label="Status" value={payload.status} />
            <StatusBadge label="Priority" tone="warning" value={payload.executionPriority} />
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">Review / Decision Page</h1>
            <p className="page-subtitle">
              Bounded governance review surface for explicit judgment. This page exists
              to show whether continuation is admissible, why that judgment was reached,
              and what the next authorized unit is.
            </p>
            <div className="status-row">
              <span className="status-pill status-pill--accent">{payload.round}</span>
              <span className="status-pill status-pill--warning">
                {payload.currentDecisionState}
              </span>
              <span className="status-pill status-pill--accent">
                {payload.currentStabilityState}
              </span>
            </div>
          </div>

          <div className="hero-callout">
            <div className="mini-label">Next authorized unit</div>
            <p>{payload.nextAuthorizedUnit}</p>
          </div>
        </div>
      </section>

      <div className="grid-overview">
        <section className="card identity-card" aria-labelledby="review-identity-title">
          <div className="card-header">
            <div className="section-label">Review Identity</div>
            <h2 className="card-title" id="review-identity-title">
              Review target identity
            </h2>
          </div>
          <div className="identity-grid">
            <div className="identity-meta">
              <div className="mini-label">Review target</div>
              <p className="card-copy">{payload.reviewTarget}</p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Review scope</div>
              <p className="card-copy">{payload.reviewScope}</p>
            </div>
          </div>
          <div className="panel-block">
            <div className="mini-label">Review result</div>
            <p className="card-copy">{payload.reviewResult}</p>
          </div>
        </section>

        <section className="card health-card" aria-labelledby="judgment-title">
          <div className="card-header">
            <div className="section-label">Review Judgment</div>
            <h2 className="card-title" id="judgment-title">
              Stability, decision, closure language
            </h2>
          </div>
          <div className="metric-row">
            <StatusBadge label="Stability" value={payload.currentStabilityState} />
            <StatusBadge
              label="Decision"
              tone="warning"
              value={payload.currentDecisionState}
            />
            <StatusBadge
              label="Closure"
              tone="warning"
              value={payload.closureLanguage}
            />
          </div>
        </section>

        <section className="card result-card" aria-labelledby="findings-title">
          <div className="card-header">
            <div className="section-label">Key Findings</div>
            <h2 className="card-title" id="findings-title">
              Passed, weak, deferred items
            </h2>
          </div>
          <div className="result-summary-layout">
            <div className="result-summary-block">
              <div className="mini-label">Passed items</div>
              <div className="bullet-list">
                {payload.passedItems.map((item) => (
                  <div className="bullet-item" key={item}>
                    <div className="bullet-title">{item}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="result-summary-block">
              <div className="mini-label">Weak items</div>
              <div className="bullet-list">
                {payload.weakItems.map((item) => (
                  <div className="bullet-item" key={item}>
                    <div className="bullet-title">{item}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="panel-block">
            <div className="mini-label">Deferred items</div>
            <div className="bullet-list">
              {payload.deferredItems.map((item) => (
                <div className="bullet-item" key={item}>
                  <div className="bullet-title">{item}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <LatestStableViewCard
          latestStableView={payload.latestStableView}
          stableViewRationale={payload.stableViewRationale}
          safeContinuation={payload.authorizedContinuation}
        />

        <section className="card next-step-card" aria-labelledby="decision-rationale-title">
          <div className="card-header">
            <div className="section-label">Decision Rationale</div>
            <h2 className="card-title" id="decision-rationale-title">
              Why this judgment was made
            </h2>
          </div>
          <div className="decision-block">
            <p>{payload.decisionRationale}</p>
            <p className="action-rationale">{payload.nextStepRationale}</p>
          </div>
          <div className="panel-block">
            <div className="mini-label">Escalation conditions</div>
            <div className="bullet-list">
              {payload.escalationConditions.map((item) => (
                <div className="bullet-item" key={item}>
                  <div className="bullet-title">{item}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="card actions-card" aria-labelledby="review-actions-title">
          <div className="card-header">
            <div className="section-label">Admissible Review Actions</div>
            <h2 className="card-title" id="review-actions-title">
              Bounded review actions only
            </h2>
            <p className="card-copy">
              These actions express governance intent only. They do not introduce
              routing, backend state, or workflow engine behavior.
            </p>
          </div>
          <div className="action-button-grid">
            {payload.admissibleActions.map((action) => (
              <button
                className="action-button"
                key={action.id}
                onClick={() => {
                  handleActionClick(action.id);
                }}
                type="button"
              >
                <span>{action.label}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="card explainability-card" aria-labelledby="explainability-title">
          <div className="card-header">
            <div className="section-label">Explainability Summary</div>
            <h2 className="card-title" id="explainability-title">
              How to read this page
            </h2>
          </div>
          <div className="section-block">
            <div className="identity-meta">
              <div className="mini-label">Why this page exists</div>
              <p className="card-copy">{payload.explainabilitySummary}</p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Read first</div>
              <p className="card-copy">
                Start with the review judgment and latest stable view, then confirm the
                next authorized unit before taking any review action.
              </p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Boundary</div>
              <p className="card-copy">
                This is a governance judgment surface, not an overview page and not an
                execution console.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
