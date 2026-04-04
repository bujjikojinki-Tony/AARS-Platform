import type { ProcessMapStep } from "../../types/aars";

type ProcessMapBarProps = {
  processMap: ProcessMapStep[];
};

export function ProcessMapBar({ processMap }: ProcessMapBarProps) {
  return (
    <section className="card process-map-card" aria-labelledby="process-map-title">
      <div className="card-header">
        <div className="section-label">Process Map Bar</div>
        <h2 className="card-title" id="process-map-title">
          Bounded progression state
        </h2>
        <p className="card-copy">
          This map is not decorative. It shows where the project is, what is complete,
          and what remains intentionally downstream.
        </p>
      </div>

      <div className="process-map-track">
        {processMap.map((step, index) => (
          <article
            className={`process-map-step process-map-step--${step.status}`}
            key={step.label}
          >
            <span className="process-step-index">{String(index + 1).padStart(2, "0")}</span>
            <div className="process-step-title">{step.label}</div>
            <div className="process-step-note">{step.note}</div>
          </article>
        ))}
      </div>
    </section>
  );
}
