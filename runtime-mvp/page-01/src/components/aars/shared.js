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

export function listItems(items) {
  return items
    .map(
      (item) => `
        <div class="list-item">
          <div class="list-title">${escapeHtml(item.title)}</div>
          <div class="list-text">${escapeHtml(item.note)}</div>
        </div>
      `,
    )
    .join("");
}

export function stepPills(steps) {
  return steps
    .map((step, index) => {
      const tone =
        step.status === "complete"
          ? "ok"
          : step.status === "current"
            ? "warning"
            : "accent";

      return `<span class="status-pill status-pill--${tone}">${String(index + 1).padStart(2, "0")} ${escapeHtml(step.label)}</span>`;
    })
    .join("");
}

export function governanceSignalRows(signals) {
  return signals
    .map(
      (signal) => `
        <div class="signal-item">
          <div class="signal-title">${escapeHtml(signal.label)}</div>
          <div class="timeline-text">${escapeHtml(signal.status)}</div>
        </div>
      `,
    )
    .join("");
}
