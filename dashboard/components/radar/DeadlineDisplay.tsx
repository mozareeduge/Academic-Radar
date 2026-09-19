import type { CaseDeadline } from "@/types";

interface DeadlineDisplayProps {
  deadline: CaseDeadline | null;
}

function getPrecisionLabel(precision: string | null | undefined): string | null {
  switch (precision) {
    case "DATE_ONLY":
      return "time not stated";
    case "LOCAL_TIME":
      return null;
    case "OFFSET_AWARE":
      return null;
    case "AMBIGUOUS":
      return "timezone not stated";
    default:
      return null;
  }
}

export function DeadlineDisplay({ deadline }: DeadlineDisplayProps) {
  if (!deadline || !deadline.original_text) {
    return null;
  }

  const precisionLabel = getPrecisionLabel(deadline.precision);

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="font-medium text-foreground">{deadline.original_text}</span>
      {precisionLabel && (
        <span className="text-muted-foreground text-xs">· {precisionLabel}</span>
      )}
    </div>
  );
}
