import type { ProjectSummary } from "../../types/aars";

type ProjectIdentityCardProps = {
  project: ProjectSummary;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function ProjectIdentityCard({ project }: ProjectIdentityCardProps) {
  return (
    <section className="card identity-card" aria-labelledby="project-identity-title">
      <div className="card-header">
        <div className="section-label">Project Identity Card</div>
        <h2 className="card-title" id="project-identity-title">
          Active project state
        </h2>
        <p className="card-copy">
          This is the bounded runtime identity surface. It frames why the project exists,
          how tightly it is constrained, and what it should not drift into.
        </p>
      </div>

      <div className="identity-grid">
        <div className="identity-meta">
          <div className="metric-row">
            <span className="chip chip--accent">
              <strong>Project ID:</strong> {project.projectId}
            </span>
            <span className="chip chip--accent">
              <strong>Status:</strong> {labelize(project.status)}
            </span>
          </div>

          <div className="section-block">
            <div>
              <div className="mini-label">Goal and track</div>
              <p className="card-copy">
                {project.goalType} / {project.primaryTrack}
              </p>
            </div>
            <div>
              <div className="mini-label">Current priority</div>
              <p className="card-copy">{project.currentPriority}</p>
            </div>
          </div>
        </div>

        <div className="identity-meta">
          <div className="mini-label">Linked continuity context</div>
          <div className="list-column">
            <div>
              <div className="metric-label">Latest stable view</div>
              <div className="tag">
                <strong>Anchor</strong> {project.latestStableViewId ?? "Not set"}
              </div>
            </div>
            <div>
              <div className="metric-label">Next step</div>
              <div className="tag">
                <strong>Next</strong> {project.nextStep ?? "No next step set"}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
