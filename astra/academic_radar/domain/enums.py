from enum import Enum


class ResearchState(str, Enum):
    DISCOVERED = "DISCOVERED"
    TRIAGED = "TRIAGED"
    RESEARCHING = "RESEARCHING"
    EVIDENCE_READY = "EVIDENCE_READY"
    STALE = "STALE"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class UserDisposition(str, Enum):
    UNDECIDED = "UNDECIDED"
    STRONG = "STRONG"
    WATCH = "WATCH"
    ACT = "ACT"
    REJECTED = "REJECTED"


class ApplicationStage(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    PREPARING = "PREPARING"
    CONTACTED = "CONTACTED"
    APPLICATION_OPEN = "APPLICATION_OPEN"
    APPLIED = "APPLIED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    DECLINED = "DECLINED"
    CLOSED = "CLOSED"


class ClaimType(str, Enum):
    EXTERNAL_FACT = "EXTERNAL_FACT"
    OBSERVED_RELATION = "OBSERVED_RELATION"
    INFERENCE = "INFERENCE"
    USER_DECISION = "USER_DECISION"


class ClaimStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"


class SnapshotState(str, Enum):
    CAPTURED = "CAPTURED"
    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"
    FETCH_FAILED = "FETCH_FAILED"


class GateResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    STALE = "STALE"


class SourceAuthority(str, Enum):
    OFFICIAL_REGULATION = "OFFICIAL_REGULATION"
    OFFICIAL_PROGRAMME = "OFFICIAL_PROGRAMME"
    OFFICIAL_DEPARTMENT_OR_PERSON = "OFFICIAL_DEPARTMENT_OR_PERSON"
    AUTHORITATIVE_REGISTRY = "AUTHORITATIVE_REGISTRY"
    PRIMARY_RESEARCH_OUTPUT = "PRIMARY_RESEARCH_OUTPUT"
    REPUTABLE_SECONDARY = "REPUTABLE_SECONDARY"
    DISCOVERY_AGGREGATOR = "DISCOVERY_AGGREGATOR"
    UNKNOWN = "UNKNOWN"


class DeadlinePrecision(str, Enum):
    DATE_ONLY = "DATE_ONLY"
    LOCAL_TIME = "LOCAL_TIME"
    OFFSET_AWARE = "OFFSET_AWARE"
    AMBIGUOUS = "AMBIGUOUS"


class RouteState(str, Enum):
    ACTIVE = "ACTIVE"
    EXPLORATORY = "EXPLORATORY"
    DORMANT = "DORMANT"
    RETIRED = "RETIRED"


class ProfileState(str, Enum):
    ACTIVE = "ACTIVE"
    NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
    SUPERSEDED = "SUPERSEDED"


class CoverageStatus(str, Enum):
    SEARCHED_FOUND = "SEARCHED_FOUND"
    SEARCHED_NONE_FOUND = "SEARCHED_NONE_FOUND"
    NOT_SEARCHED = "NOT_SEARCHED"
    BLOCKED = "BLOCKED"


class TargetKind(str, Enum):
    Person = "Person"
    Programme = "Programme"
    PhDOpportunity = "PhDOpportunity"
    FundedProject = "FundedProject"
    Institution = "Institution"
    FundingRoute = "FundingRoute"
    SupervisedProject = "SupervisedProject"
    Work = "Work"


class ApplicationRoute(str, Enum):
    SUPERVISOR_FIRST_PHD = "SUPERVISOR_FIRST_PHD"
    ADVERTISED_PHD = "ADVERTISED_PHD"
    STRUCTURED_PHD = "STRUCTURED_PHD"
    MA_PROGRAMME = "MA_PROGRAMME"


class IdentityStatus(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    CANDIDATE = "CANDIDATE"


class ResearchRunStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


LEGAL_TRANSITIONS: dict[ResearchState, set[ResearchState]] = {
    ResearchState.DISCOVERED: {ResearchState.TRIAGED, ResearchState.ARCHIVED},
    ResearchState.TRIAGED: {ResearchState.RESEARCHING, ResearchState.ARCHIVED},
    ResearchState.RESEARCHING: {ResearchState.EVIDENCE_READY, ResearchState.FAILED},
    ResearchState.FAILED: {ResearchState.RESEARCHING, ResearchState.ARCHIVED},
    ResearchState.EVIDENCE_READY: {ResearchState.STALE, ResearchState.RESEARCHING, ResearchState.ARCHIVED},
    ResearchState.STALE: {ResearchState.RESEARCHING, ResearchState.ARCHIVED},
}


def can_transition(a: ResearchState, b: ResearchState) -> bool:
    """Check if transition from state a to state b is legal."""
    return b in LEGAL_TRANSITIONS.get(a, set())
