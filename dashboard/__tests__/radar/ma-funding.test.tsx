import { render, screen } from "@testing-library/react";
import { DimensionsTable } from "@/components/radar/DimensionsTable";
import { FundingPackages } from "@/components/radar/FundingPackages";
import type { DimensionAssessment, FundingAssessment } from "@/types";

describe("MA + Funding", () => {
  describe("DimensionsTable with three separate heads", () => {
    it("renders Admission Viability, Funding Viability, and Strategic Value as three separate labelled rows", () => {
      const dimensions: DimensionAssessment[] = [
        { name: "Admission Viability", value: 2, unknown: false },
        { name: "Funding Viability", value: 1, unknown: false },
        { name: "Strategic Value", value: 3, unknown: false },
      ];

      render(<DimensionsTable dimensions={dimensions} />);

      expect(screen.getByText("Admission Viability")).toBeInTheDocument();
      expect(screen.getByText("Funding Viability")).toBeInTheDocument();
      expect(screen.getByText("Strategic Value")).toBeInTheDocument();

      // Verify they are separate rows
      const rows = screen.getAllByRole("row");
      expect(rows.length).toBeGreaterThanOrEqual(4); // header + 3 data rows
    });

    it("does not combine three heads into a single value", () => {
      const dimensions: DimensionAssessment[] = [
        { name: "Admission Viability", value: 2, unknown: false },
        { name: "Funding Viability", value: 1, unknown: false },
        { name: "Strategic Value", value: 3, unknown: false },
      ];

      const { container } = render(<DimensionsTable dimensions={dimensions} />);

      // Should show individual values, not a combined score
      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument();
      expect(screen.getByText("3")).toBeInTheDocument();

      // Should not contain "MA score" or combined language
      expect(container.textContent).not.toMatch(/ma score|combined/i);
    });

    it("handles unknown values correctly", () => {
      const dimensions: DimensionAssessment[] = [
        { name: "Admission Viability", value: null, unknown: true },
        { name: "Funding Viability", value: 1, unknown: false },
        { name: "Strategic Value", value: null, unknown: true },
      ];

      render(<DimensionsTable dimensions={dimensions} />);

      const unknownElements = screen.getAllByText("Unknown");
      expect(unknownElements.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("FundingPackages section", () => {
    it("lists every linked FundingAssessment with all required fields", () => {
      const fundingAssessments: FundingAssessment[] = [
        {
          id: "funding-1",
          funding_route_name: "Erasmus Mundus",
          currency: "EUR",
          award: "15000",
          tuition: "5000",
          known_gap: "2000",
          unknown_cost_items: ["Living expenses", "Travel"],
          fully_funded_allowed: false,
        },
        {
          id: "funding-2",
          funding_route_name: "University Scholarship",
          currency: "GBP",
          award: "20000",
          tuition: "10000",
          known_gap: "0",
          unknown_cost_items: [],
          fully_funded_allowed: true,
        },
      ];

      render(<FundingPackages assessments={fundingAssessments} />);

      // Verify both funding packages are shown
      expect(screen.getByText("Erasmus Mundus")).toBeInTheDocument();
      expect(screen.getByText("University Scholarship")).toBeInTheDocument();

      // Verify fields are rendered
      expect(screen.getByText("EUR 15000")).toBeInTheDocument();
      expect(screen.getByText("GBP 20000")).toBeInTheDocument();
      expect(screen.getByText("5000")).toBeInTheDocument();
      expect(screen.getByText("10000")).toBeInTheDocument();
      expect(screen.getByText("2000")).toBeInTheDocument();
      expect(screen.getByText("0")).toBeInTheDocument();
    });

    it("renders unknown cost items correctly", () => {
      const fundingAssessments: FundingAssessment[] = [
        {
          id: "funding-1",
          funding_route_name: "Test Scholarship",
          currency: "EUR",
          award: "12000",
          tuition: "4000",
          known_gap: "1000",
          unknown_cost_items: ["Living expenses", "Travel insurance"],
          fully_funded_allowed: false,
        },
      ];

      render(<FundingPackages assessments={fundingAssessments} />);

      expect(screen.getByText("Living expenses")).toBeInTheDocument();
      expect(screen.getByText("Travel insurance")).toBeInTheDocument();
      expect(screen.getByText("Unknown")).toBeInTheDocument();
    });

    it("never shows 'fully funded' text unless fully_funded_allowed is true", () => {
      const fundingAssessments: FundingAssessment[] = [
        {
          id: "funding-1",
          funding_route_name: "Scholarship 1",
          currency: "EUR",
          award: "15000",
          tuition: "5000",
          known_gap: "2000",
          unknown_cost_items: ["Housing"],
          fully_funded_allowed: false,
        },
        {
          id: "funding-2",
          funding_route_name: "Scholarship 2",
          currency: "GBP",
          award: "25000",
          tuition: "10000",
          known_gap: "0",
          unknown_cost_items: [],
          fully_funded_allowed: true,
        },
      ];

      const { container } = render(
        <FundingPackages assessments={fundingAssessments} />
      );

      // Should not contain "fully funded" anywhere for first scholarship
      const text = container.textContent || "";
      const fullyFundedIndex = text.toLowerCase().indexOf("fully funded");
      const scholarship2Index = text.indexOf("Scholarship 2");

      if (fullyFundedIndex !== -1) {
        // If "fully funded" appears, it should only be after Scholarship 2
        expect(fullyFundedIndex).toBeGreaterThan(scholarship2Index);
      }
    });

    it("renders amounts from strings exactly without float rounding", () => {
      const fundingAssessments: FundingAssessment[] = [
        {
          id: "funding-1",
          funding_route_name: "Test",
          currency: "EUR",
          award: "12345.67",
          tuition: "6789.00",
          known_gap: "1234.56",
          unknown_cost_items: [],
          fully_funded_allowed: false,
        },
      ];

      render(<FundingPackages assessments={fundingAssessments} />);

      // Amounts should render exactly as provided, no rounding
      expect(screen.getByText("EUR 12345.67")).toBeInTheDocument();
      expect(screen.getByText("6789.00")).toBeInTheDocument();
      expect(screen.getByText("1234.56")).toBeInTheDocument();
    });

    it("handles empty unknown cost items", () => {
      const fundingAssessments: FundingAssessment[] = [
        {
          id: "funding-1",
          funding_route_name: "Test",
          currency: "EUR",
          award: "15000",
          tuition: "5000",
          known_gap: "0",
          unknown_cost_items: [],
          fully_funded_allowed: true,
        },
      ];

      render(<FundingPackages assessments={fundingAssessments} />);

      // Should handle empty array without errors
      expect(screen.getByText("EUR 15000")).toBeInTheDocument();
      expect(screen.getByText("5000")).toBeInTheDocument();
    });

    it("renders all unknown cost items in a list", () => {
      const fundingAssessments: FundingAssessment[] = [
        {
          id: "funding-1",
          funding_route_name: "Test",
          currency: "EUR",
          award: "15000",
          tuition: "5000",
          known_gap: "1000",
          unknown_cost_items: ["Housing", "Food", "Transport"],
          fully_funded_allowed: false,
        },
      ];

      render(<FundingPackages assessments={fundingAssessments} />);

      expect(screen.getByText("Housing")).toBeInTheDocument();
      expect(screen.getByText("Food")).toBeInTheDocument();
      expect(screen.getByText("Transport")).toBeInTheDocument();
    });
  });
});
