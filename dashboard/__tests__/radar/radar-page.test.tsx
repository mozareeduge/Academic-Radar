import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RadarPage from "@/app/(app)/radar/page";
import { fetchRadarQueue } from "@/lib/api";
import type { RadarCase } from "@/types";

jest.mock("@/lib/api", () => {
  const { mockAuthApi } = jest.requireActual("../../test-utils/mock-auth");
  return mockAuthApi({ fetchRadarQueue: jest.fn() });
});

const mockFetchRadarQueue = fetchRadarQueue as jest.Mock;

function radarCase(overrides: Partial<RadarCase>): RadarCase {
  return {
    id: "case-1",
    research_state: "EVIDENCE_READY",
    suggested_disposition: "WATCH",
    user_disposition: "UNDECIDED",
    blockers: [],
    unknown_count: 0,
    deadline: { original_text: "15 January 2027", precision: "DATE_ONLY" },
    freshness: true,
    ...overrides,
  };
}

const RADAR_CASES: RadarCase[] = [
  radarCase({ id: "case-1" }),
  radarCase({
    id: "case-2",
    research_state: "RESEARCHING",
    suggested_disposition: "ACT",
    user_disposition: "STRONG",
    blockers: [{ name: "English requirement", status: "FAIL", reason: "Requirement not met" }],
    unknown_count: 2,
    deadline: { original_text: "1 February 2027", precision: "DATE_ONLY" },
    freshness: false,
  }),
];

describe("RadarPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetchRadarQueue.mockResolvedValue({ items: RADAR_CASES });
  });

  it("renders production CaseOut rows without fixture-only titles or routes", async () => {
    render(<RadarPage />);

    expect(await screen.findByText("Case case-1")).toBeInTheDocument();
    expect(screen.getByText("Case case-2")).toBeInTheDocument();
    expect(screen.queryByText(/Oxford|Cambridge|DPhil|MPhil/)).not.toBeInTheDocument();
  });

  it("keeps backend suggestion and user decision visibly separate", async () => {
    render(<RadarPage />);

    await screen.findByText("Case case-2");
    expect(screen.getAllByText(/System suggests:/)).toHaveLength(2);
    expect(screen.getAllByText(/Your decision:/)).toHaveLength(2);
    expect(screen.getByText("STRONG")).toBeInTheDocument();
  });

  it("renders backend blockers and unknown counts without deriving a readiness verdict", async () => {
    render(<RadarPage />);

    const row = await screen.findByTestId("radar-case-case-2");
    expect(within(row).getByText("1 formal blocker")).toBeInTheDocument();
    expect(within(row).getByText("2 unknown")).toBeInTheDocument();
    const unknownLabel = screen.getByText("Unknown claims");
    expect(unknownLabel.parentElement).toHaveTextContent("2");
    expect(screen.queryByText(/need attention/i)).not.toBeInTheDocument();
  });

  it("filters by exact research-state value without mutating source data", async () => {
    const user = userEvent.setup();
    render(<RadarPage />);

    await screen.findByText("Case case-2");
    await user.click(screen.getByRole("button", { name: "Researching" }));

    await waitFor(() => {
      expect(screen.queryByText("Case case-1")).not.toBeInTheDocument();
      expect(screen.getByText("Case case-2")).toBeInTheDocument();
    });
    expect(mockFetchRadarQueue).toHaveBeenCalledTimes(1);
  });

  it("displays the wrapped-list case count", async () => {
    render(<RadarPage />);
    expect(await screen.findByText(/2 cases in queue/)).toBeInTheDocument();
  });
});
