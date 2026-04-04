import { labelize } from "../../runtime.js";
import { escapeHtml } from "./shared.js";

export function renderActionCommandBar(nextStepControl) {
  return `
    <section class="action-bar" aria-labelledby="step-action-title">
      <div class="action-bar-header">
        <div>
          <div class="action-context">Action Command Bar</div>
          <h2 class="card-title" id="step-action-title">Bounded actions only</h2>
        </div>
        <span class="status-pill status-pill--warning">${escapeHtml(labelize(nextStepControl.decision))}</span>
      </div>
      <div class="action-grid">
        <div class="action-list">
          <div class="action-item">
            <div>
              <strong>Write the project conclusion</strong>
              <span>${escapeHtml(nextStepControl.immediateNextStep)}</span>
            </div>
            <span class="action-pill action-pill--warning">now</span>
          </div>
          <div class="action-item">
            <div>
              <strong>Preserve the current anchor</strong>
              <span>Continue from the strongest Loop_02 artifacts instead of opening fresh exploratory work.</span>
            </div>
            <span class="action-pill action-pill--ok">admissible</span>
          </div>
          <div class="action-item">
            <div>
              <strong>Delay non-admissible moves</strong>
              <span>${escapeHtml(nextStepControl.notAdmissible[0])}</span>
            </div>
            <span class="action-pill action-pill--accent">guardrail</span>
          </div>
        </div>
        <div class="admissibility-panel">
          <div class="mini-label">Why this is the next move</div>
          ${nextStepControl.why
            .map((item) => `<p class="action-rationale">${escapeHtml(item)}</p>`)
            .join("")}
          <div class="mini-label">Not yet admissible</div>
          ${nextStepControl.notAdmissible
            .map((item) => `<p class="action-rationale">${escapeHtml(item)}</p>`)
            .join("")}
        </div>
      </div>
    </section>
  `;
}
