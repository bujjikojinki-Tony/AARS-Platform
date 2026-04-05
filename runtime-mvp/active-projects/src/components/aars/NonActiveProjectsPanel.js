import { labelize } from "../../runtime.js";
import { escapeHtml } from "./shared.js";

export function renderNonActiveProjectsPanel(projects) {
  return `
    <section class="card non-active-card" aria-labelledby="non-active-title">
      <div class="card-header">
        <div class="section-label">Non-Active Register</div>
        <h2 class="card-title" id="non-active-title">Projects that should not currently be touched</h2>
        <p class="card-copy">
          Frozen, paused, and historical projects stay visible here so active effort does
          not get mixed with reference baselines.
        </p>
      </div>
      <div class="non-active-layout">
        ${projects
          .map(
            (project) => `
              <div class="non-active-block">
                <div class="metric-row">
                  <span class="chip chip--accent"><strong>ID:</strong> ${escapeHtml(project.projectId)}</span>
                  <span class="chip chip--warning"><strong>Status:</strong> ${escapeHtml(labelize(project.status))}</span>
                </div>
                <div class="bullet-list">
                  <div class="bullet-item">
                    <div class="bullet-title">${escapeHtml(project.projectName)}</div>
                    <div class="bullet-note">${escapeHtml(project.notes)}</div>
                  </div>
                  <div class="bullet-item">
                    <div class="bullet-title">Stable anchor</div>
                    <div class="bullet-note">${escapeHtml(project.latestStableView)}</div>
                  </div>
                  <div class="bullet-item">
                    <div class="bullet-title">Re-entry / handling rule</div>
                    <div class="bullet-note">${escapeHtml(project.nextStep)}</div>
                  </div>
                </div>
              </div>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}
