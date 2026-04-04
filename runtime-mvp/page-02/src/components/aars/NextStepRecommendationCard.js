import { labelize } from "../../runtime.js";
import { escapeHtml } from "./shared.js";

export function renderNextStepRecommendationCard(nextStepControl, currentStep) {
  return `
    <section class="card next-step-card" aria-labelledby="step-next-title">
      <div class="card-header">
        <div class="section-label">Next Step Recommendation Card</div>
        <h2 class="card-title" id="step-next-title">Immediate recommended move</h2>
      </div>
      <div class="decision-block">
        <div class="decision-title">
          <p class="decision-name">${escapeHtml(labelize(nextStepControl.decision))}</p>
          <span class="status-pill status-pill--warning">step-aware</span>
        </div>
        <p>${escapeHtml(nextStepControl.immediateNextStep)}</p>
        <p class="action-rationale">Current step support: ${escapeHtml(currentStep.immediateNextStep)}</p>
      </div>
    </section>
  `;
}
