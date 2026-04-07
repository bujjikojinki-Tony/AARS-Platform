import { escapeHtml } from "./shared.js";

export function renderCurrentObjectivePanel(payload) {
  return `
    <section class="card objective-card" aria-labelledby="objective-title">
      <div class="card-header">
        <div class="section-label">Current Objective Panel</div>
        <h2 class="card-title" id="objective-title">Active work intent</h2>
      </div>
      <div class="hero-callout">
        <p>${escapeHtml(payload.currentObjective)}</p>
      </div>
      <div class="objective-grid">
        <div class="identity-meta">
          <div class="mini-label">Key result</div>
          <p class="card-copy">${escapeHtml(payload.keyResult)}</p>
        </div>
        <div class="identity-meta">
          <div class="mini-label">Current mode</div>
          <p class="card-copy">${escapeHtml(payload.currentMode)}</p>
        </div>
      </div>
    </section>
  `;
}
