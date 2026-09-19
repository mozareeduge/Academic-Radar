"use client";

import { useEffect, useState } from "react";
import AuthGate from "@/components/AuthGate";
import { fetchChangeEvents, postResearch } from "@/lib/api";
import type { ChangeEventsResponse, ChangeEvent } from "@/types";

interface DiffLine {
  type: "added" | "removed";
  text: string;
}

function parseDiff(summary: string): DiffLine[] {
  const lines: DiffLine[] = [];
  const parts = summary.split(/[\n\r]+/);

  for (const part of parts) {
    if (part.startsWith("+")) {
      lines.push({ type: "added", text: part.substring(1) });
    } else if (part.startsWith("-")) {
      lines.push({ type: "removed", text: part.substring(1) });
    } else if (part.trim()) {
      lines.push({ type: "removed", text: part });
    }
  }

  return lines;
}

export default function WatchPage() {
  const [data, setData] = useState<ChangeEventsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rerunLoading, setRerunLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const loadData = async () => {
      try {
        const result = await fetchChangeEvents();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load changes");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleRerun = async (caseId: string) => {
    setRerunLoading((prev) => ({ ...prev, [caseId]: true }));
    try {
      await postResearch(caseId);
    } catch (err) {
      console.error("Research failed:", err);
    } finally {
      setRerunLoading((prev) => ({ ...prev, [caseId]: false }));
    }
  };

  return (
    <AuthGate>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">Watch</h1>
          <p className="text-sm text-muted-foreground">
            Track changes in monitored sources and affected cases
          </p>
        </div>

        {loading && <div className="text-sm text-muted-foreground">Loading...</div>}
        {error && (
          <div className="text-sm text-destructive">Error: {error}</div>
        )}

        {data && (
          <>
            {/* Change Events */}
            {data.items && data.items.length > 0 && (
              <div className="flex flex-col gap-4">
                <h2 className="text-lg font-semibold">Recent Changes</h2>
                {data.items.map((event: ChangeEvent) => (
                  <div
                    key={event.id}
                    className="rounded-lg border bg-card p-4 shadow-sm"
                  >
                    <div className="flex flex-col gap-3">
                      <div>
                        <h3 className="font-medium">{event.summary}</h3>
                        <p className="text-xs text-muted-foreground">
                          {new Date(event.at).toLocaleString()}
                        </p>
                      </div>

                      {/* Text Diff */}
                      <div className="rounded bg-muted/50 p-3 font-mono text-xs space-y-1">
                        {parseDiff(event.summary).map((line, idx) => (
                          <div
                            key={idx}
                            className={
                              line.type === "added"
                                ? "text-green-700 dark:text-green-400"
                                : "text-red-700 dark:text-red-400"
                            }
                          >
                            <span className="mr-2">
                              {line.type === "added" ? "+" : "−"}
                            </span>
                            {line.text}
                          </div>
                        ))}
                      </div>

                      {/* Impacted Cases */}
                      {event.impacted_cases && event.impacted_cases.length > 0 && (
                        <div className="flex flex-col gap-2">
                          <p className="text-sm font-medium text-muted-foreground">
                            Impacted cases:
                          </p>
                          <div className="flex flex-col gap-2">
                            {event.impacted_cases.map((caseId) => (
                              <div
                                key={caseId}
                                className="flex items-center justify-between gap-2 rounded bg-muted p-2 text-sm"
                              >
                                <span>{caseId}</span>
                                <button
                                  onClick={() => handleRerun(caseId)}
                                  disabled={rerunLoading[caseId]}
                                  className="inline-flex h-8 items-center justify-center rounded bg-primary px-3 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  {rerunLoading[caseId] ? "Running..." : "Re-run affected research"}
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Source Health */}
            {data.source_health && data.source_health.length > 0 && (
              <div className="flex flex-col gap-4">
                <h2 className="text-lg font-semibold">Source Health</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="px-4 py-2 text-left font-medium">
                          Source
                        </th>
                        <th className="px-4 py-2 text-left font-medium">
                          Status
                        </th>
                        <th className="px-4 py-2 text-left font-medium">
                          Last Check
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.source_health.map((row) => (
                        <tr key={row.source} className="border-b">
                          <td className="px-4 py-2">{row.source}</td>
                          <td className="px-4 py-2">
                            <span
                              className={`inline-flex items-center rounded px-2 py-1 text-xs font-medium ${
                                row.status === "FETCH_FAILED"
                                  ? "bg-destructive/10 text-destructive"
                                  : "bg-green-100 text-green-800"
                              }`}
                            >
                              {row.status}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-xs text-muted-foreground">
                            {row.last_check
                              ? new Date(row.last_check).toLocaleString()
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </AuthGate>
  );
}
