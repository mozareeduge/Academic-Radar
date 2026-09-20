import { render, screen } from "@testing-library/react";
import { DimensionsTable } from "@/components/radar/DimensionsTable";
import { FundingPackages } from "@/components/radar/FundingPackages";
import type { DimensionAssessment, FundingAssessment } from "@/types";

function funding(overrides: Partial<FundingAssessment> = {}): FundingAssessment {
  return {
    id: "funding-1",
    case_id: "case-1",
    funding_route_id: "route-erasmus",
    currency: "EUR",
    award_amount: "15000.00",
    tuition_amount: "5000.00",
    duration_months: 24,
    known_costs: { tuition: "5000.00" },
    unknown_costs: { housing: "UNKNOWN" },
    uncovered_gap: "2000.00",
    state: "FUNDING_GAP",
    created_at: "2026-09-20T10:00:00Z",
    updated_at: "2026-09-20T10:00:00Z",
    ...overrides,
  };
}

describe("MA + Funding", () => {
  describe("DimensionsTable compatibility", () => {
    it("renders Admission Viability, Funding Viability, and Strategic Value as separate rows", () => {
      const dimensions: DimensionAssessment[] = [
        { name: "Admission Viability", value: 2, unknown: false },
        { name: "Funding Viability", value: 1, unknown: false },
        { name: "Strategic Value", value: 3, unknown: false },
      ];
      render(<DimensionsTable dimensions={dimensions} />);
      expect(screen.getByText("Admission Viability")).toBeInTheDocument();
      expect(screen.getByText("Funding Viability")).toBeInTheDocument();
      expect(screen.getByText("Strategic Value")).toBeInTheDocument();
      expect(screen.getAllByRole("row")).toHaveLength(4);
    });

    it("renders unknown assessment values as Unknown, never as zero", () => {
      render(<DimensionsTable dimensions={[{ name: "Funding Viability", value: null, unknown: true }]} />);
      expect(screen.getByText("Unknown")).toBeInTheDocument();
      expect(screen.queryByText("0")).not.toBeInTheDocument();
    });
  });

  describe("FundingPackages production contract", () => {
    it("renders the backend funding route id, state, and precision-preserving string amounts", () => {
      render(<FundingPackages assessments={[funding()]} />);
      expect(screen.getByText("route-erasmus")).toBeInTheDocument();
      expect(screen.getByText("FUNDING_GAP")).toBeInTheDocument();
      expect(screen.getByText("15000.00 EUR")).toBeInTheDocument();
      expect(screen.getByText("5000.00 EUR")).toBeInTheDocument();
      expect(screen.getByText("2000.00 EUR")).toBeInTheDocument();
    });

    it("renders backend known_costs and unknown_costs without inventing arithmetic", () => {
      render(<FundingPackages assessments={[funding()]} />);
      expect(screen.getByText(/"tuition": "5000.00"/)).toBeInTheDocument();
      expect(screen.getByText(/"housing": "UNKNOWN"/)).toBeInTheDocument();
    });

    it("renders Unknown when backend amount fields are null", () => {
      render(<FundingPackages assessments={[funding({ award_amount: null, tuition_amount: null, uncovered_gap: null })]} />);
      expect(screen.getAllByText("Unknown").length).toBeGreaterThanOrEqual(3);
    });

    it("does not manufacture a fully-funded label from zero gap", () => {
      const { container } = render(
        <FundingPackages assessments={[funding({ uncovered_gap: "0", state: "ELIGIBLE" })]} />,
      );
      expect(container.textContent).not.toMatch(/fully funded/i);
    });

    it("handles no assessments explicitly", () => {
      render(<FundingPackages assessments={[]} />);
      expect(screen.getByText("No funding assessments are linked to this case yet.")).toBeInTheDocument();
    });
  });
});
