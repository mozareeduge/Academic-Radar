"""Discovery scope and country selection."""

DEFAULT_COUNTRIES = ('BE', 'NL', 'DE')
explore_europe_default = False


def resolve_scope(requested=None, explore_europe=False):
    """
    Resolve the scope of countries for discovery.

    Args:
        requested: List of country codes requested by user (for manual runs).
        explore_europe: Boolean flag to include broader European scope.

    Returns:
        Tuple of country codes to search.

    Behavior:
        - Scheduled runs (requested=None) use only DEFAULT_COUNTRIES.
        - Manual runs (requested provided) return requested countries.
        - explore_europe=True may expand the scope (reserved for future use).
    """
    if requested is not None:
        return tuple(requested)
    return DEFAULT_COUNTRIES
