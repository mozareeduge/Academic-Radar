"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import AuthGate from "@/components/AuthGate";
import { RadarCaseRow } from "@/components/RadarCaseRow";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, fetchRadarCases } from "@/lib/api";
import type { RadarCase } from "@/types";

export default function SupervisorsRadarPage() {
  const [cases, setCases] = useState<RadarCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchRadarCases({ application_route: "SUPERVISOR_FIRST_PHD" });
      setCases(result.items);
    } catch (err) {
      setCases([]);
      setError(err instanceof ApiError ? err.message : "Could not load supervisor-first cases");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  return (
    <AuthGate>
      <div className="flex min-w-0 flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold">Supervisors</h1>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            The production Radar API currently exposes supervisor-first evaluation cases, not supervisor target metadata. This view stays inside that contract and opens each case dossier for evidence and decision work.
          </p>
          <Link href="/supervisors" className="mt-2 inline-block text-sm font-medium text-primary underline-offset-4 hover:underline">
            Open legacy supervisor directory
          </Link>
        </header>

        {error && (
          <div role="alert" className="flex flex-col gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            <Button type="button" size="sm" variant="outline" onClick={() => void load()}>Retry</Button>
          </div>
        )}

        {loading && (
          <div className="space-y-2" aria-label="Loading supervisor-first cases">
            {Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} className="h-24 w-full" />)}
          </div>
        )}

        {!loading && !error && cases.length === 0 && (
          <div className="border border-border p-8 text-center text-sm text-muted-foreground">
            No supervisor-first cases found.
          </div>
        )}

        {!loading && !error && cases.length > 0 && (
          <section aria-label="Supervisor-first cases" className="border border-border">
            {cases.map((radarCase) => <RadarCaseRow key={radarCase.id} case={radarCase} />)}
          </section>
        )}
      </div>
    </AuthGate>
  );
}
