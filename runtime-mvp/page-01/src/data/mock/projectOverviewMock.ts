import type { ProjectOverviewPayload } from "../../types/aars";

export const projectOverviewPayload: ProjectOverviewPayload = {
  project: {
    projectId: "Proj_002_AARS_Internal_Validation",
    projectName: "AARS Internal Validation Project",
    projectType: "bounded internal validation project",
    status: "active",
    goalType: "Case Validation / Governance Validation",
    currentObjective:
      "Convert Loop_02 evidence into a bounded project-level validation conclusion without reopening broad AARS redesign work.",
    primaryTrack: "Validation and Operational Demonstration",
    currentPriority: "high",
    latestStableViewId: "Internal_Validation_Loop_02_LSV_01",
    nextStep:
      "Create AARS_Internal_Validation_Project_Validation_Conclusion.md from the Loop_02 stable anchor and review judgment.",
  },
  stableView: {
    stableViewId: "Internal_Validation_Loop_02_LSV_01",
    scope: "Proj_002_AARS_Internal_Validation / Loop_02",
    maturity: "conditionally_stable",
    summary:
      "AARS can open, review, and deepen a second bounded project context through dependency, risk, health, and review artifacts without losing boundedness.",
    completedElements: [
      "Second bounded validation project opened",
      "Loop_01 review and stable view captured",
      "Loop_02 dependency, risk, health, and review artifacts completed",
    ],
    unresolvedButTolerable: [
      "Evidence remains internal to AARS rather than cross-domain",
      "The chain is stronger, but not yet final production-readiness proof",
      "Project-level conclusion still needs to be written",
    ],
    continuationConditions: [
      "Stay focused on interpretation instead of system redesign",
      "Use the next step to consolidate evidence, not multiply branches",
      "Re-review before widening scope",
    ],
    recommendedNextStep:
      "Write the project validation conclusion using the Loop_02 stable anchor as the active continuity spine.",
  },
  review: {
    reviewId: "Internal_Validation_Loop_02_Review",
    targetId: "AARS_Internal_Validation_Loop_02",
    currentState: "caution",
    decision: "continue_with_caution",
    rationale: [
      "Loop_02 materially strengthened repeatability evidence.",
      "The context is still too internal and too narrow for a final production-ready claim.",
      "The next best move is synthesis, not expansion.",
    ],
    findings: [
      "The project now carries a coherent dependency -> risk -> health -> review sequence inside a second bounded context.",
      "Boundedness, review discipline, and stable-view capture all remained intact through the second loop.",
      "The internal setting proves repeatability, yet it still lacks the contrast needed for a strong terminal readiness claim.",
    ],
    weaknesses: [
      "Still concentrated inside AARS self-refinement",
      "Premature freeze or closure would overstate confidence",
      "Further value now comes from synthesis, not additional exploratory sprawl",
    ],
  },
  progression: [
    {
      label: "Project opened",
      status: "complete",
      note: "Charter and project home established.",
    },
    {
      label: "Loop_01 validated",
      status: "complete",
      note: "Review and first stable anchor captured.",
    },
    {
      label: "Loop_02 consolidation",
      status: "current",
      note: "Stronger object-chain evidence under active review.",
    },
    {
      label: "Project conclusion",
      status: "upcoming",
      note: "Synthesize project-level judgment from Loop_02.",
    },
    {
      label: "Round_02 readiness update",
      status: "upcoming",
      note: "Translate project evidence into system-level judgment.",
    },
  ],
  timeline: [
    {
      title: "Starting anchor",
      note: "Inherited Round_01 baseline provided the initial continuity point before project-specific proof existed.",
    },
    {
      title: "Loop_01 result",
      note: "Repeatability was demonstrated in a second project context, but depth remained limited.",
    },
    {
      title: "Loop_02 result",
      note: "Dependency, risk, health, and review logic now form a materially stronger continuation anchor.",
    },
  ],
  governanceSignals: [
    { label: "Boundedness", status: "holding" },
    { label: "Review discipline", status: "explicit" },
    { label: "Closure readiness", status: "not yet admissible" },
  ],
};
