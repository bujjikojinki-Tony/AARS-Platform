import React, { useEffect, useMemo, useReducer, useState } from "react";

import MilestoneExecutionTree from "../components/MilestoneExecutionTree";
import MainResultPanel from "../components/MainResultPanel";
import flowJson from "../mock/milestone-flow.mock.json";
import { connectMilestoneSSE } from "../lib/milestoneSSEAdapter";
import { milestoneEventReducer } from "../state/MilestoneEventReducer";
import {
  MilestoneEvent,
  MilestoneFlow,
  MilestoneNode,
} from "../types/milestone-flow.schema";

function findNode(
  flow: MilestoneFlow | null,
  nodeId: string | null,
): MilestoneNode | null {
  if (!flow || !nodeId) return null;

  return flow.nodes.find((node) => node.id === nodeId) ?? null;
}

export default function MilestoneDemoPage() {
  const initialFlow = useMemo(() => flowJson as MilestoneFlow, []);
  const [flow, dispatch] = useReducer(milestoneEventReducer, initialFlow);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    initialFlow.currentNodeId ?? initialFlow.nodes[0]?.id ?? null,
  );
  const [sseEnabled, setSseEnabled] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<
    "idle" | "connected" | "error"
  >("idle");

  const selectedNode = findNode(flow, selectedNodeId);

  useEffect(() => {
    if (!sseEnabled) {
      setConnectionStatus("idle");
      return;
    }

    setConnectionStatus("connected");

    const connection = connectMilestoneSSE(
      "/api/milestone-stream",
      (event: MilestoneEvent) => {
        dispatch(event);
      },
      () => {
        setConnectionStatus("error");
      },
    );

    return () => {
      connection.close();
      setConnectionStatus("idle");
    };
  }, [sseEnabled]);

  useEffect(() => {
    if (!selectedNodeId && flow?.nodes?.length) {
      setSelectedNodeId(flow.nodes[0].id);
    }
  }, [flow, selectedNodeId]);

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-slate-500">
                AARS Milestone Demo
              </div>
              <h1 className="mt-1 text-2xl font-semibold text-slate-900">
                Milestone Flow + Main Result Panel + SSE Adapter v0
              </h1>
              <p className="mt-2 text-sm text-slate-600">
                This demo shows a bounded AARS milestone flow driven by local reducer
                events first, and optionally by SSE.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 px-4 py-3 text-sm">
              <div>
                <span className="font-medium text-slate-900">Flow:</span> {flow?.flowId}
              </div>
              <div>
                <span className="font-medium text-slate-900">Overall:</span>{" "}
                {flow?.overallStatus}
              </div>
              <div>
                <span className="font-medium text-slate-900">SSE:</span>{" "}
                {connectionStatus}
              </div>
            </div>
          </div>
        </header>

        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-center gap-2">
            <button
              className="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              onClick={() =>
                dispatch({
                  type: "node_progress",
                  payload: {
                    nodeId: "N2",
                    note: "Synchronized activeStep and viewedStep in App state.",
                  },
                })
              }
              type="button"
            >
              Add Progress to N2
            </button>

            <button
              className="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              onClick={() =>
                dispatch({
                  type: "node_completed",
                  payload: {
                    nodeId: "N2",
                    outputs: ["State sync patch ready"],
                    relatedFiles: [
                      "src/App.tsx",
                      "src/ui/StepStatusBar.tsx",
                      "src/pages/CurrentStepPage.tsx",
                    ],
                  },
                })
              }
              type="button"
            >
              Complete N2
            </button>

            <button
              className="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              onClick={() =>
                dispatch({
                  type: "review_updated",
                  payload: {
                    reviewId: "REV-001",
                    nodeId: "N2",
                    decision: "accept",
                    summary:
                      "Implementation accepted as bounded and aligned with current AARS flow.",
                  },
                })
              }
              type="button"
            >
              Review Accept N2
            </button>

            <button
              className="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              onClick={() =>
                dispatch({
                  type: "node_started",
                  payload: {
                    nodeId: "N3",
                    startedAt: new Date().toISOString(),
                  },
                })
              }
              type="button"
            >
              Start N3
            </button>

            <button
              className="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              onClick={() =>
                dispatch({
                  type: "node_paused_for_approval",
                  payload: {
                    nodeId: "N3",
                    note: "Validation wants approval before shell-heavy regression pass.",
                  },
                })
              }
              type="button"
            >
              Pause N3 for Approval
            </button>

            <button
              className="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              onClick={() =>
                dispatch({
                  type: "stable_view_updated",
                  payload: {
                    stableViewId: "SV-001",
                    summary:
                      "Jump state synchronization accepted as current stable state.",
                    acceptedChanges: [
                      "Active step and viewed step sync restored",
                      "No routing redesign introduced",
                    ],
                    safeNextMoves: [
                      "Validate blocked/skipped rendering",
                      "Review explainability panel consistency",
                    ],
                  },
                })
              }
              type="button"
            >
              Update Stable View
            </button>

            <button
              className={`rounded-xl border px-3 py-2 text-sm ${
                sseEnabled ? "bg-slate-900 text-white" : "hover:bg-slate-50"
              }`}
              onClick={() => setSseEnabled(!sseEnabled)}
              type="button"
            >
              {sseEnabled ? "Disable SSE" : "Enable SSE"}
            </button>
          </div>
        </section>

        <main className="grid grid-cols-1 gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
          <div>
            <MilestoneExecutionTree
              flow={flow}
              onSelectNode={(node) => setSelectedNodeId(node.id)}
            />
          </div>

          <div>
            <MainResultPanel flow={flow} selectedNode={selectedNode} />
          </div>
        </main>
      </div>
    </div>
  );
}
