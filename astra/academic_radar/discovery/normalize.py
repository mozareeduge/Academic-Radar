"""Discovery normalization and deduplication."""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def canonical_url(url: str) -> str:
    """
    Normalize URL to canonical form for deduplication.

    - Lowercase scheme and hostname
    - Drop fragment (#...)
    - Drop utm_*, gclid, fbclid parameters
    - Drop default ports (80 for http, 443 for https)
    - Sort remaining query parameters
    - Strip trailing slash except for root
    """
    parsed = urlparse(url)

    scheme = parsed.scheme.lower() if parsed.scheme else "https"
    netloc = parsed.netloc.lower() if parsed.netloc else ""

    if ":" in netloc:
        host, port = netloc.rsplit(":", 1)
        try:
            port_num = int(port)
            default_port = 80 if scheme == "http" else 443
            if port_num == default_port:
                netloc = host
        except ValueError:
            pass

    path = parsed.path
    if path and path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    query_params = parse_qs(parsed.query, keep_blank_values=True)

    filtered_params = {}
    for key, values in query_params.items():
        if key.lower() not in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "gclid", "fbclid"):
            filtered_params[key] = values[0] if values else ""

    sorted_query_items = sorted(filtered_params.items())
    new_query = urlencode(sorted_query_items) if sorted_query_items else ""

    canonical = urlunparse((scheme, netloc, path, "", new_query, ""))

    return canonical


def dedupe_key(target_kind: str, canonical_url_str: str, external_ids: dict) -> str:
    """
    Generate deduplication key for a discovered target.

    Prefers external IDs in order: doi, orcid, openalex_id, openaire_id, ror.
    Falls back to 'url:' + canonical URL if no external IDs available.
    """
    for id_type in ("doi", "orcid", "openalex_id", "openaire_id", "ror"):
        if id_type in external_ids and external_ids[id_type]:
            return f"{id_type}:{external_ids[id_type]}"

    return f"url:{canonical_url_str}"
