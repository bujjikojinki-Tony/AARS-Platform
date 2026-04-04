import { projectOverviewPayload } from "./data/mock/projectOverviewMock.js";
import {
  renderActionCommandBar,
  renderCurrentObjectivePanel,
  renderHealthSnapshotCard,
  renderLatestStableViewCard,
  renderMainResultPanel,
  renderNextStepRecommendationCard,
  renderProjectIdentityCard,
  renderTopBanner,
} from "./components/aars/index.js";
import { validatePayload } from "./runtime.js";

const payload = validatePayload(projectOverviewPayload);
const root = document.querySelector("#app");

if (!root) {
  throw new Error("Unable to find #app root for Project Overview page");
}

root.innerHTML = `
  <div class="page-frame">
    ${renderTopBanner(payload)}
    <div class="grid-overview">
      ${renderProjectIdentityCard(payload.project)}
      ${renderHealthSnapshotCard(payload.review)}
      ${renderCurrentObjectivePanel(payload.project)}
      ${renderNextStepRecommendationCard(payload.project, payload.review, payload.stableView)}
      ${renderLatestStableViewCard(payload.stableView)}
      ${renderMainResultPanel(payload.review, payload.timeline)}
    </div>
    ${renderActionCommandBar(payload.project, payload.review, payload.stableView)}
  </div>
`;
