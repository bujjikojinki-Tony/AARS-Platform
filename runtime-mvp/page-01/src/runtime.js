/**
 * @param {string} state
 */
export function toneForState(state) {
  const normalized = state.toLowerCase();

  if (normalized.includes("stable") || normalized.includes("healthy")) {
    return "ok";
  }

  if (normalized.includes("caution")) {
    return "warning";
  }

  return "accent";
}

/**
 * @param {import("./types/aars.ts").ProjectOverviewPayload} payload
 */
export function validatePayload(payload) {
  if (!payload?.project?.projectId) {
    throw new Error("Project overview payload is missing project.projectId");
  }

  if (!payload?.stableView?.stableViewId) {
    throw new Error("Project overview payload is missing stableView.stableViewId");
  }

  if (!payload?.review?.reviewId) {
    throw new Error("Project overview payload is missing review.reviewId");
  }

  return payload;
}
