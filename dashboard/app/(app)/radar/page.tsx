"use client";

import { useCallback, useEffect, useState } from "react";
import AuthGate from "@/components/AuthGate";
import { RadarCaseRow } from "@/components/RadarCaseRow";
import { fetchRadarQueue, ApiError } from "@/lib/api";
import type { RadarCase } from "@/types";

export default function RadarPage() {
  const [cases, setCases] = useState<RadarCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <AuthGate>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">Radar</h1>
          <p className="text-sm text-muted-foreground">
            {loading
              ? "Loading…"
              : `${cases.length} case${cases.length === 1 ? "" : "s"} in queue.`}
          </p>
        </div>

        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        )}

        {!loading && !error && cases.length === 0 && (
          <div className="rounded-md border p-8 text-center text-sm text-muted-foreground">
            No cases here yet.
          </div>
        )}

        {cases.length > 0 && (
          <div className="rounded-md border border-border">
            {cases.map((radarCase) => (
              <RadarCaseRow
                key={radarCase.id}
                case={radarCase}
              />
            ))}
          </div>
        )}
      </div>
    </AuthGate>
  );
}
