import { fetchRadarCases, fetchRadarQueue, setUserDisposition } from "@/lib/api";

function response(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
    headers: new Headers(),
  } as Response;
}

describe("Academic Radar API contract", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    document.cookie = "cik_token=; Max-Age=0; path=/";
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  it("uses GET /api/radar/cases for the queue rather than a fixture-only /queue endpoint", async () => {
    global.fetch = jest.fn().mockResolvedValue(response({ items: [] })) as jest.Mock;

    await fetchRadarQueue();

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe(
      "http://localhost:8000/api/radar/cases",
    );
  });

  it("passes exact ApplicationRoute and ResearchState strings as case filters", async () => {
    global.fetch = jest.fn().mockResolvedValue(response({ items: [] })) as jest.Mock;

    await fetchRadarCases({
      application_route: "SUPERVISOR_FIRST_PHD",
      research_state: "EVIDENCE_READY",
    });

    expect((global.fetch as jest.Mock).mock.calls[0][0]).toBe(
      "http://localhost:8000/api/radar/cases?application_route=SUPERVISOR_FIRST_PHD&research_state=EVIDENCE_READY",
    );
  });

  it("keeps suggestion separate from the user-owned disposition field", async () => {
    global.fetch = jest.fn().mockResolvedValue(
      response({
        id: "case-1",
        research_state: "EVIDENCE_READY",
        suggested_disposition: "WATCH",
        user_disposition: "ACT",
        blockers: [],
        unknown_count: 0,
        deadline: null,
        freshness: true,
      }),
    ) as jest.Mock;

    await setUserDisposition("case-1", "ACT", "ready to apply");

    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/radar/cases/case-1/disposition");
    expect(JSON.parse(init.body)).toEqual({ value: "ACT", reason: "ready to apply" });
    expect(init.body).not.toContain("suggested_disposition");
  });
});
