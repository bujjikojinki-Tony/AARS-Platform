import type { PortfolioSummaryStats } from "../../../page-02/src/types/aars";

type PortfolioSummaryBarProps = {
  summary: PortfolioSummaryStats;
};

export function PortfolioSummaryBar({ summary }: PortfolioSummaryBarProps) {
  return (
    <section className="card portfolio-summary-card" aria-labelledby="portfolio-summary-title">
      <div className="card-header">
        <div className="section-label">Portfolio Summary Bar</div>
        <h2 className="card-title" id="portfolio-summary-title">
          Bounded portfolio visibility
        </h2>
        <p className="card-copy">
          This surface exists to show active effort, explicit priority, and which
          projects should remain untouched right now.
        </p>
      </div>
      <div className="portfolio-summary-layout">
        <div className="summary-metric">
          <div className="mini-label">Active projects</div>
          <strong>{summary.activeCount}</strong>
          <span>Meaningful projects currently being advanced.</span>
        </div>
        <div className="summary-metric">
          <div className="mini-label">Highest priority</div>
          <strong>{summary.highestPriorityProjectId}</strong>
          <span>Current effort should not be implicit.</span>
        </div>
        <div className="summary-metric">
          <div className="mini-label">Frozen references</div>
          <strong>{summary.frozenCount}</strong>
          <span>Preserved baselines that should stay distinguishable from active work.</span>
        </div>
        <div className="summary-metric">
          <div className="mini-label">Portfolio guardrail</div>
          <strong>{summary.cautionCount}</strong>
          <span>{summary.portfolioGuardrail}</span>
        </div>
      </div>
    </section>
  );
}
