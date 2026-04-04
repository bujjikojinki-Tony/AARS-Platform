import { escapeHtml } from "../../../page-01/src/components/aars/shared.js";

export function renderReviewTargetCard(reviewTarget, review) {
  return `
    <section class="card review-target-card" aria-labelledby="review-target-title">
      <div class="card-header">
        <div class="section-label">Review Target Card</div>
        <h2 class="card-title" id="review-target-title">${escapeHtml(reviewTarget.reviewTitle)}</h2>
        <p class="card-copy">
          This surface makes the current review target explicit so the user can see
          what is being judged before interpreting the decision that follows.
        </p>
      </div>
      <div class="review-target-layout">
        <div class="review-target-block">
          <div class="metric-row">
            <span class="chip chip--accent"><strong>Target:</strong> ${escapeHtml(review.targetId)}</span>
            <span class="chip chip--warning"><strong>Condition:</strong> ${escapeHtml(reviewTarget.currentReviewedCondition)}</span>
          </div>
          <div class="section-block">
            <div>
              <div class="mini-label">Review scope</div>
              <p class="card-copy">${escapeHtml(reviewTarget.reviewScope)}</p>
            </div>
            <div>
              <div class="mini-label">Review question</div>
              <p class="card-copy">${escapeHtml(reviewTarget.reviewQuestion)}</p>
            </div>
          </div>
        </div>
        <div class="review-target-block">
          <div class="mini-label">Linked review artifacts</div>
          <div class="artifact-list">
            ${reviewTarget.linkedArtifacts
              .map(
                (item) => `
                  <div class="artifact-item">
                    <strong>${escapeHtml(item)}</strong>
                    <span>Used to support the current bounded judgment.</span>
                  </div>
                `,
              )
              .join("")}
          </div>
        </div>
      </div>
    </section>
  `;
}
