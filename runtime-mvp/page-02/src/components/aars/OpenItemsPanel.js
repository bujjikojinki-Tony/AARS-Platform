import { renderBulletList } from "./shared.js";

export function renderOpenItemsPanel(openItems) {
  return `
    <section class="card open-card" aria-labelledby="open-items-title">
      <div class="card-header">
        <div class="section-label">Open / Remaining Items Panel</div>
        <h2 class="card-title" id="open-items-title">Still open</h2>
      </div>
      <div class="panel-block">
        <div class="bullet-list">${renderBulletList(openItems)}</div>
      </div>
    </section>
  `;
}
