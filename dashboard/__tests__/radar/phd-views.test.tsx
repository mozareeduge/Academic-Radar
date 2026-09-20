import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PhdPage from "@/app/(app)/phd/page";
import SupervisorsRadarPage from "@/app/(app)/supervisors-radar/page";
import * as api from "@/lib/api";

jest.mock("@/lib/api", () => {
  const { mockAuthApi } = jest.requireActual("../../test-utils/mock-auth");
  return mockAuthApi({ fetchRadarCases: jest.fn() });
});

const caseOut = {
  id: "case-1",
  research_state: "EVIDENCE_READY",
  suggested_disposition: "WATCH",
  user_disposition: "UNDECIDED",
  blockers: [],
  unknown_count: 0,
  deadline: { original_text: "15 January 2027", precision: "DATE_ONLY" },
  freshness: true,
};

describe("PhD route views", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.fetchRadarCases as jest.Mock).mockResolvedValue({ items: [caseOut] });
  });

  it("renders the three production PhD route tabs", async () => {
    render(<PhdPage />);
    expect(await screen.findByRole("tab", { name: "Supervisor-first" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Advertised" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Structured" })).toBeInTheDocument();
  });

  it("uses the exact SUPERVISOR_FIRST_PHD enum value", async () => {
    render(<PhdPage />);
    await waitFor(() => {
      expect(api.fetchRadarCases).toHaveBeenCalledWith({ application_route: "SUPERVISOR_FIRST_PHD" });
    });
  });

  it("uses the exact ADVERTISED_PHD enum value", async () => {
    const user = userEvent.setup();
    render(<PhdPage />);
    await user.click(await screen.findByRole("tab", { name: "Advertised" }));
    await waitFor(() => {
      expect(api.fetchRadarCases).toHaveBeenCalledWith({ application_route: "ADVERTISED_PHD" });
    });
  });

  it("uses the exact STRUCTURED_PHD enum value", async () => {
    const user = userEvent.setup();
    render(<PhdPage />);
    await user.click(await screen.findByRole("tab", { name: "Structured" }));
    await waitFor(() => {
      expect(api.fetchRadarCases).toHaveBeenCalledWith({ application_route: "STRUCTURED_PHD" });
    });
  });

  it("renders only fields supplied by CaseOut rather than fabricated dimension columns", async () => {
    const { container } = render(<PhdPage />);
    expect(await screen.findByText("Case case-1")).toBeInTheDocument();
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/Admission Viability|Supervisor Capacity|Timeline Feasibility/);
    expect(text).not.toMatch(/\bscore\b|match\s*%/i);
  });
  it("supervisors view is backed by the exact supervisor-first route", async () => {
    render(<SupervisorsRadarPage />);
    await waitFor(() => {
      expect(api.fetchRadarCases).toHaveBeenCalledWith({ application_route: "SUPERVISOR_FIRST_PHD" });
    });
    expect(await screen.findByText("Case case-1")).toBeInTheDocument();
  });

});
