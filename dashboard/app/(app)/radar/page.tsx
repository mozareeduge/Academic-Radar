"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AuthGate from "@/components/AuthGate";
import { RadarCaseRow } from "@/components/RadarCaseRow";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchRadarQueue, ApiError } from "@/lib/api";
import type { RadarCase, ResearchState } from "@/types";

const STATE_FILTERS: Array<{ value: "ALL" | ResearchState; label: string }> = [
  { value: "ALL", label: "All" },
  { value: "EVIDENCE_READY", label: "Evidence ready" },
  { value: "RESEARCHING", label: "Researching" },
  { value: "STALE", label: "Stale" },
  { value: "FAILED", label: "Failed" },
];

export default function RadarPage() {
  const [cases, setCases] = useState<RadarCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stateFilter, setStateFilter] = useState<"ALL" | ResearchState>("ALL");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRadarQueue();
      setCases(data.items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load radar queue");
      setCases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  const visibleCases = useMemo(
    () => stateFilter === "ALL" ? cases : cases.filter((item) => item.research_state === stateFilter),
    [cases, stateFilter],
  );



  return (
    <AuthGate>
      <div className="flex min-w-0 flex-col gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">Radar</h1>
          <p className="text-sm text-muted-foreground">
            {loading
              ? "Loading cases…"
              : `${cases.length} case${cases.length === 1 ? "" : "s"} in queue.`}
          </p>
        </div>

        {!loading && cases.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-3" aria-label="Radar queue summary">
            <div className="border border-border bg-card p-3">
              <div className="text-2xl font-semibold">{cases.length}</div>
              <div className="text-xs text-muted-foreground">Total cases</div>
            </div>
            <div className="border border-border bg-card p-3">
              <div className="text-2xl font-semibold">
                {cases.filter((item) => item.research_state === "EVIDENCE_READY").length}
              </div>
              <div className="text-xs text-muted-foreground">Evidence ready</div>
            </div>
            <div className="border border-border bg-card p-3">
              <div className="text-2xl font-semibold">{cases.reduce((total, item) => total + item.unknown_count, 0)}</div>
              <div className="text-xs text-muted-foreground">Unknown claims</div>
            </div>
          </div>
        )}

        {cases.length > 0 && (
          <div className="flex min-w-0 gap-2 overflow-x-auto border-b border-border pb-2" role="group" aria-label="Filter radar cases by research state">
            {STATE_FILTERS.map((filter) => (
              <Button
                key={filter.value}
                type="button"
                size="sm"
                variant={stateFilter === filter.value ? "default" : "ghost"}
                onClick={() => setStateFilter(filter.value)}
                aria-pressed={stateFilter === filter.value}
                className="shrink-0"
              >
                {filter.label}
              </Button>
            ))}
          </div>
        )}

        {error && (
          <div role="alert" className="flex flex-col gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            <Button type="button" size="sm" variant="outline" onClick={() => void load()}>
              Retry
            </Button>
          </div>
        )}

        {loading && (
          <div className="space-y-2" aria-label="Loading radar cases">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-24 w-full" />
            ))}
          </div>
        )}

        {!loading && !error && cases.length === 0 && (
          <div className="border border-border p-8 text-center text-sm text-muted-foreground">
            No cases here yet.
          </div>
        )}

        {!loading && !error && cases.length > 0 && visibleCases.length === 0 && (
          <div className="border border-border p-6 text-center text-sm text-muted-foreground">
            No cases match this state filter.
          </div>
        )}

        {visibleCases.length > 0 && (
          <section aria-label="Radar cases" className="min-w-0 border border-border">
            {visibleCases.map((radarCase) => (
              <RadarCaseRow key={radarCase.id} case={radarCase} />
            ))}
          </section>
        )}
      </div>
    </AuthGate>
  );
}
