"""Cadence-based scheduling for watch checks.

Supports 'daily' and 'weekly' cadences by comparing target's check history to now.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


def due_targets(targets: list[dict], now: datetime) -> list[dict]:
    """Filter watch targets that are due for checking based on cadence.

    Args:
        targets: list of target dicts, each with 'id', 'cadence', and optional
                 'last_check_at' (datetime or None)
        now: current timestamp (datetime with timezone)

    Returns:
        filtered list of targets that should be checked now
    """
    due = []

    for target in targets:
        cadence = target.get('cadence', '').lower()
        last_check = target.get('last_check_at')

        if cadence == 'daily':
            threshold = now - timedelta(days=1)
        elif cadence == 'weekly':
            threshold = now - timedelta(weeks=1)
        else:
            continue

        if last_check is None or last_check < threshold:
            due.append(target)

    return due
