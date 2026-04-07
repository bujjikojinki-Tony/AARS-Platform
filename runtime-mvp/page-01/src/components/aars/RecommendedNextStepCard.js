import { escapeHtml } from "./shared.js";
import { renderStatusBadge } from "./StatusBadge.js";

export function renderRecommendedNextStepCard(payload) {
  const priorityTone =
    payload.executionPriority === "P1"
      ? "warning"
      : payload.executionPriority === "P2"
        ? "accent"
        : "ok";

  return `
    <section class="card next-step-card" aria-labelledby="next-step-title">
      <div class="card-header">
        <div class="section-label">Recommended Next Step Card</div>
        <h2 class="card-title" id="next-step-title">Recommended next step</h2>
      </div>
      <div class="decision-block">
        <div class="decision-title">
          ${renderStatusBadge(payload.executionPriority, "Execution Priority", priorityTone)}
        </div>
        <p>${escapeHtml(payload.recommendedNextStep)}</p>
        <p class="action-rationale">${escapeHtml(payload.nextStepRationale)}</p>
      </div>
    </section>
  `;
}
