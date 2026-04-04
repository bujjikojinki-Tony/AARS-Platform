import { renderActionCommandBar } from "../../page-01/src/components/aars/ActionCommandBar.js";
import { renderHealthSnapshotCard } from "../../page-01/src/components/aars/HealthSnapshotCard.js";
import { renderLatestStableViewCard } from "../../page-01/src/components/aars/LatestStableViewCard.js";
import { renderMainResultPanel } from "../../page-01/src/components/aars/MainResultPanel.js";
import { renderNextStepRecommendationCard } from "../../page-01/src/components/aars/NextStepRecommendationCard.js";
import { renderProjectIdentityCard } from "../../page-01/src/components/aars/ProjectIdentityCard.js";
import { renderDecisionSummaryCard } from "./components/aars/DecisionSummaryCard.js";
import { renderReviewTargetCard } from "./components/aars/ReviewTargetCard.js";
import { reviewDecisionPayload } from "./data/mock/reviewDecisionMock.js";
import { labelize, validateReviewDecisionPayload } from "./runtime.js";

const payload = validateReviewDecisionPayload(reviewDecisionPayload);
const root = document.querySelector("#app");

if (!root) {
  throw new Error("Unable to find #app root for Review / Decision page");
}

root.innerHTML = `
  <div class="page-frame">
    <section class="top-banner" aria-label="Review decision page header">
      <div class="banner-meta">
        <div class="eyebrow">AARS Runtime MVP / Page 03 / Review Decision Surface</div>
        <div class="governance-chip-row">
          <span class="chip chip--accent"><strong>Review Target:</strong> ${payload.review.targetId}</span>
          <span class="chip chip--warning"><strong>Decision:</strong> ${labelize(payload.review.decision)}</span>
          <span class="chip chip--ok"><strong>Stable View:</strong> ${labelize(payload.stableView.maturity)}</span>
        </div>
      </div>
      <div class="banner-title-row">
        <div class="section-block">
          <h1 class="page-title">Review / Decision Page</h1>
          <p class="page-subtitle">
            Governance decision surface for explicit review judgment. This page makes
            the review target, findings, weaknesses, decision, rationale, and bounded
            next step visible in one place.
          </p>
          <div class="status-row">
            ${payload.governanceSignals
              .map(
                (signal) => `
                  <span class="status-pill status-pill--accent">${signal.label}: ${signal.status}</span>
                `,
              )
              .join("")}
          </div>
        </div>
        <div class="hero-callout">
          <div class="mini-label">Recommended bounded next step</div>
          <p>${payload.project.nextStep ?? payload.stableView.recommendedNextStep}</p>
        </div>
      </div>
    </section>
    <div class="review-grid">
      ${renderReviewTargetCard(payload.reviewTarget, payload.review)}
      ${renderDecisionSummaryCard(payload.review, payload.project, payload.stableView)}
      ${renderProjectIdentityCard(payload.project)}
      ${renderHealthSnapshotCard(payload.review)}
      ${renderLatestStableViewCard(payload.stableView)}
      ${renderMainResultPanel(payload.review, payload.timeline)}
      ${renderNextStepRecommendationCard(payload.project, payload.review, payload.stableView)}
    </div>
    ${renderActionCommandBar(payload.project, payload.review, payload.stableView)}
  </div>
`;
