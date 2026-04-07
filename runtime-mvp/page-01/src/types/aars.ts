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

export type StepState = {
  label: string;
  status: "complete" | "current" | "upcoming";
  note: string;
};

export type TimelineEntry = {
  title: string;
  note: string;
};

export type GovernanceSignal = {
  label: string;
  status: string;
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
