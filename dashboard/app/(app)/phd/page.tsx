"use client";

import { useCallback, useEffect, useState } from "react";
import AuthGate from "@/components/AuthGate";
import { apiBase, getToken, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { RadarCase, Paginated } from "@/types";

type ApplicationRoute = "supervisor-first" | "advertised" | "structured";

async function fetchCases(
  params: { application_route: ApplicationRoute }
): Promise<Paginated<RadarCase>> {
  const qs = new URLSearchParams();
  qs.set("application_route", params.application_route);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${apiBase()}/api/radar/cases?${qs.toString()}`, {
    headers,
    credentials: "include",
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const rawDetail = (data as { detail?: unknown })?.detail;
    let message: string;
    if (typeof rawDetail === "string") {
      message = rawDetail;
    } else if (Array.isArray(rawDetail)) {
      message = rawDetail
        .map((entry) => {
          if (entry && typeof entry === "object" && "msg" in entry) {
            return String((entry as { msg: unknown }).msg);
          }
          return String(entry);
        })
        .filter(Boolean)
        .join("; ");
    } else if (typeof data === "string") {
      message = data;
    } else {
      message = `Request failed (${res.status})`;
    }
    throw new ApiError(message || `Request failed (${res.status})`, res.status);
  }

  return data as Paginated<RadarCase>;
}

export default function PhdPage() {
  const [activeTab, setActiveTab] = useState<ApplicationRoute>("supervisor-first");
  const [cases, setCases] = useState<RadarCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (route: ApplicationRoute) => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchCases({ application_route: route });
        setCases(data.items);
      } catch (e) {
        setError(e instanceof ApiError ? e.message : "Could not load cases");
        setCases([]);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(activeTab);
  }, [activeTab, load]);

  const dimensions = [
    "Admission Viability",
    "Funding",
    "Strategic Value",
    "Research Alignment",
    "Supervisor Capacity",
    "Timeline Feasibility",
    "Personal Development Fit",
  ];

  return (
    <AuthGate>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">PhD</h1>
          <p className="text-sm text-muted-foreground">
            Doctoral opportunities filtered by application route
          </p>
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex gap-2 border-b border-border">
            <Button
              variant={activeTab === "supervisor-first" ? "default" : "ghost"}
              onClick={() => setActiveTab("supervisor-first")}
              role="tab"
              aria-selected={activeTab === "supervisor-first"}
              className="rounded-b-none"
            >
              Supervisor-first
            </Button>
            <Button
              variant={activeTab === "advertised" ? "default" : "ghost"}
              onClick={() => setActiveTab("advertised")}
              role="tab"
              aria-selected={activeTab === "advertised"}
              className="rounded-b-none"
            >
              Advertised
            </Button>
            <Button
              variant={activeTab === "structured" ? "default" : "ghost"}
              onClick={() => setActiveTab("structured")}
              role="tab"
              aria-selected={activeTab === "structured"}
              className="rounded-b-none"
            >
              Structured
            </Button>
          </div>

          {activeTab === "supervisor-first" && (
            <div className="space-y-4">
            {error && (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                {error}
              </div>
            )}

            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : cases.length === 0 ? (
              <div className="rounded-md border p-8 text-center text-sm text-muted-foreground">
                No supervisor-first PhD cases found
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-border text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Title
                      </th>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Research State
                      </th>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Route
                      </th>
                      {dimensions.map((dim) => (
                        <th
                          key={dim}
                          className="border border-border px-3 py-2 text-left font-semibold"
                        >
                          {dim}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cases.map((c) => (
                      <tr key={c.id} className="hover:bg-muted/50">
                        <td className="border border-border px-3 py-2">{c.title}</td>
                        <td className="border border-border px-3 py-2">{c.research_state || "—"}</td>
                        <td className="border border-border px-3 py-2">{c.route || "—"}</td>
                        {dimensions.map((dim) => (
                          <td key={dim} className="border border-border px-3 py-2 text-center">
                            —
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            </div>
          )}

          {activeTab === "advertised" && (
            <div className="space-y-4">
            {error && (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                {error}
              </div>
            )}

            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : cases.length === 0 ? (
              <div className="rounded-md border p-8 text-center text-sm text-muted-foreground">
                No advertised PhD cases found
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-border text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Title
                      </th>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Research State
                      </th>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Route
                      </th>
                      {dimensions.map((dim) => (
                        <th
                          key={dim}
                          className="border border-border px-3 py-2 text-left font-semibold"
                        >
                          {dim}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cases.map((c) => (
                      <tr key={c.id} className="hover:bg-muted/50">
                        <td className="border border-border px-3 py-2">{c.title}</td>
                        <td className="border border-border px-3 py-2">{c.research_state || "—"}</td>
                        <td className="border border-border px-3 py-2">{c.route || "—"}</td>
                        {dimensions.map((dim) => (
                          <td key={dim} className="border border-border px-3 py-2 text-center">
                            —
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            </div>
          )}

          {activeTab === "structured" && (
            <div className="space-y-4">
            {error && (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                {error}
              </div>
            )}

            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : cases.length === 0 ? (
              <div className="rounded-md border p-8 text-center text-sm text-muted-foreground">
                No structured PhD cases found
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-border text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Title
                      </th>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Research State
                      </th>
                      <th className="border border-border px-3 py-2 text-left font-semibold">
                        Route
                      </th>
                      {dimensions.map((dim) => (
                        <th
                          key={dim}
                          className="border border-border px-3 py-2 text-left font-semibold"
                        >
                          {dim}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cases.map((c) => (
                      <tr key={c.id} className="hover:bg-muted/50">
                        <td className="border border-border px-3 py-2">{c.title}</td>
                        <td className="border border-border px-3 py-2">{c.research_state || "—"}</td>
                        <td className="border border-border px-3 py-2">{c.route || "—"}</td>
                        {dimensions.map((dim) => (
                          <td key={dim} className="border border-border px-3 py-2 text-center">
                            —
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            </div>
          )}
        </div>
      </div>
    </AuthGate>
  );
}
