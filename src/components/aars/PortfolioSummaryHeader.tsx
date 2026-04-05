import type { ActiveProjectsRegister } from "../../types/aars";

type PortfolioSummaryHeaderProps = {
  register: ActiveProjectsRegister;
};

function getHighestPriorityProjectName(register: ActiveProjectsRegister): string {
  const ranking = {
    high: 0,
    medium: 1,
    low: 2,
    deferred: 3,
  } as const;

  const [project] = [...register.activeProjects].sort(
    (left, right) => ranking[left.priority] - ranking[right.priority],
  );

  return project?.projectName ?? "No active project";
}

export function PortfolioSummaryHeader({ register }: PortfolioSummaryHeaderProps) {
  const highestPriorityProjectName = getHighestPriorityProjectName(register);
  const stableAnchorCount = register.activeProjects.filter(
    (project) => Boolean(project.latestStableViewId),
  ).length;

  return (
    <section className="card portfolio-summary-card" aria-labelledby="portfolio-summary-title">
      <div className="card-header">
        <div className="section-label">Portfolio Summary Header</div>
        <h2 className="card-title" id="portfolio-summary-title">
          Active portfolio register
        </h2>
        <p className="card-copy">
          This bounded register keeps current effort explicit, shows which project is
          carrying highest priority, and preserves stable-anchor visibility before any
          new work is started.
        </p>
      </div>

      <div className="portfolio-summary-layout">
        <div className="summary-metric">
          <div className="mini-label">Active projects</div>
          <strong>{register.activeProjects.length}</strong>
          <span>Projects that are currently admissible to advance.</span>
        </div>
        <div className="summary-metric">
          <div className="mini-label">Highest priority</div>
          <strong>{highestPriorityProjectName}</strong>
          <span>Effort sequencing should remain explicit.</span>
        </div>
        <div className="summary-metric">
          <div className="mini-label">Stable anchors</div>
          <strong>{stableAnchorCount}</strong>
          <span>Active projects with a named latest stable view.</span>
        </div>
        <div className="summary-metric">
          <div className="mini-label">Touch rule</div>
          <strong>Bounded only</strong>
          <span>Do not widen scope beyond the current active register.</span>
        </div>
      </div>
    </section>
  );
}
