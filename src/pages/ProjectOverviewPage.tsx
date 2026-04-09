import { LatestStableViewCard } from "../components/aars/LatestStableViewCard";
import { StatusBadge } from "../components/aars/StatusBadge";
import { mockProjectOverviewPayload } from "../data/mock/projectOverviewMock";

type ProjectOverviewPageProps = {
  onOpenCurrentStep?: () => void;
  onOpenReviewDecision?: () => void;
  onOpenActiveProjects?: () => void;
};

export function ProjectOverviewPage({
  onOpenCurrentStep,
  onOpenReviewDecision,
  onOpenActiveProjects,
}: ProjectOverviewPageProps) {
  const payload = mockProjectOverviewPayload;

  function handleActionClick(actionId: string) {
    if (actionId === "open-current-step" || actionId === "continue-hardening") {
      onOpenCurrentStep?.();
      return;
    }

    if (actionId === "review-first-set" || actionId === "review-stable-view") {
      onOpenReviewDecision?.();
      return;
    }

    if (actionId === "open-active-projects") {
      onOpenActiveProjects?.();
      return;
    }

    console.log(`[AARS Page 01] ${actionId}`);
  }

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Project overview page header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Page 01 / Project Overview</div>
          <div className="governance-chip-row">
            <StatusBadge label="Project ID" value={payload.projectId} />
            <StatusBadge label="Health" value={payload.healthState} />
            <StatusBadge
              label="Priority"
              tone="warning"
              value={payload.executionPriority}
            />
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">{payload.title}</h1>
            <p className="page-subtitle">
              Governance-aware project control surface for bounded continuation. This
              page remains the entry surface for the accepted first-set MVP and should
              orient the operator before any bounded hardening or review move.
            </p>
            <div className="status-row">
              <span className="status-pill status-pill--accent">{payload.currentRound}</span>
              <span className="status-pill status-pill--warning">{payload.currentMode}</span>
              <span className="status-pill status-pill--accent">{payload.keyResult}</span>
            </div>
          </div>

          <div className="hero-callout">
            <div className="mini-label">What to read first</div>
            <p>
              Confirm identity, then check health and the latest stable view before
              acting on the recommended next step.
            </p>
          </div>
        </div>
      </section>

      <div className="grid-overview">
        <section className="card identity-card" aria-labelledby="project-identity-title">
          <div className="card-header">
            <div className="section-label">Project Identity</div>
            <h2 className="card-title" id="project-identity-title">
              {payload.title}
            </h2>
            <p className="card-copy">
              This compact identity block establishes where the operator is before any
              deeper execution, review, or hardening work begins.
            </p>
          </div>

          <div className="identity-grid">
            <div className="identity-meta">
              <div className="mini-label">Project ID</div>
              <p className="card-copy">{payload.projectId}</p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Current round</div>
              <p className="card-copy">{payload.currentRound}</p>
            </div>
          </div>

          <div className="metric-row">
            <StatusBadge label="Status" value={payload.status} />
          </div>
        </section>

        <section className="card objective-card" aria-labelledby="objective-title">
          <div className="card-header">
            <div className="section-label">Current Objective</div>
            <h2 className="card-title" id="objective-title">
              Active work intent
            </h2>
          </div>

          <div className="hero-callout">
            <p>{payload.currentObjective}</p>
          </div>

          <div className="objective-grid">
            <div className="identity-meta">
              <div className="mini-label">Key result</div>
              <p className="card-copy">{payload.keyResult}</p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Current mode</div>
              <p className="card-copy">{payload.currentMode}</p>
            </div>
          </div>
        </section>

        <section className="card health-card" aria-labelledby="health-title">
          <div className="card-header">
            <div className="section-label">Health State</div>
            <h2 className="card-title" id="health-title">
              Bounded health summary
            </h2>
          </div>

          <div className="health-column">
            <div className="metric-row">
              <StatusBadge label="Health" value={payload.healthState} />
              <StatusBadge
                label="Blockers"
                tone="ok"
                value={String(payload.blockersCount)}
              />
              <StatusBadge
                label="Warnings"
                tone="warning"
                value={String(payload.warningsCount)}
              />
            </div>

            <div className="panel-block">
              <div className="mini-label">Readiness judgment</div>
              <p className="card-copy">{payload.readinessJudgment}</p>
            </div>
          </div>
        </section>

        <section className="card next-step-card" aria-labelledby="next-step-title">
          <div className="card-header">
            <div className="section-label">Recommended Next Step</div>
            <h2 className="card-title" id="next-step-title">
              Recommended next step
            </h2>
          </div>

          <div className="decision-block">
            <div className="decision-title">
              <StatusBadge
                label="Execution Priority"
                tone="warning"
                value={payload.executionPriority}
              />
            </div>
            <p>{payload.recommendedNextStep}</p>
            <p className="action-rationale">{payload.nextStepRationale}</p>
          </div>
        </section>

        <LatestStableViewCard
          latestStableView={payload.latestStableView}
          stableViewRationale={payload.stableViewRationale}
          safeContinuation={payload.safeContinuation}
        />

        <section className="card actions-card" aria-labelledby="actions-title">
          <div className="card-header">
            <div className="section-label">Admissible Actions</div>
            <h2 className="card-title" id="actions-title">
              Bounded actions
            </h2>
            <p className="card-copy">
              These actions stay bounded to accepted surface switching only. They do not
              introduce persistence, backend behavior, or broader navigation expansion.
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
            {onOpenActiveProjects ? (
              <button
                className="action-button"
                onClick={onOpenActiveProjects}
                type="button"
              >
                <span>Open Active Projects</span>
              </button>
            ) : null}
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
                Start with the project identity and latest stable view, then confirm
                health and recommended next step before touching any action.
              </p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Why this is not a dashboard</div>
              <p className="card-copy">
                This surface is organized around bounded continuation, not analytics
                volume, productivity metrics, or navigation sprawl.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
