import { activeProjectsSurfacePayload } from "../data/mock/activeProjectsSurfaceMock";
import { ActiveProjectCard } from "../components/aars/ActiveProjectCard";
import { NonActiveProjectsPanel } from "../components/aars/NonActiveProjectsPanel";
import { PortfolioSummaryBar } from "../components/aars/PortfolioSummaryBar";

export function ActiveProjectsSurface() {
  const payload = activeProjectsSurfacePayload;

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Active projects header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Active Projects Surface</div>
          <div className="governance-chip-row">
            <span className="chip chip--accent">
              <strong>Highest Priority:</strong> {payload.summary.highestPriorityProjectId}
            </span>
            <span className="chip chip--warning">
              <strong>Active:</strong> {payload.summary.activeCount}
            </span>
            <span className="chip chip--ok">
              <strong>Frozen:</strong> {payload.summary.frozenCount}
            </span>
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">Active Projects Surface</h1>
            <p className="page-subtitle">
              Bounded portfolio visibility surface for explicit project-state,
              stable-anchor, priority, and do-not-touch clarity.
            </p>
          </div>
          <div className="hero-callout">
            <div className="mini-label">Portfolio guardrail</div>
            <p>{payload.summary.portfolioGuardrail}</p>
          </div>
        </div>
      </section>

      <div className="portfolio-grid">
        <PortfolioSummaryBar summary={payload.summary} />
        {payload.activeProjects.map((project) => (
          <ActiveProjectCard key={project.projectId} project={project} />
        ))}
        <NonActiveProjectsPanel projects={payload.nonActiveProjects} />
      </div>
    </div>
  );
}
