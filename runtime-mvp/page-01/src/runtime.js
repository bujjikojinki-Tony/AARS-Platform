/**
 * @param {string} state
 */
export function toneForState(state) {
  const normalized = state.toLowerCase();

  if (normalized.includes("stable") || normalized.includes("healthy")) {
    return "ok";
  }

  if (
    normalized.includes("caution") ||
    normalized.includes("watch") ||
    normalized.includes("review")
  ) {
    return "warning";
  }

  return "accent";
}

/**
 * @param {import("./types/aars.ts").ProjectOverviewPayload} payload
 */
export function validatePayload(payload) {
  if (!payload?.projectId) {
    throw new Error("Project overview payload is missing projectId");
  }

  if (!payload?.currentRound) {
    throw new Error("Project overview payload is missing currentRound");
  }

  if (!payload?.latestStableView) {
    throw new Error("Project overview payload is missing latestStableView");
  }

  return payload;
}
