import type { ReviewSummary, ReviewTargetSummary } from "../../types/aars";

type ReviewIdentityCardProps = {
  reviewTarget: ReviewTargetSummary;
  review: ReviewSummary;
};

export function ReviewIdentityCard({
  reviewTarget,
  review,
}: ReviewIdentityCardProps) {
  return (
    <section className="card review-target-card" aria-labelledby="review-identity-title">
      <div className="card-header">
        <div className="section-label">Review Identity Card</div>
        <h2 className="card-title" id="review-identity-title">
          {reviewTarget.reviewTitle}
        </h2>
        <p className="card-copy">
          This panel fixes the review target, scope, and question before the decision is
          interpreted, so governance remains explicit instead of implied.
        </p>
      </div>

      <div className="review-target-layout">
        <div className="review-target-block">
          <div className="metric-row">
            <span className="chip chip--accent">
              <strong>Review ID:</strong> {review.reviewId}
            </span>
            <span className="chip chip--warning">
              <strong>Target:</strong> {review.targetId}
            </span>
          </div>

          <div className="section-block">
            <div>
              <div className="mini-label">Scope</div>
              <p className="card-copy">{reviewTarget.reviewScope}</p>
            </div>
            <div>
              <div className="mini-label">Review question</div>
              <p className="card-copy">{reviewTarget.reviewQuestion}</p>
            </div>
            <div>
              <div className="mini-label">Current reviewed condition</div>
              <p className="card-copy">{reviewTarget.currentReviewedCondition}</p>
            </div>
          </div>
        </div>

        <div className="review-target-block">
          <div className="mini-label">Linked artifacts</div>
          <div className="artifact-list">
            {reviewTarget.linkedArtifacts.map((item) => (
              <div className="artifact-item" key={item}>
                <strong>{item}</strong>
                <span>Supports the current bounded review judgment.</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
