import type { CurrentStepSummary, ProjectSummary } from "../../types/aars";

type CurrentStepIdentityPanelProps = {
  currentStep: CurrentStepSummary;
  project: ProjectSummary;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function CurrentStepIdentityPanel({
  currentStep,
  project,
}: CurrentStepIdentityPanelProps) {
  return (
    <section className="card step-identity-card" aria-labelledby="step-identity-title">
      <div className="card-header">
        <div className="section-label">Current Step Identity Panel</div>
        <h2 className="card-title" id="step-identity-title">
          {currentStep.stepName}
        </h2>
        <p className="card-copy">
          The current step page exists to make this bounded stage operationally legible
          without asking the user to scan multiple notes manually.
        </p>
      </div>

      <div className="step-identity-layout">
        <div className="step-identity-block">
          <div className="metric-row">
            <span className="chip chip--accent">
              <strong>Step ID:</strong> {currentStep.stepId}
            </span>
            <span className="chip chip--warning">
              <strong>Status:</strong> {labelize(currentStep.stepStatus)}
            </span>
          </div>

          <div className="section-block">
            <div>
              <div className="mini-label">Scope</div>
              <p className="card-copy">{currentStep.scope}</p>
            </div>
            <div>
              <div className="mini-label">Project context</div>
              <p className="card-copy">
                {project.projectName} / {project.primaryTrack}
              </p>
            </div>
          </div>
        </div>

        <div className="step-identity-block">
          <div className="mini-label">Required outputs for this step</div>
          <div className="bullet-list">
            {currentStep.requiredOutputs.map((item) => (
              <div className="bullet-item" key={item}>
                <div className="bullet-title">{item}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
