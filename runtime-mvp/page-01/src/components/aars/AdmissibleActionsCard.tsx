import type { ProjectOverviewPayload } from "../../types/aars";

type AdmissibleActionsCardProps = {
  actions: ProjectOverviewPayload["admissibleActions"];
  onAction: (actionId: string) => void;
};

export function AdmissibleActionsCard({
  actions,
  onAction,
}: AdmissibleActionsCardProps) {
  return (
    <section className="card actions-card" aria-labelledby="actions-title">
      <div className="card-header">
        <div className="section-label">Admissible Actions Card</div>
        <h2 className="card-title" id="actions-title">
          Bounded actions
        </h2>
        <p className="card-copy">
          These actions establish the operational surface only. They are intentionally
          stubbed and do not yet introduce navigation, persistence, or backend logic.
        </p>
      </div>

      <div className="action-button-grid">
        {actions.map((action) => (
          <button
            className="action-button"
            key={action.id}
            onClick={() => onAction(action.id)}
            type="button"
          >
            <span>{action.label}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
