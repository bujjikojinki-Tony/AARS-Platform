export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function tag(label, value, tone = "accent") {
  return `<span class="chip chip--${tone}"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</span>`;
}

export function renderBulletList(items) {
  return items
    .map(
      (item) => `
        <div class="bullet-item">
          <div class="bullet-title">${escapeHtml(item.label)}</div>
          <div class="bullet-note">${escapeHtml(item.note)}</div>
        </div>
      `,
    )
    .join("");
}
