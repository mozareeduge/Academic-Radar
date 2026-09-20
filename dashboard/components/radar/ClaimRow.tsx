import { useRef } from "react";
import type { Claim } from "@/types";

interface ClaimRowProps {
  claim: Claim;
  onEvidenceClick: (claimId: string) => void;
}

export function ClaimRow({ claim, onEvidenceClick }: ClaimRowProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);

  const handleClick = () => {
    onEvidenceClick(claim.id);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onEvidenceClick(claim.id);
    }
  };

  return (
    <div className="border-b border-border py-3 px-2">
      <div className="flex flex-col gap-2">
        <p className="font-medium text-sm text-foreground">{claim.statement}</p>

        <div className="flex flex-wrap gap-2 text-xs">
          <span className="px-2 py-1 border border-border bg-muted text-muted-foreground">
            {claim.type}
          </span>
          <span className="px-2 py-1 border border-border bg-muted text-muted-foreground">
            {claim.status}
          </span>
          <span className="px-2 py-1 border border-border bg-muted text-muted-foreground">
            {claim.authority}
          </span>
          <span className="px-2 py-1 border border-border bg-muted text-muted-foreground">
            {claim.freshness}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground">{claim.evidence_count} evidence</span>
          <button
            ref={buttonRef}
            onClick={handleClick}
            onKeyDown={handleKeyDown}
            className="px-3 py-1 text-xs border border-border hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label={`View evidence for claim ${claim.id}`}
          >
            Evidence
          </button>
        </div>
      </div>
    </div>
  );
}
