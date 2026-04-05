import type { ActiveProjectsRegister } from "../../types/aars";

export const activeProjectsMock: ActiveProjectsRegister = {
  activeProjects: [
    {
      projectId: "Proj_002_AARS_Internal_Validation",
      projectName: "AARS Internal Validation Project",
      status: "conditionally_stable",
      priority: "high",
      latestStableViewId: "Internal_Validation_Loop_02_LSV_01",
      nextStep: "Create the project validation conclusion from the Loop_02 anchor.",
    },
    {
      projectId: "Proj_003_External_Validation",
      projectName: "External Validation Project",
      status: "active",
      priority: "medium",
      latestStableViewId: "Inherited bounded production-use anchor",
      nextStep: "Define working questions and open the first bounded contrastive loop.",
    },
  ],
};
