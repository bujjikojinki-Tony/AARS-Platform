import { escapeHtml } from "./shared.js";

export function renderPortfolioSummaryBar(summary) {
  return `
    <section class="card portfolio-summary-card" aria-labelledby="portfolio-summary-title">
      <div class="card-header">
        <div class="section-label">Portfolio Summary Bar</div>
        <h2 class="card-title" id="portfolio-summary-title">Bounded portfolio visibility</h2>
        <p class="card-copy">
          This surface exists to show active effort, explicit priority, and which
          projects should remain untouched right now.
        </p>
      </div>
      <div class="portfolio-summary-layout">
        <div class="summary-metric">
          <div class="mini-label">Active projects</div>
          <strong>${escapeHtml(summary.activeCount)}</strong>
          <span>Meaningful projects currently being advanced.</span>
        </div>
        <div class="summary-metric">
          <div class="mini-label">Highest priority</div>
          <strong>${escapeHtml(summary.highestPriorityProjectId)}</strong>
          <span>Current effort should not be implicit.</span>
        </div>
        <div class="summary-metric">
          <div class="mini-label">Frozen references</div>
          <strong>${escapeHtml(summary.frozenCount)}</strong>
          <span>Preserved baselines that should stay distinguishable from active work.</span>
        </div>
        <div class="summary-metric">
          <div class="mini-label">Portfolio guardrail</div>
          <strong>${escapeHtml(summary.cautionCount)}</strong>
          <span>${escapeHtml(summary.portfolioGuardrail)}</span>
        </div>
      </div>
    </section>
  `;
}
