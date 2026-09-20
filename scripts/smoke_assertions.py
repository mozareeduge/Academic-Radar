"""Independent, database-level verifier for the end-to-end smoke.

Reads the SQLite file the API wrote to. It checks REAL persisted state, so dev/fixture endpoints cannot fake it.
Usage: python scripts/smoke_assertions.py <sqlite_path> [--stage research|all]
Not editable by executors (protected by the slice rules).
"""
import sqlite3
import sys

db = sys.argv[1]
stage = "all"
if "--stage" in sys.argv:
    stage = sys.argv[sys.argv.index("--stage") + 1]

con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
errs = []


def q(sql, *a):
    return con.execute(sql, a).fetchall()


def check(cond, msg):
    if not cond:
        errs.append(msg)


SUP_MANDATORY = ["IDENTITY_POSITION", "RESEARCH_OBJECTS", "THEORY_TOOLKIT", "METHODS", "RECENT_WORKS",
                 "PROJECTS_GRANTS", "SUPERVISION_RECORD", "SUPERVISED_PROJECTS"]
MA_MANDATORY = ["FORMAL_ELIGIBILITY", "CURRICULUM_FIT", "ENGLISH_REQUIREMENT", "DEADLINE", "EXISTING_MA_RULE"]
COVERED = ("SEARCHED_FOUND", "SEARCHED_NONE_FOUND")

sup = q("select * from radar_evaluation_cases where application_route='SUPERVISOR_FIRST_PHD'")
ma = q("select * from radar_evaluation_cases where application_route='MA_PROGRAMME'")
check(len(sup) >= 1, "no supervisor-first case exists")
check(len(ma) >= 1, "no MA programme case exists")


def verify_research(case, mandatory, label):
    runs = q("select * from radar_research_runs where case_id=? and status='COMPLETE'", case["id"])
    check(len(runs) >= 1, f"{label}: no COMPLETE research run persisted")
    if not runs:
        return
    check(runs[0]["protocol_version"] == "1.0.0", f"{label}: run did not record protocol_version 1.0.0")
    check(bool(runs[0]["prompt_hash"]) and bool(runs[0]["schema_version"]), f"{label}: run identity incomplete")
    cov = {r["evidence_class"]: r["status"] for r in q("select * from radar_research_coverage where run_id=?", runs[0]["id"])}
    for c in mandatory:
        check(cov.get(c) in COVERED, f"{label}: mandatory class {c} not covered (got {cov.get(c)})")
    claims = q("select * from radar_claims where case_id=?", case["id"])
    check(len(claims) >= 3, f"{label}: fewer than 3 persisted claims ({len(claims)})")
    for cl in claims:
        if cl["claim_type"] != "UNKNOWN":
            n = q("select count(*) c from radar_claim_evidence where claim_id=?", cl["id"])[0]["c"]
            check(n >= 1, f"{label}: consequential claim {cl['id']} has no evidence link")


if sup:
    verify_research(sup[0], SUP_MANDATORY, "supervisor case")
if ma:
    verify_research(ma[0], MA_MANDATORY, "MA case")

check(q("select count(*) c from radar_evidence_dependencies")[0]["c"] >= 2, "fewer than 2 evidence dependency edges persisted")
check(all(r["user_disposition"] == "UNDECIDED" for r in sup + ma), "automation changed a user disposition")
check(q("select count(*) c from radar_case_disposition_history where actor!='USER'")[0]["c"] == 0,
      "a non-USER row exists in disposition history")

if stage == "research":
    check(all(r["research_state"] == "EVIDENCE_READY" for r in (sup[:1] + ma[:1])),
          "after research both cases must be EVIDENCE_READY")
else:
    fa = q("select * from radar_funding_assessments where case_id=?", ma[0]["id"]) if ma else []
    check(len(fa) >= 2, f"MA case needs >= 2 funding assessments ({len(fa)})")
    for f in fa:
        check(f["currency"] is not None and f["award_amount"] is not None, "funding assessment missing currency/award")
    snaps = q("select state from radar_source_snapshots")
    check(any(s["state"] == "CHANGED" for s in snaps), "no CHANGED snapshot recorded by the watch")
    check(q("select count(*) c from radar_change_events where material=1")[0]["c"] >= 1, "no material change event")
    if sup and ma:
        check(ma[0]["research_state"] == "STALE", f"MA case must be STALE after its funding source changed (is {ma[0]['research_state']})")
        check(sup[0]["research_state"] == "EVIDENCE_READY",
              f"unrelated supervisor case must stay EVIDENCE_READY (is {sup[0]['research_state']}): invalidation must be targeted")
    briefs = q("select * from radar_application_briefs")
    check(len(briefs) >= 1, "no application brief persisted")
    for b in briefs:
        n = q("select count(*) c from radar_brief_dependencies where brief_id=?", b["id"])[0]["c"]
        check(n >= 1, f"brief {b['id']} has no recorded dependencies")

if errs:
    print("SMOKE ASSERTIONS FAILED:")
    for e in errs:
        print(" -", e)
    sys.exit(1)
print(f"SMOKE ASSERTIONS OK (stage={stage})")
