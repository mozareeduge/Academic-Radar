from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IdentityStatus(str, Enum):
    RESOLVED = "RESOLVED"
    CANDIDATE = "CANDIDATE"
    UNRESOLVED_DIFFERENT = "UNRESOLVED_DIFFERENT"


@dataclass
class PersonRecord:
    name: str
    institution: str
    orcid: Optional[str] = None
    openalex_id: Optional[str] = None
    openaire_id: Optional[str] = None
    official_url: Optional[str] = None
    works: set = field(default_factory=set)
    topics: set = field(default_factory=set)


@dataclass
class Resolution:
    status: IdentityStatus
    basis: str


def _normalize_string(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    return s.lower().strip()


def resolve(a: PersonRecord, b: PersonRecord) -> Resolution:
    """
    Resolve identity between two person records.

    Rules (in order):
    1. If both have same explicit external ID (ORCID/OpenAlex/OpenAIRE) -> RESOLVED
    2. If different explicit IDs of the same kind -> UNRESOLVED_DIFFERENT
    3. If same official_url AND same institution -> RESOLVED
    4. If same normalized name AND same institution AND (works or topics overlap >= 1) -> RESOLVED
    5. Different institution with same name and no shared ID -> CANDIDATE (never RESOLVED)
    6. Otherwise -> CANDIDATE (unresolved)
    """

    # Rule 1 & 2: explicit external IDs
    external_ids = {
        'orcid': (a.orcid, b.orcid),
        'openalex_id': (a.openalex_id, b.openalex_id),
        'openaire_id': (a.openaire_id, b.openaire_id),
    }

    for id_type, (id_a, id_b) in external_ids.items():
        if id_a and id_b:
            if id_a == id_b:
                return Resolution(IdentityStatus.RESOLVED, f'external_id:{id_type}')
            else:
                return Resolution(IdentityStatus.UNRESOLVED_DIFFERENT, f'different_{id_type}')

    # Rule 3: same official_url AND same institution
    if a.official_url and b.official_url and a.official_url == b.official_url:
        if _normalize_string(a.institution) == _normalize_string(b.institution):
            return Resolution(IdentityStatus.RESOLVED, 'official_url+institution')

    # Rule 4: same normalized name AND same institution AND corroboration
    a_name = _normalize_string(a.name)
    b_name = _normalize_string(b.name)
    a_inst = _normalize_string(a.institution)
    b_inst = _normalize_string(b.institution)

    if a_name and b_name and a_name == b_name and a_inst and b_inst and a_inst == b_inst:
        # Check for overlap in works or topics
        if a.works & b.works or a.topics & b.topics:
            return Resolution(IdentityStatus.RESOLVED, 'name+institution+corroboration')

    # Rule 5: Different institution with same name and no shared ID -> CANDIDATE, never RESOLVED
    if a_name and b_name and a_name == b_name:
        if a_inst != b_inst:
            return Resolution(IdentityStatus.CANDIDATE, 'different_institutions_same_name')
        # Same institution, same name, but no corroboration -> CANDIDATE
        return Resolution(IdentityStatus.CANDIDATE, 'same_institution_same_name_no_corroboration')

    # Rule 6: Otherwise -> CANDIDATE
    return Resolution(IdentityStatus.CANDIDATE, 'unresolved')


def can_merge_relation(resolution: Resolution) -> bool:
    """
    Determine if two entities can have their relations merged based on identity resolution.

    Only RESOLVED identities permit relation merges (publications, supervision, grants, etc.).
    CANDIDATE or UNRESOLVED_DIFFERENT block merges.
    """
    return resolution.status == IdentityStatus.RESOLVED


def check_no_same_name_merge(resolve_fn) -> None:
    """
    Canary assertion: verify that two same-name people at different institutions
    without shared IDs do NOT resolve to RESOLVED status.

    This is a negative proof function for testing mutation of resolve logic.
    """
    person_a = PersonRecord(
        name='Jan Peeters',
        institution='KU Leuven',
        orcid='0000-0001-2345-6789',
        openalex_id='A123456',
        openaire_id='O123456',
        official_url=None,
        works=set(),
        topics=set(),
    )

    person_b = PersonRecord(
        name='Jan Peeters',
        institution='Ghent University',
        orcid=None,
        openalex_id=None,
        openaire_id=None,
        official_url=None,
        works=set(),
        topics=set(),
    )

    resolution = resolve_fn(person_a, person_b)

    assert resolution.status != IdentityStatus.RESOLVED, (
        f"same-name people at different institutions without shared IDs should not "
        f"RESOLVE; got {resolution.status} with basis={resolution.basis}"
    )
