import type { ReviewSummary } from "../../types/aars";

type HealthSnapshotCardProps = {
  review: ReviewSummary;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function HealthSnapshotCard({ review }: HealthSnapshotCardProps) {
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
