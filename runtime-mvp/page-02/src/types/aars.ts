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
  stepId: string;
  stepName: string;
  state: "current" | "completed" | "blocked" | "upcoming" | "skipped";
  objective: string;
  completedItems: string[];
  openItems: string[];
  blockers: string[];
};

export type StepProgressStatus = "complete" | "current" | "blocked" | "upcoming";

export type ProcessMapStep = {
  label: string;
  status: StepProgressStatus;
  note: string;
};

export type CurrentStepSummary = {
  stepId: string;
  stepName: string;
  stepStatus: "in_progress" | "reviewable" | "blocked";
  scope: string;
  currentObjective: string;
  requiredOutputs: string[];
  admissibilityRule: string;
  immediateNextStep: string;
};

export type WorkItem = {
  id: string;
  label: string;
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

export type StepHealthSummary = {
  healthId: string;
  state: "healthy" | "caution" | "blocked";
  summary: string;
  blockerNote: string;
  continuationJudgment: string;
};

export type NextStepControl = {
  decision:
    | "review_required"
    | "continue_with_caution"
    | "closure_allowed"
    | "freeze_recommended"
    | "recover_before_continue"
    | "no_recovery_needed";
  immediateNextStep: string;
  why: string[];
  notAdmissible: string[];
};

export type ReviewTargetSummary = {
  reviewTitle: string;
  reviewScope: string;
  reviewQuestion: string;
  linkedArtifacts: string[];
  currentReviewedCondition: string;
};

export type CurrentStepPagePayload = {
  project: ProjectSummary;
  currentStep: CurrentStepSummary;
  processMap: ProcessMapStep[];
  completedItems: WorkItem[];
  openItems: WorkItem[];
  blockers: WorkItem[];
  health: StepHealthSummary;
  nextStepControl: NextStepControl;
};

export type ReviewDecisionPagePayload = {
  project: ProjectSummary;
  reviewTarget: ReviewTargetSummary;
  review: ReviewSummary;
  stableView: StableViewSummary;
  health: StepHealthSummary;
  timeline: TimelineEntry[];
  governanceSignals: GovernanceSignal[];
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

export type PortfolioProjectSummary = {
  projectId: string;
  projectName: string;
  domain: string;
  goalType: string;
  primaryTrack: string;
  currentStage: string;
  status:
    | "active"
    | "reviewable"
    | "conditionally_stable"
    | "frozen"
    | "paused"
    | "recovering"
    | "archived";
  latestStableView: string;
  stableAnchorState: "explicit" | "inherited" | "frozen_reference" | "none";
  nextStep: string;
  priority: "highest" | "high" | "medium" | "reference";
  touchPolicy: "advance" | "review_only" | "do_not_touch";
  notes: string;
};

export type PortfolioSummaryStats = {
  activeCount: number;
  highestPriorityProjectId: string;
  frozenCount: number;
  cautionCount: number;
  portfolioGuardrail: string;
};

export type ActiveProjectsSurfacePayload = {
  summary: PortfolioSummaryStats;
  activeProjects: PortfolioProjectSummary[];
  nonActiveProjects: PortfolioProjectSummary[];
};
