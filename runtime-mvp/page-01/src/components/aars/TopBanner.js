import { toneForState } from "../../runtime.js";
import { escapeHtml, governanceSignalRows, stepPills, tag } from "./shared.js";

export function renderTopBanner(payload) {
  const reviewTone = toneForState(payload.review.currentState);
  const stableTone = toneForState(payload.stableView.maturity);
  const nextStep = payload.project.nextStep ?? payload.stableView.recommendedNextStep;

  return `
    <section class="top-banner" aria-label="Project control surface header">
      <div class="banner-meta">
        <div class="eyebrow">AARS Runtime MVP / Page 01 / Governance Overview</div>
        <div class="governance-chip-row">
          ${tag("Active Project", payload.project.projectId)}
          ${tag("Health", payload.review.currentState, reviewTone)}
          ${tag("Stable View", payload.stableView.maturity, stableTone)}
        </div>
      </div>
      <div class="banner-title-row">
        <div class="section-block">
          <h1 class="page-title">${escapeHtml(payload.project.projectName)}</h1>
          <p class="page-subtitle">
            Governance-aware project control surface for bounded continuation.
            This page answers where the project stands, what is safe to continue
            from, and which actions remain admissible right now.
          </p>
          <div class="status-row">
            <span class="status-pill status-pill--accent">${escapeHtml(payload.project.projectType)}</span>
            <span class="status-pill status-pill--warning">${escapeHtml(payload.project.status)}</span>
            <span class="status-pill status-pill--accent">${escapeHtml(payload.project.primaryTrack)}</span>
          </div>
        </div>
        <div class="hero-callout">
          <div class="mini-label">Current bounded recommendation</div>
          <p>${escapeHtml(nextStep)}</p>
        </div>
      </div>
      <div class="signal-list">
        ${governanceSignalRows(payload.governanceSignals)}
      </div>
      <div class="status-row">${stepPills(payload.progression)}</div>
    </section>
  `;
}
