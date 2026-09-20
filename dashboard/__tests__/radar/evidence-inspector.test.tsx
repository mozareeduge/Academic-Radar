import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CoveragePanel } from "@/components/radar/CoveragePanel";
import { ClaimRow } from "@/components/radar/ClaimRow";
import { EvidenceInspector } from "@/components/radar/EvidenceInspector";
import * as api from "@/lib/api";
import type { Claim, CoverageItem } from "@/types";

jest.mock("@/lib/api", () => ({
  fetchClaimEvidence: jest.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

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

  const mockCoverageStatuses: CoverageItem[] = [
    { evidence_class: "Supervisor presence", status: "SEARCHED_FOUND", evidence_ids: ["e-1"] },
    { evidence_class: "Project alignment", status: "SEARCHED_NONE_FOUND", evidence_ids: [] },
    { evidence_class: "Funding eligibility", status: "NOT_SEARCHED", evidence_ids: [] },
    { evidence_class: "Visa requirements", status: "BLOCKED", evidence_ids: [] },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (api.fetchClaimEvidence as jest.Mock).mockResolvedValue({
      artifacts: [
        {
          id: "art-1",
          source_url: "https://example.org/source",
          authority: "OFFICIAL_PROGRAMME",
          retrieved_at: "2026-09-20T10:00:00Z",
          excerpt: "Relevant source excerpt",
        },
      ],
      independent_support_count: 2,
      contradiction_state: "SUPPORTED",
    });
  });

  describe("CoveragePanel", () => {
    it("renders all exact backend coverage states with text labels", () => {
      render(<CoveragePanel statuses={mockCoverageStatuses} protocolVersion="1.0" />);
      expect(screen.getByText("Supervisor presence")).toBeInTheDocument();
      expect(screen.getByText("Searched · evidence found")).toBeInTheDocument();
      expect(screen.getByText("Project alignment")).toBeInTheDocument();
      expect(screen.getByText("Searched · none found")).toBeInTheDocument();
      expect(screen.getByText("Funding eligibility")).toBeInTheDocument();
      expect(screen.getByText("Not searched")).toBeInTheDocument();
      expect(screen.getByText("Visa requirements")).toBeInTheDocument();
      expect(screen.getByText("Blocked")).toBeInTheDocument();
      expect(screen.getByText("Protocol 1.0")).toBeInTheDocument();
    });
  });

  describe("ClaimRow", () => {
    it("renders claim metadata and evidence count", () => {
      render(<ClaimRow claim={mockClaim} onEvidenceClick={() => {}} />);
      expect(screen.getByText(mockClaim.statement)).toBeInTheDocument();
      expect(screen.getByText("EXTERNAL_FACT")).toBeInTheDocument();
      expect(screen.getByText("SUPPORTED")).toBeInTheDocument();
      expect(screen.getByText("OFFICIAL_PROGRAMME")).toBeInTheDocument();
      expect(screen.getByText("recent")).toBeInTheDocument();
      expect(screen.getByText(/3 evidence/)).toBeInTheDocument();
    });

    it("opens evidence from pointer and keyboard activation", async () => {
      const onEvidenceClick = jest.fn();
      const user = userEvent.setup();
      render(<ClaimRow claim={mockClaim} onEvidenceClick={onEvidenceClick} />);
      const button = screen.getByRole("button", { name: /evidence/i });
      await user.click(button);
      expect(onEvidenceClick).toHaveBeenCalledWith("claim-1");
      button.focus();
      await user.keyboard("{Enter}");
      expect(onEvidenceClick).toHaveBeenCalled();
    });
  });

  describe("EvidenceInspector", () => {
    it("opens as an accessible dialog and loads production evidence", async () => {
      render(
        <EvidenceInspector claimId="claim-1" isOpen onClose={() => {}} invokerRef={null} />,
      );
      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-modal", "true");
      await waitFor(() => expect(api.fetchClaimEvidence).toHaveBeenCalledWith("claim-1"));
      expect(await within(dialog).findByText("Relevant source excerpt")).toBeInTheDocument();
      expect(within(dialog).getByRole("link", { name: /open original source/i })).toHaveAttribute(
        "href",
        "https://example.org/source",
      );
    });

    it("closes and restores focus via Escape", async () => {
      const onClose = jest.fn();
      const invoker = document.createElement("button");
      document.body.appendChild(invoker);
      const invokerRef = { current: invoker };
      const user = userEvent.setup();

      render(<EvidenceInspector claimId="claim-1" isOpen onClose={onClose} invokerRef={invokerRef} />);
      await user.keyboard("{Escape}");
      expect(onClose).toHaveBeenCalled();
      await waitFor(() => expect(document.activeElement).toBe(invoker));
      invoker.remove();
    });

    it("supports supplied summary metadata without requiring a fetch", () => {
      render(
        <EvidenceInspector
          claimId="claim-1"
          isOpen
          onClose={() => {}}
          invokerRef={null}
          independentSupportCount={2}
          authority="OFFICIAL_PROGRAMME"
        />,
      );
      const dialog = screen.getByRole("dialog");
      expect(within(dialog).getByText("2")).toBeInTheDocument();
      expect(within(dialog).getByText("OFFICIAL_PROGRAMME")).toBeInTheDocument();
      expect(api.fetchClaimEvidence).not.toHaveBeenCalled();
    });

    it("is full-screen by default and becomes a desktop drawer at xl", () => {
      const { container } = render(
        <EvidenceInspector claimId="claim-1" isOpen onClose={() => {}} invokerRef={null} />,
      );
      const inspector = container.querySelector("[data-testid='evidence-inspector']");
      expect(inspector).toHaveClass("fixed", "inset-0", "right-0", "top-0", "xl:w-96");
    });
    it("traps Tab focus inside the modal inspector", async () => {
      const user = userEvent.setup();
      render(<EvidenceInspector claimId="claim-1" isOpen onClose={() => {}} invokerRef={null} />);
      const dialog = screen.getByRole("dialog");
      const closeButton = within(dialog).getByRole("button", { name: /close evidence inspector/i });
      await within(dialog).findByRole("link", { name: /open original source/i });
      const sourceLink = within(dialog).getByRole("link", { name: /open original source/i });

      sourceLink.focus();
      await user.keyboard("{Tab}");
      expect(document.activeElement).toBe(closeButton);

      closeButton.focus();
      await user.keyboard("{Shift>}{Tab}{/Shift}");
      expect(document.activeElement).toBe(sourceLink);
    });

  });
});
