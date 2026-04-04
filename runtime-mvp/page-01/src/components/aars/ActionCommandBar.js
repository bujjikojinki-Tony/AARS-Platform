import { escapeHtml } from "./shared.js";

export function renderActionCommandBar(project, review, stableView) {
  const decisionLabel = review.decision.replaceAll("_", " ");
  const nextStep = project.nextStep ?? stableView.recommendedNextStep;

  return `
    <section class="action-bar" aria-labelledby="action-command-title">
      <div class="action-bar-header">
        <div>
          <div class="action-context">Action Command Bar</div>
          <h2 class="card-title" id="action-command-title">Admissible actions only</h2>
        </div>
        <span class="status-pill status-pill--warning">${escapeHtml(decisionLabel)}</span>
      </div>
      <div class="action-grid">
        <div class="action-list">
          <div class="action-item">
            <div>
              <strong>Promote current stable anchor</strong>
              <span>Use ${escapeHtml(stableView.stableViewId)} as the live continuation spine.</span>
            </div>
            <span class="action-pill action-pill--ok">admissible</span>
          </div>
          <div class="action-item">
            <div>
              <strong>Write project validation conclusion</strong>
              <span>${escapeHtml(nextStep)}</span>
            </div>
            <span class="action-pill action-pill--warning">next</span>
          </div>
          <div class="action-item">
            <div>
              <strong>Defer new branches</strong>
              <span>Do not widen into full platform scope before synthesis is complete.</span>
            </div>
            <span class="action-pill action-pill--accent">guardrail</span>
          </div>
        </div>
        <div class="admissibility-panel">
          <div class="mini-label">Decision rationale</div>
          ${review.rationale
            .map((item) => `<p class="action-rationale">${escapeHtml(item)}</p>`)
            .join("")}
          <div class="mini-label">Why these are bounded</div>
          <p class="action-rationale">
            The page only surfaces actions supported by review logic and the latest stable
            view. Closure, freeze, and expansion remain intentionally unavailable.
          </p>
        </div>
      </div>
    </section>
  `;
}
