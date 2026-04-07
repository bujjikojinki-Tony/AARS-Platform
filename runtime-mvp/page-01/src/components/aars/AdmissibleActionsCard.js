import { escapeHtml } from "./shared.js";

export function renderAdmissibleActionsCard(actions) {
  return `
    <section class="card actions-card" aria-labelledby="actions-title">
      <div class="card-header">
        <div class="section-label">Admissible Actions Card</div>
        <h2 class="card-title" id="actions-title">Bounded actions</h2>
        <p class="card-copy">
          These actions establish the operational surface only. They are intentionally
          stubbed and do not yet introduce navigation, persistence, or backend logic.
        </p>
      </div>
      <div class="action-button-grid">
        ${actions
          .map(
            (action) => `
              <button class="action-button" data-action-id="${escapeHtml(action.id)}" type="button">
                <span>${escapeHtml(action.label)}</span>
              </button>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}
