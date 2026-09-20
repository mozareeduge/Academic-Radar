"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";
import AuthGate from "@/components/AuthGate";
import { BlockerRegion } from "@/components/radar/BlockerRegion";
import { DecisionPanel } from "@/components/radar/DecisionPanel";
import { DeadlineDisplay } from "@/components/radar/DeadlineDisplay";
import { BriefTab } from "@/components/radar/BriefTab";
import { CoveragePanel } from "@/components/radar/CoveragePanel";
import { FundingPackages } from "@/components/radar/FundingPackages";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  fetchCase,
  fetchCoverage,
  fetchFunding,
  setUserDisposition,
  ApiError,
} from "@/lib/api";
import type { CaseDossier, CoverageResponse, FundingAssessment, UserDisposition } from "@/types";

export default function CaseDossierPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;

  const [caseData, setCaseData] = useState<CaseDossier | null>(null);
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const [funding, setFunding] = useState<FundingAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [secondaryErrors, setSecondaryErrors] = useState<string[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSecondaryErrors([]);
    try {
      const data = await fetchCase(caseId);
      setCaseData(data);

      const [coverageResult, fundingResult] = await Promise.allSettled([
        fetchCoverage(caseId),
        fetchFunding(caseId),
      ]);

      const nextSecondaryErrors: string[] = [];
      if (coverageResult.status === "fulfilled") {
        setCoverage(coverageResult.value);
      } else {
        setCoverage(null);
        const reason = coverageResult.reason;
        if (!(reason instanceof ApiError && reason.status === 404)) {
          nextSecondaryErrors.push("Research coverage could not be loaded.");
        }
      }

      if (fundingResult.status === "fulfilled") {
        setFunding(fundingResult.value.items);
      } else {
        setFunding([]);
        const reason = fundingResult.reason;
        if (!(reason instanceof ApiError && reason.status === 404)) {
          nextSecondaryErrors.push("Funding assessments could not be loaded.");
        }
      }
      setSecondaryErrors(nextSecondaryErrors);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load case");
      setCaseData(null);
      setCoverage(null);
      setFunding([]);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  const handleDispositionChange = async (disposition: UserDisposition) => {
    if (!caseData) return;
    setError(null);
    try {
      const updated = await setUserDisposition(caseId, disposition);
      setCaseData(updated);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not update disposition");
    }
  };

  return (
    <AuthGate>
      <div className="flex min-w-0 flex-col gap-6">
        <div>
          <Link href="/radar" className="inline-flex items-center gap-1 text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline">
            <ArrowLeft className="size-4" aria-hidden />
            Radar
          </Link>
        </div>

        {loading && (
          <div className="space-y-3" aria-label="Loading case">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-36 w-full" />
          </div>
        )}

        {error && (
          <div role="alert" className="flex flex-col gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            {!caseData && (
              <Button type="button" size="sm" variant="outline" onClick={() => void load()}>
                Retry
              </Button>
            )}
          </div>
        )}

        {!loading && caseData && (
          <>
            <header className="border-b border-border pb-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="min-w-0">
                  <h1 className="text-2xl font-semibold">Case dossier</h1>
                  <p className="mt-1 break-all font-mono text-xs text-muted-foreground">{caseData.id}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="border border-border bg-muted px-2 py-1 font-medium">{caseData.research_state}</span>
                  <span className="inline-flex items-center gap-1 border border-border px-2 py-1 text-muted-foreground">
                    <RefreshCw className="size-3" aria-hidden />
                    {caseData.freshness ? "Fresh" : "Stale"}
                  </span>
                </div>
              </div>
            </header>

            <BlockerRegion blockers={caseData.blockers} unknownCount={caseData.unknown_count} />

            <DecisionPanel
              suggestedDisposition={caseData.suggested_disposition}
              userDisposition={caseData.user_disposition}
              onDispositionChange={handleDispositionChange}
            />

            {caseData.deadline && caseData.deadline.original_text && (
              <section className="border border-border p-4" aria-labelledby="deadline-title">
                <h2 id="deadline-title" className="mb-2 text-sm font-semibold text-muted-foreground">Deadline</h2>
                <DeadlineDisplay deadline={caseData.deadline} />
              </section>
            )}

            {secondaryErrors.length > 0 && (
              <div role="status" className="border border-border bg-muted/30 p-3 text-sm text-muted-foreground">
                {secondaryErrors.join(" ")}
              </div>
            )}

            {coverage && (
              <CoveragePanel statuses={coverage.coverage} protocolVersion={coverage.protocol_version} />
            )}

            <FundingPackages assessments={funding} />

            <BriefTab caseId={caseId} caseData={caseData} />
          </>
        )}
      </div>
    </AuthGate>
  );
}
