import { ActionCommandBar } from "../components/aars/ActionCommandBar";
import { BlockerPanel } from "../components/aars/BlockerPanel";
import { HealthSnapshotCard } from "../components/aars/HealthSnapshotCard";
import { MainResultPanel } from "../components/aars/MainResultPanel";
import { NextStepRecommendationCard } from "../components/aars/NextStepRecommendationCard";
import { ProcessMapBar } from "../components/aars/ProcessMapBar";
import { StepIdentityCard } from "../components/aars/StepIdentityCard";
import { currentStepPayload } from "../data/mock/currentStepMock";

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function CurrentStepPage() {
  const payload = currentStepPayload;

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Current step page header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Page 02 / Current Step Control</div>
          <div className="governance-chip-row">
            <span className="chip chip--accent">
              <strong>Active Project:</strong> {payload.project.projectId}
            </span>
            <span className="chip chip--warning">
              <strong>Current Step:</strong> {payload.currentStep.stepName}
            </span>
            <span className="chip chip--ok">
              <strong>Health:</strong> {payload.health.state}
            </span>
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">Current Step Page</h1>
            <p className="page-subtitle">
              Bounded current-step control surface for immediate operational legibility.
              It shows what is current, what is already complete, what remains open, and
              which next move is actually admissible.
            </p>
            <div className="status-row">
              <span className="status-pill status-pill--accent">{payload.currentStep.stepId}</span>
              <span className="status-pill status-pill--warning">
                {labelize(payload.currentStep.stepStatus)}
              </span>
              <span className="status-pill status-pill--accent">
                {payload.project.primaryTrack}
              </span>
            </div>
          </div>

          <div className="hero-callout">
            <div className="mini-label">Immediate bounded move</div>
            <p>{payload.nextStepControl.immediateNextStep}</p>
          </div>
        </div>
      </section>

      <div className="step-grid">
        <ProcessMapBar processMap={payload.processMap} />
        <StepIdentityCard currentStep={payload.currentStep} project={payload.project} />
        <HealthSnapshotCard health={payload.health} />
        <NextStepRecommendationCard
          nextStepControl={payload.nextStepControl}
          currentStep={payload.currentStep}
        />
        <MainResultPanel
          completedItems={payload.completedItems}
          openItems={payload.openItems}
        />
        <BlockerPanel blockers={payload.blockers} />
      </div>

      <ActionCommandBar nextStepControl={payload.nextStepControl} />
    </div>
  );
}
