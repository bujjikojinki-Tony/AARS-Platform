import { renderBulletList } from "./shared.js";

export function renderBlockerPanel(blockers) {
  return `
    <section class="card blocker-card" aria-labelledby="blocker-panel-title">
      <div class="card-header">
        <div class="section-label">Blocker Panel</div>
        <h2 class="card-title" id="blocker-panel-title">Blocked or cautionary conditions</h2>
      </div>
      <div class="blocker-list">
        <div class="blocker-item">
          <span class="status-pill status-pill--warning blocker-state">bounded caution</span>
          <div class="bullet-list">${renderBulletList(blockers)}</div>
        </div>
      </div>
    </section>
  `;
}
