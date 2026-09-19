import type { CoverageItem, CoverageStatus } from "@/types";

interface CoveragePanelProps {
  statuses: CoverageItem[];
}

function getStatusLabel(status: CoverageStatus): string {
  const labels: Record<CoverageStatus, string> = {
    "searched+found": "Searched + found",
    "searched+none": "Searched + none",
    "not searched": "Not searched",
    "blocked": "Blocked",
  };
  return labels[status];
}

function getStatusClasses(status: CoverageStatus): string {
  switch (status) {
    case "searched+found":
      return "state-pass";
    case "searched+none":
    case "not searched":
      return "state-unknown";
    case "blocked":
      return "state-fail";
    default:
      return "";
  }
}

export function CoveragePanel({ statuses }: CoveragePanelProps) {
  return (
    <section
      className="rounded-md border border-border p-4"
      aria-label="Research coverage"
    >
      <h3 className="font-semibold text-sm mb-3">Research coverage</h3>
      <ul className="flex flex-col gap-2">
        {statuses.map((item) => (
          <li
            key={item.class}
            className={`flex items-center justify-between p-2 rounded text-sm ${getStatusClasses(item.status)}`}
          >
            <span className="text-foreground">{item.class}</span>
            <span className="text-muted-foreground">{getStatusLabel(item.status)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
