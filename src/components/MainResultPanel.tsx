import React from "react";
import { MilestoneFlow, MilestoneNode } from "../types/milestone-flow.schema";

type Props = {
  flow: MilestoneFlow | null;
  selectedNode: MilestoneNode | null;
};

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <div className="mt-3 text-sm text-slate-700">{children}</div>
    </section>
  );
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
      Select a milestone node to inspect its details.
    </div>
  );
}

export default function MainResultPanel({ flow, selectedNode }: Props) {
  if (!flow || !selectedNode) {
    return <EmptyState />;
  }

  const latestReviewForNode =
    flow.latestReview?.nodeId === selectedNode.id ? flow.latestReview : null;

  return (
    <div className="space-y-4">
      <Section title="Node Summary">
        <div className="space-y-2">
          <div>
            <span className="font-medium text-slate-900">Title:</span> {selectedNode.title}
          </div>
          <div>
            <span className="font-medium text-slate-900">Status:</span> {selectedNode.status}
          </div>
          <div>
            <span className="font-medium text-slate-900">Owner:</span> {selectedNode.owner}
          </div>
          <div>
            <span className="font-medium text-slate-900">Description:</span>{" "}
            {selectedNode.description}
          </div>
          {selectedNode.riskLevel && (
            <div>
              <span className="font-medium text-slate-900">Risk:</span> {selectedNode.riskLevel}
            </div>
          )}
          {selectedNode.startedAt && (
            <div>
              <span className="font-medium text-slate-900">Started:</span> {selectedNode.startedAt}
            </div>
          )}
          {selectedNode.completedAt && (
            <div>
              <span className="font-medium text-slate-900">Completed:</span>{" "}
              {selectedNode.completedAt}
            </div>
          )}
        </div>
      </Section>

      <Section title="Related Files">
        {selectedNode.relatedFiles && selectedNode.relatedFiles.length > 0 ? (
          <ul className="list-disc space-y-1 pl-5">
            {selectedNode.relatedFiles.map((file) => (
              <li key={file}>
                <code className="rounded bg-slate-100 px-1 py-0.5 text-xs text-slate-800">
                  {file}
                </code>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-slate-500">No related files recorded.</div>
        )}
      </Section>

      <Section title="Outputs">
        {selectedNode.outputs && selectedNode.outputs.length > 0 ? (
          <ul className="list-disc space-y-1 pl-5">
            {selectedNode.outputs.map((output, idx) => (
              <li key={`${selectedNode.id}-output-${idx}`}>{output}</li>
            ))}
          </ul>
        ) : (
          <div className="text-slate-500">No outputs recorded yet.</div>
        )}
      </Section>

      <Section title="Notes / Progress">
        {selectedNode.notes && selectedNode.notes.length > 0 ? (
          <ul className="list-disc space-y-1 pl-5">
            {selectedNode.notes.map((note, idx) => (
              <li key={`${selectedNode.id}-note-${idx}`}>{note}</li>
            ))}
          </ul>
        ) : (
          <div className="text-slate-500">No notes yet.</div>
        )}
      </Section>

      <Section title="Review">
        {latestReviewForNode ? (
          <div className="space-y-2">
            <div>
              <span className="font-medium text-slate-900">Decision:</span>{" "}
              {latestReviewForNode.decision}
            </div>
            <div>
              <span className="font-medium text-slate-900">Summary:</span>{" "}
              {latestReviewForNode.summary}
            </div>
          </div>
        ) : (
          <div className="text-slate-500">No review attached to this node.</div>
        )}
      </Section>

      <Section title="Latest Stable View">
        {flow.latestStableView ? (
          <div className="space-y-3">
            <div>
              <span className="font-medium text-slate-900">Summary:</span>{" "}
              {flow.latestStableView.summary}
            </div>

            <div>
              <div className="font-medium text-slate-900">Accepted Changes</div>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {flow.latestStableView.acceptedChanges.map((item, idx) => (
                  <li key={`accepted-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>

            <div>
              <div className="font-medium text-slate-900">Safe Next Moves</div>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {flow.latestStableView.safeNextMoves.map((item, idx) => (
                  <li key={`safe-next-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <div className="text-slate-500">No stable view recorded yet.</div>
        )}
      </Section>
    </div>
  );
}
