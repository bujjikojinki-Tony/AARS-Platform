import type { WorkItem } from "../../types/aars";

type OpenItemsPanelProps = {
  openItems: WorkItem[];
};

export function OpenItemsPanel({ openItems }: OpenItemsPanelProps) {
  return (
    <section className="card open-card" aria-labelledby="open-items-title">
      <div className="card-header">
        <div className="section-label">Open / Remaining Items Panel</div>
        <h2 className="card-title" id="open-items-title">
          Still open
        </h2>
      </div>
      <div className="panel-block">
        <div className="bullet-list">
          {openItems.map((item) => (
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
