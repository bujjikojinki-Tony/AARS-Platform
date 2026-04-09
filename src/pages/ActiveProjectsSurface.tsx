import { useState } from "react";

import { LatestStableViewCard } from "../components/aars/LatestStableViewCard";
import { StatusBadge } from "../components/aars/StatusBadge";
import { mockActiveProjectsSurfacePayload } from "../data/mock/activeProjectsSurfaceMock";
import type { ActiveProjectItem } from "../types/aars";

type ReviewAttentionLabel =
  | "Review Required"
  | "Continue With Caution"
  | "Closure Allowed";

function getReviewAttentionLabel(
  status: ActiveProjectItem["status"],
): ReviewAttentionLabel {
  if (status === "Review Required" || status === "Blocked") {
    return "Review Required";
  }

  if (status === "Closure Allowed") {
    return "Closure Allowed";
  }

  return "Continue With Caution";
}

function getProjectById(projectId: string) {
  return mockActiveProjectsSurfacePayload.projects.find(
    (project) => project.id === projectId,
  );
}

function getNextProjectId(currentProjectId: string) {
  const currentIndex = mockActiveProjectsSurfacePayload.projects.findIndex(
    (project) => project.id === currentProjectId,
  );

  if (currentIndex === -1) {
    return mockActiveProjectsSurfacePayload.projects[0]?.id;
  }

  const nextIndex =
    (currentIndex + 1) % mockActiveProjectsSurfacePayload.projects.length;

  return mockActiveProjectsSurfacePayload.projects[nextIndex]?.id;
}

type ActiveProjectsSurfaceProps = {
  onOpenHighlightedProject?: () => void;
  onReviewProjectState?: () => void;
};

