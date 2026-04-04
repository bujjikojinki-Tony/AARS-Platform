import type { ReviewSummary, StepHealthSummary } from "../../types/aars";

type HealthSnapshotCardProps =
  | {
      health: StepHealthSummary;
      review?: never;
    }
  | {
      review: ReviewSummary;
      health?: never;
    };

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function HealthSnapshotCard(props: HealthSnapshotCardProps) {
  if ("health" in props && props.health) {
    const { health } = props;
    const meterWidth =
      health.state === "caution" ? "70%" : health.state === "blocked" ? "42%" : "88%";

    return (
      <section className="card health-card" aria-labelledby="step-health-title">
        <div className="card-header">
          <div className="section-label">Health Snapshot Card</div>
          <h2 className="card-title" id="step-health-title">
            Current step condition
          </h2>
        </div>

        <div className="health-column">
          <div className="decision-title">
            <p className="decision-name">{health.state}</p>
            <span className="status-pill status-pill--warning">
              {labelize(health.continuationJudgment)}
            </span>
          </div>

          <div className="state-meter">
            <div className="meter-bar" aria-hidden="true">
              <div className="meter-fill" style={{ width: meterWidth }} />
            </div>
            <p className="card-copy">{health.summary}</p>
            <p className="card-copy">{health.blockerNote}</p>
          </div>
        </div>
      </section>
    );
  }

  const { review } = props;
  const meterWidth = review.currentState === "caution" ? "68%" : "84%";

  return (
    <section className="card health-card" aria-labelledby="health-title">
      <div className="card-header">
        <div className="section-label">Health Snapshot Card</div>
        <h2 className="card-title" id="health-title">
          Current health state
        </h2>
      </div>

      <div className="health-column">
        <div className="decision-title">
          <p className="decision-name">{review.currentState}</p>
          <span className="status-pill status-pill--warning">{labelize(review.decision)}</span>
        </div>

        <div className="state-meter">
          <div className="meter-bar" aria-hidden="true">
            <div className="meter-fill" style={{ width: meterWidth }} />
          </div>
          {review.rationale.map((item) => (
            <p className="card-copy" key={item}>
              {item}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
}
