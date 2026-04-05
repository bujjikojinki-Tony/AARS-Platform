import type { ActiveProjectsSurfacePayload } from "../../../page-02/src/types/aars";

export const activeProjectsSurfacePayload: ActiveProjectsSurfacePayload = {
  summary: {
    activeCount: 2,
    highestPriorityProjectId: "Proj_002_AARS_Internal_Validation",
    frozenCount: 1,
    cautionCount: 2,
    portfolioGuardrail:
      "Keep active work explicit, preserve frozen references as non-active, and do not widen simultaneous effort without named priority.",
  },
  activeProjects: [
    {
      projectId: "Proj_002_AARS_Internal_Validation",
      projectName: "AARS Internal Validation Project",
      domain: "AARS self-refinement",
      goalType: "Case Validation / Governance Validation",
      primaryTrack: "Validation and Operational Demonstration",
      currentStage: "Project conclusion synthesis",
      status: "conditionally_stable",
      latestStableView: "Internal_Validation_Loop_02_LSV_01",
      stableAnchorState: "explicit",
      nextStep: "Create the project validation conclusion from the Loop_02 anchor.",
      priority: "highest",
      touchPolicy: "advance",
      notes:
        "Highest-priority active project because it is closest to converting bounded evidence into a reusable project-level conclusion.",
    },
    {
      projectId: "Proj_003_External_Validation",
      projectName: "External Validation Project",
      domain: "Contrastive external validation",
      goalType: "Case Validation / Comparative Diagnosis",
      primaryTrack: "Validation and Operational Demonstration",
      currentStage: "Opening / loop-definition setup",
      status: "active",
      latestStableView: "Inherited bounded production-use anchor",
      stableAnchorState: "inherited",
      nextStep: "Define working questions and open the first bounded contrastive loop.",
      priority: "high",
      touchPolicy: "review_only",
      notes:
        "Meaningful active project, but secondary priority until Internal Validation completes its current synthesis step.",
    },
  ],
  nonActiveProjects: [
    {
      projectId: "Pilot_001_CDA",
      projectName: "CDA Pilot",
      domain: "Critical Digital Assets",
      goalType: "Bounded research pilot",
      primaryTrack: "Freeze / reuse reference",
      currentStage: "Frozen baseline reference",
      status: "frozen",
      latestStableView: "First bounded pilot baseline",
      stableAnchorState: "frozen_reference",
      nextStep: "Reuse as bounded reference; do not casually reopen the baseline.",
      priority: "reference",
      touchPolicy: "do_not_touch",
      notes:
        "Frozen reference project used to test whether active and non-active states remain distinguishable under portfolio load.",
    },
    {
      projectId: "Round_05_Multi_Project_Stress_Validation",
      projectName: "Multi-Project Stress Validation Round",
      domain: "Portfolio governance",
      goalType: "Portfolio validation",
      primaryTrack: "System stress validation",
      currentStage: "Scenario selection",
      status: "paused",
      latestStableView: "Bounded production-use anchor",
      stableAnchorState: "inherited",
      nextStep: "Resume only after the smallest useful simultaneous-project scenario is selected.",
      priority: "medium",
      touchPolicy: "do_not_touch",
      notes:
        "Structurally important, but not yet the project that should receive current implementation effort.",
    },
  ],
};
