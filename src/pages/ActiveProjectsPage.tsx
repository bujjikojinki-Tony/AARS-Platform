import { ActiveProjectRow } from "../components/aars/ActiveProjectRow";
import { PortfolioSummaryHeader } from "../components/aars/PortfolioSummaryHeader";
import { activeProjectsMock } from "../data/mock/activeProjectsMock";

function getHighestPriorityProjectId() {
  const ranking = {
    high: 0,
    medium: 1,
    low: 2,
    deferred: 3,
  } as const;

  const [project] = [...activeProjectsMock.activeProjects].sort(
    (left, right) => ranking[left.priority] - ranking[right.priority],
  );

  return project?.projectId;
}

export function ActiveProjectsPage() {
  const highestPriorityProjectId = getHighestPriorityProjectId();

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Active projects page header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Active Projects Register</div>
          <div className="governance-chip-row">
            <span className="chip chip--accent">
              <strong>Highest Priority:</strong> {highestPriorityProjectId ?? "None"}
            </span>
            <span className="chip chip--warning">
              <strong>Active Projects:</strong> {activeProjectsMock.activeProjects.length}
            </span>
            <span className="chip chip--ok">
              <strong>Scope:</strong> bounded register
            </span>
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">Active Projects Page</h1>
            <p className="page-subtitle">
              Bounded portfolio visibility surface for current active work. It makes
              priority, project state, stable-anchor visibility, and next-step control
              legible without widening into a full portfolio manager.
            </p>
          </div>

          <div className="hero-callout">
            <div className="mini-label">Portfolio rule</div>
            <p>Advance only the named active register and keep priority explicit.</p>
          </div>
        </div>
      </section>

      <div className="portfolio-grid">
        <PortfolioSummaryHeader register={activeProjectsMock} />
        {activeProjectsMock.activeProjects.map((project) => (
          <ActiveProjectRow
            key={project.projectId}
            project={project}
            isHighestPriority={project.projectId === highestPriorityProjectId}
          />
        ))}
      </div>
    </div>
  );
}
