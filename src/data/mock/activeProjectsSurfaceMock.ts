import type { ActiveProjectsSurfacePayload } from "../../types/aars";

export const mockActiveProjectsSurfacePayload: ActiveProjectsSurfacePayload = {
  title: "Active Projects Surface",
  round: "Round_06_MVP_Implementation",
  status: "Conditionally Stable",
  activeProjectsCount: 3,
  highlightedProjectId: "aars-r06-mvp",
  projects: [
    {
      id: "aars-r06-mvp",
      title: "AARS Round_06 MVP Implementation",
      projectId: "AARS-R06-MVP",
      currentRound: "Round_06_MVP_Implementation",
      status: "Conditionally Stable",
      objectiveSummary:
        "Preserve and harden the accepted first-set MVP surfaces without widening scope.",
      latestStableViewSummary:
        "Page 01 remains entry, while Page 02, Page 03, and the Active Projects Surface are accepted continuation units in one bounded MVP set.",
      healthState: "Watch",
      recommendedNextStep:
        "Continue bounded hardening and review of the accepted first-set MVP surfaces.",
    },
    {
      id: "pilot-001-cda",
      title: "Pilot_001_CDA",
      projectId: "PILOT-001-CDA",
      currentRound: "Pilot stabilization",
      status: "Conditionally Stable",
      objectiveSummary:
        "Maintain the CDA pilot as a governed domain migration reference.",
      latestStableViewSummary:
        "The pilot remains usable as a stable continuity anchor for domain migration patterns.",
      healthState: "Healthy",
      recommendedNextStep: "Review second-pass strengthening opportunities.",
    },
    {
      id: "project-placeholder-01",
      title: "Bounded Project Placeholder",
      projectId: "PROJECT-PLACEHOLDER-01",
      currentRound: "Framing",
      status: "Review Required",
      objectiveSummary:
        "Hold a placeholder for future bounded project visibility without expanding MVP scope.",
      latestStableViewSummary:
        "Project exists as a visibility placeholder and is not yet an execution surface.",
      healthState: "Watch",
      recommendedNextStep:
        "Confirm whether the project should enter bounded implementation.",
    },
  ],
  explainabilitySummary:
    "This page exists to provide bounded visibility across active projects. Read the highlighted project and review attention summary first. It differs from Page 01 because it is not the control surface for one project, but the active-project visibility surface for several within the accepted first-set MVP.",
};
