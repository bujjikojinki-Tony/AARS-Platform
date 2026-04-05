import {
  renderActiveProjectCard,
  renderNonActiveProjectsPanel,
  renderPortfolioSummaryBar,
} from "./components/aars/index.js";
import { activeProjectsSurfacePayload } from "./data/mock/activeProjectsSurfaceMock.js";
import { validateActiveProjectsPayload } from "./runtime.js";

const payload = validateActiveProjectsPayload(activeProjectsSurfacePayload);
const root = document.querySelector("#app");

if (!root) {
  throw new Error("Unable to find #app root for Active Projects Surface");
}

root.innerHTML = `
  <div class="page-frame">
    <section class="top-banner" aria-label="Active projects header">
      <div class="banner-meta">
        <div class="eyebrow">AARS Runtime MVP / Active Projects Surface</div>
        <div class="governance-chip-row">
          <span class="chip chip--accent"><strong>Highest Priority:</strong> ${payload.summary.highestPriorityProjectId}</span>
          <span class="chip chip--warning"><strong>Active:</strong> ${payload.summary.activeCount}</span>
          <span class="chip chip--ok"><strong>Frozen:</strong> ${payload.summary.frozenCount}</span>
        </div>
      </div>
      <div class="banner-title-row">
        <div class="section-block">
          <h1 class="page-title">Active Projects Surface</h1>
          <p class="page-subtitle">
            Bounded portfolio visibility surface for explicit project-state,
            stable-anchor, priority, and do-not-touch clarity.
          </p>
        </div>
        <div class="hero-callout">
          <div class="mini-label">Portfolio guardrail</div>
          <p>${payload.summary.portfolioGuardrail}</p>
        </div>
      </div>
    </section>
    <div class="portfolio-grid">
      ${renderPortfolioSummaryBar(payload.summary)}
      ${payload.activeProjects.map((project) => renderActiveProjectCard(project)).join("")}
      ${renderNonActiveProjectsPanel(payload.nonActiveProjects)}
    </div>
  </div>
`;
