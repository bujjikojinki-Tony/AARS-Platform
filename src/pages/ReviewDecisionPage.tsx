import { ActionCommandBar } from "../components/aars/ActionCommandBar";
import { DecisionBanner } from "../components/aars/DecisionBanner";
import { HealthSnapshotCard } from "../components/aars/HealthSnapshotCard";
import { LatestStableViewCard } from "../components/aars/LatestStableViewCard";
import { MainResultPanel } from "../components/aars/MainResultPanel";
import { NextStepRecommendationCard } from "../components/aars/NextStepRecommendationCard";
import { ProjectIdentityCard } from "../components/aars/ProjectIdentityCard";
import { RationalePanel } from "../components/aars/RationalePanel";
import { ReviewIdentityCard } from "../components/aars/ReviewIdentityCard";
import { WeaknessListPanel } from "../components/aars/WeaknessListPanel";
import { reviewDecisionPayload } from "../data/mock/reviewDecisionMock";

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function ReviewDecisionPage() {
  const payload = reviewDecisionPayload;
  const nextStep = payload.project.nextStep ?? payload.stableView.recommendedNextStep;

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Review decision page header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Page 03 / Review Decision Surface</div>
          <div className="governance-chip-row">
            <span className="chip chip--accent">
              <strong>Review Target:</strong> {payload.review.targetId}
            </span>
            <span className="chip chip--warning">
              <strong>Decision:</strong> {labelize(payload.review.decision)}
            </span>
            <span className="chip chip--ok">
              <strong>Stable View:</strong> {labelize(payload.stableView.maturity)}
            </span>
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">Review / Decision Page</h1>
            <p className="page-subtitle">
              Governance decision surface for explicit review judgment. This page makes
              the review target, findings, weaknesses, decision, rationale, and bounded
              next step visible in one place.
            </p>
            <div className="status-row">
              {payload.governanceSignals.map((signal) => (
                <span className="status-pill status-pill--accent" key={signal.label}>
                  {signal.label}: {signal.status}
                </span>
              ))}
            </div>
          </div>

          <div className="hero-callout">
            <div className="mini-label">Recommended bounded next step</div>
            <p>{nextStep}</p>
          </div>
        </div>
      </section>

      <div className="review-grid">
        <ReviewIdentityCard reviewTarget={payload.reviewTarget} review={payload.review} />
        <DecisionBanner review={payload.review} project={payload.project} stableView={payload.stableView} />
        <ProjectIdentityCard project={payload.project} />
        <HealthSnapshotCard review={payload.review} />
        <WeaknessListPanel weaknesses={payload.review.weaknesses} />
        <RationalePanel rationale={payload.review.rationale} />
        <LatestStableViewCard stableView={payload.stableView} />
        <MainResultPanel review={payload.review} timeline={payload.timeline} />
        <NextStepRecommendationCard
          project={payload.project}
          review={payload.review}
          stableView={payload.stableView}
        />
      </div>

      <ActionCommandBar
        project={payload.project}
        review={payload.review}
        stableView={payload.stableView}
      />
    </div>
  );
}
