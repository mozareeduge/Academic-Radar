"use client";

import { useRef, useState } from "react";
import { FileCheck2, Loader2, RefreshCw } from "lucide-react";
import type { Brief, CaseDossier } from "@/types";
import { freezeBrief, fetchBrief, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { EvidenceInspector } from "@/components/radar/EvidenceInspector";

interface BriefTabProps {
  caseId: string;
  caseData: CaseDossier | null;
}

export function BriefTab({ caseId, caseData }: BriefTabProps) {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [blockReasons, setBlockReasons] = useState<string[]>([]);
  const [freezing, setFreezing] = useState(false);
  const [claimId, setClaimId] = useState<string | null>(null);
  const evidenceInvokerRef = useRef<HTMLButtonElement | null>(null);

  const handleFreezeBrief = async () => {
    setFreezing(true);
    setError(null);
    setBlockReasons([]);
    try {
      const result = await freezeBrief(caseId);
      try {
        setBrief(await fetchBrief(result.id));
      } catch {
        setBrief({
          id: result.id,
          case_id: result.case_id,
          frozen_at: result.frozen_at,
          state: result.state,
          superseded: false,
          content: null,
        });
      }
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        const headers = e.details?.headers as Record<string, unknown> | undefined;
        const reasonsHeader = headers?.["x-brief-blocked-reasons"];
        if (typeof reasonsHeader === "string") {
          setBlockReasons(reasonsHeader.split("; ").filter(Boolean));
        }
        setError(e.message || "Brief cannot be frozen from the current evidence state");
      } else {
        setError(e instanceof ApiError ? e.message : "Could not freeze brief");
      }
    } finally {
      setFreezing(false);
    }
  };

  const reasons = caseData?.brief_block_reasons ?? [];
  const disabledReason = caseData ? reasons[0] ?? null : "Case data not loaded";

  return (
    <section className="border border-border" aria-labelledby="application-brief-title">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border bg-muted/50 px-4 py-3">
        <div>
          <h2 id="application-brief-title" className="font-semibold">Application Brief</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            The backend decides whether the current evidence can be frozen.
          </p>
        </div>
        {caseData && (
          <span className="text-xs text-muted-foreground">
            Case state: {caseData.research_state}
          </span>
        )}
      </div>

      <div className="p-4">
        {error && (
          <div role="alert" className="mb-4 border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {blockReasons.length > 0 && (
          <div className="mb-4 border border-border bg-muted/40 p-3">
            <h3 className="text-sm font-semibold">Backend blocking reasons</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
              {blockReasons.map((reason) => <li key={reason}>{reason}</li>)}
            </ul>
          </div>
        )}

        {!brief ? (
          <div className="flex flex-col items-start gap-3">
            <p className="max-w-2xl text-sm text-muted-foreground">
              Freeze the current evidence into an application-preparation brief. This action does not deliver anything to anyone.
            </p>
            {disabledReason && (
              <div data-testid="brief-disabled-reason" role="status" className="text-sm text-muted-foreground">
                {reasons.length ? (
                  <ul className="list-disc pl-5">
                    {reasons.map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
                ) : disabledReason}
              </div>
            )}
            <Button type="button" onClick={() => void handleFreezeBrief()} disabled={!!disabledReason || freezing}>
              {freezing ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <FileCheck2 className="size-4" aria-hidden />}
              {freezing ? "Freezing…" : "Prepare evidence brief"}
            </Button>
          </div>
        ) : (
          <div className="space-y-5">
            {brief.superseded && (
              <div className="border border-destructive/30 bg-destructive/10 p-3">
                <h3 className="text-sm font-semibold text-destructive">Superseded</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Current case dependencies changed after this brief was frozen.
                </p>
                <Button className="mt-3" type="button" size="sm" variant="outline" onClick={() => void handleFreezeBrief()} disabled={freezing}>
                  <RefreshCw className="size-3.5" aria-hidden />
                  Generate updated brief
                </Button>
              </div>
            )}

            <dl className="grid gap-3 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-xs text-muted-foreground">Brief</dt>
                <dd className="mt-1 break-all font-mono">{brief.id}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">State</dt>
                <dd className="mt-1 font-medium">{brief.state}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Frozen at</dt>
                <dd className="mt-1">{brief.frozen_at ? new Date(brief.frozen_at).toLocaleString() : "Unknown"}</dd>
              </div>
            </dl>

            {!brief.content && (
              <p className="border border-border p-3 text-sm text-muted-foreground">
                The brief was frozen, but detailed brief content was not available in the follow-up response.
              </p>
            )}

            {brief.content?.claims && brief.content.claims.length > 0 && (
              <section aria-labelledby="brief-evidence-title">
                <h3 id="brief-evidence-title" className="text-sm font-semibold">Supporting evidence</h3>
                <div className="mt-2 divide-y divide-border border border-border">
                  {brief.content.claims.map((claim) => (
                    <article key={claim.id} className="p-3">
                      <p className="text-sm font-medium">{claim.statement}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        <span>{claim.claim_type}</span>
                        <span>·</span>
                        <span>{claim.status}</span>
                        <span>·</span>
                        <span>{claim.evidence_ids.length} evidence</span>
                        <button
                          ref={claimId === claim.id ? evidenceInvokerRef : undefined}
                          type="button"
                          className="ml-auto font-medium text-primary underline-offset-4 hover:underline"
                          onClick={(event) => {
                            evidenceInvokerRef.current = event.currentTarget;
                            setClaimId(claim.id);
                          }}
                        >
                          Inspect evidence
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            )}

            {brief.content?.gates && brief.content.gates.length > 0 && (
              <section aria-labelledby="brief-gates-title">
                <h3 id="brief-gates-title" className="text-sm font-semibold">Formal gates</h3>
                <div className="mt-2 divide-y divide-border border border-border">
                  {brief.content.gates.map((gate) => (
                    <div key={gate.id} className="flex flex-col gap-1 p-3 text-sm sm:flex-row sm:items-center sm:justify-between">
                      <span className="font-medium">{gate.requirement}</span>
                      <span className="text-xs text-muted-foreground">{gate.result}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {brief.content?.dimensions && brief.content.dimensions.length > 0 && (
              <section aria-labelledby="brief-dimensions-title">
                <h3 id="brief-dimensions-title" className="text-sm font-semibold">Assessments</h3>
                <div className="mt-2 divide-y divide-border border border-border">
                  {brief.content.dimensions.map((dimension) => (
                    <div key={dimension.id} className="flex items-center justify-between gap-3 p-3 text-sm">
                      <span>{dimension.dimension_id}</span>
                      <span className="font-mono text-muted-foreground">{dimension.value === null ? "Unknown" : dimension.value}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {brief.content?.funding_assessments && brief.content.funding_assessments.length > 0 && (
              <section aria-labelledby="brief-funding-title">
                <h3 id="brief-funding-title" className="text-sm font-semibold">Funding</h3>
                <div className="mt-2 divide-y divide-border border border-border">
                  {brief.content.funding_assessments.map((funding) => (
                    <div key={funding.id} className="flex flex-col gap-1 p-3 text-sm sm:flex-row sm:items-center sm:justify-between">
                      <span className="break-all">{funding.funding_route_id}</span>
                      <span className="font-mono text-muted-foreground">
                        {funding.award_amount ?? "Unknown"} {funding.currency}
                      </span>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>

      {claimId && (
        <EvidenceInspector
          claimId={claimId}
          isOpen={true}
          onClose={() => setClaimId(null)}
          invokerRef={evidenceInvokerRef}
        />
      )}
    </section>
  );
}
