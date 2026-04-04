import type { WorkItem } from "../../types/aars";

type BlockerPanelProps = {
  blockers: WorkItem[];
};

export function BlockerPanel({ blockers }: BlockerPanelProps) {
  return (
    <section className="card blocker-card" aria-labelledby="blocker-panel-title">
      <div className="card-header">
        <div className="section-label">Blocker Panel</div>
        <h2 className="card-title" id="blocker-panel-title">
          Blocked or cautionary conditions
        </h2>
      </div>
      <div className="blocker-list">
        <div className="blocker-item">
          <span className="status-pill status-pill--warning blocker-state">bounded caution</span>
          <div className="bullet-list">
            {blockers.map((item) => (
              <div className="bullet-item" key={item.id}>
                <div className="bullet-title">{item.label}</div>
                <div className="bullet-note">{item.note}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
