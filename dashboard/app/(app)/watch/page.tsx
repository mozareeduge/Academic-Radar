"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ExternalLink, Loader2, RefreshCw, TriangleAlert } from "lucide-react";
import AuthGate from "@/components/AuthGate";
import { Button } from "@/components/ui/button";
import { ApiError, fetchChangeEvents, fetchWatchTargets, postResearch } from "@/lib/api";
import type { ChangeEvent, ChangeEventsResponse, WatchTarget } from "@/types";

export default function WatchPage() {
  const [changes, setChanges] = useState<ChangeEventsResponse>({ items: [] });
  const [targets, setTargets] = useState<WatchTarget[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rerunLoading, setRerunLoading] = useState<Record<string, boolean>>({});
  const [rerunStatus, setRerunStatus] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [changeResult, targetResult] = await Promise.allSettled([
      fetchChangeEvents(),
      fetchWatchTargets(),
    ]);

    const errors: string[] = [];
    if (changeResult.status === "fulfilled") setChanges(changeResult.value);
    else {
      setChanges({ items: [] });
      errors.push(changeResult.reason instanceof ApiError ? changeResult.reason.message : "Could not load change events");
    }

    if (targetResult.status === "fulfilled") setTargets(targetResult.value.items);
    else {
      setTargets([]);
      errors.push(targetResult.reason instanceof ApiError ? targetResult.reason.message : "Could not load watch targets");
    }

    setError(errors.length > 0 ? errors.join(" ") : null);
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const handleRerun = async (caseId: string) => {
    setRerunLoading((prev) => ({ ...prev, [caseId]: true }));
    setRerunStatus((prev) => ({ ...prev, [caseId]: "" }));
    try {
      const result = await postResearch(caseId);
      setRerunStatus((prev) => ({ ...prev, [caseId]: `Research queued · ${result.run_id}` }));
    } catch (err) {
      setRerunStatus((prev) => ({
        ...prev,
        [caseId]: err instanceof ApiError ? err.message : "Research could not be queued",
      }));
    } finally {
      setRerunLoading((prev) => ({ ...prev, [caseId]: false }));
    }
  };

  return (
    <AuthGate>
      <div className="flex min-w-0 flex-col gap-7">
        <header>
          <h1 className="text-2xl font-semibold">Watch</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Monitored targets, material source changes, and the cases the backend marks as impacted.
          </p>
        </header>

        {error && (
          <div role="alert" className="flex flex-col gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive sm:flex-row sm:items-center sm:justify-between">
            <span>{error}</span>
            <Button type="button" size="sm" variant="outline" onClick={() => void load()}>Retry</Button>
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground" role="status">
            <Loader2 className="size-4 animate-spin" aria-hidden />
            Loading watch data…
          </div>
        ) : (
          <>
            <section aria-labelledby="watch-targets-title">
              <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
                <div>
                  <h2 id="watch-targets-title" className="text-lg font-semibold">Watch targets</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{targets.length} monitored target{targets.length === 1 ? "" : "s"}.</p>
                </div>
              </div>
              {targets.length === 0 ? (
                <div className="border border-border p-4 text-sm text-muted-foreground">No production watch targets are configured.</div>
              ) : (
                <div className="divide-y divide-border border border-border">
                  {targets.map((target) => (
                    <div key={target.id} className="flex flex-col gap-2 p-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium">{target.target_id}</span>
                          <span className="border border-border bg-muted px-2 py-0.5 text-xs">{target.state}</span>
                          <span className="text-xs text-muted-foreground">{target.cadence}</span>
                        </div>
                        <div className="mt-1 truncate text-xs text-muted-foreground" title={target.url}>{target.url}</div>
                      </div>
                      <a href={target.url} target="_blank" rel="noopener noreferrer" className="inline-flex shrink-0 items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline">
                        Open source <ExternalLink className="size-3.5" aria-hidden />
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section aria-labelledby="recent-changes-title">
              <div className="mb-3">
                <h2 id="recent-changes-title" className="text-lg font-semibold">Recent changes</h2>
                <p className="mt-1 text-sm text-muted-foreground">Only backend-reported change summaries and impacted case IDs are shown.</p>
              </div>

              {changes.items.length === 0 ? (
                <div className="border border-border p-4 text-sm text-muted-foreground">No change events recorded.</div>
              ) : (
                <div className="space-y-3">
                  {changes.items.map((event: ChangeEvent) => (
                    <article key={event.id} className="border border-border bg-card p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            {event.material && <TriangleAlert className="size-4 text-destructive" aria-hidden />}
                            <h3 className="font-medium">{event.summary}</h3>
                          </div>
                          <time className="mt-1 block text-xs text-muted-foreground" dateTime={event.at}>
                            {new Date(event.at).toLocaleString()}
                          </time>
                        </div>
                        <span className="border border-border bg-muted px-2 py-1 text-xs font-medium">
                          {event.material ? "Material change" : "Non-material change"}
                        </span>
                      </div>

                      {event.impacted_cases.length > 0 ? (
                        <div className="mt-4">
                          <p className="text-sm font-medium">Impacted cases:</p>
                          <div className="mt-2 divide-y divide-border border border-border">
                            {event.impacted_cases.map((caseId) => (
                              <div key={caseId} className="flex flex-col gap-2 p-3 sm:flex-row sm:items-center sm:justify-between">
                                <div className="min-w-0">
                                  <Link href={`/cases/${encodeURIComponent(caseId)}`} className="break-all font-mono text-sm font-medium underline-offset-4 hover:underline">
                                    {caseId}
                                  </Link>
                                  {rerunStatus[caseId] && (
                                    <p className="mt-1 break-all text-xs text-muted-foreground" role="status">{rerunStatus[caseId]}</p>
                                  )}
                                </div>
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="outline"
                                  onClick={() => void handleRerun(caseId)}
                                  disabled={rerunLoading[caseId]}
                                >
                                  {rerunLoading[caseId] ? <Loader2 className="size-3.5 animate-spin" aria-hidden /> : <RefreshCw className="size-3.5" aria-hidden />}
                                  {rerunLoading[caseId] ? "Queuing…" : "Re-run affected research"}
                                </Button>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <p className="mt-4 text-sm text-muted-foreground">No impacted cases reported.</p>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </AuthGate>
  );
}
