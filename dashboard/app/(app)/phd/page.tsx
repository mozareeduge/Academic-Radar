"use client";

import { useCallback, useEffect, useState } from "react";
import AuthGate from "@/components/AuthGate";
import { RadarCaseRow } from "@/components/RadarCaseRow";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, fetchRadarCases } from "@/lib/api";
import type { ApplicationRoute, RadarCase } from "@/types";

const ROUTES: Array<{ value: Exclude<ApplicationRoute, "MA_PROGRAMME">; label: string; description: string }> = [
  {
    value: "SUPERVISOR_FIRST_PHD",
    label: "Supervisor-first",
    description: "Cases where the route starts from a potential supervisor relationship.",
  },
  {
    value: "ADVERTISED_PHD",
    label: "Advertised",
    description: "Cases tied to a specific advertised doctoral opportunity.",
  },
  {
    value: "STRUCTURED_PHD",
    label: "Structured",
    description: "Cases for structured doctoral programmes and cohorts.",
  },
];

type PhdRoute = (typeof ROUTES)[number]["value"];

export default function PhdPage() {
  const [activeRoute, setActiveRoute] = useState<PhdRoute>("SUPERVISOR_FIRST_PHD");
  const [cases, setCases] = useState<RadarCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (route: PhdRoute) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchRadarCases({ application_route: route });
      setCases(result.items);
    } catch (err) {
      setCases([]);
      setError(err instanceof ApiError ? err.message : "Could not load PhD cases");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(activeRoute);
  }, [activeRoute, load]);

  const currentRoute = ROUTES.find((route) => route.value === activeRoute)!;

  return (
    <AuthGate>
      <div className="flex min-w-0 flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold">PhD</h1>
          <p className="mt-1 text-sm text-muted-foreground">Doctoral cases grouped by the backend application route.</p>
        </header>

        <div className="min-w-0 overflow-x-auto border-b border-border" role="tablist" aria-label="PhD application routes">
          <div className="flex min-w-max gap-1">
            {ROUTES.map((route) => (
              <Button
                key={route.value}
                type="button"
                role="tab"
                aria-selected={activeRoute === route.value}
                aria-controls="phd-route-panel"
                variant={activeRoute === route.value ? "default" : "ghost"}
                onClick={() => setActiveRoute(route.value)}
                className="shrink-0"
              >
                {route.label}
              </Button>
            ))}
          </div>
        </div>

        <section id="phd-route-panel" role="tabpanel" className="min-w-0" aria-label={`${currentRoute.label} PhD cases`}>
          <div className="mb-4">
            <h2 className="font-semibold">{currentRoute.label}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{currentRoute.description}</p>
          </div>

          {error && (
            <div role="alert" className="flex flex-col gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between">
              <span>{error}</span>
              <Button type="button" size="sm" variant="outline" onClick={() => void load(activeRoute)}>Retry</Button>
            </div>
          )}

          {loading && (
            <div className="space-y-2" aria-label="Loading PhD cases">
              {Array.from({ length: 3 }).map((_, index) => <Skeleton key={index} className="h-24 w-full" />)}
            </div>
          )}

          {!loading && !error && cases.length === 0 && (
            <div className="border border-border p-8 text-center text-sm text-muted-foreground">
              No {currentRoute.label.toLowerCase()} PhD cases found.
            </div>
          )}

          {!loading && !error && cases.length > 0 && (
            <div className="border border-border">
              {cases.map((radarCase) => <RadarCaseRow key={radarCase.id} case={radarCase} />)}
            </div>
          )}
        </section>
      </div>
    </AuthGate>
  );
}
