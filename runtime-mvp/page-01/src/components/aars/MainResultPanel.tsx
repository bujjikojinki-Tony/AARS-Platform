import type { ReviewSummary, TimelineEntry } from "../../types/aars";

type MainResultPanelProps = {
  review: ReviewSummary;
  timeline: TimelineEntry[];
};

export function MainResultPanel({ review, timeline }: MainResultPanelProps) {
  return (
    <section className="card result-card" aria-labelledby="result-panel-title">
      <div className="card-header">
        <div className="section-label">Main Result Panel</div>
        <h2 className="card-title" id="result-panel-title">
          Review-backed operating result
        </h2>
        <p className="card-copy">
          This panel captures the bounded outcome of the current project state without
          degrading into a generic notes dump.
        </p>
      </div>

      <div className="result-layout">
        <div className="result-summary-block">
          <div className="result-index">Main findings</div>
          <div className="finding-list">
            {review.findings.map((finding, index) => (
              <article className="finding-item" key={finding}>
                <div className="finding-head">
                  <span className="finding-index">{String(index + 1).padStart(2, "0")}</span>
                  <strong>{finding}</strong>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className="result-side-panel">
          <div className="section-block">
            <div>
              <div className="result-index">Weaknesses to watch</div>
              <div className="timeline-list">
                {review.weaknesses.map((item) => (
                  <div className="timeline-item" key={item}>
                    <div className="timeline-title">{item}</div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="result-index">Stable-view timeline</div>
              <div className="timeline-list">
                {timeline.map((item) => (
                  <div className="list-item" key={item.title}>
                    <div className="list-title">{item.title}</div>
                    <div className="list-text">{item.note}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
