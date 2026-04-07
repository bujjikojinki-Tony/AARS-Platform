type StatusBadgeTone = "accent" | "warning" | "ok";

type StatusBadgeProps = {
  label?: string;
  value: string;
  tone?: StatusBadgeTone;
};

function inferTone(value: string): StatusBadgeTone {
  const normalized = value.toLowerCase();

  if (normalized.includes("stable") || normalized.includes("healthy")) {
    return "ok";
  }

  if (normalized.includes("watch") || normalized.includes("review")) {
    return "warning";
  }

  return "accent";
}

export function StatusBadge({
  label,
  value,
  tone = inferTone(value),
}: StatusBadgeProps) {
  return (
    <span className={`chip chip--${tone}`}>
      {label ? <strong>{label}:</strong> : null} {value}
    </span>
  );
}
