from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
import re
import zoneinfo

from academic_radar.domain.enums import DeadlinePrecision


@dataclass(frozen=True)
class Deadline:
    """
    Represents a deadline with preserved precision and no invented data.

    Attributes:
        original_text: The raw text as provided (never modified).
        date_value: Normalized date (YYYY-MM-DD parsed date object).
        local_time_value: Time component if provided (HH:MM format), None if not present.
        timezone_name: IANA timezone name (e.g., 'Europe/Brussels'), None if not provided.
        utc_instant: UTC timestamp if fully specified, None for ambiguous/date-only.
        precision: Enum indicating the precision level of the deadline.
        source_evidence_id: Optional reference to evidence artifact.
        last_checked_at: Optional timestamp of when this was last verified.
    """
    original_text: str
    date_value: Optional[date]
    local_time_value: Optional[str]
    timezone_name: Optional[str]
    utc_instant: Optional[datetime]
    precision: DeadlinePrecision
    source_evidence_id: Optional[str] = None
    last_checked_at: Optional[datetime] = None


def parse_deadline(text: str, *, assume_tz: Optional[str] = None) -> Deadline:
    """
    Parse a deadline string with preserved precision.

    Handles:
    - '15 January 2027' / 'January 15, 2027' / '2027-01-15' => DATE_ONLY
    - With clock time but no zone => AMBIGUOUS
    - With IANA timezone (Europe/Brussels) or CET/CEST => LOCAL_TIME with computed UTC
    - With explicit offset (+01:00, UTC+1, Z) => OFFSET_AWARE with computed UTC
    - assume_tz used only if passed explicitly; precision stays AMBIGUOUS-derived

    Args:
        text: The deadline text to parse.
        assume_tz: Optional IANA timezone to apply if text lacks timezone info.
                  If provided, precision is LOCAL_TIME only if zone appears in text.

    Returns:
        Deadline object with preserved original_text and appropriate precision.
    """
    original_text = text

    # Try date-only patterns first
    date_only_patterns = [
        r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
        r'(\d{4})-(\d{2})-(\d{2})',
    ]

    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }

    parsed_date = None
    time_part = None
    tz_part = None
    has_explicit_tz = False

    # Try date-only patterns
    for pattern in date_only_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if pattern == date_only_patterns[0]:
                day, month_name, year = groups
                month = month_map[month_name]
                parsed_date = date(int(year), month, int(day))
            elif pattern == date_only_patterns[1]:
                month_name, day, year = groups
                month = month_map[month_name]
                parsed_date = date(int(year), month, int(day))
            else:
                year, month, day = groups
                parsed_date = date(int(year), int(month), int(day))

            # Check if there's a time component after the date
            remaining = text[match.end():].strip()
            if remaining:
                # Handle both ", HH:MM" and " HH:MM" formats
                remaining = remaining.lstrip(',').strip()
                time_match = re.match(r'(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s+(.+))?', remaining)
                if time_match:
                    hour, minute, second, tz_str = time_match.groups()
                    time_part = f"{int(hour):02d}:{int(minute):02d}"
                    if tz_str:
                        tz_part = tz_str.strip()
                        has_explicit_tz = True
            break

    if parsed_date is None:
        # Could not parse - return AMBIGUOUS with only original_text
        return Deadline(
            original_text=original_text,
            date_value=None,
            local_time_value=None,
            timezone_name=None,
            utc_instant=None,
            precision=DeadlinePrecision.AMBIGUOUS
        )

    # No time component and no assume_tz
    if time_part is None and assume_tz is None:
        return Deadline(
            original_text=original_text,
            date_value=parsed_date,
            local_time_value=None,
            timezone_name=None,
            utc_instant=None,
            precision=DeadlinePrecision.DATE_ONLY
        )

    # Time present but no timezone
    if time_part is not None and tz_part is None and assume_tz is None:
        return Deadline(
            original_text=original_text,
            date_value=parsed_date,
            local_time_value=time_part,
            timezone_name=None,
            utc_instant=None,
            precision=DeadlinePrecision.AMBIGUOUS
        )

    # Map CET/CEST to IANA timezone
    tz_name = tz_part if has_explicit_tz else assume_tz
    if tz_name in ('CET', 'CEST'):
        tz_name = 'Europe/Brussels'

    # Attempt to compute UTC
    utc_instant = None
    final_precision = DeadlinePrecision.AMBIGUOUS

    if tz_name and time_part:
        try:
            tz_info = zoneinfo.ZoneInfo(tz_name)
            hour, minute = map(int, time_part.split(':'))
            local_dt = datetime.combine(parsed_date, datetime.min.time().replace(hour=hour, minute=minute))
            local_dt_aware = local_dt.replace(tzinfo=tz_info)
            utc_instant = local_dt_aware.astimezone(zoneinfo.ZoneInfo('UTC'))

            if has_explicit_tz:
                final_precision = DeadlinePrecision.LOCAL_TIME
            else:
                final_precision = DeadlinePrecision.AMBIGUOUS
        except (ValueError, zoneinfo.ZoneInfoNotFoundError):
            pass
    elif tz_part:
        # Offset-aware without time (shouldn't happen, but handle gracefully)
        final_precision = DeadlinePrecision.OFFSET_AWARE

    # Handle numeric offsets like +01:00, UTC+1, Z
    if not utc_instant and tz_part:
        offset_match = re.match(r'UTC([+-]\d+)|([+-]\d{2}):(\d{2})|Z', tz_part)
        if offset_match:
            try:
                if tz_part == 'Z':
                    offset_hours = 0
                elif offset_match.group(1):
                    offset_hours = int(offset_match.group(1))
                else:
                    sign = 1 if offset_match.group(2)[0] == '+' else -1
                    offset_hours = sign * int(offset_match.group(2)[1:])

                if time_part:
                    hour, minute = map(int, time_part.split(':'))
                    local_dt = datetime.combine(parsed_date, datetime.min.time().replace(hour=hour, minute=minute))
                    # Create UTC time by subtracting offset
                    from datetime import timedelta
                    utc_instant = local_dt - timedelta(hours=offset_hours)
                    final_precision = DeadlinePrecision.OFFSET_AWARE
            except (ValueError, IndexError):
                pass

    # If assume_tz was used but no explicit tz in text, precision stays AMBIGUOUS-derived
    if time_part and not has_explicit_tz and assume_tz:
        final_precision = DeadlinePrecision.LOCAL_TIME

    return Deadline(
        original_text=original_text,
        date_value=parsed_date,
        local_time_value=time_part,
        timezone_name=tz_name if (tz_name or has_explicit_tz or assume_tz) else None,
        utc_instant=utc_instant,
        precision=final_precision
    )


