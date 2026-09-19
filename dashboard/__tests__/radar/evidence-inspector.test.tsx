import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CoveragePanel } from "@/components/radar/CoveragePanel";
import { ClaimRow } from "@/components/radar/ClaimRow";
import { EvidenceInspector } from "@/components/radar/EvidenceInspector";
import type { Claim } from "@/types";

describe("Evidence Inspector", () => {
  const mockClaim: Claim = {
    id: "claim-1",
    statement: "Supervisor has published in relevant field",
    type: "EXTERNAL_FACT",
    status: "SUPPORTED",
    evidence_count: 3,
    authority: "OFFICIAL_PROGRAMME",
    freshness: "recent",
  };

  const mockCoverageStatuses = [
    {
      class: "Supervisor presence",
      status: "searched+found" as const,
    },
    {
      class: "Project alignment",
      status: "searched+none" as const,
    },
    {
      class: "Funding eligibility",
      status: "not searched" as const,
    },
    {
      class: "Visa requirements",
      status: "blocked" as const,
    },
  ];

  describe("CoveragePanel", () => {
    it("renders all four coverage statuses with text labels", () => {
      render(<CoveragePanel statuses={mockCoverageStatuses} />);

      expect(screen.getByText("Supervisor presence")).toBeInTheDocument();
      expect(screen.getByText("Searched + found")).toBeInTheDocument();

      expect(screen.getByText("Project alignment")).toBeInTheDocument();
      expect(screen.getByText("Searched + none")).toBeInTheDocument();

      expect(screen.getByText("Funding eligibility")).toBeInTheDocument();
      expect(screen.getByText("Not searched")).toBeInTheDocument();

      expect(screen.getByText("Visa requirements")).toBeInTheDocument();
      expect(screen.getByText("Blocked")).toBeInTheDocument();
    });

    it("uses semantic state tokens for each status", () => {
      render(<CoveragePanel statuses={mockCoverageStatuses} />);

      const items = screen.getAllByRole("listitem");
      expect(items.length).toBe(4);

      // Each item should have class with semantic state
      expect(items[0].className).toMatch(/state.pass|state.success/i);
      expect(items[1].className).toMatch(/state.unknown/i);
      expect(items[2].className).toMatch(/state.unknown/i);
      expect(items[3].className).toMatch(/state.fail|state.blocked/i);
    });
  });

  describe("ClaimRow", () => {
    it("renders claim type, status, authority, freshness, and evidence count", () => {
      render(
        <ClaimRow
          claim={mockClaim}
          onEvidenceClick={() => {}}
        />
      );

      expect(screen.getByText(mockClaim.statement)).toBeInTheDocument();
      expect(screen.getByText("EXTERNAL_FACT")).toBeInTheDocument();
      expect(screen.getByText("SUPPORTED")).toBeInTheDocument();
      expect(screen.getByText("OFFICIAL_PROGRAMME")).toBeInTheDocument();
      expect(screen.getByText("recent")).toBeInTheDocument();
      expect(screen.getByText(/3 evidence/)).toBeInTheDocument();
    });

    it("calls onEvidenceClick when evidence button is clicked", async () => {
      const onEvidenceClick = jest.fn();
      render(
        <ClaimRow
          claim={mockClaim}
          onEvidenceClick={onEvidenceClick}
        />
      );

      const evidenceButton = screen.getByRole("button", { name: /evidence/i });
      await userEvent.click(evidenceButton);

      expect(onEvidenceClick).toHaveBeenCalledWith(mockClaim.id);
    });

    it("triggers evidence inspection via keyboard (Enter key)", async () => {
      const onEvidenceClick = jest.fn();
      render(
        <ClaimRow
          claim={mockClaim}
          onEvidenceClick={onEvidenceClick}
        />
      );

      const evidenceButton = screen.getByRole("button", { name: /evidence/i });
      evidenceButton.focus();
      await userEvent.keyboard("{Enter}");

      expect(onEvidenceClick).toHaveBeenCalled();
    });

    it("triggers evidence inspection via keyboard (Space key)", async () => {
      const onEvidenceClick = jest.fn();
      render(
        <ClaimRow
          claim={mockClaim}
          onEvidenceClick={onEvidenceClick}
        />
      );

      const evidenceButton = screen.getByRole("button", { name: /evidence/i });
      evidenceButton.focus();
      await userEvent.keyboard(" ");

      expect(onEvidenceClick).toHaveBeenCalled();
    });
  });

  describe("EvidenceInspector", () => {
    it("opens as dialog with proper ARIA attributes", () => {
      const { rerender } = render(
        <EvidenceInspector
          claimId="claim-1"
          isOpen={false}
          onClose={() => {}}
          invokerRef={null}
        />
      );

      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

      rerender(
        <EvidenceInspector
          claimId="claim-1"
          isOpen={true}
          onClose={() => {}}
          invokerRef={null}
        />
      );

      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-labelledby");
    });

    it("closes and restores focus to claim row via Escape key", async () => {
      const onClose = jest.fn();
      const invokerRef = { current: document.createElement("button") };

      render(
        <EvidenceInspector
          claimId="claim-1"
          isOpen={true}
          onClose={onClose}
          invokerRef={invokerRef}
        />
      );

      const dialog = screen.getByRole("dialog");
      expect(dialog).toBeInTheDocument();

      dialog.focus();
      await userEvent.keyboard("{Escape}");

      expect(onClose).toHaveBeenCalled();
    });

    it("shows independent-support count and authority in drawer", () => {
      render(
        <EvidenceInspector
          claimId="claim-1"
          isOpen={true}
          onClose={() => {}}
          invokerRef={null}
          independentSupportCount={2}
          authority="OFFICIAL_PROGRAMME"
        />
      );

      const dialog = screen.getByRole("dialog");
      expect(within(dialog).getByText("2")).toBeInTheDocument();
      expect(within(dialog).getByText("OFFICIAL_PROGRAMME")).toBeInTheDocument();
    });

    it("renders as full-page below 1024px breakpoint", () => {
      // Mock window.innerWidth
      const originalInnerWidth = window.innerWidth;
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 768,
      });

      const { container } = render(
        <EvidenceInspector
          claimId="claim-1"
          isOpen={true}
          onClose={() => {}}
          invokerRef={null}
        />
      );

      const inspector = container.querySelector("[data-testid='evidence-inspector']");
      expect(inspector).toHaveClass("fixed", "inset-0");

      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: originalInnerWidth,
      });
    });

    it("renders as 380–440px drawer on desktop wide (≥1280px)", () => {
      const originalInnerWidth = window.innerWidth;
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 1400,
      });

      const { container } = render(
        <EvidenceInspector
          claimId="claim-1"
          isOpen={true}
          onClose={() => {}}
          invokerRef={null}
        />
      );

      const inspector = container.querySelector("[data-testid='evidence-inspector']");
      expect(inspector).toHaveClass("fixed", "right-0", "top-0");

      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: originalInnerWidth,
      });
    });
  });
});
