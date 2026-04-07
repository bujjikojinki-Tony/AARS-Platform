import { StatusBadge } from "../components/aars/StatusBadge";
import { mockCurrentStepPayload } from "../data/mock/currentStepMock";

export function CurrentStepPage() {
  const payload = mockCurrentStepPayload;

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Current step page header">
        <div className="banner-meta">
          <div className="eyebrow">AARS Runtime MVP / Page 02 / Current Step Control</div>
          <div className="governance-chip-row">
            <StatusBadge label="Step" value={payload.stepNumber} />
            <StatusBadge label="Status" value={payload.status} />
            <StatusBadge label="Priority" tone="warning" value={payload.executionPriority} />
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">{payload.stepName}</h1>
            <p className="page-subtitle">
              Bounded operational surface for the active execution step. This page exists
              to make the current step legible without widening into a workflow engine or
              reopening Round_06 system-definition work.
            </p>
            <div className="status-row">
              <span className="status-pill status-pill--accent">{payload.phase}</span>
              <span className="status-pill status-pill--warning">{payload.currentDecisionState}</span>
              <span className="status-pill status-pill--accent">{payload.currentStabilityState}</span>
            </div>
          </div>

          <div className="hero-callout">
            <div className="mini-label">Recommended next action</div>
            <p>{payload.recommendedNextAction}</p>
          </div>
        </div>
      </section>

      <div className="grid-overview">
        <section className="card identity-card" aria-labelledby="step-identity-title">
          <div className="card-header">
            <div className="section-label">Step Identity</div>
            <h2 className="card-title" id="step-identity-title">
              Current step identity
            </h2>
          </div>
          <div className="identity-grid">
            <div className="identity-meta">
              <div className="mini-label">Step number</div>
              <p className="card-copy">{payload.stepNumber}</p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Phase</div>
              <p className="card-copy">{payload.phase}</p>
            </div>
          </div>
          <div className="metric-row">
            <StatusBadge label="Step state" value={payload.currentStepState} />
          </div>
        </section>

        <section className="card objective-card" aria-labelledby="step-objective-title">
          <div className="card-header">
            <div className="section-label">Step Objective</div>
            <h2 className="card-title" id="step-objective-title">
              What this step is trying to achieve
            </h2>
          </div>
          <div className="hero-callout">
            <p>{payload.stepObjective}</p>
          </div>
          <div className="section-block">
            <div className="identity-meta">
              <div className="mini-label">Active task</div>
              <p className="card-copy">{payload.activeTask}</p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Expected output</div>
              <p className="card-copy">{payload.expectedOutput}</p>
            </div>
          </div>
        </section>

        <section className="card health-card" aria-labelledby="step-state-title">
          <div className="card-header">
            <div className="section-label">Execution State</div>
            <h2 className="card-title" id="step-state-title">
              Step, milestone, stability, decision
            </h2>
          </div>
          <div className="metric-row">
            <StatusBadge label="Milestone" value={payload.currentMilestoneState} />
            <StatusBadge label="Stability" value={payload.currentStabilityState} />
            <StatusBadge label="Decision" value={payload.currentDecisionState} />
          </div>
        </section>

        <section className="card next-step-card" aria-labelledby="readiness-title">
          <div className="card-header">
            <div className="section-label">Inputs and Readiness</div>
            <h2 className="card-title" id="readiness-title">
              Required inputs and upstream artifacts
            </h2>
          </div>
          <div className="result-summary-layout">
            <div className="result-summary-block">
              <div className="mini-label">Required inputs</div>
              <div className="bullet-list">
                {payload.requiredInputs.map((item) => (
                  <div className="bullet-item" key={item}>
                    <div className="bullet-title">{item}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="result-summary-block">
              <div className="mini-label">Upstream artifacts</div>
              <div className="bullet-list">
                {payload.upstreamArtifacts.map((item) => (
                  <div className="bullet-item" key={item}>
                    <div className="bullet-title">{item}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="panel-block">
            <div className="mini-label">Readiness signal</div>
            <p className="card-copy">{payload.readinessSignal}</p>
          </div>
        </section>

        <section className="card result-card" aria-labelledby="cautions-title">
          <div className="card-header">
            <div className="section-label">Risks and Cautions</div>
            <h2 className="card-title" id="cautions-title">
              Current risks and scope cautions
            </h2>
          </div>
          <div className="result-summary-layout">
            <div className="result-summary-block">
              <div className="mini-label">Execution risks</div>
              <div className="bullet-list">
                {payload.executionRisks.map((item) => (
                  <div className="bullet-item" key={item}>
                    <div className="bullet-title">{item}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="result-summary-block">
              <div className="mini-label">Scope cautions</div>
              <div className="bullet-list">
                {payload.scopeCautions.map((item) => (
                  <div className="bullet-item" key={item}>
                    <div className="bullet-title">{item}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="card stable-card" aria-labelledby="stable-view-title">
          <div className="card-header">
            <div className="section-label">Latest Stable View</div>
            <h2 className="card-title" id="stable-view-title">
              Current continuation anchor
            </h2>
          </div>
          <div className="stability-grid">
            <div className="stability-column">
              <div className="mini-label">Latest stable view</div>
              <p className="card-copy">{payload.latestStableView}</p>
            </div>
            <div className="stability-column">
              <div className="mini-label">Why this is stable enough</div>
              <p className="card-copy">{payload.stableViewRationale}</p>
            </div>
            <div className="stability-column stability-column--wide">
              <div className="mini-label">Allowed continuation</div>
              <p className="card-copy">{payload.allowedContinuation}</p>
            </div>
          </div>
        </section>

        <section className="card next-step-card" aria-labelledby="next-action-title">
          <div className="card-header">
            <div className="section-label">Recommended Next Action</div>
            <h2 className="card-title" id="next-action-title">
              Immediate bounded move
            </h2>
          </div>
          <div className="decision-block">
            <div className="decision-title">
              <StatusBadge label="Execution Priority" tone="warning" value={payload.executionPriority} />
            </div>
            <p>{payload.recommendedNextAction}</p>
            <p className="action-rationale">{payload.nextActionRationale}</p>
          </div>
        </section>

        <section className="card actions-card" aria-labelledby="actions-title">
          <div className="card-header">
            <div className="section-label">Admissible Step Actions</div>
            <h2 className="card-title" id="actions-title">
              Bounded step actions only
            </h2>
            <p className="card-copy">
              These actions establish operational structure only. They intentionally stop
              short of routing, persistence, or workflow engine behavior.
            </p>
          </div>
          <div className="action-button-grid">
            {payload.admissibleActions.map((action) => (
              <button
                className="action-button"
                key={action.id}
                onClick={() => {
                  console.log(`[AARS Page 02] ${action.id}`);
                }}
                type="button"
              >
                <span>{action.label}</span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
