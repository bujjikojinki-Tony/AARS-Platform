import type { ActiveProjectEntry } from "../../types/aars";

type PriorityBadgeProps = {
  priority: ActiveProjectEntry["priority"];
};

function labelize(value: string): string {
  return value.replaceAll("_", " ");
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const className =
    priority === "high"
      ? "chip chip--accent"
      : priority === "medium"
        ? "chip chip--warning"
        : "chip chip--ok";

  return (
    <span className={className}>
      <strong>Priority:</strong> {labelize(priority)}
    </span>
  );
}
