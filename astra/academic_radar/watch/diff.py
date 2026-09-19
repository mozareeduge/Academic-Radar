"""Line-based diff utilities for watch checks.

Supports change detection and summary extraction for material change assessment.
"""


def line_diff(old: str, new: str) -> dict[str, list[str]]:
    """Compute line-based diff between two text versions.

    Returns a dict with 'added' and 'removed' keys containing lists of lines.
    Each line is normalized (leading/trailing whitespace stripped).

    Args:
        old: previous text version (may be empty)
        new: current text version (may be empty)

    Returns:
        dict with keys 'added' (lines in new but not old) and 'removed'
        (lines in old but not new)
    """
    old_lines = set(line.strip() for line in old.split('\n') if line.strip())
    new_lines = set(line.strip() for line in new.split('\n') if line.strip())

    added = list(new_lines - old_lines)
    removed = list(old_lines - new_lines)

    return {
        'added': sorted(added),
        'removed': sorted(removed),
    }
