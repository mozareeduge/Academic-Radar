import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RadarProfilePage from "@/app/(app)/radar/profile/page";
import { ToastProvider } from "@/components/ui/toast";
import { checkAxeViolations } from "@/test-utils/axe";
import {
  ApiError,
  createRadarRoute,
  fetchRadarProfile,
  fetchRadarRoutes,
  updateRadarProfile,
  updateRadarRoute,
} from "@/lib/api";
import type { RadarProfile, RadarRoute } from "@/types";

jest.mock("@/lib/api", () => {
  const { mockAuthApi } = jest.requireActual("../../test-utils/mock-auth");
  return mockAuthApi({
    fetchRadarProfile: jest.fn(),
    fetchRadarRoutes: jest.fn(),
    updateRadarProfile: jest.fn(),
    createRadarRoute: jest.fn(),
    updateRadarRoute: jest.fn(),
    setRadarRouteState: jest.fn(),
  });
});

const mockFetchProfile = fetchRadarProfile as jest.Mock;
const mockFetchRoutes = fetchRadarRoutes as jest.Mock;
const mockUpdateProfile = updateRadarProfile as jest.Mock;
const mockCreateRoute = createRadarRoute as jest.Mock;
const mockUpdateRoute = updateRadarRoute as jest.Mock;

