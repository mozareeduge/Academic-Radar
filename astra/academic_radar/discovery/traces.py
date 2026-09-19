"""Discovery trace creation and management."""


def make_trace(target_id: str, source, query, run_id, at: str) -> dict:
    """
    Create a discovery trace record.

    Args:
        target_id: ID of the discovered target entity
        source: Source adapter/query name (must not be empty)
        query: Search query used (must not be empty)
        run_id: ID of the research run (may be None)
        at: Timestamp of discovery (ISO format string)

    Returns:
        Plain dict matching radar_discovery_traces columns:
        {target_id, source, query, run_id, at}

    Raises:
        ValueError: if source or query is empty/None
    """
    if not source:
        raise ValueError("source cannot be empty")
    if not query:
        raise ValueError("query cannot be empty")

    return {
        "target_id": target_id,
        "source": source,
        "query": query,
        "run_id": run_id,
        "at": at,
    }