export function ActiveProjectsSurface({
  onOpenHighlightedProject,
  onReviewProjectState,
}: ActiveProjectsSurfaceProps) {
  const payload = mockActiveProjectsSurfacePayload;
  const [highlightedProjectId, setHighlightedProjectId] = useState(
    payload.highlightedProjectId,
  );

  const highlightedProject =
    getProjectById(highlightedProjectId) ?? payload.projects[0];

  const reviewAttentionGroups: Record<ReviewAttentionLabel, ActiveProjectItem[]> = {
    "Review Required": [],
    "Continue With Caution": [],
    "Closure Allowed": [],
  };

  payload.projects.forEach((project) => {
    reviewAttentionGroups[getReviewAttentionLabel(project.status)].push(project);
  });

  function handleHighlightChange(projectId: string) {
    setHighlightedProjectId(projectId);
    console.log(`[AARS Active Projects] highlight:${projectId}`);
  }

  function handleCycleHighlight() {
    const nextProjectId = getNextProjectId(highlightedProjectId);

    if (!nextProjectId) {
      return;
    }

    handleHighlightChange(nextProjectId);
  }

  return (
    <div className="page-frame">
      <section className="top-banner" aria-label="Active projects surface header">
        <div className="banner-meta">
          <div className="eyebrow">
            AARS Runtime MVP / Active Projects Visibility Surface
          </div>
          <div className="governance-chip-row">
            <StatusBadge label="Round" value={payload.round} />
            <StatusBadge label="Projects" value={String(payload.activeProjectsCount)} />
            <StatusBadge label="Surface Status" value={payload.status} />
          </div>
        </div>

        <div className="banner-title-row">
          <div className="section-block">
            <h1 className="page-title">{payload.title}</h1>
            <p className="page-subtitle">
              Bounded governance-aware visibility surface for active projects. This page
              helps the user scan what is active, what needs review attention, and which
              project is currently highlighted without widening into portfolio
              orchestration.
            </p>
          </div>

          <div className="hero-callout">
            <div className="mini-label">Highlighted project</div>
            <p>{highlightedProject.title}</p>
          </div>
        </div>
      </section>

      <div className="grid-overview">
        <section className="card result-card" aria-labelledby="active-projects-list-title">
          <div className="card-header">
            <div className="section-label">Active Projects List</div>
            <h2 className="card-title" id="active-projects-list-title">
              Active projects at a glance
            </h2>
            <p className="card-copy">
              Select a project row to move the bounded highlight. Each item stays concise
              so the surface remains operational rather than dashboard-like.
            </p>
          </div>

          <div className="bullet-list">
            {payload.projects.map((project) => {
              const isHighlighted = project.id === highlightedProject.id;

              return (
                <div className="bullet-item" key={project.id}>
                  <div className="bullet-title">{project.title}</div>
                  <p className="card-copy">{project.projectId}</p>
                  <div className="metric-row">
                    <StatusBadge label="Round" value={project.currentRound} />
                    <StatusBadge label="Status" value={project.status} />
                    {isHighlighted ? (
                      <span className="status-pill status-pill--ok">Highlighted</span>
                    ) : null}
                  </div>
                  <p className="card-copy">{project.objectiveSummary}</p>
                  <p className="card-copy">{project.latestStableViewSummary}</p>
                  <button
                    className="action-button"
                    onClick={() => {
                      handleHighlightChange(project.id);
                    }}
                    type="button"
                  >
                    <span>{isHighlighted ? "Highlighted Project" : "Highlight Project"}</span>
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        <section className="card identity-card" aria-labelledby="highlighted-project-title">
          <div className="card-header">
            <div className="section-label">Highlighted Project Detail</div>
            <h2 className="card-title" id="highlighted-project-title">
              Current highlighted project
            </h2>
          </div>

          <div className="identity-grid">
            <div className="identity-meta">
              <div className="mini-label">Project title</div>
              <p className="card-copy">{highlightedProject.title}</p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Project ID</div>
              <p className="card-copy">{highlightedProject.projectId}</p>
            </div>
          </div>

          <div className="panel-block">
            <div className="mini-label">Current objective</div>
            <p className="card-copy">{highlightedProject.objectiveSummary}</p>
          </div>

          <div className="metric-row">
            <StatusBadge label="Health" value={highlightedProject.healthState} />
            <StatusBadge label="Status" value={highlightedProject.status} />
          </div>

          <div className="panel-block">
            <div className="mini-label">Recommended next step</div>
            <p className="card-copy">{highlightedProject.recommendedNextStep}</p>
          </div>
        </section>

        <LatestStableViewCard
          latestStableView={highlightedProject.latestStableViewSummary}
          stableViewRationale="The highlighted project summary is treated as the current safe portfolio anchor because it expresses the strongest accepted continuation point without widening into cross-project orchestration."
          safeContinuation={highlightedProject.recommendedNextStep}
        />

        <section className="card next-step-card" aria-labelledby="review-attention-title">
          <div className="card-header">
            <div className="section-label">Review Attention</div>
            <h2 className="card-title" id="review-attention-title">
              Which projects need what kind of governance attention
            </h2>
          </div>

          <div className="result-summary-layout">
            {(
              [
                "Review Required",
                "Continue With Caution",
                "Closure Allowed",
              ] as ReviewAttentionLabel[]
            ).map((label) => (
              <div className="result-summary-block" key={label}>
                <div className="mini-label">{label}</div>
                <div className="bullet-list">
                  {reviewAttentionGroups[label].length > 0 ? (
                    reviewAttentionGroups[label].map((project) => (
                      <div className="bullet-item" key={`${label}-${project.id}`}>
                        <div className="bullet-title">{project.title}</div>
                        <p className="card-copy">{project.status}</p>
                      </div>
                    ))
                  ) : (
                    <div className="bullet-item">
                      <div className="bullet-title">No projects currently in this lane</div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card actions-card" aria-labelledby="active-project-actions-title">
          <div className="card-header">
            <div className="section-label">Admissible Actions</div>
            <h2 className="card-title" id="active-project-actions-title">
              Bounded active-project actions only
            </h2>
            <p className="card-copy">
              These controls keep the surface operational without adding routing,
              persistence, or workflow behavior.
            </p>
          </div>

          <div className="action-button-grid">
            <button
              className="action-button"
              onClick={() => {
                if (onOpenHighlightedProject) {
                  onOpenHighlightedProject();
                  return;
                }

                console.log(`[AARS Active Projects] open:${highlightedProject.id}`);
              }}
              type="button"
            >
              <span>Open Highlighted Project</span>
            </button>
            <button
              className="action-button"
              onClick={() => {
                if (onReviewProjectState) {
                  onReviewProjectState();
                  return;
                }

                console.log(`[AARS Active Projects] review:${highlightedProject.id}`);
              }}
              type="button"
            >
              <span>Review Project State</span>
            </button>
            <button
              className="action-button"
              onClick={handleCycleHighlight}
              type="button"
            >
              <span>Switch Highlight</span>
            </button>
            <button
              className="action-button"
              onClick={() => {
                console.log(`[AARS Active Projects] continue:${highlightedProject.id}`);
              }}
              type="button"
            >
              <span>Continue Project</span>
            </button>
          </div>
        </section>

        <section className="card explainability-card" aria-labelledby="surface-explainability-title">
          <div className="card-header">
            <div className="section-label">Explainability Summary</div>
            <h2 className="card-title" id="surface-explainability-title">
              How to read this surface
            </h2>
          </div>

          <div className="section-block">
            <div className="identity-meta">
              <div className="mini-label">Why this page exists</div>
              <p className="card-copy">{payload.explainabilitySummary}</p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">Read first</div>
              <p className="card-copy">
                Start with the highlighted project, then check the review attention block
                before taking any surface-level action.
              </p>
            </div>
            <div className="identity-meta">
              <div className="mini-label">How it differs from Page 01</div>
              <p className="card-copy">
                Page 01 is a control surface for one active project. This surface stays
                lighter and exists to make several active projects legible at once.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
