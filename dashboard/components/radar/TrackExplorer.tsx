import Link from "next/link";
import { Info } from "lucide-react";

interface TrackExplorerProps {
  caseId: string;
}

/**
 * Production-safe boundary for the legacy "supervision precedents" surface.
 *
 * The production Radar API currently exposes case evidence/coverage but no
 * `/cases/{id}/precedents` resource. Keep this component non-fetching so it
 * cannot silently reintroduce a fixture-only contract. When a precedents
 * endpoint becomes part of OpenAPI, this surface can be wired through
 * `dashboard/lib/api.ts`.
 */
export function TrackExplorer({ caseId }: TrackExplorerProps) {
  return (
    <section className="border border-border bg-muted/30 p-4" aria-label="Supervision precedent availability">
      <div className="flex items-start gap-3">
        <Info className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
        <div className="min-w-0">
          <h3 className="text-sm font-semibold">Supervision precedents are not exposed by the production Radar API</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            This case can use its production evidence and coverage views; precedent records are intentionally not fabricated in the client.
          </p>
          <Link
            href={`/cases/${encodeURIComponent(caseId)}`}
            className="mt-2 inline-block text-sm font-medium text-primary underline-offset-4 hover:underline"
          >
            Return to case evidence
          </Link>
        </div>
      </div>
    </section>
  );
}
