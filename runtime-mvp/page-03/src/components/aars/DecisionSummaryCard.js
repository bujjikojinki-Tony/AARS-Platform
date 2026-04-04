import { labelize } from "../../runtime.js";
import { escapeHtml } from "../../../page-01/src/components/aars/shared.js";

const decisionOptions = [
  "review_required",
  "continue_with_caution",
  "closure_allowed",
  "freeze_recommended",
  "recover_before_continue",
];

export function renderDecisionSummaryCard(review, project, stableView) {
  const nextStep = project.nextStep ?? stableView.recommendedNextStep;

  return `
    <section class="card decision-summary-card" aria-labelledby="decision-summary-title">
      <div class="card-header">
        <div class="section-label">Decision Summary Panel</div>
        <h2 class="card-title" id="decision-summary-title">Current decision</h2>
      </div>
      <div class="decision-block">
        <div class="decision-title">
          <p class="decision-name">${escapeHtml(labelize(review.decision))}</p>
          <span class="status-pill status-pill--warning">governance gate</span>
        </div>
        <div class="decision-options">
          ${decisionOptions
            .map((option) => {
              const activeClass = option === review.decision ? " decision-option--active" : "";
              return `<span class="decision-option${activeClass}">${escapeHtml(labelize(option))}</span>`;
            })
            .join("")}
        </div>
        <div class="rationale-list">
          ${review.rationale
            .map(
              (item, index) => `
                <div class="rationale-item">
                  <strong>Why ${String(index + 1).padStart(2, "0")}</strong>
                  <span>${escapeHtml(item)}</span>
                </div>
              `,
            )
            .join("")}
        </div>
        <p class="action-rationale">Bounded next step: ${escapeHtml(nextStep)}</p>
      </div>
    </section>
  `;
}
