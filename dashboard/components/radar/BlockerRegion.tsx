import type { CaseBlocker } from "@/types";

interface BlockerRegionProps {
  blockers: CaseBlocker[];
  unknownCount: number;
}

export function BlockerRegion({ blockers, unknownCount }: BlockerRegionProps) {
  return (
    <section aria-label="Formal blockers" className="rounded-md border border-border p-4 mb-6">
      {blockers.length > 0 ? (
        <div className="flex flex-col gap-3">
          <h2 className="font-semibold text-destructive">Formal blockers</h2>
          {blockers.map((blocker, i) => (
            <div key={i} className="flex items-start gap-3">
              <span className="text-destructive font-medium">✕</span>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground">{blocker.name}</p>
                {blocker.reason && (
                  <p className="text-sm text-muted-foreground">{blocker.reason}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : unknownCount > 0 ? (
        <p className="text-sm text-muted-foreground">Eligibility unknown</p>
      ) : (
        <p className="text-sm text-muted-foreground">No formal blockers found</p>
      )}
    </section>
  );
}
