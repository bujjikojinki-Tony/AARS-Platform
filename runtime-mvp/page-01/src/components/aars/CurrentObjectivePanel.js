import { escapeHtml } from "./shared.js";

export function renderCurrentObjectivePanel(project) {
  return `
    <section class="card objective-card" aria-labelledby="objective-title">
      <div class="card-header">
        <div class="section-label">Current Objective Panel</div>
        <h2 class="card-title" id="objective-title">Immediate objective</h2>
      </div>
      <div class="hero-callout">
        <p>${escapeHtml(project.currentObjective)}</p>
      </div>
    </section>
  `;
}
