import type { ProjectSummary } from "../../types/aars";

type CurrentObjectivePanelProps = {
  project: ProjectSummary;
};

export function CurrentObjectivePanel({ project }: CurrentObjectivePanelProps) {
  return (
    <section className="card objective-card" aria-labelledby="objective-title">
      <div className="card-header">
        <div className="section-label">Current Objective Panel</div>
        <h2 className="card-title" id="objective-title">
          Immediate objective
        </h2>
      </div>

      <div className="hero-callout">
        <p>{project.currentObjective}</p>
      </div>
    </section>
  );
}
