import { mockProjectOverviewPayload } from "./data/mock/projectOverviewMock.js";
import {
  renderAdmissibleActionsCard,
  renderCurrentObjectivePanel,
  renderExplainabilitySummaryCard,
  renderHealthStateCard,
  renderLatestStableViewCard,
  renderProjectIdentityCard,
  renderRecommendedNextStepCard,
  renderStatusBadge,
} from "./components/aars/index.js";
import { validatePayload } from "./runtime.js";

const payload = validatePayload(mockProjectOverviewPayload);
const root = document.querySelector("#app");

if (!root) {
  throw new Error("Unable to find #app root for Project Overview page");
}

root.innerHTML = `
  <div class="page-frame">
    <section class="top-banner" aria-label="Project overview page header">
      <div class="banner-meta">
        <div class="eyebrow">AARS Runtime MVP / Page 01 / Project Overview</div>
        <div class="governance-chip-row">
          ${renderStatusBadge(payload.projectId, "Project ID")}
          ${renderStatusBadge(payload.healthState, "Health")}
          ${renderStatusBadge(payload.executionPriority, "Priority", "warning")}
        </div>
      </div>
      <div class="banner-title-row">
        <div class="section-block">
          <h1 class="page-title">${payload.title}</h1>
          <p class="page-subtitle">
            Governance-aware project control surface for bounded continuation. This
            page makes the active project state, stable continuation anchor, and
            admissible next actions visible in one bounded runtime entry surface.
          </p>
          <div class="status-row">
            <span class="status-pill status-pill--accent">${payload.currentRound}</span>
            <span class="status-pill status-pill--warning">${payload.currentMode}</span>
            <span class="status-pill status-pill--accent">${payload.keyResult}</span>
          </div>
        </div>
        <div class="hero-callout">
          <div class="mini-label">What to read first</div>
          <p>
            Confirm identity, then check health and the latest stable view before
            acting on the recommended next step.
          </p>
        </div>
      </div>
    </section>
    <div class="grid-overview">
      ${renderProjectIdentityCard(payload)}
      ${renderCurrentObjectivePanel(payload)}
      ${renderHealthStateCard(payload)}
      ${renderRecommendedNextStepCard(payload)}
      ${renderLatestStableViewCard(payload)}
      ${renderAdmissibleActionsCard(payload.admissibleActions)}
      ${renderExplainabilitySummaryCard(payload.explainabilitySummary)}
    </div>
  </div>
`;

root.querySelectorAll("[data-action-id]").forEach((button) => {
  button.addEventListener("click", () => {
    const actionId = button.getAttribute("data-action-id");
    console.log(`[AARS Page 01] ${actionId}`);
  });
});
