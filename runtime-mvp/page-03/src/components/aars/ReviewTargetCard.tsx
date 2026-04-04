import type { ReviewSummary, ReviewTargetSummary } from "../../../page-02/src/types/aars";

type ReviewTargetCardProps = {
  reviewTarget: ReviewTargetSummary;
  review: ReviewSummary;
};

export function ReviewTargetCard({ reviewTarget, review }: ReviewTargetCardProps) {
  return (
    <section className="card review-target-card" aria-labelledby="review-target-title">
      <div className="card-header">
        <div className="section-label">Review Target Card</div>
        <h2 className="card-title" id="review-target-title">
          {reviewTarget.reviewTitle}
        </h2>
        <p className="card-copy">
          This surface makes the current review target explicit so the user can see what
          is being judged before interpreting the decision that follows.
        </p>
      </div>

      <div className="review-target-layout">
        <div className="review-target-block">
          <div className="metric-row">
            <span className="chip chip--accent">
              <strong>Target:</strong> {review.targetId}
            </span>
            <span className="chip chip--warning">
              <strong>Condition:</strong> {reviewTarget.currentReviewedCondition}
            </span>
          </div>
          <div className="section-block">
            <div>
              <div className="mini-label">Review scope</div>
              <p className="card-copy">{reviewTarget.reviewScope}</p>
            </div>
            <div>
              <div className="mini-label">Review question</div>
              <p className="card-copy">{reviewTarget.reviewQuestion}</p>
            </div>
          </div>
        </div>

        <div className="review-target-block">
          <div className="mini-label">Linked review artifacts</div>
          <div className="artifact-list">
            {reviewTarget.linkedArtifacts.map((item) => (
              <div className="artifact-item" key={item}>
                <strong>{item}</strong>
                <span>Used to support the current bounded judgment.</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
