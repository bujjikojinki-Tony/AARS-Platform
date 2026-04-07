import type { CurrentStepPayload } from "../../types/aars";

export const mockCurrentStepPayload: CurrentStepPayload = {
  stepNumber: "02",
  stepName: "Current Step Page",
  phase: "Round_06_MVP_Implementation",
  status: "In Progress",
  stepObjective: "Implement the bounded execution surface for the active Round_06 step.",
  activeTask: "Build the Current Step Page using a mock-data-driven governance layout.",
  expectedOutput:
    "A runnable page that expresses active step state, dependencies, cautions, stable view, and allowed next actions.",
  currentStepState: "Authorized and in implementation.",
  currentMilestoneState: "Page 02 is the active unit after Page 01 freeze.",
  currentStabilityState: "Stable enough to proceed under bounded scope.",
  currentDecisionState: "Continue with caution.",
  requiredInputs: [
    "Round_06 implementation notes",
    "Page 01 latest stable view",
    "Current Step Page prompt",
    "bounded payload model",
  ],
  upstreamArtifacts: [
    "AARS_Round_06_Page_01_Implementation_Review_Note.md",
    "AARS_Round_06_MVP_Implementation_Latest_Stable_View.md",
    "AARS_Round_06_MVP_Execution_Note.md",
    "AARS_Round_06_MVP_Status_Note.md",
  ],
  readinessSignal: "Inputs are sufficient and Page 02 is authorized to proceed.",
  executionRisks: [
    "Accidental expansion into multi-step orchestration",
    "Reopening Page 01 contract",
    "Overbuilding dependency visual logic",
  ],
  scopeCautions: [
    "Keep Page 02 bounded to current-step execution only",
    "Reuse shared components without broad UI abstraction",
  ],
  latestStableView:
    "Page 01 is accepted as the current continuation anchor and Page 02 is the next bounded execution surface.",
  stableViewRationale:
    "Implementation governance and forward lane are already explicit in the repo.",
  allowedContinuation:
    "Proceed to Page 02 without widening Page 01 or returning to conceptual redesign.",
  recommendedNextAction:
    "Implement the Current Step Page with bounded state, dependency, caution, and action blocks.",
  nextActionRationale:
    "This page establishes the second operational surface needed for step-aware execution.",
  executionPriority: "P1",
  admissibleActions: [
    { id: "mark-reviewed", label: "Mark Reviewed" },
    { id: "continue-step", label: "Continue Step" },
    { id: "jump-forward", label: "Jump Forward" },
    { id: "return-overview", label: "Return to Overview" },
  ],
};

export const currentStepPayload = mockCurrentStepPayload;
