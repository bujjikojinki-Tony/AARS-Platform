import React from "react";
import {
  MilestoneFlow,
  MilestoneNode,
  MilestoneStatus,
} from "../types/milestone-flow.schema";

type Props = {
  flow: MilestoneFlow | null;
  onSelectNode?: (node: MilestoneNode) => void;
};

function statusLabel(status: MilestoneStatus): string {
  switch (status) {
    case "planned":
      return "Planned";
    case "ready":
      return "Ready";
    case "running":
      return "Running";
    case "paused_for_approval":
      return "Awaiting Approval";
    case "blocked":
      return "Blocked";
    case "awaiting_review":
      return "Awaiting Review";
    case "accepted":
      return "Accepted";
    case "failed":
      return "Failed";
    default:
      return status;
  }
}

function statusDotClass(status: MilestoneStatus): string {
  switch (status) {
    case "accepted":
      return "bg-green-500";
    case "running":
      return "bg-blue-500 animate-pulse";
    case "blocked":
      return "bg-red-500";
    case "failed":
      return "bg-red-700";
    case "paused_for_approval":
      return "bg-amber-500";
    case "awaiting_review":
      return "bg-violet-500";
    case "ready":
      return "bg-cyan-500";
    case "planned":
    default:
      return "bg-slate-400";
  }
}

function ownerBadge(owner: MilestoneNode["owner"]) {
  const map = {
    gpt: "GPT",
    codex: "Codex",
    human: "Human",
  } as const;

  return (
    <span className="rounded-full border px-2 py-0.5 text-xs text-slate-600">
      {map[owner]}
    </span>
  );
}

function NodeCard({
  node,
  isCurrent,
  onClick,
}: {
  node: MilestoneNode;
  isCurrent: boolean;
  onClick?: () => void;
  key?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-2xl border p-4 text-left shadow-sm transition hover:shadow-md ${
        isCurrent ? "border-blue-500 ring-2 ring-blue-100" : "border-slate-200"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className={`mt-1 h-3 w-3 rounded-full ${statusDotClass(node.status)}`} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <h3 className="truncate text-sm font-semibold text-slate-900">
              {node.order}. {node.title}
            </h3>
            <span className="text-xs text-slate-500">{statusLabel(node.status)}</span>
          </div>

          <p className="mt-1 text-sm text-slate-600">{node.description}</p>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            {ownerBadge(node.owner)}
            {node.riskLevel && (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                Risk: {node.riskLevel}
              </span>
            )}
            {node.approvalRequired && (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700">
                Approval Required
              </span>
            )}
          </div>

          {node.relatedFiles && node.relatedFiles.length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-medium text-slate-500">Related files</div>
              <ul className="mt-1 space-y-1 text-xs text-slate-600">
                {node.relatedFiles.slice(0, 3).map((file) => (
                  <li key={file} className="truncate">
                    {file}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {node.notes && node.notes.length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-medium text-slate-500">Notes</div>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-xs text-slate-600">
                {node.notes.slice(-2).map((note, idx) => (
                  <li key={`${node.id}-note-${idx}`}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </button>
  );
}

export function MilestoneExecutionTree({ flow, onSelectNode }: Props) {
  if (!flow) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 p-6 text-sm text-slate-500">
        No milestone flow loaded.
      </div>
    );
  }

  const sortedNodes = [...flow.nodes].sort((a, b) => a.order - b.order);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4">
        <div className="text-xs uppercase tracking-wide text-slate-500">
          Milestone Execution Tree
        </div>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">{flow.title}</h2>
        <div className="mt-2 text-sm text-slate-600">
          Flow: {flow.flowId} · Goal: {flow.goalId} · Task: {flow.taskId}
        </div>
        <div className="mt-1 text-sm text-slate-600">
          Overall status: <span className="font-medium">{flow.overallStatus}</span>
        </div>
      </div>

      <div className="space-y-3">
        {sortedNodes.map((node) => (
          <NodeCard
            key={node.id}
            node={node}
            isCurrent={flow.currentNodeId === node.id}
            onClick={() => onSelectNode?.(node)}
          />
        ))}
      </div>

      {flow.latestReview && (
        <div className="mt-5 rounded-xl border border-violet-200 bg-violet-50 p-3">
          <div className="text-xs uppercase tracking-wide text-violet-700">
            Latest Review
          </div>
          <div className="mt-1 text-sm font-medium text-violet-900">
            {flow.latestReview.decision}
          </div>
          <p className="mt-1 text-sm text-violet-800">{flow.latestReview.summary}</p>
        </div>
      )}

      {flow.latestStableView && (
        <div className="mt-4 rounded-xl border border-green-200 bg-green-50 p-3">
          <div className="text-xs uppercase tracking-wide text-green-700">
            Latest Stable View
          </div>
          <p className="mt-1 text-sm text-green-900">{flow.latestStableView.summary}</p>
        </div>
      )}
    </section>
  );
}

export default MilestoneExecutionTree;
