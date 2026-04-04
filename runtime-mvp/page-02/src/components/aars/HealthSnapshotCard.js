import { labelize, toneForValue } from "../../runtime.js";
import { escapeHtml } from "./shared.js";

export function renderHealthSnapshotCard(health) {
  const tone = toneForValue(health.state);
  const meterWidth = health.state === "caution" ? "70%" : health.state === "blocked" ? "42%" : "88%";

  return `
    <section class="card health-card" aria-labelledby="step-health-title">
      <div class="card-header">
        <div class="section-label">Health Snapshot Card</div>
        <h2 class="card-title" id="step-health-title">Current step condition</h2>
      </div>
      <div class="health-column">
        <div class="decision-title">
          <p class="decision-name">${escapeHtml(health.state)}</p>
          <span class="status-pill status-pill--${tone}">${escapeHtml(labelize(health.continuationJudgment))}</span>
        </div>
        <div class="state-meter">
          <div class="meter-bar" aria-hidden="true">
            <div class="meter-fill" style="width: ${meterWidth};"></div>
          </div>
          <p class="card-copy">${escapeHtml(health.summary)}</p>
          <p class="card-copy">${escapeHtml(health.blockerNote)}</p>
        </div>
      </div>
    </section>
  `;
}
