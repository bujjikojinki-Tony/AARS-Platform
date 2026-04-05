import { labelize } from "../../runtime.js";
import { escapeHtml } from "./shared.js";

export function renderActiveProjectCard(project) {
  const cardTone =
    project.priority === "highest"
      ? " project-card--highest"
      : project.priority === "reference"
        ? " project-card--reference"
        : "";

  return `
    <section class="card project-card${cardTone}" aria-labelledby="${escapeHtml(project.projectId)}-title">
      <div class="card-header">
        <div class="section-label">Portfolio Project Card</div>
        <h2 class="card-title" id="${escapeHtml(project.projectId)}-title">${escapeHtml(project.projectName)}</h2>
        <div class="metric-row">
          <span class="chip chip--accent"><strong>Priority:</strong> ${escapeHtml(labelize(project.priority))}</span>
          <span class="chip chip--warning"><strong>Status:</strong> ${escapeHtml(labelize(project.status))}</span>
          <span class="chip chip--ok"><strong>Touch:</strong> ${escapeHtml(labelize(project.touchPolicy))}</span>
        </div>
      </div>
      <div class="project-card-body">
        <div class="project-detail-grid">
          <div class="detail-block">
            <div class="mini-label">Domain</div>
            <div class="project-note">${escapeHtml(project.domain)}</div>
          </div>
          <div class="detail-block">
            <div class="mini-label">Current stage</div>
            <div class="project-note">${escapeHtml(project.currentStage)}</div>
          </div>
          <div class="detail-block">
            <div class="mini-label">Stable anchor</div>
            <div class="project-note">${escapeHtml(project.latestStableView)}</div>
          </div>
          <div class="detail-block">
            <div class="mini-label">Anchor state</div>
            <div class="project-note">${escapeHtml(labelize(project.stableAnchorState))}</div>
          </div>
        </div>
        <div class="detail-block">
          <div class="mini-label">Next step</div>
          <div class="project-note">${escapeHtml(project.nextStep)}</div>
        </div>
        <div class="detail-block">
          <div class="mini-label">Why this state matters</div>
          <div class="project-note">${escapeHtml(project.notes)}</div>
        </div>
      </div>
    </section>
  `;
}
