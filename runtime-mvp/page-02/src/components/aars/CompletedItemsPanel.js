import { renderBulletList } from "./shared.js";

export function renderCompletedItemsPanel(completedItems) {
  return `
    <section class="card completed-card" aria-labelledby="completed-items-title">
      <div class="card-header">
        <div class="section-label">Completed Items Panel</div>
        <h2 class="card-title" id="completed-items-title">Already completed</h2>
      </div>
      <div class="panel-block">
        <div class="bullet-list">${renderBulletList(completedItems)}</div>
      </div>
    </section>
  `;
}
