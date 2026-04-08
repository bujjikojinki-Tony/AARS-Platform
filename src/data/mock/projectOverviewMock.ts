import type { ProjectOverviewPayload } from "../../types/aars";

export const mockProjectOverviewPayload: ProjectOverviewPayload = {
  title: "AARS Round_06 MVP Implementation",
  projectId: "AARS-R06-MVP",
  currentRound: "Round_06_MVP_Implementation",
  status: "In Progress",
  currentObjective:
    "Preserve and harden the accepted first-set MVP surfaces as one coherent bounded runtime group.",
  keyResult:
    "Pages 01–03 and the Active Projects Surface remain coherent, governance-aware, and reviewable as a single bounded MVP set.",
  currentMode: "Bounded Hardening Mode",
  healthState: "Watch",
  blockersCount: 0,
  warningsCount: 2,
  readinessJudgment:
    "Accepted with caution and ready for bounded hardening rather than new surface expansion.",
  latestStableView:
    "Page 01 remains the entry surface, while Page 02, Page 03, and the Active Projects Surface are accepted continuation units in the current Round_06 MVP set.",
  stableViewRationale:
    "The first four bounded governance-aware surfaces are now implemented and aligned strongly enough to review as one accepted MVP set.",
  safeContinuation:
    "Proceed with bounded coherence hardening and review while preserving the frozen Page 01, Page 02, Page 03, and Active Projects contracts.",
  recommendedNextStep:
    "Address the highest-value coherence findings and preserve the accepted first-set MVP baseline.",
  nextStepRationale:
    "This strengthens the MVP continuation anchor without widening the surface set, payload family, or runtime scope.",
  executionPriority: "P1",
  admissibleActions: [
    { id: "open-current-step", label: "Open Current Step" },
    { id: "review-first-set", label: "Review First Set" },
    { id: "review-stable-view", label: "Review Stable View" },
    { id: "continue-hardening", label: "Continue Hardening" },
  ],
  explainabilitySummary:
    "This page remains the bounded entry surface for project control. It now represents the accepted first MVP surface set and should be read as the primary control point for bounded hardening and review rather than new page expansion.",
};
