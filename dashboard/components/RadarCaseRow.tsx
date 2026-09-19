import type { RadarCase } from "@/types";

interface RadarCaseRowProps {
  case: RadarCase;
}

export function RadarCaseRow({ case: radarCase }: RadarCaseRowProps) {
  return (
    <div
      data-testid={`radar-case-${radarCase.id}`}
      className="flex flex-col gap-3 border-b border-border py-4 px-4 last:border-0"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1 flex-1 min-w-0">
          <h3 className="font-semibold text-foreground line-clamp-2">
            {radarCase.title}
          </h3>
          <p className="text-sm text-muted-foreground">{radarCase.route}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        {radarCase.blocker && (
          <span
            data-testid="chip"
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md bg-destructive/10 text-destructive border border-destructive/20"
          >
            {radarCase.blocker}
          </span>
        )}

        {radarCase.suggested_disposition && (
          <div className="inline-flex items-center gap-1">
            <span className="text-xs text-muted-foreground">
              System suggests:
            </span>
            <span
              data-testid="chip"
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md bg-blue/10 text-blue border border-blue/20"
            >
              {radarCase.suggested_disposition}
            </span>
          </div>
        )}

        {radarCase.user_disposition && (
          <div className="inline-flex items-center gap-1">
            <span className="text-xs text-muted-foreground">
              Your decision:
            </span>
            <span
              data-testid="chip"
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md bg-green/10 text-green border border-green/20"
            >
              {radarCase.user_disposition}
            </span>
          </div>
        )}

        {radarCase.deadline && (
          <span
            data-testid="chip"
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-muted-foreground"
          >
            {radarCase.deadline}
          </span>
        )}

        {radarCase.freshness && (
          <span className="text-xs text-muted-foreground">
            {radarCase.freshness}
          </span>
        )}
      </div>
    </div>
  );
}
