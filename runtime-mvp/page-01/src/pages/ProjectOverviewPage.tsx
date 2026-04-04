import { ActionCommandBar } from "../components/aars/ActionCommandBar";
import { CurrentObjectivePanel } from "../components/aars/CurrentObjectivePanel";
import { HealthSnapshotCard } from "../components/aars/HealthSnapshotCard";
import { LatestStableViewCard } from "../components/aars/LatestStableViewCard";
import { MainResultPanel } from "../components/aars/MainResultPanel";
import { NextStepRecommendationCard } from "../components/aars/NextStepRecommendationCard";
import { ProjectIdentityCard } from "../components/aars/ProjectIdentityCard";
import { projectOverviewPayload } from "../data/mock/projectOverviewMock";

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function ProjectOverviewPage() {
  const { project, review, stableView, progression, timeline, governanceSignals } =
    projectOverviewPayload;
  const nextStep = project.nextStep ?? stableView.recommendedNextStep;

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Project control surface header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Page 01 / Governance Overview</div>
          <div className="governance-chip-row">
            <span className="chip chip--accent">
              <strong>Active Project:</strong> {project.projectId}
            </span>
            <span className="chip chip--warning">
              <strong>Health:</strong> {review.currentState}
            </span>
            <span className="chip chip--ok">
              <strong>Stable View:</strong> {labelize(stableView.maturity)}
            </span>
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">{project.projectName}</h1>
            <p className="page-subtitle">
              Governance-aware project control surface for bounded continuation. This
              page answers where the project stands, what is safe to continue from, and
              which actions remain admissible right now.
            </p>
            <div className="status-row">
              <span className="status-pill status-pill--accent">{project.projectType}</span>
              <span className="status-pill status-pill--warning">{project.status}</span>
              <span className="status-pill status-pill--accent">{project.primaryTrack}</span>
            </div>
          </div>

          <div className="hero-callout">
            <div className="mini-label">Current bounded recommendation</div>
            <p>{nextStep}</p>
          </div>
        </div>

        <div className="signal-list">
          {governanceSignals.map((signal) => (
            <div className="signal-item" key={signal.label}>
              <div className="signal-title">{signal.label}</div>
              <div className="timeline-text">{signal.status}</div>
            </div>
          ))}
        </div>

        <div className="status-row">
          {progression.map((step, index) => {
            const tone =
              step.status === "complete"
                ? "ok"
                : step.status === "current"
                  ? "warning"
                  : "accent";

            return (
              <span className={`status-pill status-pill--${tone}`} key={step.label}>
                {String(index + 1).padStart(2, "0")} {step.label}
              </span>
            );
          })}
        </div>
      </section>

      <div className="grid-overview">
        <ProjectIdentityCard project={project} />
        <HealthSnapshotCard review={review} />
        <CurrentObjectivePanel project={project} />
        <NextStepRecommendationCard
          project={project}
          review={review}
          stableView={stableView}
        />
        <LatestStableViewCard stableView={stableView} />
        <MainResultPanel review={review} timeline={timeline} />
      </div>

      <ActionCommandBar project={project} review={review} stableView={stableView} />
    </div>
  );
}
