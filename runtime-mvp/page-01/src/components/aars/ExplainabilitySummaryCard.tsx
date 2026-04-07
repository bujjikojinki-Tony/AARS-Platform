type ExplainabilitySummaryCardProps = {
  explainabilitySummary: string;
};

export function ExplainabilitySummaryCard({
  explainabilitySummary,
}: ExplainabilitySummaryCardProps) {
  return (
    <section className="card explainability-card" aria-labelledby="explainability-title">
      <div className="card-header">
        <div className="section-label">Explainability Summary Card</div>
        <h2 className="card-title" id="explainability-title">
          How to read this page
        </h2>
      </div>

      <div className="section-block">
        <div className="identity-meta">
          <div className="mini-label">Why this page exists</div>
          <p className="card-copy">{explainabilitySummary}</p>
        </div>
        <div className="identity-meta">
          <div className="mini-label">Read first</div>
          <p className="card-copy">
            Start with the project identity and latest stable view, then confirm health
            and recommended next step before touching any action.
          </p>
        </div>
        <div className="identity-meta">
          <div className="mini-label">Why this is not a dashboard</div>
          <p className="card-copy">
            This surface is organized around bounded continuation, not analytics volume,
            productivity metrics, or navigation sprawl.
          </p>
        </div>
      </div>
    </section>
  );
}
