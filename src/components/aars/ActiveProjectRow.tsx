import type { ActiveProjectEntry } from "../../types/aars";
import { PriorityBadge } from "./PriorityBadge";
import { ProjectStateBadge } from "./ProjectStateBadge";

type ActiveProjectRowProps = {
  project: ActiveProjectEntry;
  isHighestPriority?: boolean;
};

export function ActiveProjectRow({
  project,
  isHighestPriority = false,
}: ActiveProjectRowProps) {
  return (
    <section className="card project-card" aria-labelledby={`${project.projectId}-title`}>
      <div className="card-header">
        <div className="section-label">Active Project Row</div>
        <h2 className="card-title" id={`${project.projectId}-title`}>
          {project.projectName}
        </h2>
        <div className="metric-row">
          <PriorityBadge priority={project.priority} />
          <ProjectStateBadge status={project.status} />
          {isHighestPriority ? (
            <span className="chip chip--accent">
              <strong>Rank:</strong> highest current priority
            </span>
          ) : null}
        </div>
      </div>

      <div className="project-card-body">
        <div className="project-detail-grid">
          <div className="detail-block">
            <div className="mini-label">Project ID</div>
            <div className="project-note">{project.projectId}</div>
          </div>
          <div className="detail-block">
            <div className="mini-label">Latest stable view</div>
            <div className="project-note">
              {project.latestStableViewId ?? "No explicit stable anchor named yet."}
            </div>
          </div>
        </div>

        <div className="detail-block">
          <div className="mini-label">Recommended next step</div>
          <div className="project-note">
            {project.nextStep ?? "No next step is currently recorded."}
          </div>
        </div>
      </div>
    </section>
  );
}
