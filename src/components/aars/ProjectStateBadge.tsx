import type { ActiveProjectEntry } from "../../types/aars";

type ProjectStateBadgeProps = {
  status: ActiveProjectEntry["status"];
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function ProjectStateBadge({ status }: ProjectStateBadgeProps) {
  const className =
    status === "active"
      ? "chip chip--accent"
      : status === "conditionally_stable" || status === "reviewable"
        ? "chip chip--warning"
        : "chip chip--ok";

  return (
    <span className={className}>
      <strong>Status:</strong> {labelize(status)}
    </span>
  );
}
