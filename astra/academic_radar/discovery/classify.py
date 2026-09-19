"""Route classification for discovered candidates."""

from academic_radar.domain.enums import ApplicationRoute


def classify_route(candidate: dict) -> ApplicationRoute:
    """
    Classify a candidate into an ApplicationRoute by deterministic keyword rules.

    Args:
        candidate: A normalised candidate dict with 'kind' and 'title'.

    Returns:
        ApplicationRoute enum value.

    Rules (applied in order):
        - kind == 'Person' → SUPERVISOR_FIRST_PHD
        - kind == 'PhDOpportunity' → ADVERTISED_PHD
        - kind == 'Programme' and 'PhD' or 'Structured' in title → STRUCTURED_PHD
        - kind == 'Programme' → MA_PROGRAMME (default for programmes)
    """
    kind = candidate.get('kind', '').strip()
    title = candidate.get('title', '').strip()

    if kind == 'Person':
        return ApplicationRoute.SUPERVISOR_FIRST_PHD

    if kind == 'PhDOpportunity':
        return ApplicationRoute.ADVERTISED_PHD

    if kind == 'Programme':
        title_lower = title.lower()
        if 'phd' in title_lower or 'structured' in title_lower:
            return ApplicationRoute.STRUCTURED_PHD
        return ApplicationRoute.MA_PROGRAMME

    return ApplicationRoute.MA_PROGRAMME
