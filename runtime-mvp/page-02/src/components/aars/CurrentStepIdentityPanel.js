import { labelize } from "../../runtime.js";
import { escapeHtml, tag } from "./shared.js";

export function renderCurrentStepIdentityPanel(currentStep, project) {
  return `
    <section class="card step-identity-card" aria-labelledby="step-identity-title">
      <div class="card-header">
        <div class="section-label">Current Step Identity Panel</div>
        <h2 class="card-title" id="step-identity-title">${escapeHtml(currentStep.stepName)}</h2>
        <p class="card-copy">
          The current step page exists to make this bounded stage operationally legible
          without asking the user to scan multiple notes manually.
        </p>
      </div>
      <div class="step-identity-layout">
        <div class="step-identity-block">
          <div class="metric-row">
            ${tag("Step ID", currentStep.stepId)}
            ${tag("Status", labelize(currentStep.stepStatus), "warning")}
          </div>
          <div class="section-block">
            <div>
              <div class="mini-label">Scope</div>
              <p class="card-copy">${escapeHtml(currentStep.scope)}</p>
            </div>
            <div>
              <div class="mini-label">Project context</div>
              <p class="card-copy">${escapeHtml(project.projectName)} / ${escapeHtml(project.primaryTrack)}</p>
            </div>
          </div>
        </div>
        <div class="step-identity-block">
          <div class="mini-label">Required outputs for this step</div>
          <div class="bullet-list">
            ${currentStep.requiredOutputs
              .map(
                (item) => `
                  <div class="bullet-item">
                    <div class="bullet-title">${escapeHtml(item)}</div>
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
