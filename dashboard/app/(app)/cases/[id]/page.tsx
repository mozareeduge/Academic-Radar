"use client";

import { useCallback, useEffect, useState } from "react";
import AuthGate from "@/components/AuthGate";
import { BlockerRegion } from "@/components/radar/BlockerRegion";
import { DecisionPanel } from "@/components/radar/DecisionPanel";
import { GatesTable } from "@/components/radar/GatesTable";
import { DimensionsTable } from "@/components/radar/DimensionsTable";
import { DeadlineDisplay } from "@/components/radar/DeadlineDisplay";
import { TrackExplorer } from "@/components/radar/TrackExplorer";
import { fetchCase, setUserDisposition, ApiError } from "@/lib/api";
import type { CaseDossier } from "@/types";

interface Props {
  params: { id: string };
}

export default function CaseDossierPage({ params }: Props) {
  const caseId = params.id;

  const [caseData, setCaseData] = useState<CaseDossier | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCase(caseId);
      setCaseData(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load case");
      setCaseData(null);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  const handleDispositionChange = async (disposition: string) => {
    if (!caseData) return;
    try {
      const updated = await setUserDisposition(caseId, disposition);
      setCaseData(updated);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not update disposition");
    }
  };

  return (
    <AuthGate>
      <main className="flex flex-col gap-6">
        {loading && (
          <div className="text-center text-muted-foreground">Loading case…</div>
        )}

        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        )}

        {!loading && caseData && (
          <>
            <div className="flex flex-col gap-1">
              <h1 className="text-2xl font-semibold">Case Details</h1>
              <p className="text-sm text-muted-foreground">{caseData.id}</p>
            </div>

            <BlockerRegion
              blockers={caseData.blockers}
              unknownCount={caseData.unknown_count}
            />

            <DecisionPanel
              suggestedDisposition={caseData.suggested_disposition}
              userDisposition={caseData.user_disposition}
              onDispositionChange={handleDispositionChange}
            />

            {caseData.deadline && (
              <div className="rounded-md border border-border p-4">
                <h2 className="text-sm font-semibold text-muted-foreground mb-2">
                  Deadline
                </h2>
                <DeadlineDisplay deadline={caseData.deadline} />
              </div>
            )}

            {caseData.gates.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold mb-4">Gates</h2>
                <GatesTable gates={caseData.gates} />
              </div>
            )}

            {caseData.dimensions.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold mb-4">Dimensions</h2>
                <DimensionsTable dimensions={caseData.dimensions} />
              </div>
            )}

            <div className="rounded-md border border-border p-4">
              <h2 className="text-lg font-semibold mb-4">Track Explorer</h2>
              <TrackExplorer caseId={caseId} />
            </div>
          </>
        )}
      </main>
    </AuthGate>
  );
}
