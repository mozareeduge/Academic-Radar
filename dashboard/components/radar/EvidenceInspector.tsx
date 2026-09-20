"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ExternalLink, Loader2, X } from "lucide-react";
import { fetchClaimEvidence, ApiError } from "@/lib/api";
import type { EvidenceResponse } from "@/types";

interface EvidenceInspectorProps {
  claimId: string;
  isOpen: boolean;
  onClose: () => void;
  invokerRef: React.RefObject<HTMLElement | null> | null;
  independentSupportCount?: number;
  authority?: string;
}

export function EvidenceInspector({
  claimId,
  isOpen,
  onClose,
  invokerRef,
  independentSupportCount,
  authority,
}: EvidenceInspectorProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<EvidenceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const close = useCallback(() => {
    onClose();
    queueMicrotask(() => invokerRef?.current?.focus());
  }, [invokerRef, onClose]);

  useEffect(() => {
    if (!isOpen) return;

    dialogRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;

      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((element) => !element.hasAttribute("hidden"));

      if (focusable.length === 0) {
        event.preventDefault();
        dialogRef.current.focus();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [close, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    if (independentSupportCount !== undefined && authority) return;

    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      setLoading(true);
      setError(null);
    });
    fetchClaimEvidence(claimId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load evidence");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [authority, claimId, independentSupportCount, isOpen]);

  if (!isOpen) return null;

  const supportCount = data?.independent_support_count ?? independentSupportCount;
  const primaryAuthority = authority ?? data?.artifacts[0]?.authority;

  return (
    <>
      <button
        type="button"
        className="fixed inset-0 z-40 bg-foreground/35"
        aria-label="Close evidence inspector"
        onClick={close}
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="evidence-inspector-title"
        tabIndex={-1}
        data-testid="evidence-inspector"
        className="fixed inset-0 right-0 top-0 z-50 flex min-w-0 flex-col border border-border bg-background outline-none xl:inset-y-0 xl:left-auto xl:w-96"
      >
        <div className="flex items-center justify-between gap-3 border-b border-border p-4">
          <div className="min-w-0">
            <h2 id="evidence-inspector-title" className="text-lg font-semibold">Evidence</h2>
            <p className="truncate font-mono text-xs text-muted-foreground">{claimId}</p>
          </div>
          <button
            type="button"
            onClick={close}
            className="inline-flex size-9 items-center justify-center border border-border hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Close evidence inspector"
          >
            <X className="size-4" aria-hidden />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground" role="status">
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Loading evidence…
            </div>
          )}

          {error && (
            <div role="alert" className="border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {!loading && (
            <div className="space-y-4">
              {(supportCount !== undefined || primaryAuthority || data?.contradiction_state) && (
                <dl className="grid grid-cols-2 gap-3 border border-border bg-muted/30 p-3 text-sm">
                  {supportCount !== undefined && (
                    <div>
                      <dt className="text-xs text-muted-foreground">Independent support</dt>
                      <dd className="mt-1 text-xl font-semibold">{supportCount}</dd>
                    </div>
                  )}
                  {data?.contradiction_state && (
                    <div>
                      <dt className="text-xs text-muted-foreground">Claim state</dt>
                      <dd className="mt-1 font-medium">{data.contradiction_state}</dd>
                    </div>
                  )}
                  {primaryAuthority && (
                    <div className="col-span-2">
                      <dt className="text-xs text-muted-foreground">Authority</dt>
                      <dd className="mt-1 break-words font-medium">{primaryAuthority}</dd>
                    </div>
                  )}
                </dl>
              )}

              {data && data.artifacts.length === 0 && (
                <p className="border border-border p-3 text-sm text-muted-foreground">No evidence artifacts are linked to this claim.</p>
              )}

              {data?.artifacts.map((artifact) => (
                <article key={artifact.id} className="border border-border p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <span className="text-xs font-medium">{artifact.authority}</span>
                    <time className="text-xs text-muted-foreground" dateTime={artifact.retrieved_at}>
                      {new Date(artifact.retrieved_at).toLocaleString()}
                    </time>
                  </div>
                  {artifact.excerpt && (
                    <blockquote className="mt-3 border-l-2 border-border pl-3 text-sm text-muted-foreground">
                      {artifact.excerpt}
                    </blockquote>
                  )}
                  <a
                    href={artifact.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
                  >
                    Open original source
                    <ExternalLink className="size-3.5" aria-hidden />
                  </a>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
