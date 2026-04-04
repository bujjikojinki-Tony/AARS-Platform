import { toneForState } from "../../runtime.js";
import { escapeHtml } from "./shared.js";

export function renderHealthSnapshotCard(review) {
  const tone = toneForState(review.currentState);
  const meterWidth = review.currentState === "caution" ? "68%" : "84%";
  const decisionLabel = review.decision.replaceAll("_", " ");

  return `
    <section class="card health-card" aria-labelledby="health-title">
      <div class="card-header">
        <div class="section-label">Health Snapshot Card</div>
        <h2 class="card-title" id="health-title">Current health state</h2>
      </div>
      <div class="health-column">
        <div class="decision-title">
          <p class="decision-name">${escapeHtml(review.currentState)}</p>
          <span class="status-pill status-pill--${tone}">${escapeHtml(decisionLabel)}</span>
        </div>
        <div class="state-meter">
          <div class="meter-bar" aria-hidden="true">
            <div class="meter-fill" style="width: ${meterWidth};"></div>
          </div>
          ${review.rationale
            .map((item) => `<p class="card-copy">${escapeHtml(item)}</p>`)
            .join("")}
        </div>
      </div>
    </section>
  `;
}
