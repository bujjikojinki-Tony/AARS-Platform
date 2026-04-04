import { escapeHtml } from "./shared.js";

export function renderCurrentObjectivePanel(currentStep) {
  return `
    <section class="card objective-card" aria-labelledby="step-objective-title">
      <div class="card-header">
        <div class="section-label">Current Objective Panel</div>
        <h2 class="card-title" id="step-objective-title">What this step is trying to achieve</h2>
      </div>
      <div class="hero-callout">
        <p>${escapeHtml(currentStep.currentObjective)}</p>
      </div>
      <div class="panel-block">
        <div class="mini-label">Admissibility rule</div>
        <p class="card-copy">${escapeHtml(currentStep.admissibilityRule)}</p>
      </div>
    </section>
  `;
}
