import { escapeHtml } from "./shared.js";

export function renderNextStepRecommendationCard(project, review, stableView) {
  const decisionLabel = review.decision.replaceAll("_", " ");
  const nextStep = project.nextStep ?? stableView.recommendedNextStep;

  return `
    <section class="card next-step-card" aria-labelledby="next-step-title">
      <div class="card-header">
        <div class="section-label">Next Step Recommendation Card</div>
        <h2 class="card-title" id="next-step-title">Recommended next move</h2>
      </div>
      <div class="decision-block">
        <div class="decision-title">
          <p class="decision-name">${escapeHtml(decisionLabel)}</p>
          <span class="status-pill status-pill--warning">Decision-aware</span>
        </div>
        <p>${escapeHtml(nextStep)}</p>
        <p class="action-rationale">
          Stable-view support: ${escapeHtml(stableView.recommendedNextStep)}
        </p>
      </div>
    </section>
  `;
}
