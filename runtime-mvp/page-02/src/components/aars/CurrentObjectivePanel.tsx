import type { CurrentStepSummary } from "../../types/aars";

type CurrentObjectivePanelProps = {
  currentStep: CurrentStepSummary;
};

export function CurrentObjectivePanel({ currentStep }: CurrentObjectivePanelProps) {
  return (
    <section className="card objective-card" aria-labelledby="step-objective-title">
      <div className="card-header">
        <div className="section-label">Current Objective Panel</div>
        <h2 className="card-title" id="step-objective-title">
          What this step is trying to achieve
        </h2>
      </div>
      <div className="hero-callout">
        <p>{currentStep.currentObjective}</p>
      </div>
      <div className="panel-block">
        <div className="mini-label">Admissibility rule</div>
        <p className="card-copy">{currentStep.admissibilityRule}</p>
      </div>
    </section>
  );
}
