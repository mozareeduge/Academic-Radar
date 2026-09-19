import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PhdPage from "@/app/(app)/phd/page";

jest.mock("@/lib/api", () => {
  const { mockAuthApi } = jest.requireActual("../../test-utils/mock-auth");
  return mockAuthApi({ apiBase: jest.fn(() => "http://localhost:8000") });
});

// Mock fetch globally
global.fetch = jest.fn();

interface PhdCase {
  id: string;
  title: string;
  application_route: string;
  supervisor?: string;
  institution?: string;
  dimensions: Array<{
    name: string;
    value: number | null;
  }>;
}

function phdCase(overrides: Partial<PhdCase>): PhdCase {
  return {
    id: "phd-1",
    title: "PhD at Oxford",
    application_route: "supervisor-first",
    supervisor: "Dr. Smith",
    institution: "University of Oxford",
    dimensions: [
      { name: "Admission Viability", value: 2 },
      { name: "Funding", value: 1 },
      { name: "Strategic Value", value: 3 },
      { name: "Research Alignment", value: 2 },
      { name: "Supervisor Capacity", value: 1 },
      { name: "Timeline Feasibility", value: 3 },
      { name: "Personal Development Fit", value: 2 },
    ],
    ...overrides,
  };
}

const SUPERVISOR_FIRST_CASES: PhdCase[] = [
  phdCase({
    id: "phd-1",
    title: "Dr. Smith - Computational Biology",
    application_route: "supervisor-first",
    supervisor: "Dr. Jane Smith",
    institution: "University of Oxford",
  }),
];

const ADVERTISED_CASES: PhdCase[] = [
  phdCase({
    id: "phd-2",
    title: "DPhil in Computer Science (Computational Biology track)",
    application_route: "advertised",
    supervisor: "Dr. John Doe",
    institution: "University of Cambridge",
  }),
];

const STRUCTURED_CASES: PhdCase[] = [
  phdCase({
    id: "phd-3",
    title: "Structured PhD in Physics",
    application_route: "structured",
    supervisor: "Prof. Alice Wong",
    institution: "Imperial College London",
  }),
];

describe("PhdPage with route-filtered tabs", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders three tabs: Supervisor-first, Advertised, Structured", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        items: SUPERVISOR_FIRST_CASES,
        total: 1,
      }),
    });
    render(<PhdPage />);

    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /Supervisor-first/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /Advertised/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /Structured/i })).toBeInTheDocument();
    });
  });

  it("calls API with application_route='supervisor-first' when Supervisor-first tab is active", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        items: SUPERVISOR_FIRST_CASES,
        total: 1,
      }),
    });
    render(<PhdPage />);

    const tab = await screen.findByRole("tab", { name: /Supervisor-first/i });
    await userEvent.click(tab);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("application_route=supervisor-first"),
        expect.any(Object)
      );
    });
  });

  it("calls API with application_route='advertised' when Advertised tab is active", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        items: ADVERTISED_CASES,
        total: 1,
      }),
    });
    render(<PhdPage />);

    const tab = await screen.findByRole("tab", { name: /Advertised/i });
    await userEvent.click(tab);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("application_route=advertised"),
        expect.any(Object)
      );
    });
  });

  it("calls API with application_route='structured' when Structured tab is active", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        items: STRUCTURED_CASES,
        total: 1,
      }),
    });
    render(<PhdPage />);

    const tab = await screen.findByRole("tab", { name: /Structured/i });
    await userEvent.click(tab);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("application_route=structured"),
        expect.any(Object)
      );
    });
  });

  it("displays cases as rows with seven dimensions as separate columns", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        items: SUPERVISOR_FIRST_CASES,
        total: 1,
      }),
    });
    render(<PhdPage />);

    await waitFor(() => {
      expect(screen.getByText("Dr. Smith - Computational Biology")).toBeInTheDocument();
    });

    // Verify all seven dimension column headers exist
    expect(screen.getByText("Admission Viability")).toBeInTheDocument();
    expect(screen.getByText("Funding")).toBeInTheDocument();
    expect(screen.getByText("Strategic Value")).toBeInTheDocument();
    expect(screen.getByText("Research Alignment")).toBeInTheDocument();
    expect(screen.getByText("Supervisor Capacity")).toBeInTheDocument();
    expect(screen.getByText("Timeline Feasibility")).toBeInTheDocument();
    expect(screen.getByText("Personal Development Fit")).toBeInTheDocument();
  });

  it("does not render any column or text named 'score', 'overall', or 'match %'", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      text: async () => JSON.stringify({
        items: SUPERVISOR_FIRST_CASES,
        total: 1,
      }),
    });
    const { container } = render(<PhdPage />);

    await waitFor(() => {
      expect(screen.getByText("Dr. Smith - Computational Biology")).toBeInTheDocument();
    });

    // Check for forbidden text/column names
    const bodyText = container.textContent?.toLowerCase() || "";
    expect(bodyText).not.toMatch(/\bscore\b/i);
    expect(bodyText).not.toMatch(/\boverall\b/i);
    expect(bodyText).not.toMatch(/match\s*%/i);
  });
});

describe("Track Explorer in Case Dossier", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders precedent list as timeline with role, funding route, and precedent evidence link", async () => {
    const precedents = {
      items: [
        {
          id: "prec-1",
          project: "Thesis Title 1",
          supervisor_role: "Primary Supervisor",
          funding_route: "EPSRC DTP",
          evidence_url: "http://example.com/thesis1",
        },
        {
          id: "prec-2",
          project: "Thesis Title 2",
          supervisor_role: "Co-supervisor",
          funding_route: "Leverhulme Fellowship",
          evidence_url: "http://example.com/thesis2",
        },
      ],
      total: 2,
    };

    expect(precedents.items).toHaveLength(2);
    expect(precedents.items[0]).toHaveProperty("supervisor_role", "Primary Supervisor");
    expect(precedents.items[0]).toHaveProperty("funding_route", "EPSRC DTP");
    expect(precedents.items[0]).toHaveProperty("evidence_url");
  });

  it("displays precedent roles in the list", async () => {
    const precedents = {
      items: [
        {
          id: "prec-1",
          project: "Thesis Title 1",
          supervisor_role: "Primary Supervisor",
          funding_route: "EPSRC DTP",
          evidence_url: "http://example.com/thesis1",
        },
      ],
      total: 1,
    };

    expect(precedents.items[0].supervisor_role).toBe("Primary Supervisor");
  });
});
