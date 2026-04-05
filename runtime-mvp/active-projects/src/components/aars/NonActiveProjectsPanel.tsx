import type { PortfolioProjectSummary } from "../../../page-02/src/types/aars";

type NonActiveProjectsPanelProps = {
  projects: PortfolioProjectSummary[];
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function NonActiveProjectsPanel({ projects }: NonActiveProjectsPanelProps) {
  return (
    <section className="card non-active-card" aria-labelledby="non-active-title">
      <div className="card-header">
        <div className="section-label">Non-Active Register</div>
        <h2 className="card-title" id="non-active-title">
          Projects that should not currently be touched
        </h2>
        <p className="card-copy">
          Frozen, paused, and historical projects stay visible here so active effort does
          not get mixed with reference baselines.
        </p>
      </div>
      <div className="non-active-layout">
        {projects.map((project) => (
          <div className="non-active-block" key={project.projectId}>
            <div className="metric-row">
              <span className="chip chip--accent">
                <strong>ID:</strong> {project.projectId}
              </span>
              <span className="chip chip--warning">
                <strong>Status:</strong> {labelize(project.status)}
              </span>
            </div>
            <div className="bullet-list">
              <div className="bullet-item">
                <div className="bullet-title">{project.projectName}</div>
                <div className="bullet-note">{project.notes}</div>
              </div>
              <div className="bullet-item">
                <div className="bullet-title">Stable anchor</div>
                <div className="bullet-note">{project.latestStableView}</div>
              </div>
              <div className="bullet-item">
                <div className="bullet-title">Re-entry / handling rule</div>
                <div className="bullet-note">{project.nextStep}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
