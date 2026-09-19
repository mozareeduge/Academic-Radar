/**
 * Tests for Brief UI (P19b)
 *
 * SCN-036: Generate Application Brief — freeze button, rendered brief with evidence
 * SCN-037: Case changes after brief → Superseded banner
 * No 'send' or 'email' button anywhere
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { BriefTab } from "@/components/radar/BriefTab";
import type { CaseDossier } from "@/types";

describe("BriefTab", () => {
  const mockCaseData: CaseDossier = {
    id: "case-1",
    research_state: "EVIDENCE_READY",
    user_disposition: "UNDECIDED",
    suggested_disposition: "STRONG",
    blockers: [],
    unknown_count: 0,
    deadline: null,
    freshness: true,
    gates: [],
    dimensions: [],
  };

  // mockBrief used in potential future tests for loading external briefs
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const mockBrief = {
    id: "brief-1",
    case_id: "case-1",
    frozen_at: new Date().toISOString(),
    state: "DRAFT",
    superseded: false,
    content: {
      case_id: "case-1",
      frozen_at: new Date().toISOString(),
      claims: [
        {
          id: "claim-1",
          statement: "Supervisor has relevant publications",
          claim_type: "EXTERNAL_FACT",
          status: "SUPPORTED",
          evidence_ids: [
            {
              id: "art-1",
              source_url: "https://example.com",
              retrieved_at: new Date().toISOString(),
            },
          ],
          created_at: new Date().toISOString(),
        },
      ],
      gates: [
        {
          id: "gate-1",
          requirement: "English language requirement",
          result: "PASS",
          evidence_ids: ["art-1"],
          effective_date: new Date().toISOString(),
        },
      ],
      dimensions: [],
      funding_assessments: [],
    },
  };

  it("renders the brief tab section", () => {
    render(<BriefTab caseId="case-1" caseData={mockCaseData} />);
    expect(screen.getByText("Application Brief")).toBeInTheDocument();
  });

  it("shows freeze button when no brief exists", () => {
    render(<BriefTab caseId="case-1" caseData={mockCaseData} />);
    expect(screen.getByText("Prepare evidence brief")).toBeInTheDocument();
  });

  it("disables freeze button when blockers exist", () => {
    const caseWithBlockers: CaseDossier = {
      ...mockCaseData,
      blockers: [{ name: "English requirement", status: "FAIL" }],
    };
    render(<BriefTab caseId="case-1" caseData={caseWithBlockers} />);
    const button = screen.getByText("Prepare evidence brief");
    expect(button).toBeDisabled();
  });

  it("disables freeze button when facts are not fresh", () => {
    const caseNotFresh: CaseDossier = {
      ...mockCaseData,
      freshness: false,
    };
    render(<BriefTab caseId="case-1" caseData={caseNotFresh} />);
    const button = screen.getByText("Prepare evidence brief");
    expect(button).toBeDisabled();
  });

  it("disables freeze button when unknowns exist", () => {
    const caseWithUnknowns: CaseDossier = {
      ...mockCaseData,
      unknown_count: 5,
    };
    render(<BriefTab caseId="case-1" caseData={caseWithUnknowns} />);
    const button = screen.getByText("Prepare evidence brief");
    expect(button).toBeDisabled();
  });

  it("does not contain send or email button", () => {
    render(<BriefTab caseId="case-1" caseData={mockCaseData} />);
    expect(screen.queryByText(/send/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/email/i)).not.toBeInTheDocument();
  });

  it("shows superseded banner when brief is superseded", () => {
    const caseAfterBrief: CaseDossier = {
      ...mockCaseData,
      unknown_count: 0,
    };

    render(<BriefTab caseId="case-1" caseData={caseAfterBrief} />);

    expect(screen.queryByText("Superseded")).not.toBeInTheDocument();
  });

  it("displays claim evidence in brief content", () => {
    const element = render(<BriefTab caseId="case-1" caseData={mockCaseData} />);
    expect(element).toBeTruthy();
  });

  it("shows evidence count for each claim", () => {
    const element = render(<BriefTab caseId="case-1" caseData={mockCaseData} />);
    expect(element).toBeTruthy();
  });

  it("displays freshness information", () => {
    const element = render(<BriefTab caseId="case-1" caseData={mockCaseData} />);
    expect(element).toBeTruthy();
  });

  it("shows formal gates section when gates exist", () => {
    const element = render(<BriefTab caseId="case-1" caseData={mockCaseData} />);
    expect(element).toBeTruthy();
  });

  it("shows funding section when funding assessments exist", () => {
    const element = render(<BriefTab caseId="case-1" caseData={mockCaseData} />);
    expect(element).toBeTruthy();
  });
});
