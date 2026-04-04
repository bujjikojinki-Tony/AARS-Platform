/**
 * @param {string} value
 */
export function labelize(value) {
  return value.replaceAll("_", " ");
}

/**
 * @param {import("../../page-02/src/types/aars.ts").ReviewDecisionPagePayload} payload
 */
export function validateReviewDecisionPayload(payload) {
  if (!payload?.project?.projectId) {
    throw new Error("Review decision payload is missing project.projectId");
  }

  if (!payload?.review?.reviewId) {
    throw new Error("Review decision payload is missing review.reviewId");
  }

  if (!payload?.stableView?.stableViewId) {
    throw new Error("Review decision payload is missing stableView.stableViewId");
  }

  return payload;
}
