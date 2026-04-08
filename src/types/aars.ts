export type ProjectSummary = {
  projectId: string;
  projectName: string;
  projectType: string;
  status:
    | "active"
    | "reviewable"
    | "conditionally_stable"
    | "frozen"
    | "paused"
    | "recovering"
    | "archived";
  goalType: string;
  primaryTrack: string;
  currentObjective: string;
  currentPriority: "high" | "medium" | "low" | "deferred";
  latestStableViewId?: string;
  nextStep?: string;
};

export type ReviewSummary = {
  reviewId: string;
  targetId: string;
  currentState: string;
  findings: string[];
  weaknesses: string[];
  decision:
    | "review_required"
    | "continue_with_caution"
    | "closure_allowed"
    | "freeze_recommended"
    | "recover_before_continue"
    | "no_recovery_needed";
  rationale: string[];
};

export type StableViewSummary = {
  stableViewId: string;
  scope: string;
  maturity: "reviewable" | "conditionally_stable" | "stable" | "frozen_candidate";
  summary: string;
  completedElements: string[];
  unresolvedButTolerable: string[];
  continuationConditions: string[];
  recommendedNextStep: string;
};

export type ActiveProjectEntry = {
  projectId: string;
  projectName: string;
  status:
    | "active"
    | "reviewable"
    | "conditionally_stable"
    | "frozen"
    | "paused"
    | "recovering"
    | "archived";
  priority: "high" | "medium" | "low" | "deferred";
  latestStableViewId?: string;
  nextStep?: string;
};

export type ActiveProjectsRegister = {
  activeProjects: ActiveProjectEntry[];
};

export type ProjectOverviewPayload = {
  title: string;
  projectId: string;
  currentRound: string;
  status: "Stable" | "Review Required" | "Blocked" | "In Progress";
  currentObjective: string;
  keyResult: string;
  currentMode: string;
  healthState: "Healthy" | "Watch" | "At Risk";
  blockersCount: number;
  warningsCount: number;
  readinessJudgment: string;
  latestStableView: string;
  stableViewRationale: string;
  safeContinuation: string;
  recommendedNextStep: string;
  nextStepRationale: string;
  executionPriority: "P1" | "P2" | "P3";
  admissibleActions: { id: string; label: string }[];
  explainabilitySummary: string;
};

export type ActiveProjectItem = {
  id: string;
  title: string;
  projectId: string;
  currentRound: string;
  status:
    | "In Progress"
    | "Review Required"
    | "Blocked"
    | "Conditionally Stable"
    | "Closure Allowed";
  objectiveSummary: string;
  latestStableViewSummary: string;
  healthState: string;
  recommendedNextStep: string;
};

export type ActiveProjectsSurfacePayload = {
  title: string;
  round: string;
  status: "In Progress" | "Reviewable" | "Conditionally Stable";
  activeProjectsCount: number;
  highlightedProjectId: string;
  projects: ActiveProjectItem[];
  explainabilitySummary: string;
};

export type CurrentStepPayload = {
  stepNumber: string;
  stepName: string;
  phase: string;
  status: "In Progress" | "Review Required" | "Blocked" | "Completed";
  stepObjective: string;
  activeTask: string;
  expectedOutput: string;
  currentStepState: string;
  currentMilestoneState: string;
  currentStabilityState: string;
  currentDecisionState: string;
  requiredInputs: string[];
  upstreamArtifacts: string[];
  readinessSignal: string;
  executionRisks: string[];
  scopeCautions: string[];
  latestStableView: string;
  stableViewRationale: string;
  allowedContinuation: string;
  recommendedNextAction: string;
  nextActionRationale: string;
  executionPriority: "P1" | "P2" | "P3";
  admissibleActions: { id: string; label: string }[];
};

export type ReviewDecisionPayload = {
  reviewTarget: string;
  round: string;
  reviewScope: string;
  status: "Reviewable" | "Stable" | "Blocked" | "Conditionally Stable";
  reviewResult: string;
  currentStabilityState: string;
  currentDecisionState: "Review Required" | "Continue With Caution" | "Closure Allowed";
  closureLanguage: "Review Required" | "Continue With Caution" | "Closure Allowed";
  passedItems: string[];
  weakItems: string[];
  deferredItems: string[];
  latestStableView: string;
  stableViewRationale: string;
  authorizedContinuation: string;
  decisionRationale: string;
  escalationConditions: string[];
  nextAuthorizedUnit: string;
  nextStepRationale: string;
  executionPriority: "P1" | "P2" | "P3";
  admissibleActions: { id: string; label: string }[];
  explainabilitySummary: string;
};

export type {
  CurrentStepPagePayload,
  CurrentStepSummary,
  GovernanceSignal,
  NextStepControl,
  ProcessMapStep,
  ReviewDecisionPagePayload,
  ReviewTargetSummary,
  StepState,
  StepHealthSummary,
  StepProgressStatus,
  TimelineEntry,
  WorkItem,
} from "../../runtime-mvp/page-02/src/types/aars";
