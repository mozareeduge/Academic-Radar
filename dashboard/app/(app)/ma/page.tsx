"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowRight, Loader2 } from "lucide-react";
import AuthGate from "@/components/AuthGate";
import { FundingPackages } from "@/components/radar/FundingPackages";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, fetchFunding, fetchRadarCases } from "@/lib/api";
import type { FundingAssessment, RadarCase } from "@/types";

export default function MaPage() {
  const [cases, setCases] = useState<RadarCase[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [funding, setFunding] = useState<FundingAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [fundingLoading, setFundingLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fundingError, setFundingError] = useState<string | null>(null);

  const loadCases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchRadarCases({ application_route: "MA_PROGRAMME" });
      setCases(result.items);
      setSelectedCaseId((current) => current ?? result.items[0]?.id ?? null);
    } catch (err) {
      setCases([]);
      setSelectedCaseId(null);
      setError(err instanceof ApiError ? err.message : "Could not load MA cases");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadCases();
  }, [loadCases]);

  useEffect(() => {
    if (!selectedCaseId) {
      // Deferred (not synchronous) to satisfy react-hooks/set-state-in-effect.
      queueMicrotask(() => setFunding([]));
      return;
    }

    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      setFundingLoading(true);
      setFundingError(null);
    });
    fetchFunding(selectedCaseId)
      .then((result) => {
        if (!cancelled) setFunding(result.items);
      })
      .catch((err) => {
        if (!cancelled) {
          setFunding([]);
          setFundingError(err instanceof ApiError ? err.message : "Could not load funding assessments");
        }
      })
      .finally(() => {
        if (!cancelled) setFundingLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedCaseId]);

  return (
    <AuthGate>
      <div className="flex min-w-0 flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold">MA + Funding</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            MA programme cases and their backend funding assessments, kept as separate evidence-backed records.
          </p>
        </header>

        {error && (
          <div role="alert" className="flex flex-col gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            <Button type="button" size="sm" variant="outline" onClick={() => void loadCases()}>Retry</Button>
          </div>
        )}

        {loading && (
          <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.4fr)]">
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        )}

        {!loading && !error && cases.length === 0 && (
          <div className="border border-border p-8 text-center text-sm text-muted-foreground">
            No MA programme cases found.
          </div>
        )}

        {!loading && !error && cases.length > 0 && (
          <div className="grid min-w-0 gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.4fr)]">
            <section className="min-w-0" aria-labelledby="ma-cases-title">
              <h2 id="ma-cases-title" className="mb-3 font-semibold">MA cases</h2>
              <div className="divide-y divide-border border border-border">
                {cases.map((radarCase) => {
                  const selected = selectedCaseId === radarCase.id;
                  return (
                    <button
                      key={radarCase.id}
                      type="button"
                      onClick={() => setSelectedCaseId(radarCase.id)}
                      aria-pressed={selected}
                      className={`block w-full p-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset ${selected ? "bg-muted" : "hover:bg-muted/50"}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="font-medium">Case {radarCase.id}</div>
                          <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
                            <span>{radarCase.research_state}</span>
                            <span>·</span>
                            <span>{radarCase.user_disposition}</span>
                          </div>
                        </div>
                        <ArrowRight className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="min-w-0" aria-labelledby="ma-funding-title">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 id="ma-funding-title" className="font-semibold">Funding for selected case</h2>
                {selectedCaseId && (
                  <Link href={`/cases/${encodeURIComponent(selectedCaseId)}`} className="text-sm font-medium text-primary underline-offset-4 hover:underline">
                    Open case dossier
                  </Link>
                )}
              </div>

              {fundingLoading ? (
                <div className="flex items-center gap-2 border border-border p-4 text-sm text-muted-foreground" role="status">
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                  Loading funding assessments…
                </div>
              ) : fundingError ? (
                <div role="alert" className="border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                  {fundingError}
                </div>
              ) : (
                <FundingPackages assessments={funding} />
              )}
            </section>
          </div>
        )}
      </div>
    </AuthGate>
  );
}
