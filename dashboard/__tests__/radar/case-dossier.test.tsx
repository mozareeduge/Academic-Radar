import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CaseDossier from "@/app/(app)/cases/[id]/page";
import * as api from "@/lib/api";

// Mock Next.js navigation
jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "case-123" }),
}));

// Mock the API
jest.mock("@/lib/api", () => ({
  fetchCase: jest.fn(),
  fetchCoverage: jest.fn(),
  fetchFunding: jest.fn(),
  setUserDisposition: jest.fn(),
  freezeBrief: jest.fn(),
  fetchBrief: jest.fn(),
  fetchClaimEvidence: jest.fn(),
  fetchMe: jest.fn(() => Promise.resolve({ user_id: 1, email: "test@example.com" })),
  fetchAuthConfig: jest.fn(() => Promise.resolve({ auth_mode: "password", invite_required: false })),
  fetchCurrentUser: jest.fn(() => Promise.resolve({ user_id: 1, email: "test@example.com" })),
  apiBase: () => "http://localhost:8000",
  apiStartupError: () => null,
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

const mockCase = {
  id: "case-123",
  research_state: "EVIDENCE_READY",
  user_disposition: "UNDECIDED",
  suggested_disposition: "WATCH",
  blockers: [
    { name: "English requirement", status: "FAIL", reason: "Not met according to source" }
  ],
  unknown_count: 2,
  deadline: {
    original_text: "15 January 2027",
    precision: "DATE_ONLY"
  },
  freshness: true
};

describe("Case Dossier", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.fetchCase as jest.Mock).mockResolvedValue(mockCase);
    (api.fetchCoverage as jest.Mock).mockResolvedValue({ coverage: [], protocol_version: "1.0" });
    (api.fetchFunding as jest.Mock).mockResolvedValue({ items: [] });
  });

  it("renders blocker region as first landmark", async () => {
    render(<CaseDossier />);

    // Wait for async content
    await screen.findByRole("heading", { name: "Case dossier" });

    // Find the blocker region as first landmark
    const landmarks = screen.getAllByRole("region");
    expect(landmarks[0]).toHaveAttribute("aria-label", "Formal blockers");
  });

  it("shows 'No formal blockers found' when no blockers", async () => {
    const caseWithoutBlockers = { ...mockCase, blockers: [], unknown_count: 0 };
    (api.fetchCase as jest.Mock).mockResolvedValue(caseWithoutBlockers);

    render(<CaseDossier />);

    await screen.findByText("No formal blockers found");
  });

  it("shows 'Eligibility unknown' when no blockers but unknown_count > 0", async () => {
    const caseUnknown = { ...mockCase, blockers: [], unknown_count: 2 };
    (api.fetchCase as jest.Mock).mockResolvedValue(caseUnknown);

    render(<CaseDossier />);

    await screen.findByText("Eligibility unknown");
  });

  it("renders decision panel with system suggestion and user decision separately", async () => {
    render(<CaseDossier />);

    await screen.findByRole("heading", { name: "Case dossier" });

    // System suggestion section
    expect(screen.getByText("System suggests")).toBeInTheDocument();
    expect(screen.getByText("WATCH")).toBeInTheDocument();
    expect(screen.queryByText(/reasons?.*uncertain/i)).not.toBeInTheDocument();

    // User decision section (separate block)
    const decisionButtons = screen.getAllByRole("button", {
      name: /undecided|strong|watch|act|rejected/i
    });
    expect(decisionButtons.length).toBeGreaterThan(0);
  });

  it("does not change suggestion block when user changes decision", async () => {
    (api.setUserDisposition as jest.Mock).mockResolvedValue({ ...mockCase, user_disposition: "STRONG" });

    render(<CaseDossier />);

    await screen.findByRole("heading", { name: "Case dossier" });

    const strongButton = screen.getByRole("button", { name: /strong/i });
    await userEvent.click(strongButton);

    // Verify POST was called
    expect(api.setUserDisposition).toHaveBeenCalledWith("case-123", "STRONG");

    // Suggestion should still be WATCH
    expect(screen.getByText("System suggests")).toBeInTheDocument();
    expect(screen.getByText("WATCH")).toBeInTheDocument();
  });

  it("shows deadline with original wording and precision label", async () => {
    render(<CaseDossier />);

    const deadline = await screen.findByText(/15 January 2027/);
    expect(deadline).toBeInTheDocument();
    expect(deadline.parentElement).toHaveTextContent("time not stated");
  });

  it("does not render fixture-only gates or dimensions from CaseOut", async () => {
    render(<CaseDossier />);
    await screen.findByRole("heading", { name: "Case dossier" });
    expect(screen.queryByRole("table", { name: /formal gates/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("table", { name: /assessment dimensions/i })).not.toBeInTheDocument();
  });

});
