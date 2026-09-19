"use client";

import { useState } from "react";
import type { Brief, CaseDossier } from "@/types";
import { freezeBrief, ApiError } from "@/lib/api";

interface BriefTabProps {
  caseId: string;
  caseData: CaseDossier | null;
}

export function BriefTab({ caseId, caseData }: BriefTabProps) {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [blockReasons, setBlockReasons] = useState<string[]>([]);
  const [freezing, setFreezing] = useState(false);

  const handleFreezeBrief = async () => {
    setFreezing(true);
    setError(null);
    setBlockReasons([]);
    try {
      const result = await freezeBrief(caseId);
      const newBrief: Brief = {
        id: result.id,
        case_id: result.case_id,
        frozen_at: result.frozen_at,
        state: "DRAFT",
        superseded: false,
        content: null,
      };
      setBrief(newBrief);
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) {
          const reasonsHeader = (e.details?.headers as Record<string, unknown> | undefined)?.["x-brief-blocked-reasons"];
          if (typeof reasonsHeader === "string") {
            setBlockReasons(reasonsHeader.split("; "));
          }
          setError("Brief cannot be frozen: stale or unknown critical facts");
        } else {
          setError(e.message);
        }
      } else {
        setError("Could not freeze brief");
      }
    } finally {
      setFreezing(false);
    }
  };


  const briefDisabledReason = (): string | null => {
    if (!caseData) return "Case data not loaded";
    if (caseData.blockers.length > 0) return "Formal blockers must be resolved";
    if (caseData.unknown_count > 0) return "Unknown facts must be resolved";
    if (!caseData.freshness) return "Critical facts need rechecking";
    return null;
  };

  const disabledReason = briefDisabledReason();

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-md border border-border p-4">
        <h2 className="text-lg font-semibold mb-4">Application Brief</h2>

        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 mb-4 text-sm text-destructive">
            {error}
          </div>
        )}

        {blockReasons.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-4 mb-4">
            <h3 className="text-sm font-semibold text-amber-900 mb-2">
              Brief cannot be frozen
            </h3>
            <ul className="text-sm text-amber-800 space-y-1 list-disc list-inside">
              {blockReasons.map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>
          </div>
        )}

        {!brief ? (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">
              Generate a brief to freeze the current evidence and prepare for application.
            </p>
            <button
              onClick={handleFreezeBrief}
              disabled={!!disabledReason || freezing}
              className="inline-flex items-center justify-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {freezing ? "Freezing…" : "Prepare evidence brief"}
            </button>
            {disabledReason && (
              <p className="text-xs text-muted-foreground">{disabledReason}</p>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {brief.superseded && (
              <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
                <h3 className="text-sm font-semibold text-amber-900">
                  Superseded
                </h3>
                <p className="text-sm text-amber-800 mt-1">
                  This brief is older than the current case evidence. Case changes after this brief was generated.
                </p>
                <button
                  onClick={handleFreezeBrief}
                  disabled={!!disabledReason || freezing}
                  className="mt-3 inline-flex items-center justify-center px-3 py-1 text-sm bg-amber-900 text-amber-50 rounded hover:bg-amber-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {freezing ? "Generating…" : "Generate updated brief"}
                </button>
              </div>
            )}

            <div className="text-xs text-muted-foreground">
              Frozen at {brief.frozen_at ? new Date(brief.frozen_at).toLocaleString() : "unknown"}
            </div>

            {brief.content && (
              <div className="flex flex-col gap-4">
                {brief.content.claims.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-semibold">Supporting Evidence</h3>
                    <div className="space-y-2 max-h-96 overflow-auto">
                      {brief.content.claims.map((claim) => (
                        <div
                          key={claim.id}
                          className="p-3 bg-muted rounded-sm border border-border"
                        >
                          <p className="text-sm font-medium">{claim.statement}</p>
                          <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                            <span>Evidence: {claim.evidence_ids.length}</span>
                            <span>Type: {claim.claim_type}</span>
                            <span>Status: {claim.status}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {brief.content.gates.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-semibold">Formal Gates</h3>
                    <div className="space-y-2 max-h-48 overflow-auto">
                      {brief.content.gates.map((gate) => (
                        <div
                          key={gate.id}
                          className="p-2 bg-muted rounded-sm border border-border text-sm"
                        >
                          <p className="font-medium">{gate.requirement}</p>
                          <p className="text-xs text-muted-foreground">Result: {gate.result}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {brief.content.dimensions.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-semibold">Assessments</h3>
                    <div className="space-y-1 text-sm">
                      {brief.content.dimensions.map((dim) => (
                        <div
                          key={dim.id}
                          className="flex justify-between text-xs"
                        >
                          <span>{dim.dimension_id}</span>
                          <span className="text-muted-foreground">
                            {dim.value !== null ? `${dim.value}/3` : "Unknown"}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {brief.content.funding_assessments.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <h3 className="text-sm font-semibold">Funding</h3>
                    <div className="space-y-1 text-sm">
                      {brief.content.funding_assessments.map((fa) => (
                        <div
                          key={fa.id}
                          className="flex justify-between text-xs"
                        >
                          <span>{fa.funding_route_id}</span>
                          <span className="text-muted-foreground">
                            {fa.award_amount} {fa.currency}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
