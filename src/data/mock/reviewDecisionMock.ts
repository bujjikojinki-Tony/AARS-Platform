import type { ReviewDecisionPayload } from "../../types/aars";

export const mockReviewDecisionPayload: ReviewDecisionPayload = {
  reviewTarget: "Round_06 MVP First-Set Surface Group",
  round: "Round_06_MVP_Implementation",
  reviewScope:
    "Bounded governance review of the accepted first-set MVP surfaces after initial implementation.",
  status: "Conditionally Stable",
  reviewResult:
    "The first-set MVP surface group is accepted with caution and is suitable for bounded hardening and review.",
  currentStabilityState:
    "Stable enough to continue within the current MVP scope, but not yet strong enough for broad expansion.",
  currentDecisionState: "Continue With Caution",
  closureLanguage: "Continue With Caution",
  passedItems: [
    "Page 01 remains the entry surface",
    "Page 02 is accepted as the current-step surface",
    "Page 03 is accepted as the review / decision surface",
    "Active Projects Surface is accepted as bounded multi-project visibility",
    "Authoritative implementation surface remains src/",
  ],
  weakItems: [
    "A full TS build verification path still does not exist",
    "Legacy compatibility wrappers and older root exports still need discipline",
  ],
  deferredItems: [
    "Routing",
    "Backend integration",
    "Workflow orchestration",
    "Broad payload unification",
  ],
  latestStableView:
    "Round_06 now has an accepted four-surface MVP set composed of Page 01, Page 02, Page 03, and the Active Projects Surface.",
  stableViewRationale:
    "The surface set is now coherent enough to review as one bounded group, provided hardening stays within the accepted implementation lane.",
  authorizedContinuation:
    "Proceed with bounded hardening and review without adding new surfaces, widening page contracts, or reopening system-definition work.",
  decisionRationale:
    "The current implementation maturity is strong enough for first-set acceptance, but remaining coherence and verification debt means continuation should stay cautious and bounded.",
  escalationConditions: [
    "If new work starts adding broad new surfaces instead of hardening the accepted set",
    "If page contracts begin widening toward a global schema",
    "If root ownership and semantic coherence drift again across the accepted surfaces",
  ],
  nextAuthorizedUnit: "Round_06 MVP bounded hardening / review",
  nextStepRationale:
    "This protects the accepted first-set MVP baseline while improving coherence, ownership clarity, and review confidence.",
  executionPriority: "P1",
  admissibleActions: [
    { id: "accept-review", label: "Accept Review" },
    { id: "continue-with-caution", label: "Continue With Caution" },
    { id: "review-hardening", label: "Review Hardening" },
    { id: "return-current-step", label: "Return to Current Step" },
  ],
  explainabilitySummary:
    "This page exists to express bounded governance judgment over the accepted first-set MVP surfaces. It is not an overview surface and not an execution page. Read the review judgment and latest stable view first.",
};
