type CurrentObjectivePanelProps = {
  currentObjective: string;
  keyResult: string;
  currentMode: string;
};

export function CurrentObjectivePanel({
  currentObjective,
  keyResult,
  currentMode,
}: CurrentObjectivePanelProps) {
  return (
    <section className="card objective-card" aria-labelledby="objective-title">
      <div className="card-header">
        <div className="section-label">Current Objective Panel</div>
        <h2 className="card-title" id="objective-title">
          Active work intent
        </h2>
      </div>

      <div className="hero-callout">
        <p>{currentObjective}</p>
      </div>

      <div className="objective-grid">
        <div className="identity-meta">
          <div className="mini-label">Key result</div>
          <p className="card-copy">{keyResult}</p>
        </div>
        <div className="identity-meta">
          <div className="mini-label">Current mode</div>
          <p className="card-copy">{currentMode}</p>
        </div>
      </div>
    </section>
  );
}
