import type { CurrentStepPayload } from "../../types/aars";

export const mockCurrentStepPayload: CurrentStepPayload = {
  stepNumber: "02",
  stepName: "Current Step Page",
  phase: "Round_06_MVP_Implementation",
  status: "In Progress",
  stepObjective:
    "Use the current-step surface to make bounded hardening work legible across the accepted first-set MVP surfaces.",
  activeTask:
    "Run the Round_06 coherence hardening pass without widening page contracts or adding new surfaces.",
  expectedOutput:
    "A coherent four-surface MVP set whose ownership, mock narratives, and cross-surface semantics are aligned for bounded continuation.",
  currentStepState: "Accepted and active for bounded hardening.",
  currentMilestoneState:
    "Pages 01–03 and the Active Projects Surface are implemented and accepted with caution as the first MVP set.",
  currentStabilityState: "Stable enough to continue under bounded hardening scope.",
  currentDecisionState: "Continue with caution.",
  requiredInputs: [
    "Round_06 implementation notes",
    "Round_06 integration review findings",
    "accepted first-set MVP contracts",
    "bounded payload model",
  ],
  upstreamArtifacts: [
    "AARS_Round_06_MVP_Implementation_Latest_Stable_View.md",
    "AARS_Round_06_MVP_Implementation_Review_Note.md",
    "AARS_Round_06_MVP_Execution_Note.md",
    "AARS_Round_06_MVP_Status_Note.md",
  ],
  readinessSignal:
    "Inputs are sufficient and bounded hardening can proceed without reopening system-definition work.",
  executionRisks: [
    "Accidental expansion into orchestration or app-shell behavior",
    "Hidden ownership drift between src and sandbox/reference code",
    "Narrative drift between accepted surface mocks",
  ],
  scopeCautions: [
    "Keep Page 02 bounded to current-step execution only",
    "Refresh only the highest-value coherence issues",
  ],
  latestStableView:
    "Page 01 remains the entry surface, while Page 02, Page 03, and the Active Projects Surface are accepted continuation units in the first-set MVP group.",
  stableViewRationale:
    "The accepted four-surface set is strong enough to continue from, provided hardening stays bounded and contract-preserving.",
  allowedContinuation:
    "Proceed with bounded coherence hardening and review without adding new surfaces or widening the current page contracts.",
  recommendedNextAction:
    "Address the highest-value coherence findings across the accepted first-set MVP surfaces.",
  nextActionRationale:
    "This preserves the accepted MVP baseline while improving ownership clarity, narrative alignment, and semantic legibility.",
  executionPriority: "P1",
  admissibleActions: [
    { id: "mark-reviewed", label: "Mark Reviewed" },
    { id: "continue-step", label: "Continue Step" },
    { id: "jump-forward", label: "Jump Forward" },
    { id: "return-overview", label: "Return to Overview" },
  ],
};

export const currentStepPayload = mockCurrentStepPayload;
