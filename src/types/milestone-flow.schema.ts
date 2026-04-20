export type NodeOwner = "gpt" | "codex" | "human";

export type MilestoneStatus =
  | "planned"
  | "ready"
  | "running"
  | "paused_for_approval"
  | "blocked"
  | "awaiting_review"
  | "accepted"
  | "failed";

export type OverallFlowStatus =
  | "idle"
  | "active"
  | "blocked"
  | "reviewing"
  | "stable"
  | "failed";

export type RiskLevel = "low" | "medium" | "high";

export interface MilestoneNode {
  id: string;
  title: string;
  description: string;
  owner: NodeOwner;
  status: MilestoneStatus;
  order: number;

  inputs?: string[];
  outputs?: string[];
  relatedFiles?: string[];

  riskLevel?: RiskLevel;
  approvalRequired?: boolean;

  startedAt?: string;
  completedAt?: string;

  notes?: string[];
}

export interface StableViewSummary {
  stableViewId: string;
  summary: string;
  acceptedChanges: string[];
  safeNextMoves: string[];
}

export interface ReviewSummary {
  reviewId: string;
  nodeId: string;
  decision: "accept" | "accept_with_notes" | "needs_revision" | "reject";
  summary: string;
}

export interface MilestoneFlow {
  flowId: string;
  goalId: string;
  taskId: string;
  title: string;
  currentNodeId: string | null;
  overallStatus: OverallFlowStatus;
  nodes: MilestoneNode[];
  latestReview?: ReviewSummary;
  latestStableView?: StableViewSummary;
}

export type FlowCreatedEvent = {
  type: "flow_created";
  payload: MilestoneFlow;
};

export type NodeReadyEvent = {
  type: "node_ready";
  payload: {
    nodeId: string;
  };
};

export type NodeStartedEvent = {
  type: "node_started";
  payload: {
    nodeId: string;
    startedAt?: string;
  };
};

export type NodeProgressEvent = {
  type: "node_progress";
  payload: {
    nodeId: string;
    note: string;
  };
};

export type NodePausedForApprovalEvent = {
  type: "node_paused_for_approval";
  payload: {
    nodeId: string;
    note?: string;
  };
};

export type NodeBlockedEvent = {
  type: "node_blocked";
  payload: {
    nodeId: string;
    note?: string;
  };
};

export type NodeCompletedEvent = {
  type: "node_completed";
  payload: {
    nodeId: string;
    completedAt?: string;
    outputs?: string[];
    relatedFiles?: string[];
  };
};

export type ReviewUpdatedEvent = {
  type: "review_updated";
  payload: ReviewSummary;
};

export type StableViewUpdatedEvent = {
  type: "stable_view_updated";
  payload: StableViewSummary;
};

export type MilestoneEvent =
  | FlowCreatedEvent
  | NodeReadyEvent
  | NodeStartedEvent
  | NodeProgressEvent
  | NodePausedForApprovalEvent
  | NodeBlockedEvent
  | NodeCompletedEvent
  | ReviewUpdatedEvent
  | StableViewUpdatedEvent;
