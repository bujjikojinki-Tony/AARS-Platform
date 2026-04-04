import type { WorkItem } from "../../types/aars";

type CompletedItemsPanelProps = {
  completedItems: WorkItem[];
};

export function CompletedItemsPanel({ completedItems }: CompletedItemsPanelProps) {
  return (
    <section className="card completed-card" aria-labelledby="completed-items-title">
      <div className="card-header">
        <div className="section-label">Completed Items Panel</div>
        <h2 className="card-title" id="completed-items-title">
          Already completed
        </h2>
      </div>
      <div className="panel-block">
        <div className="bullet-list">
          {completedItems.map((item) => (
            <div className="bullet-item" key={item.id}>
              <div className="bullet-title">{item.label}</div>
              <div className="bullet-note">{item.note}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
