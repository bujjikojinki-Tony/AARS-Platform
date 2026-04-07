type StatusBadgeTone = "accent" | "warning" | "ok";

type StatusBadgeProps = {
  label?: string;
  tone?: StatusBadgeTone;
  value: string;
};

function inferTone(value: string): StatusBadgeTone {
  const normalized = value.toLowerCase();

  if (
    normalized.includes("completed") ||
    normalized.includes("stable") ||
    normalized.includes("healthy")
  ) {
    return "ok";
  }

  if (
    normalized.includes("watch") ||
    normalized.includes("review") ||
    normalized.includes("progress") ||
    normalized.includes("p1")
  ) {
    return "warning";
  }

  return "accent";
}

export function StatusBadge({
  label,
  tone,
  value,
}: StatusBadgeProps) {
  const resolvedTone = tone ?? inferTone(value);

  return (
    <span className={`chip chip--${resolvedTone}`}>
      {label ? <strong>{label}:</strong> : null} {value}
    </span>
  );
}
