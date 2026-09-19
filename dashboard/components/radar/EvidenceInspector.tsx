"use client";

import { useEffect, useRef } from "react";

interface EvidenceInspectorProps {
  claimId: string;
  isOpen: boolean;
  onClose: () => void;
  invokerRef: React.RefObject<HTMLElement> | null;
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
  const isWideScreen = typeof window !== "undefined" && window.innerWidth >= 1280;

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        // Restore focus to invoker
        if (invokerRef?.current) {
          invokerRef.current.focus();
        }
      }
    };

    // Use document listener so it works regardless of focus
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose, invokerRef]);

  if (!isOpen) return null;

  const closeButton = () => {
    onClose();
    if (invokerRef?.current) {
      invokerRef.current.focus();
    }
  };

  return (
    <>
      {/* Backdrop */}
      {!isWideScreen && (
        <div
          className="fixed inset-0 bg-black/50 z-40"
          onClick={closeButton}
        />
      )}

      {/* Inspector */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-labelledby="evidence-inspector-title"
        data-testid="evidence-inspector"
        className={`fixed z-50 bg-surface-base border border-border flex flex-col ${
          isWideScreen
            ? "right-0 top-0 w-96 h-screen rounded-l-md"
            : "inset-0 rounded-t-lg"
        }`}
        style={isWideScreen ? { width: "380px" } : {}}
      >
        {/* Header */}
        <div className="border-b border-border p-4 flex justify-between items-center">
          <h2 id="evidence-inspector-title" className="text-lg font-semibold">
            Evidence
          </h2>
          <button
            onClick={closeButton}
            className="p-1 hover:bg-surface-subtle rounded focus:outline-none focus:ring-2 focus:ring-focus"
            aria-label="Close evidence inspector"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {independentSupportCount !== undefined && (
            <div className="rounded border border-border p-3 bg-surface-subtle">
              <p className="text-sm font-medium">Independent support</p>
              <p className="text-2xl font-bold">{independentSupportCount}</p>
            </div>
          )}

          {authority && (
            <div className="rounded border border-border p-3 bg-surface-subtle">
              <p className="text-sm font-medium">Authority</p>
              <p className="text-sm text-foreground">{authority}</p>
            </div>
          )}

          <div className="text-sm text-muted-foreground p-3 border border-border rounded">
            <p>Evidence details for claim {claimId}</p>
          </div>
        </div>

        {/* Footer with source link */}
        <div className="border-t border-border p-4">
          <button className="w-full px-3 py-2 rounded border border-border hover:bg-surface-raised text-sm font-medium focus:outline-none focus:ring-2 focus:ring-focus">
            Open original source
          </button>
        </div>
      </div>
    </>
  );
}
