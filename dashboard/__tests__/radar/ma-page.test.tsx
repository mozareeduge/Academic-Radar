import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MAPage from "@/app/(app)/ma/page";
import * as api from "@/lib/api";

jest.mock("@/lib/api", () => {
  const { mockAuthApi } = jest.requireActual("../../test-utils/mock-auth");
  return mockAuthApi({ fetchRadarCases: jest.fn(), fetchFunding: jest.fn() });
});

const maCases = [
  {
    id: "ma-1",
    research_state: "EVIDENCE_READY",
    suggested_disposition: "ACT",
    user_disposition: "WATCH",
    blockers: [],
    unknown_count: 0,
    deadline: null,
    freshness: true,
  },
  {
    id: "ma-2",
    research_state: "RESEARCHING",
    suggested_disposition: null,
    user_disposition: "UNDECIDED",
    blockers: [],
    unknown_count: 1,
    deadline: null,
    freshness: true,
  },
];

describe("MA production view", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.fetchRadarCases as jest.Mock).mockResolvedValue({ items: maCases });
    (api.fetchFunding as jest.Mock).mockResolvedValue({ items: [] });
  });

  it("requests only the exact MA_PROGRAMME route", async () => {
    render(<MAPage />);
    await waitFor(() => {
      expect(api.fetchRadarCases).toHaveBeenCalledWith({ application_route: "MA_PROGRAMME" });
    });
  });

  it("loads funding for the selected case and switches by case id", async () => {
    const user = userEvent.setup();
    render(<MAPage />);

    await waitFor(() => expect(api.fetchFunding).toHaveBeenCalledWith("ma-1"));
    await user.click(screen.getByRole("button", { name: /Case ma-2/i }));
    await waitFor(() => expect(api.fetchFunding).toHaveBeenCalledWith("ma-2"));
  });

  it("does not derive funding status when the backend returns no assessments", async () => {
    render(<MAPage />);
    expect(await screen.findByText("No funding assessments are linked to this case yet.")).toBeInTheDocument();
    expect(screen.queryByText(/fully funded|fundable|funding score/i)).not.toBeInTheDocument();
  });
});
