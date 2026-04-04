import { escapeHtml, listItems } from "./shared.js";

export function renderMainResultPanel(review, timeline) {
  return `
    <section class="card result-card" aria-labelledby="result-panel-title">
      <div class="card-header">
        <div class="section-label">Main Result Panel</div>
        <h2 class="card-title" id="result-panel-title">Review-backed operating result</h2>
        <p class="card-copy">
          This panel captures the bounded outcome of the current project state without
          degrading into a generic notes dump.
        </p>
      </div>
      <div class="result-layout">
        <div class="result-summary-block">
          <div class="result-index">Main findings</div>
          <div class="finding-list">
            ${review.findings
              .map(
                (finding, index) => `
                  <article class="finding-item">
                    <div class="finding-head">
                      <span class="finding-index">${String(index + 1).padStart(2, "0")}</span>
                      <strong>${escapeHtml(finding)}</strong>
                    </div>
                  </article>
                `,
              )
              .join("")}
          </div>
        </div>
        <div class="result-side-panel">
          <div class="section-block">
            <div>
              <div class="result-index">Weaknesses to watch</div>
              <div class="timeline-list">
                ${review.weaknesses
                  .map(
                    (item) => `
                      <div class="timeline-item">
                        <div class="timeline-title">${escapeHtml(item)}</div>
                      </div>
                    `,
                  )
                  .join("")}
              </div>
            </div>
            <div>
              <div class="result-index">Stable-view timeline</div>
              <div class="timeline-list">${listItems(timeline)}</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  `;
}
