"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface DecisionPanelProps {
  suggestedDisposition?: string | null;
  userDisposition: string;
  onDispositionChange: (disposition: string) => Promise<void>;
  isLoading?: boolean;
}

const DISPOSITION_OPTIONS = ["UNDECIDED", "STRONG", "WATCH", "ACT", "REJECTED"];

export function DecisionPanel({
  suggestedDisposition,
  userDisposition,
  onDispositionChange,
  isLoading = false,
}: DecisionPanelProps) {
  const [pendingDisposition, setPendingDisposition] = useState<string | null>(null);

  const handleDispositionChange = async (disposition: string) => {
    setPendingDisposition(disposition);
    try {
      await onDispositionChange(disposition);
    } finally {
      setPendingDisposition(null);
    }
  };

  return (
    <div className="flex flex-col gap-6 mb-6">
      {/* System suggestion block */}
      {suggestedDisposition && (
        <div className="rounded-md border border-border p-4 bg-surface-subtle">
          <h3 className="text-sm font-semibold text-muted-foreground mb-2">
            System suggests
          </h3>
          <p className="text-base font-medium text-foreground">
            {suggestedDisposition}
          </p>
        </div>
      )}

      {/* User decision block */}
      <div className="rounded-md border border-border p-4">
        <h3 className="text-sm font-semibold text-muted-foreground mb-3">
          Your decision
        </h3>
        <div className="flex flex-wrap gap-2">
          {DISPOSITION_OPTIONS.map((option) => (
            <Button
              key={option}
              variant={userDisposition === option ? "default" : "outline"}
              onClick={() => handleDispositionChange(option)}
              disabled={isLoading || pendingDisposition !== null}
              size="sm"
            >
              {option.charAt(0) + option.slice(1).toLowerCase()}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
