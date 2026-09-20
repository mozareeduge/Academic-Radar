import { Ban, Check, CircleHelp, SearchX } from "lucide-react";
import type { CoverageItem, CoverageStatus } from "@/types";

interface CoveragePanelProps {
  statuses: CoverageItem[];
  protocolVersion?: string;
}

function getStatusLabel(status: CoverageStatus): string {
  const labels: Record<CoverageStatus, string> = {
    SEARCHED_FOUND: "Searched · evidence found",
    SEARCHED_NONE_FOUND: "Searched · none found",
    NOT_SEARCHED: "Not searched",
    BLOCKED: "Blocked",
  };
  return labels[status];
}

function StatusIcon({ status }: { status: CoverageStatus }) {
  if (status === "SEARCHED_FOUND") return <Check className="size-4" aria-hidden />;
  if (status === "SEARCHED_NONE_FOUND") return <SearchX className="size-4" aria-hidden />;
  if (status === "BLOCKED") return <Ban className="size-4" aria-hidden />;
  return <CircleHelp className="size-4" aria-hidden />;
}

export function CoveragePanel({ statuses, protocolVersion }: CoveragePanelProps) {
  return (
    <section className="border border-border" aria-label="Research coverage">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-muted/50 px-4 py-3">
        <h3 className="font-semibold">Research coverage</h3>
        {protocolVersion && (
          <span className="font-mono text-xs text-muted-foreground">Protocol {protocolVersion}</span>
        )}
      </div>
      {statuses.length === 0 ? (
        <p className="p-4 text-sm text-muted-foreground">No coverage records are available for the latest research run.</p>
      ) : (
        <ul className="divide-y divide-border">
          {statuses.map((item) => (
            <li key={item.evidence_class} className="flex flex-col gap-2 p-3 text-sm sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <div className="font-medium">{item.evidence_class}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {item.evidence_ids.length} evidence artifact{item.evidence_ids.length === 1 ? "" : "s"}
                </div>
              </div>
              <span className="inline-flex shrink-0 items-center gap-1 border border-border bg-muted px-2 py-1 text-xs">
                <StatusIcon status={item.status} />
                {getStatusLabel(item.status)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
