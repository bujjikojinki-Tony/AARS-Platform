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
  project: ProjectSummary;
  review: ReviewSummary;
  stableView: StableViewSummary;
  progression: StepState[];
  timeline: TimelineEntry[];
  governanceSignals: GovernanceSignal[];
};
