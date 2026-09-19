"""Source authority classification and canonical-origin grouping.

OBJ-018: SourceAuthority with host rules and text-hash grouping for syndication detection.
DEC-037: Official current programme/funder rules govern formal gates.
DEC-038: Copied evidence grouped by canonical-origin, not counted as independent.
"""

import hashlib
import re
from urllib.parse import urlparse

from academic_radar.domain.enums import SourceAuthority


def classify_source(url: str) -> SourceAuthority:
    """Classify a URL into a SourceAuthority category.

    Rules are applied in order of host suffix matching:
    - Belgian/Dutch/German universities (official department or programme)
    - Authoritative registries (OpenAlex, OpenAIRE, ORCID, ROR)
    - Primary research outputs (DOI)
    - Discovery aggregators (job boards, portals)
    - Everything else: UNKNOWN

    Programme classification triggered by path keywords: /programme, /program,
    /master, /phd, /studium, /admission.
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        path = parsed.path.lower()
    except Exception:
        return SourceAuthority.UNKNOWN

    if not host:
        return SourceAuthority.UNKNOWN

    host_lower = host.lower()

    # Authoritative registries (checked first, path-independent)
    if host_lower in ("api.openalex.org", "openalex.org"):
        return SourceAuthority.AUTHORITATIVE_REGISTRY
    if host_lower in ("api.openaire.eu", "explore.openaire.eu"):
        return SourceAuthority.AUTHORITATIVE_REGISTRY
    if host_lower == "orcid.org":
        return SourceAuthority.AUTHORITATIVE_REGISTRY
    if host_lower == "ror.org":
        return SourceAuthority.AUTHORITATIVE_REGISTRY

    # Primary research output
    if host_lower == "doi.org":
        return SourceAuthority.PRIMARY_RESEARCH_OUTPUT

    # Discovery aggregators
    if host_lower in (
        "findaphd.com",
        "euraxess.ec.europa.eu",
        "academictransfer.com",
        "jobs.ac.uk",
        "mastersportal.com",
        "studyportals.com",
    ):
        return SourceAuthority.DISCOVERY_AGGREGATOR

    # Check for official university hosts (Belgian, Dutch, German)
    programme_keywords = ("/programme", "/program", "/master", "/phd", "/studium", "/admission")
    is_programme = any(path.find(kw) >= 0 for kw in programme_keywords)

    # Belgian universities
    if host_lower.endswith("kuleuven.be"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("ugent.be"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("vub.be"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("uantwerpen.be"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("uhasselt.be"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    # Dutch universities
    if host_lower.endswith("uu.nl"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("uva.nl"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("leidenuniv.nl"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("ru.nl"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("rug.nl"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("vu.nl"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("tudelft.nl"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    # German universities
    if re.search(r"uni-[a-z]+\.de$", host_lower):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("hu-berlin.de"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("fu-berlin.de"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
    if host_lower.endswith("lmu.de"):
        return SourceAuthority.OFFICIAL_PROGRAMME if is_programme else SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    return SourceAuthority.UNKNOWN


def _get_registrable_host(url: str) -> str:
    """Extract the registrable domain from a URL.

    For most cases, this is the last two labels (e.g., example.edu).
    For special cases like *.hu-berlin.de, we keep the full hu-berlin.de part.
    """
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
    except Exception:
        return ""

    if not host:
        return ""

    # Special handling for hu-berlin.de (keep full "hu-berlin.de")
    if host.endswith("hu-berlin.de"):
        # Return the registrable host (everything that should be in origin_group)
        if host == "hu-berlin.de":
            return host
        # For subdomains like "example.hu-berlin.de", extract "hu-berlin.de"
        parts = host.split(".")
        # Find "hu" and "-berlin.de" pattern
        if len(parts) >= 3:
            return "hu-berlin.de"
        return host

    # For other domains, extract the registrable host (last two labels)
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])

    return host


def _normalize_text(text: str) -> str:
    """Normalize text: take first 500 chars, then lowercase and collapse whitespace.

    Takes first 500 characters of raw text before normalization, then applies
    whitespace-collapse and lowercase to create stable hash.
    """
    # First take first 500 chars of raw text
    truncated = text[:500]
    # Then normalize: collapse multiple whitespaces to single space and lowercase
    normalized = re.sub(r"\s+", " ", truncated.strip()).lower()
    return normalized


def origin_group(url: str, text: str) -> str:
    """Generate canonical-origin grouping for syndication detection.

    Returns sha256 hash of normalized_first_500_chars_of_text only.
    All mirrors/copies with identical text share the same origin group,
    regardless of publication host, allowing detection of syndication.
    """
    normalized_text = _normalize_text(text)
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def same_origin(url_a: str, text_a: str, url_b: str, text_b: str) -> bool:
    """Check if two syndicated sources are mirrors (same text hash).

    Returns True only when origin_group values are identical, indicating
    the content came from a shared source despite different publication hosts.
    """
    return origin_group(url_a, text_a) == origin_group(url_b, text_b)
