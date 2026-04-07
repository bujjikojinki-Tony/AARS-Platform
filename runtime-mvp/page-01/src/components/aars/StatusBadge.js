import { toneForState } from "../../runtime.js";
import { escapeHtml } from "./shared.js";

export function renderStatusBadge(value, label = "", tone = toneForState(value)) {
  return `<span class="chip chip--${escapeHtml(tone)}">${label ? `<strong>${escapeHtml(label)}:</strong> ` : ""}${escapeHtml(value)}</span>`;
}
