import {
  MilestoneEvent,
  MilestoneFlow,
  MilestoneNode,
  MilestoneStatus,
  OverallFlowStatus,
} from "../types/milestone-flow.schema";

function updateNode(
  nodes: MilestoneNode[],
  nodeId: string,
  updater: (node: MilestoneNode) => MilestoneNode,
): MilestoneNode[] {
  return nodes.map((node) => (node.id === nodeId ? updater(node) : node));
}

function appendNote(node: MilestoneNode, note?: string): MilestoneNode {
  if (!note) return node;

  return {
    ...node,
    notes: [...(node.notes ?? []), note],
  };
}

function deriveOverallStatus(flow: MilestoneFlow): OverallFlowStatus {
  if (flow.nodes.some((n) => n.status === "failed")) return "failed";
  if (flow.nodes.some((n) => n.status === "blocked")) return "blocked";
  if (flow.nodes.some((n) => n.status === "awaiting_review")) return "reviewing";
  if (flow.latestStableView && flow.nodes.every((n) => n.status === "accepted")) {
    return "stable";
  }
  if (flow.nodes.some((n) => n.status === "running")) return "active";
  return flow.overallStatus ?? "idle";
}

export function milestoneEventReducer(
  state: MilestoneFlow | null,
  event: MilestoneEvent,
): MilestoneFlow | null {
  if (event.type === "flow_created") {
    return event.payload;
  }

  if (!state) return state;

  switch (event.type) {
    case "node_ready": {
      const next: MilestoneFlow = {
        ...state,
        nodes: updateNode(state.nodes, event.payload.nodeId, (node) => ({
          ...node,
          status: "ready",
        })),
      };
      return {
        ...next,
        overallStatus: deriveOverallStatus(next),
      };
    }

    case "node_started": {
      const next: MilestoneFlow = {
        ...state,
        currentNodeId: event.payload.nodeId,
        nodes: updateNode(state.nodes, event.payload.nodeId, (node) => ({
          ...node,
          status: "running",
          startedAt: event.payload.startedAt ?? new Date().toISOString(),
        })),
      };
      return {
        ...next,
        overallStatus: deriveOverallStatus(next),
      };
    }

    case "node_progress": {
      const next: MilestoneFlow = {
        ...state,
        nodes: updateNode(state.nodes, event.payload.nodeId, (node) =>
          appendNote(node, event.payload.note),
        ),
      };
      return {
        ...next,
        overallStatus: deriveOverallStatus(next),
      };
    }

    case "node_paused_for_approval": {
      const next: MilestoneFlow = {
        ...state,
        nodes: updateNode(state.nodes, event.payload.nodeId, (node) =>
          appendNote(
            {
              ...node,
              status: "paused_for_approval",
            },
            event.payload.note,
          ),
        ),
      };
      return {
        ...next,
        overallStatus: deriveOverallStatus(next),
      };
    }

    case "node_blocked": {
      const next: MilestoneFlow = {
        ...state,
        nodes: updateNode(state.nodes, event.payload.nodeId, (node) =>
          appendNote(
            {
              ...node,
              status: "blocked",
            },
            event.payload.note,
          ),
        ),
      };
      return {
        ...next,
        overallStatus: deriveOverallStatus(next),
      };
    }

    case "node_completed": {
      const nextNodes = updateNode(state.nodes, event.payload.nodeId, (node) => ({
        ...node,
        status: node.owner === "codex" ? "awaiting_review" : "accepted",
        completedAt: event.payload.completedAt ?? new Date().toISOString(),
        outputs: event.payload.outputs ?? node.outputs,
        relatedFiles: event.payload.relatedFiles ?? node.relatedFiles,
      }));

      const next: MilestoneFlow = {
        ...state,
        currentNodeId: null,
        nodes: nextNodes,
      };

      return {
        ...next,
        overallStatus: deriveOverallStatus(next),
      };
    }

    case "review_updated": {
      const { nodeId, decision } = event.payload;

      let targetStatus: MilestoneStatus = "accepted";
      if (decision === "needs_revision") targetStatus = "ready";
      if (decision === "reject") targetStatus = "failed";

      const next: MilestoneFlow = {
        ...state,
        latestReview: event.payload,
        nodes: updateNode(state.nodes, nodeId, (node) =>
          appendNote(
            {
              ...node,
              status: targetStatus,
            },
            event.payload.summary,
          ),
        ),
      };

      return {
        ...next,
        overallStatus: deriveOverallStatus(next),
      };
    }

    case "stable_view_updated": {
      const next: MilestoneFlow = {
        ...state,
        latestStableView: event.payload,
      };
      return {
        ...next,
        overallStatus: deriveOverallStatus(next),
      };
    }

    default:
      return state;
  }
}

export default milestoneEventReducer;
