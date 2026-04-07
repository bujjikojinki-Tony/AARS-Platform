import { toneForState } from "../../runtime.js";
import { escapeHtml, tag } from "./shared.js";
import { renderStatusBadge } from "./StatusBadge.js";

export function renderProjectIdentityCard(project) {
  if ("title" in project) {
    return `
      <section class="card identity-card" aria-labelledby="project-identity-title">
        <div class="card-header">
          <div class="section-label">Project Identity Card</div>
          <h2 class="card-title" id="project-identity-title">${escapeHtml(project.title)}</h2>
          <p class="card-copy">
            This compact identity block establishes where the operator is before any
            deeper execution or review work begins.
          </p>
        </div>
        <div class="identity-grid">
          <div class="identity-meta">
            <div class="mini-label">Project ID</div>
            <p class="card-copy">${escapeHtml(project.projectId)}</p>
          </div>
          <div class="identity-meta">
            <div class="mini-label">Current round</div>
            <p class="card-copy">${escapeHtml(project.currentRound)}</p>
          </div>
        </div>
        <div class="metric-row">
          ${renderStatusBadge(project.status, "Status")}
        </div>
      </section>
    `;
  }

  const statusLabel = project.status.replaceAll("_", " ");

  return `
    <section class="card identity-card" aria-labelledby="project-identity-title">
      <div class="card-header">
        <div class="section-label">Project Identity Card</div>
        <h2 class="card-title" id="project-identity-title">Active project state</h2>
        <p class="card-copy">
          This is the bounded runtime identity surface. It frames why the project exists,
          how tightly it is constrained, and what it should not drift into.
        </p>
      </div>
      <div class="identity-grid">
        <div class="identity-meta">
          <div class="metric-row">
            ${tag("Project ID", project.projectId)}
            ${tag("Status", statusLabel, toneForState(project.status))}
          </div>
          <div class="section-block">
            <div>
              <div class="mini-label">Goal and track</div>
              <p class="card-copy">${escapeHtml(project.goalType)} / ${escapeHtml(project.primaryTrack)}</p>
            </div>
            <div>
              <div class="mini-label">Current priority</div>
              <p class="card-copy">${escapeHtml(project.currentPriority)}</p>
            </div>
          </div>
        </div>
        <div class="identity-meta">
          <div class="mini-label">Linked continuity context</div>
          <div class="list-column">
            <div>
              <div class="metric-label">Latest stable view</div>
              <div class="tag"><strong>Anchor</strong> ${escapeHtml(project.latestStableViewId ?? "Not set")}</div>
            </div>
            <div>
              <div class="metric-label">Next step</div>
              <div class="tag"><strong>Next</strong> ${escapeHtml(project.nextStep ?? "No next step set")}</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  `;
}
