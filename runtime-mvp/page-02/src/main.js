import { currentStepPayload } from "./data/mock/currentStepMock.js";
import {
  renderActionCommandBar,
  renderBlockerPanel,
  renderCompletedItemsPanel,
  renderCurrentObjectivePanel,
  renderCurrentStepIdentityPanel,
  renderHealthSnapshotCard,
  renderNextStepRecommendationCard,
  renderOpenItemsPanel,
  renderProcessMapBar,
} from "./components/aars/index.js";
import { labelize, validateCurrentStepPayload } from "./runtime.js";

const payload = validateCurrentStepPayload(currentStepPayload);
const root = document.querySelector("#app");

if (!root) {
  throw new Error("Unable to find #app root for Current Step page");
}

root.innerHTML = `
  <div class="page-frame">
    <section class="top-banner" aria-label="Current step page header">
      <div class="banner-meta">
        <div class="eyebrow">AARS Runtime MVP / Page 02 / Current Step Control</div>
        <div class="governance-chip-row">
          <span class="chip chip--accent"><strong>Active Project:</strong> ${payload.project.projectId}</span>
          <span class="chip chip--warning"><strong>Current Step:</strong> ${payload.currentStep.stepName}</span>
          <span class="chip chip--ok"><strong>Health:</strong> ${payload.health.state}</span>
        </div>
      </div>
      <div class="banner-title-row">
        <div class="section-block">
          <h1 class="page-title">Current Step Page</h1>
          <p class="page-subtitle">
            Bounded current-step control surface for immediate operational legibility.
            It shows what is current, what is already complete, what remains open, and
            which next move is actually admissible.
          </p>
          <div class="status-row">
            <span class="status-pill status-pill--accent">${payload.currentStep.stepId}</span>
            <span class="status-pill status-pill--warning">${labelize(payload.currentStep.stepStatus)}</span>
            <span class="status-pill status-pill--accent">${payload.project.primaryTrack}</span>
          </div>
        </div>
        <div class="hero-callout">
          <div class="mini-label">Immediate bounded move</div>
          <p>${payload.nextStepControl.immediateNextStep}</p>
        </div>
      </div>
    </section>
    <div class="step-grid">
      ${renderProcessMapBar(payload.processMap)}
      ${renderCurrentStepIdentityPanel(payload.currentStep, payload.project)}
      ${renderHealthSnapshotCard(payload.health)}
      ${renderCurrentObjectivePanel(payload.currentStep)}
      ${renderNextStepRecommendationCard(payload.nextStepControl, payload.currentStep)}
      ${renderCompletedItemsPanel(payload.completedItems)}
      ${renderOpenItemsPanel(payload.openItems)}
      ${renderBlockerPanel(payload.blockers)}
    </div>
    ${renderActionCommandBar(payload.nextStepControl)}
  </div>
`;
