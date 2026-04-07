import { StatusBadge } from "./StatusBadge";

type RecommendedNextStepCardProps = {
  recommendedNextStep: string;
  nextStepRationale: string;
  executionPriority: "P1" | "P2" | "P3";
};

export function RecommendedNextStepCard({
  recommendedNextStep,
  nextStepRationale,
  executionPriority,
}: RecommendedNextStepCardProps) {
  const priorityTone =
    executionPriority === "P1" ? "warning" : executionPriority === "P2" ? "accent" : "ok";

  return (
    <section className="card next-step-card" aria-labelledby="next-step-title">
      <div className="card-header">
        <div className="section-label">Recommended Next Step Card</div>
        <h2 className="card-title" id="next-step-title">
          Recommended next step
        </h2>
      </div>

      <div className="decision-block">
        <div className="decision-title">
          <StatusBadge label="Execution Priority" value={executionPriority} tone={priorityTone} />
        </div>
        <p>{recommendedNextStep}</p>
        <p className="action-rationale">{nextStepRationale}</p>
      </div>
    </section>
  );
}
