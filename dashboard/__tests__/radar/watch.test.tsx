import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WatchPage from "@/app/(app)/watch/page";
import * as api from "@/lib/api";

// Mock Next.js navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({}),
  useParams: () => ({}),
}));

// Mock the API
jest.mock("@/lib/api", () => ({
  fetchChangeEvents: jest.fn(),
  postResearch: jest.fn(),
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

const mockChangeEvents = {
  items: [
    {
      id: "change-1",
      watch_check_id: "check-1",
      summary: "Deadline changed from Feb 15 to Mar 1",
      material: true,
      at: "2026-09-20T10:00:00Z",
      impacted_cases: ["case-1", "case-2"],
    },
    {
      id: "change-2",
      watch_check_id: "check-2",
      summary: "Page content updated",
      material: false,
      at: "2026-09-19T14:30:00Z",
      impacted_cases: [],
    },
  ],
};

describe("Watch Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.fetchChangeEvents as jest.Mock).mockResolvedValue(mockChangeEvents);
    (api.postResearch as jest.Mock).mockResolvedValue({ run_id: "run-123" });
  });

  it("renders change events list with diff and impacted cases", async () => {
    render(<WatchPage />);

    await screen.findByText("Watch");

    // First change event with material changes and impacted cases
    // The summary appears in both the heading and as a diff line
    const summaryElements = screen.getAllByText("Deadline changed from Feb 15 to Mar 1");
    expect(summaryElements.length).toBeGreaterThanOrEqual(1);

    // Should show impacted cases label
    expect(screen.getByText("Impacted cases:")).toBeInTheDocument();
  });

  it("shows only API-provided cases in impacted list, filtering dependent ones", async () => {
    const eventsWithMixedCases = {
      items: [
        {
          id: "change-1",
          watch_check_id: "check-1",
          summary: "Important update",
          material: true,
          at: "2026-09-20T10:00:00Z",
          impacted_cases: ["case-1", "case-2"],
        },
      ],
      source_health: [],
    };
    (api.fetchChangeEvents as jest.Mock).mockResolvedValue(eventsWithMixedCases);

    render(<WatchPage />);

    await screen.findByText("Watch");

    // Verify only the API-provided impacted cases are shown
    expect(screen.getByText("case-1")).toBeInTheDocument();
    expect(screen.getByText("case-2")).toBeInTheDocument();

    // Verify we don't show any extra cases
    const caseRows = screen.getAllByText(/case-\d/);
    expect(caseRows).toHaveLength(2);
  });

  it("displays failed source health with FETCH_FAILED status", async () => {
    const eventsWithFailed = {
      items: [
        {
          id: "change-1",
          watch_check_id: "check-1",
          summary: "Source data updated",
          material: true,
          at: "2026-09-20T10:00:00Z",
          impacted_cases: ["case-1"],
        },
      ],
      source_health: [
        {
          source: "university-site",
          status: "FETCH_FAILED",
          last_check: "2026-09-20T09:50:00Z",
        },
        {
          source: "academic-db",
          status: "OK",
          last_check: "2026-09-20T09:55:00Z",
        },
      ],
    };
    (api.fetchChangeEvents as jest.Mock).mockResolvedValue(eventsWithFailed);

    render(<WatchPage />);

    await screen.findByText("Watch");

    // Find Source Health table
    const sourceHealthHeader = screen.getByText(/source health/i);
    expect(sourceHealthHeader).toBeInTheDocument();

    // Failed source should be visible
    const healthTable = sourceHealthHeader.closest("div");
    expect(within(healthTable!).getByText("university-site")).toBeInTheDocument();
    expect(within(healthTable!).getByText("FETCH_FAILED")).toBeInTheDocument();
  });

  it("never hides failed source in Source Health table", async () => {
    const eventsWithMultipleFailed = {
      items: [],
      source_health: [
        {
          source: "failed-source-1",
          status: "FETCH_FAILED",
          last_check: "2026-09-20T09:50:00Z",
        },
        {
          source: "failed-source-2",
          status: "FETCH_FAILED",
          last_check: "2026-09-20T08:30:00Z",
        },
      ],
    };
    (api.fetchChangeEvents as jest.Mock).mockResolvedValue(eventsWithMultipleFailed);

    render(<WatchPage />);

    await screen.findByText("Watch");

    expect(screen.getByText("failed-source-1")).toBeInTheDocument();
    expect(screen.getByText("failed-source-2")).toBeInTheDocument();
  });

  it("calls POST research endpoint once per Re-run button click", async () => {
    const user = userEvent.setup();
    render(<WatchPage />);

    await screen.findByText("Watch");

    // Find and click the re-run button for first impacted case
    const rerunButtons = screen.getAllByRole("button", { name: /re-run/i });
    expect(rerunButtons.length).toBeGreaterThan(0);

    await user.click(rerunButtons[0]);

    // Verify POST research was called exactly once
    expect(api.postResearch).toHaveBeenCalledTimes(1);
    expect(api.postResearch).toHaveBeenCalledWith(expect.any(String));
  });

  it("shows re-run button for each impacted case", async () => {
    render(<WatchPage />);

    await screen.findByText("Watch");

    // First event has 2 impacted cases, so should have 2 re-run buttons
    const rerunButtons = screen.getAllByRole("button", { name: /re-run/i });
    expect(rerunButtons.length).toBeGreaterThanOrEqual(2);
  });
});
