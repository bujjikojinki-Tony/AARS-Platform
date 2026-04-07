import { escapeHtml } from "./shared.js";

export function renderExplainabilitySummaryCard(explainabilitySummary) {
  return `
    <section class="card explainability-card" aria-labelledby="explainability-title">
      <div class="card-header">
        <div class="section-label">Explainability Summary Card</div>
        <h2 class="card-title" id="explainability-title">How to read this page</h2>
      </div>
      <div class="section-block">
        <div class="identity-meta">
          <div class="mini-label">Why this page exists</div>
          <p class="card-copy">${escapeHtml(explainabilitySummary)}</p>
        </div>
        <div class="identity-meta">
          <div class="mini-label">Read first</div>
          <p class="card-copy">
            Start with the project identity and latest stable view, then confirm health
            and recommended next step before touching any action.
          </p>
        </div>
        <div class="identity-meta">
          <div class="mini-label">Why this is not a dashboard</div>
          <p class="card-copy">
            This surface is organized around bounded continuation, not analytics volume,
            productivity metrics, or navigation sprawl.
          </p>
        </div>
      </div>
    </section>
  `;
}
