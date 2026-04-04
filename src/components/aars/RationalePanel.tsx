type RationalePanelProps = {
  rationale: string[];
};

export function RationalePanel({ rationale }: RationalePanelProps) {
  return (
    <section className="card rationale-card" aria-labelledby="rationale-panel-title">
      <div className="card-header">
        <div className="section-label">Rationale Panel</div>
        <h2 className="card-title" id="rationale-panel-title">
          Why this decision was made
        </h2>
      </div>

      <div className="review-target-block">
        <div className="rationale-list">
          {rationale.map((item, index) => (
            <div className="rationale-item" key={item}>
              <strong>Why {String(index + 1).padStart(2, "0")}</strong>
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