const PROFILE: RadarProfile = {
  id: "profile-1",
  state: "ACTIVE",
  fixed_constraints: "English language proficiency (IELTS 7.0+)",
  education: [
    {
      degree: "BSc Physics",
      institution: "University of Example",
      year: "2020",
      provenance: { source: "CV provided by applicant", verified: true },
    },
  ],
  language_evidence: [],
  scholarly_work: [],
  artistic_curatorial_work: [],
  professional_technical_evidence: [],
  verification_status: null,
  documents: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const ROUTE: RadarRoute = {
  id: "route-1",
  name: "Quantum Simulation Route",
  state: "ACTIVE",
  route_statement: "Investigate quantum simulation supervisors.",
  core_problem: "Decoherence limits quantum advantage.",
  operations_methods: ["Topological error correction"],
  relevant_corpora_material: ["arXiv quant-ph"],
  target_disciplines: ["Quantum Physics"],
  prohibited_overclaims: ["Near-term quantum advantage claims"],
  maturity: "EXPLORATORY",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

function renderPage() {
  return render(
    <ToastProvider>
      <RadarProfilePage />
    </ToastProvider>,
  );
}

describe("RadarProfilePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetchProfile.mockResolvedValue(PROFILE);
    mockFetchRoutes.mockResolvedValue({ items: [ROUTE] });
  });

  it("loads and displays the candidate profile and routes", async () => {
    renderPage();

    expect(await screen.findByDisplayValue("English language proficiency (IELTS 7.0+)")).toBeInTheDocument();
    expect(screen.getByDisplayValue("BSc Physics")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Quantum Simulation Route")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save profile" })).toBeInTheDocument();
  });

  it("starts with an empty form (not an error) when no profile exists yet", async () => {
    mockFetchProfile.mockRejectedValue(new ApiError("No active profile found", 404));
    renderPage();

    await screen.findByTestId("education-empty");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create profile" })).toBeInTheDocument();
  });

  it("shows a retryable error when the profile fails to load for a reason other than 404", async () => {
    mockFetchProfile.mockRejectedValue(new ApiError("Server exploded", 500));
    renderPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("Server exploded");
  });

  it("saves edited constraints and existing facts, stripped of provenance", async () => {
    const user = userEvent.setup();
    mockUpdateProfile.mockResolvedValue({ ...PROFILE, fixed_constraints: "Updated constraint" });
    renderPage();

    const constraints = await screen.findByLabelText("Fixed constraints");
    await user.clear(constraints);
    await user.type(constraints, "Updated constraint");

    await user.click(screen.getByRole("button", { name: "Save profile" }));

    await waitFor(() => expect(mockUpdateProfile).toHaveBeenCalledTimes(1));
    const payload = mockUpdateProfile.mock.calls[0][0];
    expect(payload.fixed_constraints).toBe("Updated constraint");
    expect(payload.education).toEqual([
      { degree: "BSc Physics", institution: "University of Example", year: "2020" },
    ]);
    await screen.findByText("Profile saved");
  });

  it("adds a new education entry and drops empty entries on save", async () => {
    const user = userEvent.setup();
    mockUpdateProfile.mockResolvedValue(PROFILE);
    renderPage();

    await screen.findByDisplayValue("BSc Physics");
    // Add a second (blank, unfilled) entry — it should be dropped on save.
    await user.click(screen.getByRole("button", { name: "Add degree" }));
    expect(screen.getByTestId("education-entry-1")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save profile" }));

    await waitFor(() => expect(mockUpdateProfile).toHaveBeenCalledTimes(1));
    const payload = mockUpdateProfile.mock.calls[0][0];
    expect(payload.education).toHaveLength(1);
    expect(payload.education[0].degree).toBe("BSc Physics");
  });

  it("requires a name before adding a new route", async () => {
    const user = userEvent.setup();
    renderPage();
    await screen.findByDisplayValue("Quantum Simulation Route");

    await user.click(screen.getByRole("button", { name: "Add route" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/name/i);
    expect(mockCreateRoute).not.toHaveBeenCalled();
  });

  it("adds a new research route", async () => {
    const user = userEvent.setup();
    const created: RadarRoute = {
      id: "route-2",
      name: "New Route",
      state: "ACTIVE",
      route_statement: null,
      core_problem: null,
      operations_methods: [],
      relevant_corpora_material: [],
      target_disciplines: [],
      prohibited_overclaims: [],
      maturity: null,
      created_at: "2026-02-01T00:00:00Z",
      updated_at: "2026-02-01T00:00:00Z",
    };
    mockCreateRoute.mockResolvedValue(created);
    renderPage();
    await screen.findByDisplayValue("Quantum Simulation Route");

    await user.type(screen.getByLabelText("New route name"), "New Route");
    await user.click(screen.getByRole("button", { name: "Add route" }));

    await waitFor(() => expect(mockCreateRoute).toHaveBeenCalledTimes(1));
    expect(mockCreateRoute.mock.calls[0][0].name).toBe("New Route");
    expect(await screen.findByDisplayValue("New Route")).toBeInTheDocument();
  });

  it("edits and saves an existing route's fields", async () => {
    const user = userEvent.setup();
    mockUpdateRoute.mockResolvedValue({ ...ROUTE, name: "Renamed Route" });
    renderPage();

    const routeName = await screen.findByDisplayValue("Quantum Simulation Route");
    await user.clear(routeName);
    await user.type(routeName, "Renamed Route");

    await user.click(screen.getByRole("button", { name: "Save route" }));

    await waitFor(() => expect(mockUpdateRoute).toHaveBeenCalledTimes(1));
    expect(mockUpdateRoute).toHaveBeenCalledWith(
      "route-1",
      expect.objectContaining({ name: "Renamed Route" }),
    );
  });

  it("deactivates a route by setting its state to RETIRED and saving", async () => {
    const user = userEvent.setup();
    mockUpdateRoute.mockResolvedValue({ ...ROUTE, state: "RETIRED" });
    renderPage();

    await screen.findByDisplayValue("Quantum Simulation Route");
    await user.click(screen.getByRole("combobox", { name: "Route state" }));
    await user.click(await screen.findByRole("option", { name: "RETIRED" }));
    await user.click(screen.getByRole("button", { name: "Save route" }));

    await waitFor(() => expect(mockUpdateRoute).toHaveBeenCalledTimes(1));
    expect(mockUpdateRoute).toHaveBeenCalledWith(
      "route-1",
      expect.objectContaining({ state: "RETIRED" }),
    );
  });

  it("has no axe violations", async () => {
    const { container } = renderPage();
    await screen.findByDisplayValue("Quantum Simulation Route");
    await checkAxeViolations(container);
  });
});
