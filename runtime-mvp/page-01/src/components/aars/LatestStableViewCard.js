import { toneForState } from "../../runtime.js";
import { escapeHtml, tag } from "./shared.js";

export function renderLatestStableViewCard(stableView) {
  if ("latestStableView" in stableView) {
    return `
      <section class="card stable-card" aria-labelledby="stable-view-title">
        <div class="card-header">
          <div class="section-label">Latest Stable View Card</div>
          <h2 class="card-title" id="stable-view-title">Active continuation anchor</h2>
          <p class="card-copy">
            This block exists to show the last safe bounded state, why it is trusted,
            and what work can continue from it without reopening broader system definition.
          </p>
        </div>
        <div class="stability-grid">
          <div class="stability-column">
            <div class="mini-label">Latest stable view summary</div>
            <p class="card-copy">${escapeHtml(stableView.latestStableView)}</p>
          </div>
          <div class="stability-column">
            <div class="mini-label">Why this is the stable view</div>
            <p class="card-copy">${escapeHtml(stableView.stableViewRationale)}</p>
          </div>
          <div class="stability-column stability-column--wide">
            <div class="mini-label">What can safely continue</div>
            <p class="card-copy">${escapeHtml(stableView.safeContinuation)}</p>
          </div>
        </div>
      </section>
    `;
  }

  return `
    <section class="card stable-card" aria-labelledby="stable-view-title">
      <div class="card-header">
        <div class="section-label">Latest Stable View Card</div>
        <h2 class="card-title" id="stable-view-title">Current continuity anchor</h2>
        <p class="card-copy">
          The Latest Stable View is the continuity spine for safe continuation. It should
          be stronger than raw activity logs and clearer than a generic status summary.
        </p>
      </div>
      <div class="stability-grid">
        <div class="stability-column">
          <div class="metric-row">
            ${tag("Stable View ID", stableView.stableViewId)}
            ${tag("Scope", stableView.scope)}
            ${tag("Maturity", stableView.maturity, toneForState(stableView.maturity))}
          </div>
          <div class="section-block">
            <div>
              <div class="mini-label">Stable state summary</div>
              <p class="card-copy">${escapeHtml(stableView.summary)}</p>
            </div>
            <div>
              <div class="mini-label">Recommended next step</div>
              <p class="card-copy">${escapeHtml(stableView.recommendedNextStep)}</p>
            </div>
          </div>
        </div>
        <div class="stability-column">
          <div class="mini-label">Completed elements</div>
          <div class="list-column">
            ${stableView.completedElements
              .map((item) => `<div class="tag"><strong>Done</strong> ${escapeHtml(item)}</div>`)
              .join("")}
          </div>
          <div class="mini-label">Unresolved but tolerable</div>
          <div class="list-column">
            ${stableView.unresolvedButTolerable
              .map((item) => `<div class="tag"><strong>Tolerate</strong> ${escapeHtml(item)}</div>`)
              .join("")}
          </div>
          <div class="mini-label">Continuation conditions</div>
          <div class="list-column">
            ${stableView.continuationConditions
              .map((item) => `<div class="tag"><strong>Require</strong> ${escapeHtml(item)}</div>`)
              .join("")}
          </div>
        </div>
      </div>
    </section>
  `;
}
