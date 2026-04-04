/**
 * @param {string} value
 */
export function labelize(value) {
  return value.replaceAll("_", " ");
}

/**
 * @param {string} value
 */
export function toneForValue(value) {
  const normalized = value.toLowerCase();

  if (
    normalized.includes("healthy") ||
    normalized.includes("stable") ||
    normalized.includes("complete")
  ) {
    return "ok";
  }

  if (normalized.includes("block")) {
    return "accent";
  }

  if (normalized.includes("caution") || normalized.includes("current")) {
    return "warning";
  }

  return "accent";
}

/**
 * @param {import("./types/aars.ts").CurrentStepPagePayload} payload
 */
export function validateCurrentStepPayload(payload) {
  if (!payload?.project?.projectId) {
    throw new Error("Current step payload is missing project.projectId");
  }

  if (!payload?.currentStep?.stepId) {
    throw new Error("Current step payload is missing currentStep.stepId");
  }

  if (!Array.isArray(payload?.processMap) || payload.processMap.length === 0) {
    throw new Error("Current step payload is missing processMap entries");
  }

  return payload;
}
