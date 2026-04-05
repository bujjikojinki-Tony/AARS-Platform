import type { PortfolioProjectSummary } from "../../../page-02/src/types/aars";

type ActiveProjectCardProps = {
  project: PortfolioProjectSummary;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function ActiveProjectCard({ project }: ActiveProjectCardProps) {
  const cardTone =
    project.priority === "highest"
      ? " project-card--highest"
      : project.priority === "reference"
        ? " project-card--reference"
        : "";

  return (
    <section
      className={`card project-card${cardTone}`}
      aria-labelledby={`${project.projectId}-title`}
    >
      <div className="card-header">
        <div className="section-label">Portfolio Project Card</div>
        <h2 className="card-title" id={`${project.projectId}-title`}>
          {project.projectName}
        </h2>
        <div className="metric-row">
          <span className="chip chip--accent">
            <strong>Priority:</strong> {labelize(project.priority)}
          </span>
          <span className="chip chip--warning">
            <strong>Status:</strong> {labelize(project.status)}
          </span>
          <span className="chip chip--ok">
            <strong>Touch:</strong> {labelize(project.touchPolicy)}
          </span>
        </div>
      </div>
      <div className="project-card-body">
        <div className="project-detail-grid">
          <div className="detail-block">
            <div className="mini-label">Domain</div>
            <div className="project-note">{project.domain}</div>
          </div>
          <div className="detail-block">
            <div className="mini-label">Current stage</div>
            <div className="project-note">{project.currentStage}</div>
          </div>
          <div className="detail-block">
            <div className="mini-label">Stable anchor</div>
            <div className="project-note">{project.latestStableView}</div>
          </div>
          <div className="detail-block">
            <div className="mini-label">Anchor state</div>
            <div className="project-note">{labelize(project.stableAnchorState)}</div>
          </div>
        </div>
        <div className="detail-block">
          <div className="mini-label">Next step</div>
          <div className="project-note">{project.nextStep}</div>
        </div>
        <div className="detail-block">
          <div className="mini-label">Why this state matters</div>
          <div className="project-note">{project.notes}</div>
        </div>
      </div>
    </section>
  );
}
