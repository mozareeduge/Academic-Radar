import type { CaseBlocker } from "@/types";

interface BlockerRegionProps {
  blockers: CaseBlocker[];
  unknownCount: number;
}

export function BlockerRegion({ blockers, unknownCount }: BlockerRegionProps) {
  return (
    <section aria-label="Formal blockers" className="border border-border p-4">
      {blockers.length > 0 ? (
        <div className="flex flex-col gap-3">
          <h2 className="font-semibold text-destructive">Formal blockers</h2>
          {blockers.map((blocker, i) => (
            <div key={i} className="flex items-start gap-3">
              <span className="font-medium text-destructive" aria-hidden="true">✕</span>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground">{blocker.name ?? "Formal blocker"}</p>
                {blocker.reason && (
                  <p className="text-sm text-muted-foreground">{blocker.reason}</p>
                )}
              </div>
            </div>
          ))}
          {unknownCount > 0 && (
            <p className="text-sm text-muted-foreground">
              {unknownCount} unresolved claim{unknownCount === 1 ? "" : "s"} also remain.
            </p>
          )}
        </div>
      ) : unknownCount > 0 ? (
        <p className="text-sm text-muted-foreground">Eligibility unknown</p>
      ) : (
        <p className="text-sm text-muted-foreground">No formal blockers found</p>
      )}
    </section>
  );
}
