"use client";

import { useCallback, useEffect, useState } from "react";
import { apiBase, getToken, ApiError } from "@/lib/api";
import { ExternalLink, Loader2 } from "lucide-react";

interface SupervisionPrecedent {
  id: string;
  project: string;
  supervisor_role: string;
  funding_route?: string | null;
  evidence_url?: string | null;
}

interface TrackExplorerProps {
  caseId: string;
}

async function fetchPrecedents(
  caseId: string
): Promise<{ items: SupervisionPrecedent[] }> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${apiBase()}/api/radar/cases/${caseId}/precedents`, {
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

  return data as { items: SupervisionPrecedent[] };
}

export function TrackExplorer({ caseId }: TrackExplorerProps) {
  const [precedents, setPrecedents] = useState<SupervisionPrecedent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPrecedents(caseId);
      setPrecedents(data.items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load precedents");
      setPrecedents([]);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="size-4 animate-spin mr-2" aria-hidden />
        <span className="text-sm text-muted-foreground">Loading precedents…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
        {error}
      </div>
    );
  }

  if (precedents.length === 0) {
    return (
      <div className="rounded-md border p-4 text-center text-sm text-muted-foreground">
        No supervision precedents found
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {precedents.map((prec, idx) => (
        <div
          key={prec.id}
          className="flex items-start gap-3 pb-3 border-b last:border-b-0 last:pb-0"
          data-testid={`precedent-${idx}`}
        >
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm">{prec.project}</div>
            <div className="text-xs text-muted-foreground mt-1">
              <span className="font-semibold">Role:</span> {prec.supervisor_role}
            </div>
            {prec.funding_route && (
              <div className="text-xs text-muted-foreground">
                <span className="font-semibold">Funding:</span> {prec.funding_route}
              </div>
            )}
          </div>
          {prec.evidence_url && (
            <a
              href={prec.evidence_url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 text-primary hover:underline inline-flex items-center gap-1 text-xs"
              data-testid={`precedent-link-${idx}`}
            >
              Evidence
              <ExternalLink className="size-3" aria-hidden />
            </a>
          )}
        </div>
      ))}
    </div>
  );
}
