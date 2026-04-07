import { escapeHtml } from "./shared.js";
import { renderStatusBadge } from "./StatusBadge.js";

export function renderHealthStateCard(payload) {
  return `
    <section class="card health-card" aria-labelledby="health-title">
      <div class="card-header">
        <div class="section-label">Health State Card</div>
        <h2 class="card-title" id="health-title">Bounded health summary</h2>
      </div>
      <div class="health-column">
        <div class="metric-row">
          ${renderStatusBadge(payload.healthState, "Health")}
          ${renderStatusBadge(String(payload.blockersCount), "Blockers", "ok")}
          ${renderStatusBadge(String(payload.warningsCount), "Warnings", "warning")}
        </div>
        <div class="panel-block">
          <div class="mini-label">Readiness judgment</div>
          <p class="card-copy">${escapeHtml(payload.readinessJudgment)}</p>
        </div>
      </div>
    </section>
  `;
}
