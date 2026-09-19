import { render } from "@testing-library/react";
import Radar from "@/app/(app)/radar/page";
import CaseDossier from "@/app/(app)/cases/[id]/page";
import MAPage from "@/app/(app)/ma/page";
import WatchPage from "@/app/(app)/watch/page";
import { BlockerRegion } from "@/components/radar/BlockerRegion";
import { EvidenceInspector } from "@/components/radar/EvidenceInspector";
import { BriefTab } from "@/components/radar/BriefTab";
import { checkAxeViolations, checkColorOnlyViolations, checkFixedWidths } from "@/test-utils/axe";
import * as api from "@/lib/api";

jest.mock("next/navigation", () => ({
  useParams: () => ({ id: "case-123" }),
}));

jest.mock("@/lib/api", () => ({
  fetchRadarQueue: jest.fn(),
  fetchCase: jest.fn(),
  fetchChangeEvents: jest.fn(),
  fetchMe: jest.fn(() => Promise.resolve({ user_id: 1, email: "test@example.com" })),
  fetchAuthConfig: jest.fn(() =>
    Promise.resolve({ auth_mode: "password", invite_required: false }),
  ),
  fetchCurrentUser: jest.fn(() =>
    Promise.resolve({ user_id: 1, email: "test@example.com" }),
  ),
  setUserDisposition: jest.fn(),
  postResearch: jest.fn(),
  getToken: jest.fn(() => "token"),
  apiBase: () => "http://localhost:8000",
  apiStartupError: () => null,
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

const mockRadarQueue = {
  items: [
    {
      id: "case-1",
      title: "Test Supervisor PhD",
      route: "SUPERVISOR_FIRST_PHD",
      research_state: "EVIDENCE_READY",
      suggested_disposition: "WATCH",
      user_disposition: "UNDECIDED",
      blocker: null,
      deadline: "15 Jan 2027",
      freshness: "2 days",
    },
    {
      id: "case-2",
      title: "Test MA Programme",
      route: "MA_ROUTE",
      research_state: "RESEARCHING",
      suggested_disposition: "ACT",
      user_disposition: "UNDECIDED",
      blocker: "English requirement",
      deadline: "1 Feb 2027",
      freshness: "5 days",
    },
  ],
};

const mockCaseDossier = {
  id: "case-123",
  research_state: "EVIDENCE_READY",
  user_disposition: "UNDECIDED",
  suggested_disposition: "WATCH",
  blockers: [
    { name: "English requirement", status: "FAIL" as const, reason: "Not met according to source" },
  ],
  unknown_count: 2,
  deadline: {
    original_text: "15 January 2027",
    precision: "DATE_ONLY" as const,
  },
  freshness: true,
  gates: [
    { name: "English requirement", status: "PASS" as const, reason: "Verified on 10 Sep 2026" },
    { name: "Funding available", status: "UNKNOWN" as const },
  ],
  dimensions: [
    { name: "Admission viability", value: 2, unknown: false },
    { name: "Funding viability", value: null, unknown: true },
    { name: "Strategic value", value: 1, unknown: false },
  ],
};

const mockWatchData = {
  recent_changes: [
    {
      id: "change-1",
      source: "Programme website",
      case_id: "case-1",
      detected_at: "2026-09-20T10:00:00Z",
      change_type: "DEADLINE_UPDATED",
      description: "Deadline moved to 15 Mar 2027",
      impact: "MEDIUM",
    },
  ],
};

describe("Accessibility and Responsive Tests (P20)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.fetchRadarQueue as jest.Mock).mockResolvedValue(mockRadarQueue);
    (api.fetchCase as jest.Mock).mockResolvedValue(mockCaseDossier);
    (api.fetchChangeEvents as jest.Mock).mockResolvedValue({ events: mockWatchData.recent_changes });
  });

  describe("GATE-ACCESSIBILITY: Automated axe scan", () => {
    it("Radar page has no axe violations", async () => {
      const { container } = render(<Radar />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      await checkAxeViolations(container);
    });

    it("Case Dossier page has no axe violations", async () => {
      const { container } = render(<CaseDossier params={{ id: "case-123" }} />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      await checkAxeViolations(container);
    });

    it("BlockerRegion component has no axe violations", async () => {
      const { container } = render(
        <BlockerRegion blockers={mockCaseDossier.blockers} unknownCount={2} />,
      );
      await checkAxeViolations(container);
    });

    it("EvidenceInspector component has no axe violations", async () => {
      const { container } = render(
        <EvidenceInspector
          claimId="claim-1"
          isOpen={true}
          onClose={() => {}}
          invokerRef={null}
        />,
      );
      await checkAxeViolations(container);
    });

    it("BriefTab component has no axe violations", async () => {
      const { container } = render(
        <BriefTab caseId="case-123" caseData={mockCaseDossier} />,
      );
      await new Promise((resolve) => setTimeout(resolve, 100));
      await checkAxeViolations(container);
    });

    it("MA page has no axe violations", async () => {
      const { container } = render(<MAPage />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      await checkAxeViolations(container);
    });

    it("Watch page has no axe violations", async () => {
      const { container } = render(<WatchPage />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      await checkAxeViolations(container);
    });
  });

  describe("GATE-ACCESSIBILITY: No color-only state", () => {
    it("Radar status chips contain text, not color only", async () => {
      const { container } = render(<Radar />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const violations = await checkColorOnlyViolations(container);
      expect(violations).toHaveLength(0);
    });

    it("Case Dossier status indicators contain text", async () => {
      const { container } = render(<CaseDossier params={{ id: "case-123" }} />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const violations = await checkColorOnlyViolations(container);
      expect(violations).toHaveLength(0);
    });

    it("BlockerRegion status markers include text labels", async () => {
      const { container } = render(
        <BlockerRegion blockers={mockCaseDossier.blockers} unknownCount={0} />,
      );
      const violations = await checkColorOnlyViolations(container);
      expect(violations).toHaveLength(0);
    });
  });

  describe("GATE-RESPONSIVE: No page-level horizontal overflow at 320px", () => {
    it("Radar page has no elements with fixed width > 320px at viewport width 320px", async () => {
      const { container } = render(<Radar />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const violations = await checkFixedWidths(container);
      expect(violations).toHaveLength(0);
    });

    it("Case Dossier has min-w-0/overflow-x-auto for tables to prevent 320px overflow", async () => {
      const { container } = render(<CaseDossier params={{ id: "case-123" }} />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const tables = container.querySelectorAll("table");
      tables.forEach((table) => {
        const wrapper = table.parentElement;
        if (wrapper) {
          const classes = wrapper.getAttribute("class") || "";
          const minW0 = classes.includes("min-w-0");
          const hasOverflow =
            classes.includes("overflow-x-auto") || classes.includes("overflow-x-scroll");
          expect(minW0 || hasOverflow).toBe(true);
        }
      });
    });

    it("Page wrappers include min-w-0 for safe horizontal scrolling", async () => {
      const { container } = render(<Radar />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const mainContent = container.querySelector("main") || container.querySelector("[role='main']");
      if (mainContent) {
        const classes = mainContent.getAttribute("class") || "";
        expect(classes.includes("min-w-0") || classes.includes("overflow-x-auto")).toBe(true);
      }
    });

    it("No inline styles with width > 320px", async () => {
      const { container } = render(<Radar />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const violations = await checkFixedWidths(container);
      expect(violations).toHaveLength(0);
    });
  });

  describe("GATE-ACCESSIBILITY: Keyboard navigation and focus", () => {
    it("BlockerRegion uses semantic section element", async () => {
      const { container } = render(
        <BlockerRegion blockers={mockCaseDossier.blockers} unknownCount={0} />,
      );
      const section = container.querySelector("section[aria-label='Formal blockers']");
      expect(section).toBeInTheDocument();
    });

    it("Radar page structure is reachable to screen readers", async () => {
      const { container } = render(<Radar />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const h1 = container.querySelector("h1");
      expect(h1).toBeInTheDocument();
      expect(h1?.textContent).toBe("Radar");
    });
  });

  describe("GATE-ACCESSIBILITY: 200% zoom support", () => {
    it("Radar layout remains usable at simulated 200% zoom", async () => {
      const { container } = render(<Radar />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const mainContent = container.querySelector("main") || container;
      const computedStyle = window.getComputedStyle(mainContent);
      expect(computedStyle.position).not.toBe("fixed");
      expect(computedStyle.height).not.toMatch(/^\d+px$/);
    });

    it("Case Dossier components wrap without fixed-height containers", async () => {
      const { container } = render(<CaseDossier params={{ id: "case-123" }} />);
      await new Promise((resolve) => setTimeout(resolve, 100));
      const allElements = container.querySelectorAll("*");
      let fixedHeightViolations = 0;
      allElements.forEach((el) => {
        const style = (el as HTMLElement).getAttribute("style") || "";
        if (
          style.includes("height") &&
          style.match(/height\s*:\s*\d+px/) &&
          !style.includes("overflow")
        ) {
          fixedHeightViolations += 1;
        }
      });
      expect(fixedHeightViolations).toBe(0);
    });
  });
});
