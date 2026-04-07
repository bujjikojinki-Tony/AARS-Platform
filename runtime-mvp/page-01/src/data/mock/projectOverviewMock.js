/** @type {import("../../types/aars.ts").ProjectOverviewPayload} */
export const mockProjectOverviewPayload = {
  title: "AARS Round_06 MVP Implementation",
  projectId: "AARS-R06-MVP",
  currentRound: "Round_06_MVP_Implementation",
  status: "In Progress",
  currentObjective:
    "Implement the first bounded operational UI surface for the AARS runtime MVP.",
  keyResult:
    "Project Overview Page is renderable, governance-aware, and mock-data-driven.",
  currentMode: "Implementation Mode",
  healthState: "Watch",
  blockersCount: 0,
  warningsCount: 2,
  readinessJudgment: "Ready to continue under bounded MVP scope.",
  latestStableView:
    "Round_06 implementation authority is established and Page 01 is the active execution unit.",
  stableViewRationale:
    "Scope, payload intent, and page role are sufficiently defined for bounded implementation without reopening system-definition work.",
  safeContinuation:
    "Proceed with Page 01 implementation using local mock payload and minimum shared components only.",
  recommendedNextStep:
    "Implement Project Overview Page and verify all required governance blocks render correctly.",
  nextStepRationale:
    "This creates the first stable runtime surface and exposes the minimum reusable component set for later pages.",
  executionPriority: "P1",
  admissibleActions: [
    { id: "open-current-step", label: "Open Current Step" },
    { id: "jump-to-step", label: "Jump to Step" },
    { id: "review-stable-view", label: "Review Stable View" },
    { id: "continue-execution", label: "Continue Execution" },
  ],
  explainabilitySummary:
    "This page is the bounded entry surface for project control. It is designed to show the active project state, health, stable continuation anchor, and admissible next actions without behaving like a generic dashboard.",
};
