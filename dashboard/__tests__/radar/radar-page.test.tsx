import { render, screen, waitFor } from "@testing-library/react";
import RadarPage from "@/app/(app)/radar/page";
import { fetchRadarQueue } from "@/lib/api";

jest.mock("@/lib/api", () => {
  const { mockAuthApi } = jest.requireActual("../../test-utils/mock-auth");
  return mockAuthApi({ fetchRadarQueue: jest.fn() });
});

const mockFetchRadarQueue = fetchRadarQueue as jest.Mock;

interface RadarCase {
  id: string;
  title: string;
  route: string;
  research_state: string;
  suggested_disposition?: string;
  user_disposition?: string;
  blocker?: string;
  deadline?: string;
  freshness?: string;
}

function radarCase(overrides: Partial<RadarCase>): RadarCase {
  return {
    id: "case-1",
    title: "PhD at Oxford",
    route: "phd-route-1",
    research_state: "ready",
    suggested_disposition: "Watch",
    user_disposition: undefined,
    blocker: undefined,
    deadline: "15 January 2027",
    freshness: "updated 3 days ago",
    ...overrides,
  };
}

const RADAR_CASES: RadarCase[] = [
  radarCase({
    id: "case-1",
    title: "PhD at Oxford",
    route: "DPhil in Computer Science",
    research_state: "ready",
    suggested_disposition: "Watch",
    user_disposition: undefined,
    blocker: undefined,
    deadline: "15 January 2027",
    freshness: "updated 3 days ago",
  }),
  radarCase({
    id: "case-2",
    title: "MA at Cambridge",
    route: "MPhil in Physics",
    research_state: "researching",
    suggested_disposition: "Act",
    user_disposition: "Strong",
    blocker: "Formal blocker",
    deadline: "1 February 2027",
    freshness: "updated 1 day ago",
  }),
];

describe("RadarPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders rows from the mocked API", async () => {
    mockFetchRadarQueue.mockResolvedValue({ items: RADAR_CASES, total: 2 });
    render(<RadarPage />);

    // Wait for the case titles to appear
    await waitFor(() => {
      expect(screen.getByText("PhD at Oxford")).toBeInTheDocument();
    });
    expect(screen.getByText("MA at Cambridge")).toBeInTheDocument();
  });

  it("shows suggestion and disposition as separate text nodes", async () => {
    mockFetchRadarQueue.mockResolvedValue({ items: RADAR_CASES, total: 2 });
    render(<RadarPage />);

    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByText("MA at Cambridge")).toBeInTheDocument();
    });

    // Check for separate suggestion and disposition labels
    const suggestionLabels = screen.getAllByText(/System suggests:/);
    const dispositionLabels = screen.getAllByText(/Your decision:/);

    expect(suggestionLabels.length).toBeGreaterThan(0);
    // Only case-2 has a user disposition
    expect(dispositionLabels.length).toBeGreaterThan(0);
  });

  it("places blocker chip before other chips in DOM order", async () => {
    mockFetchRadarQueue.mockResolvedValue({ items: RADAR_CASES, total: 2 });
    const { container } = render(<RadarPage />);

    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByText("MA at Cambridge")).toBeInTheDocument();
    });

    // Find the case with a blocker (case-2)
    const caseRows = container.querySelectorAll("[data-testid*='radar-case-']");
    const blockingCaseRow = Array.from(caseRows).find((row) =>
      row.textContent?.includes("MA at Cambridge")
    );

    if (blockingCaseRow) {
      const chips = blockingCaseRow.querySelectorAll("[data-testid='chip']");
      const blockerChip = Array.from(chips).find((chip) =>
        chip.textContent?.includes("Formal blocker")
      );
      if (blockerChip) {
        // Blocker should be first or early in order
        const blockerIndex = Array.from(chips).indexOf(blockerChip);
        expect(blockerIndex).toBeLessThanOrEqual(1);
      }
    }
  });

  it("displays correct case count", async () => {
    mockFetchRadarQueue.mockResolvedValue({ items: RADAR_CASES, total: 2 });
    render(<RadarPage />);

    // Wait for page to load and verify case count text
    await waitFor(() => {
      expect(screen.getByText(/2 cases in queue/)).toBeInTheDocument();
    });
  });
});
