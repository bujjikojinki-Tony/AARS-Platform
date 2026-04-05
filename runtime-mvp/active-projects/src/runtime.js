/**
 * @param {string} value
 */
export function labelize(value) {
  return value.replaceAll("_", " ");
}

/**
 * @param {import("../../page-02/src/types/aars.ts").ActiveProjectsSurfacePayload} payload
 */
export function validateActiveProjectsPayload(payload) {
  if (!payload?.summary?.highestPriorityProjectId) {
    throw new Error("Active projects payload is missing summary.highestPriorityProjectId");
  }

  if (!Array.isArray(payload?.activeProjects) || payload.activeProjects.length === 0) {
    throw new Error("Active projects payload is missing activeProjects entries");
  }

  return payload;
}