def urgency(deadline: Deadline, now: datetime, tz_for_date_only: Optional[str] = None) -> dict:
    """
    Calculate urgency for a deadline.

    Args:
        deadline: The deadline to evaluate.
        now: Current datetime.
        tz_for_date_only: Timezone to use for DATE_ONLY comparisons.

    Returns:
        Dictionary with 'label' and optionally 'days_left'.
    """
    if deadline.precision == DeadlinePrecision.DATE_ONLY:
        # Compare dates in the specified timezone
        if tz_for_date_only:
            try:
                tz_info = zoneinfo.ZoneInfo(tz_for_date_only)
                now_in_tz = now.astimezone(tz_info)
                now_date = now_in_tz.date()
            except (ValueError, zoneinfo.ZoneInfoNotFoundError):
                now_date = now.date()
        else:
            now_date = now.date()

        days_left = (deadline.date_value - now_date).days

        if days_left < 0:
            return {'label': 'PASSED', 'days_left': days_left}
        elif days_left <= 30:
            return {'label': 'DUE_SOON', 'days_left': days_left}
        else:
            return {'label': 'OPEN', 'days_left': days_left}

    elif deadline.precision == DeadlinePrecision.AMBIGUOUS:
        return {'label': 'UNKNOWN_TIME'}

    # For LOCAL_TIME and OFFSET_AWARE, compare with UTC instant
    if deadline.utc_instant:
        now_utc = now.astimezone(zoneinfo.ZoneInfo('UTC')) if now.tzinfo else now
        time_left = deadline.utc_instant - now_utc
        days_left = time_left.days

        if time_left.total_seconds() < 0:
            return {'label': 'PASSED', 'days_left': days_left}
        elif days_left <= 30:
            return {'label': 'DUE_SOON', 'days_left': days_left}
        else:
            return {'label': 'OPEN', 'days_left': days_left}

    return {'label': 'UNKNOWN_TIME'}
