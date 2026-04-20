import { useState } from "react";

import { ActiveProjectsSurface } from "./pages/ActiveProjectsSurface";
import { ControlConsolePage } from "./pages/ControlConsolePage";
import { CurrentStepPage } from "./pages/CurrentStepPage";
import { ProjectOverviewPage } from "./pages/ProjectOverviewPage";
import { ReviewDecisionPage } from "./pages/ReviewDecisionPage";

type AcceptedSurfaceId =
  | "overview"
  | "current-step"
  | "review-decision"
  | "active-projects"
  | "control-console";

type SurfaceOption = {
  id: AcceptedSurfaceId;
  label: string;
  note: string;
};

const surfaceOptions: SurfaceOption[] = [
  {
    id: "overview",
    label: "Overview",
    note: "Entry surface",
  },
  {
    id: "current-step",
    label: "Current Step",
    note: "Execution surface",
  },
  {
    id: "review-decision",
    label: "Review / Decision",
    note: "Governance surface",
  },
  {
    id: "active-projects",
    label: "Active Projects",
    note: "Multi-project surface",
  },
  {
    id: "control-console",
    label: "Control Console",
    note: "Sketch-style procedure surface",
  },
];

type SurfaceNavigationHandlers = {
  openOverview: () => void;
  openCurrentStep: () => void;
  openReviewDecision: () => void;
  openActiveProjects: () => void;
  openControlConsole: () => void;
};

function renderSurface(
  surfaceId: AcceptedSurfaceId,
  navigationHandlers: SurfaceNavigationHandlers,
) {
  switch (surfaceId) {
    case "current-step":
      return (
        <CurrentStepPage
          onOpenOverview={navigationHandlers.openOverview}
          onOpenReviewDecision={navigationHandlers.openReviewDecision}
          onOpenActiveProjects={navigationHandlers.openActiveProjects}
        />
      );
    case "review-decision":
      return (
        <ReviewDecisionPage
          onReturnCurrentStep={navigationHandlers.openCurrentStep}
        />
      );
    case "active-projects":
      return (
        <ActiveProjectsSurface
          onOpenHighlightedProject={navigationHandlers.openOverview}
          onReviewProjectState={navigationHandlers.openReviewDecision}
        />
      );
    case "control-console":
      return <ControlConsolePage />;
    case "overview":
    default:
      return (
        <ProjectOverviewPage
          onOpenCurrentStep={navigationHandlers.openCurrentStep}
          onOpenReviewDecision={navigationHandlers.openReviewDecision}
          onOpenActiveProjects={navigationHandlers.openActiveProjects}
        />
      );
  }
}

export function App() {
  const [activeSurfaceId, setActiveSurfaceId] =
    useState<AcceptedSurfaceId>("overview");
  const navigationHandlers: SurfaceNavigationHandlers = {
    openOverview: () => {
      setActiveSurfaceId("overview");
    },
    openCurrentStep: () => {
      setActiveSurfaceId("current-step");
    },
    openReviewDecision: () => {
      setActiveSurfaceId("review-decision");
    },
    openActiveProjects: () => {
      setActiveSurfaceId("active-projects");
    },
    openControlConsole: () => {
      setActiveSurfaceId("control-console");
    },
  };

  const activeSurface =
    surfaceOptions.find((surface) => surface.id === activeSurfaceId) ??
    surfaceOptions[0];

  return (
    <div>
      <section className="card" aria-label="Round 07 bounded navigation control">
        <div className="card-header">
          <div className="section-label">Bounded Navigation Gate</div>
          <h1 className="card-title">Accepted first-set surface switching</h1>
          <p className="card-copy">
            This control keeps the accepted MVP surfaces in one bounded flow without
            adding routing, history management, or app-shell expansion.
          </p>
        </div>

        <div className="metric-row">
          <span className="status-pill status-pill--ok">Default entry: Overview</span>
          <span className="status-pill status-pill--accent">
            Active surface: {activeSurface.label}
          </span>
        </div>

        <div className="action-button-grid">
          {surfaceOptions.map((surface) => {
            const isActive = surface.id === activeSurfaceId;

            return (
              <button
                className="action-button"
                key={surface.id}
                onClick={() => {
                  setActiveSurfaceId(surface.id);
                }}
                type="button"
              >
                <span>{surface.label}</span>
                <span>{isActive ? "Active now" : surface.note}</span>
              </button>
            );
          })}
        </div>
      </section>

      {renderSurface(activeSurfaceId, navigationHandlers)}
    </div>
  );
}

export default App;
