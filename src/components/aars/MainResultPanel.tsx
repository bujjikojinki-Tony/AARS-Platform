import type { ReviewSummary, TimelineEntry, WorkItem } from "../../types/aars";

type MainResultPanelProps =
  | {
      completedItems: WorkItem[];
      openItems: WorkItem[];
      review?: never;
      timeline?: never;
    }
  | {
      review: ReviewSummary;
      timeline: TimelineEntry[];
      completedItems?: never;
      openItems?: never;
    };

export function MainResultPanel(props: MainResultPanelProps) {
  if ("review" in props && props.review) {
    const { review, timeline } = props;

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
      </section>
    );
  }

  const { completedItems, openItems } = props;

  return (
    <section className="card result-summary-card" aria-labelledby="main-result-title">
      <div className="card-header">
        <div className="section-label">Main Result Panel</div>
        <h2 className="card-title" id="main-result-title">
          Completed versus remaining work
        </h2>
        <p className="card-copy">
          This panel keeps the current step legible by separating what is already secured
          from what still needs bounded follow-through.
        </p>
      </div>

      <div className="result-summary-layout">
        <div className="result-summary-block">
          <div className="mini-label">Completed items</div>
          <div className="bullet-list">
            {completedItems.map((item) => (
              <div className="bullet-item" key={item.id}>
                <div className="bullet-title">{item.label}</div>
                <div className="bullet-note">{item.note}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="result-summary-block">
          <div className="mini-label">Open items</div>
          <div className="bullet-list">
            {openItems.map((item) => (
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
