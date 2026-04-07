import { AdmissibleActionsCard } from "../components/aars/AdmissibleActionsCard";
import { CurrentObjectivePanel } from "../components/aars/CurrentObjectivePanel";
import { ExplainabilitySummaryCard } from "../components/aars/ExplainabilitySummaryCard";
import { HealthStateCard } from "../components/aars/HealthStateCard";
import { LatestStableViewCard } from "../components/aars/LatestStableViewCard";
import { ProjectIdentityCard } from "../components/aars/ProjectIdentityCard";
import { RecommendedNextStepCard } from "../components/aars/RecommendedNextStepCard";
import { StatusBadge } from "../components/aars/StatusBadge";
import { mockProjectOverviewPayload } from "../data/mock/projectOverviewMock";

export function ProjectOverviewPage() {
  const payload = mockProjectOverviewPayload;

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Project overview page header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Page 01 / Project Overview</div>
          <div className="governance-chip-row">
            <StatusBadge label="Project ID" value={payload.projectId} />
            <StatusBadge label="Health" value={payload.healthState} />
            <StatusBadge label="Priority" value={payload.executionPriority} tone="warning" />
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">{payload.title}</h1>
            <p className="page-subtitle">
              Governance-aware project control surface for bounded continuation. This
              page makes the active project state, stable continuation anchor, and
              admissible next actions visible in one bounded runtime entry surface.
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
        <ProjectIdentityCard
          title={payload.title}
          projectId={payload.projectId}
          currentRound={payload.currentRound}
          status={payload.status}
        />
        <CurrentObjectivePanel
          currentObjective={payload.currentObjective}
          keyResult={payload.keyResult}
          currentMode={payload.currentMode}
        />
        <HealthStateCard
          healthState={payload.healthState}
          blockersCount={payload.blockersCount}
          warningsCount={payload.warningsCount}
          readinessJudgment={payload.readinessJudgment}
        />
        <RecommendedNextStepCard
          recommendedNextStep={payload.recommendedNextStep}
          nextStepRationale={payload.nextStepRationale}
          executionPriority={payload.executionPriority}
        />
        <LatestStableViewCard
          latestStableView={payload.latestStableView}
          stableViewRationale={payload.stableViewRationale}
          safeContinuation={payload.safeContinuation}
        />
        <AdmissibleActionsCard
          actions={payload.admissibleActions}
          onAction={(actionId) => {
            console.log(`[AARS Page 01] ${actionId}`);
          }}
        />
        <ExplainabilitySummaryCard explainabilitySummary={payload.explainabilitySummary} />
      </div>
    </div>
  );
}
