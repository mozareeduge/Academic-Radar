import Link from "next/link";
import { AlertTriangle, ArrowRight, Clock3, RefreshCw } from "lucide-react";
import type { RadarCase } from "@/types";

interface RadarCaseRowProps {
  case: RadarCase;
  compact?: boolean;
}

export function RadarCaseRow({ case: radarCase, compact = false }: RadarCaseRowProps) {
  const blockerCount = radarCase.blockers.length;
  const deadline = radarCase.deadline?.original_text ?? null;
  const heading = `Case ${radarCase.id}`;

  return (
    <Link
      href={`/cases/${encodeURIComponent(radarCase.id)}`}
      data-testid={`radar-case-${radarCase.id}`}
      className="group block border-b border-border px-4 py-4 transition-colors last:border-0 hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
      aria-label={`Open ${heading}`}
    >
      <div className="flex min-w-0 items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <h2 className="line-clamp-2 font-semibold text-foreground">{heading}</h2>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <span>{radarCase.research_state}</span>
            <span className="truncate font-mono" title={radarCase.id}>{radarCase.id}</span>
          </div>
        </div>
        <ArrowRight className="mt-0.5 size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" aria-hidden />
      </div>

      {!compact && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {blockerCount > 0 && (
            <span
              data-testid="chip"
              className="inline-flex items-center gap-1 border border-destructive/30 bg-destructive/10 px-2.5 py-1 text-xs font-medium text-destructive"
            >
              <AlertTriangle className="size-3" aria-hidden />
              {blockerCount} formal blocker{blockerCount === 1 ? "" : "s"}
            </span>
          )}

          {radarCase.unknown_count > 0 && (
            <span data-testid="chip" className="inline-flex items-center border border-border bg-muted px-2.5 py-1 text-xs font-medium">
              {radarCase.unknown_count} unknown
            </span>
          )}

          {radarCase.suggested_disposition && (
            <span data-testid="chip" className="inline-flex items-center gap-1 border border-border bg-muted px-2.5 py-1 text-xs">
              <span className="text-muted-foreground">System suggests:</span>
              <strong className="font-semibold text-foreground">{radarCase.suggested_disposition}</strong>
            </span>
          )}

          <span data-testid="chip" className="inline-flex items-center gap-1 border border-border bg-background px-2.5 py-1 text-xs">
            <span className="text-muted-foreground">Your decision:</span>
            <strong className="font-semibold text-foreground">{radarCase.user_disposition}</strong>
          </span>

          {deadline && (
            <span data-testid="chip" className="inline-flex items-center gap-1 px-1 py-1 text-xs text-muted-foreground">
              <Clock3 className="size-3" aria-hidden />
              {deadline}
            </span>
          )}

          <span className="inline-flex items-center gap-1 px-1 py-1 text-xs text-muted-foreground">
            <RefreshCw className="size-3" aria-hidden />
            {radarCase.freshness ? "Fresh" : "Stale"}
          </span>
        </div>
      )}
    </Link>
  );
}
