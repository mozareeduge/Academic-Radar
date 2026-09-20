import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WatchPage from "@/app/(app)/watch/page";
import * as api from "@/lib/api";

jest.mock("@/lib/api", () => ({
  fetchChangeEvents: jest.fn(),
  fetchWatchTargets: jest.fn(),
  postResearch: jest.fn(),
  fetchMe: jest.fn(() => Promise.resolve({ user_id: 1, email: "test@example.com" })),
  fetchAuthConfig: jest.fn(() => Promise.resolve({ auth_mode: "password", invite_required: false })),
  fetchCurrentUser: jest.fn(() => Promise.resolve({ user_id: 1, email: "test@example.com" })),
  apiBase: () => "http://localhost:8000",
  apiStartupError: () => null,
  ApiError: class ApiError extends Error {
    status: number;
    details?: unknown;
    constructor(message: string, status: number, details?: unknown) {
      super(message);
      this.status = status;
      this.details = details;
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

const mockWatchTargets = {
  items: [
    {
      id: "watch-1",
      target_id: "programme-123",
      url: "https://example.edu/programme",
      cadence: "DAILY",
      state: "ACTIVE",
    },
  ],
};

describe("Watch Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.fetchChangeEvents as jest.Mock).mockResolvedValue(mockChangeEvents);
    (api.fetchWatchTargets as jest.Mock).mockResolvedValue(mockWatchTargets);
    (api.postResearch as jest.Mock).mockResolvedValue({ run_id: "run-123" });
  });

  it("renders production watch targets and backend-reported change events", async () => {
    render(<WatchPage />);

    expect(await screen.findByText("Watch")).toBeInTheDocument();
    expect(screen.getByText("programme-123")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open source/i })).toHaveAttribute(
      "href",
      "https://example.edu/programme",
    );
    expect(screen.getByText("Deadline changed from Feb 15 to Mar 1")).toBeInTheDocument();
    expect(screen.getByText("Material change")).toBeInTheDocument();
    expect(screen.getByText("Non-material change")).toBeInTheDocument();
  });

  it("shows exactly the backend-provided impacted case IDs", async () => {
    (api.fetchChangeEvents as jest.Mock).mockResolvedValue({
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
    });

    render(<WatchPage />);

    expect(await screen.findByText("case-1")).toBeInTheDocument();
    expect(screen.getByText("case-2")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /case-[12]/ })).toHaveLength(2);
  });

  it("does not fabricate a textual diff or source-health data absent from the production response", async () => {
    render(<WatchPage />);

    await screen.findByText("Deadline changed from Feb 15 to Mar 1");
    expect(screen.queryByText(/source health/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^\+/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^-/)).not.toBeInTheDocument();
  });

  it("queues research only for the impacted case whose button is clicked", async () => {
    const user = userEvent.setup();
    render(<WatchPage />);

    const rerunButtons = await screen.findAllByRole("button", { name: /re-run affected research/i });
    await user.click(rerunButtons[0]);

    expect(api.postResearch).toHaveBeenCalledTimes(1);
    expect(api.postResearch).toHaveBeenCalledWith("case-1");
    expect(await screen.findByText("Research queued · run-123")).toBeInTheDocument();
  });

  it("keeps watch-target and change-event failures visible without discarding the other section", async () => {
    (api.fetchWatchTargets as jest.Mock).mockRejectedValue(new Error("target failure"));

    render(<WatchPage />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load watch targets");
    expect(screen.getByText("Deadline changed from Feb 15 to Mar 1")).toBeInTheDocument();
    expect(screen.getByText("No production watch targets are configured.")).toBeInTheDocument();
  });
});
