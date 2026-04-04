import { escapeHtml } from "./shared.js";

export function renderProcessMapBar(processMap) {
  return `
    <section class="card process-map-card" aria-labelledby="process-map-title">
      <div class="card-header">
        <div class="section-label">Process Map Bar</div>
        <h2 class="card-title" id="process-map-title">Bounded progression state</h2>
        <p class="card-copy">
          This map is not decorative. It shows where the project is, what is complete,
          and what remains intentionally downstream.
        </p>
      </div>
      <div class="process-map-track">
        ${processMap
          .map(
            (step, index) => `
              <article class="process-map-step process-map-step--${escapeHtml(step.status)}">
                <span class="process-step-index">${String(index + 1).padStart(2, "0")}</span>
                <div class="process-step-title">${escapeHtml(step.label)}</div>
                <div class="process-step-note">${escapeHtml(step.note)}</div>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}
