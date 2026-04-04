import type { NextStepControl } from "../../types/aars";

type ActionCommandBarProps = {
  nextStepControl: NextStepControl;
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function ActionCommandBar({ nextStepControl }: ActionCommandBarProps) {
  return (
    <section className="action-bar" aria-labelledby="step-action-title">
      <div className="action-bar-header">
        <div>
          <div className="action-context">Action Command Bar</div>
          <h2 className="card-title" id="step-action-title">
            Bounded actions only
          </h2>
        </div>
        <span className="status-pill status-pill--warning">
          {labelize(nextStepControl.decision)}
        </span>
      </div>

      <div className="action-grid">
        <div className="action-list">
          <div className="action-item">
            <div>
              <strong>Write the project conclusion</strong>
              <span>{nextStepControl.immediateNextStep}</span>
            </div>
            <span className="action-pill action-pill--warning">now</span>
          </div>
          <div className="action-item">
            <div>
              <strong>Preserve the current anchor</strong>
              <span>
                Continue from the strongest Loop_02 artifacts instead of opening fresh
                exploratory work.
              </span>
            </div>
            <span className="action-pill action-pill--ok">admissible</span>
          </div>
          <div className="action-item">
            <div>
              <strong>Delay non-admissible moves</strong>
              <span>{nextStepControl.notAdmissible[0]}</span>
            </div>
            <span className="action-pill action-pill--accent">guardrail</span>
          </div>
        </div>
        <div className="admissibility-panel">
          <div className="mini-label">Why this is the next move</div>
          {nextStepControl.why.map((item) => (
            <p className="action-rationale" key={item}>
              {item}
            </p>
          ))}
          <div className="mini-label">Not yet admissible</div>
          {nextStepControl.notAdmissible.map((item) => (
            <p className="action-rationale" key={item}>
              {item}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
}
