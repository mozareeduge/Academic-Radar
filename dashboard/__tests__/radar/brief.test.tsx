import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BriefTab } from "@/components/radar/BriefTab";
import * as api from "@/lib/api";
import type { CaseDossier } from "@/types";

jest.mock("@/lib/api", () => ({
  freezeBrief: jest.fn(),
  fetchBrief: jest.fn(),
  fetchClaimEvidence: jest.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    details?: Record<string, unknown>;
    constructor(message: string, status: number, details?: Record<string, unknown>) {
      super(message);
      this.status = status;
      this.details = details;
    }
  },
}));

const cleanCase: CaseDossier = {
  id: "case-1",
  research_state: "EVIDENCE_READY",
  user_disposition: "ACT",
  suggested_disposition: "STRONG",
  blockers: [],
  unknown_count: 0,
  deadline: null,
  freshness: true,
  brief_block_reasons: [],
};

const brief = {
  id: "brief-1",
  case_id: "case-1",
  frozen_at: "2026-09-20T10:00:00Z",
  state: "FROZEN",
  superseded: false,
  content: {
    claims: [
      { id: "claim-1", statement: "Supervisor has relevant publications", claim_type: "EXTERNAL_FACT", status: "SUPPORTED", evidence_ids: ["art-1"] },
    ],
    gates: [{ id: "gate-1", requirement: "English requirement", result: "PASS", evidence_ids: ["art-1"] }],
    dimensions: [{ id: "dim-1", dimension_id: "ADMISSION_VIABILITY", value: 2 }],
    funding_assessments: [{ id: "fund-1", funding_route_id: "route-1", award_amount: "15000", currency: "EUR" }],
  },
};

describe("BriefTab", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.freezeBrief as jest.Mock).mockResolvedValue({
      id: "brief-1",
      case_id: "case-1",
      frozen_at: "2026-09-20T10:00:00Z",
      state: "FROZEN",
    });
    (api.fetchBrief as jest.Mock).mockResolvedValue(brief);
  });

  it("renders application brief controls without send/email actions", () => {
    render(<BriefTab caseId="case-1" caseData={cleanCase} />);
    expect(screen.getByText("Application Brief")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Prepare evidence brief" })).toBeEnabled();
    expect(screen.queryByText(/send/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/email/i)).not.toBeInTheDocument();
  });

  it("uses exact backend reasons to disable freeze", () => {
    render(
      <BriefTab
        caseId="case-1"
        caseData={{ ...cleanCase, brief_block_reasons: ["Hard gate failed: English proficiency"] }}
      />,
    );
    expect(screen.getByRole("button", { name: "Prepare evidence brief" })).toBeDisabled();
    expect(screen.getByTestId("brief-disabled-reason")).toHaveTextContent("Hard gate failed: English proficiency");
  });

  it("does not recompute freeze eligibility from noncritical unknowns or display fields", () => {
    render(<BriefTab caseId="case-1" caseData={{
      ...cleanCase,
      blockers: [{ name: "Displayed assessment", status: "FAIL" }],
      unknown_count: 3,
      freshness: false,
    }} />);
    expect(screen.getByRole("button", { name: "Prepare evidence brief" })).toBeEnabled();
  });

  it("enables freeze only for a clean case", () => {
    render(<BriefTab caseId="case-1" caseData={cleanCase} />);
    expect(screen.getByRole("button", { name: "Prepare evidence brief" })).toBeEnabled();
    expect(screen.queryByTestId("brief-disabled-reason")).not.toBeInTheDocument();
  });

  it("fetches and renders the frozen brief after a successful freeze", async () => {
    render(<BriefTab caseId="case-1" caseData={cleanCase} />);
    await userEvent.click(screen.getByRole("button", { name: "Prepare evidence brief" }));

    expect(api.freezeBrief).toHaveBeenCalledWith("case-1");
    expect(api.fetchBrief).toHaveBeenCalledWith("brief-1");
    expect(await screen.findByText("Supervisor has relevant publications")).toBeInTheDocument();
    expect(screen.getByText("English requirement")).toBeInTheDocument();
    expect(screen.getByText("ADMISSION_VIABILITY")).toBeInTheDocument();
    expect(screen.getByText("route-1")).toBeInTheDocument();
  });

  it("surfaces backend 409 blocking reasons", async () => {
    (api.freezeBrief as jest.Mock).mockRejectedValue(
      new api.ApiError("Brief cannot be frozen from the current evidence state", 409, {
        headers: { "x-brief-blocked-reasons": "Unknown facts must be resolved; Facts are stale" },
      }),
    );
    render(<BriefTab caseId="case-1" caseData={cleanCase} />);
    await userEvent.click(screen.getByRole("button", { name: "Prepare evidence brief" }));

    expect(await screen.findByText("Unknown facts must be resolved")).toBeInTheDocument();
    expect(screen.getByText("Facts are stale")).toBeInTheDocument();
  });

  it("shows superseded state returned by the backend", async () => {
    (api.fetchBrief as jest.Mock).mockResolvedValue({ ...brief, superseded: true });
    render(<BriefTab caseId="case-1" caseData={cleanCase} />);
    await userEvent.click(screen.getByRole("button", { name: "Prepare evidence brief" }));
    expect(await screen.findByText("Superseded")).toBeInTheDocument();
  });
});
