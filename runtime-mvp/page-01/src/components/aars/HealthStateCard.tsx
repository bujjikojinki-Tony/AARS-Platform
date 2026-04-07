import { StatusBadge } from "./StatusBadge";

type HealthStateCardProps = {
  healthState: "Healthy" | "Watch" | "At Risk";
  blockersCount: number;
  warningsCount: number;
  readinessJudgment: string;
};

export function HealthStateCard({
  healthState,
  blockersCount,
  warningsCount,
  readinessJudgment,
}: HealthStateCardProps) {
  return (
    <section className="card health-card" aria-labelledby="health-title">
      <div className="card-header">
        <div className="section-label">Health State Card</div>
        <h2 className="card-title" id="health-title">
          Bounded health summary
        </h2>
      </div>

      <div className="health-column">
        <div className="metric-row">
          <StatusBadge label="Health" value={healthState} />
          <StatusBadge label="Blockers" value={String(blockersCount)} tone="ok" />
          <StatusBadge label="Warnings" value={String(warningsCount)} tone="warning" />
        </div>

        <div className="panel-block">
          <div className="mini-label">Readiness judgment</div>
          <p className="card-copy">{readinessJudgment}</p>
        </div>
      </div>
    </section>
  );
}
