import pytest
from datetime import datetime, date
import zoneinfo

from academic_radar.domain.deadlines import parse_deadline, Deadline, urgency
from academic_radar.domain.enums import DeadlinePrecision
from tests.academic_radar.canary import expect_violation


class TestDateOnlyParsing:
    """Test date-only deadline parsing without time or timezone."""

    # ORACLE-017, ORACLE-018
    def test_parse_date_only_dmy_format(self):
        """15 January 2027 should parse as DATE_ONLY."""
        deadline = parse_deadline("15 January 2027")
        assert deadline.precision == DeadlinePrecision.DATE_ONLY
        assert deadline.date_value == date(2027, 1, 15)
        assert deadline.local_time_value is None
        assert deadline.timezone_name is None
        assert deadline.utc_instant is None
        assert deadline.original_text == "15 January 2027"

    def test_parse_date_only_mdy_format(self):
        """January 15, 2027 should parse as DATE_ONLY."""
        deadline = parse_deadline("January 15, 2027")
        assert deadline.precision == DeadlinePrecision.DATE_ONLY
        assert deadline.date_value == date(2027, 1, 15)
        assert deadline.local_time_value is None
        assert deadline.timezone_name is None
        assert deadline.utc_instant is None

    def test_parse_date_only_iso_format(self):
        """2027-01-15 should parse as DATE_ONLY."""
        deadline = parse_deadline("2027-01-15")
        assert deadline.precision == DeadlinePrecision.DATE_ONLY
        assert deadline.date_value == date(2027, 1, 15)
        assert deadline.local_time_value is None
        assert deadline.timezone_name is None
        assert deadline.utc_instant is None


class TestTimeWithoutTimezone:
    """Test deadline with time but no timezone information."""

    def test_parse_time_no_tz(self):
        """15 January 2027 17:00 with no timezone should be AMBIGUOUS."""
        deadline = parse_deadline("15 January 2027 17:00")
        assert deadline.precision == DeadlinePrecision.AMBIGUOUS
        assert deadline.date_value == date(2027, 1, 15)
        assert deadline.local_time_value == "17:00"
        assert deadline.timezone_name is None
        assert deadline.utc_instant is None
        assert deadline.original_text == "15 January 2027 17:00"


class TestLocalTimeWithTimezone:
    """Test deadline with explicit timezone (IANA or abbreviation)."""

    # ORACLE-017, ORACLE-018
    def test_parse_local_time_with_iana_tz(self):
        """15 January 2027, 17:00 Europe/Brussels should compute UTC."""
        deadline = parse_deadline("15 January 2027, 17:00 Europe/Brussels")
        assert deadline.precision == DeadlinePrecision.LOCAL_TIME
        assert deadline.date_value == date(2027, 1, 15)
        assert deadline.local_time_value == "17:00"
        assert deadline.timezone_name == "Europe/Brussels"
        assert deadline.utc_instant is not None
        # 17:00 CET (UTC+1) = 16:00 UTC
        assert deadline.utc_instant.hour == 16
        assert deadline.utc_instant.minute == 0

    def test_parse_local_time_cet_mapped_to_iana(self):
        """CET abbreviation should map to Europe/Brussels."""
        deadline = parse_deadline("15 January 2027 17:00 CET")
        assert deadline.precision == DeadlinePrecision.LOCAL_TIME
        assert deadline.timezone_name == "Europe/Brussels"
        assert deadline.utc_instant is not None
        assert deadline.utc_instant.hour == 16  # 17:00 CET -> 16:00 UTC

    def test_parse_local_time_cest_mapped_to_iana(self):
        """CEST abbreviation should map to Europe/Brussels."""
        deadline = parse_deadline("28 March 2027 12:00 CEST")
        assert deadline.precision == DeadlinePrecision.LOCAL_TIME
        assert deadline.timezone_name == "Europe/Brussels"
        assert deadline.utc_instant is not None
        # 12:00 CEST (UTC+2, DST active) = 10:00 UTC
        assert deadline.utc_instant.hour == 10
        assert deadline.utc_instant.minute == 0

    def test_parse_dst_boundary_spring(self):
        """28 March 2027 12:00 Europe/Brussels (DST begins that day)."""
        deadline = parse_deadline("28 March 2027 12:00 Europe/Brussels")
        assert deadline.precision == DeadlinePrecision.LOCAL_TIME
        # DST started on 28 March 2027, so CEST (UTC+2) should apply
        assert deadline.utc_instant.hour == 10  # 12:00 CEST -> 10:00 UTC

    def test_parse_dst_boundary_fall(self):
        """31 October 2027 23:00 Europe/Brussels (DST ends that day)."""
        deadline = parse_deadline("31 October 2027 23:00 Europe/Brussels")
        assert deadline.precision == DeadlinePrecision.LOCAL_TIME
        # DST ended on 31 October 2027, so CET (UTC+1) should apply
        assert deadline.utc_instant.hour == 22  # 23:00 CET -> 22:00 UTC


class TestOffsetAwareParsing:
    """Test deadline with explicit numeric offset."""

    def test_parse_with_z_offset(self):
        """15 January 2027 17:00 Z should have OFFSET_AWARE precision."""
        deadline = parse_deadline("15 January 2027 17:00 Z")
        assert deadline.precision == DeadlinePrecision.OFFSET_AWARE
        assert deadline.utc_instant is not None
        assert deadline.utc_instant.hour == 17

    def test_parse_with_plus_offset(self):
        """15 January 2027 17:00 +01:00 should compute UTC."""
        deadline = parse_deadline("15 January 2027 17:00 +01:00")
        assert deadline.precision == DeadlinePrecision.OFFSET_AWARE
        assert deadline.utc_instant is not None
        # 17:00 +01:00 = 16:00 UTC
        assert deadline.utc_instant.hour == 16


class TestGarbageAndUnparseable:
    """Test handling of unparseable input."""

    def test_parse_garbage_input(self):
        """Unparseable text should return AMBIGUOUS with original_text."""
        deadline = parse_deadline("definitely not a deadline")
        assert deadline.precision == DeadlinePrecision.AMBIGUOUS
        assert deadline.date_value is None
        assert deadline.local_time_value is None
        assert deadline.timezone_name is None
        assert deadline.utc_instant is None
        assert deadline.original_text == "definitely not a deadline"

    # ORACLE-017
    def test_original_text_always_preserved(self):
        """Original text should never be modified."""
        text = "  Some   Weird  FORMATTING  15 January 2027  "
        deadline = parse_deadline(text)
        assert deadline.original_text == text


class TestAssumeTimezone:
    """Test the assume_tz parameter."""

    def test_assume_tz_without_text_tz(self):
        """assume_tz should be used when no timezone in text."""
        deadline = parse_deadline("15 January 2027 17:00", assume_tz="Europe/Paris")
        assert deadline.timezone_name == "Europe/Paris"
        assert deadline.local_time_value == "17:00"
        assert deadline.utc_instant is not None

    def test_assume_tz_text_tz_takes_precedence(self):
        """Explicit timezone in text should take precedence over assume_tz."""
        deadline = parse_deadline("15 January 2027 17:00 Europe/Brussels", assume_tz="Europe/Paris")
        assert deadline.timezone_name == "Europe/Brussels"


class TestUrgency:
    """Test urgency calculation."""

    def test_urgency_date_only_open(self):
        """Deadline >30 days away should be OPEN."""
        deadline = parse_deadline("15 January 2027")
        now = datetime(2026, 10, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))
        result = urgency(deadline, now, tz_for_date_only="UTC")
        assert result['label'] == 'OPEN'
        assert result['days_left'] > 30

    def test_urgency_date_only_due_soon(self):
        """Deadline <=30 days away should be DUE_SOON."""
        deadline = parse_deadline("15 January 2027")
        now = datetime(2026, 12, 26, tzinfo=zoneinfo.ZoneInfo("UTC"))
        result = urgency(deadline, now, tz_for_date_only="UTC")
        assert result['label'] == 'DUE_SOON'
        assert result['days_left'] <= 30

    def test_urgency_date_only_passed(self):
        """Past deadline should be PASSED."""
        deadline = parse_deadline("15 January 2027")
        now = datetime(2027, 2, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))
        result = urgency(deadline, now, tz_for_date_only="UTC")
        assert result['label'] == 'PASSED'
        assert result['days_left'] < 0

    def test_urgency_ambiguous_time(self):
        """AMBIGUOUS precision should return UNKNOWN_TIME."""
        deadline = parse_deadline("15 January 2027 17:00")
        now = datetime(2026, 10, 1, tzinfo=zoneinfo.ZoneInfo("UTC"))
        result = urgency(deadline, now)
        assert result['label'] == 'UNKNOWN_TIME'


class TestCanaryInventedTimezone:
    """Canary test: mutated parser that invents 23:59 for date-only."""

    def test_canary_invented_deadline_timezone(self):
        """
        Mutated parser fills 23:59 for date-only input.
        This check must be detected by expect_violation.
        """
        def mutated_parser(text):
            """Intentionally broken parser that invents time."""
            deadline = parse_deadline(text)
            if deadline.precision == DeadlinePrecision.DATE_ONLY:
                # Mutate: add 23:59 time
                return Deadline(
                    original_text=deadline.original_text,
                    date_value=deadline.date_value,
                    local_time_value="23:59",  # INVENTED
                    timezone_name=None,
                    utc_instant=None,
                    precision=DeadlinePrecision.LOCAL_TIME
                )
            return deadline

        def check_no_invented_time():
            d = mutated_parser("15 January 2027")
            assert d.local_time_value is None, "local_time_value should not be invented"

        # The check must fail when run against the mutated parser
        expect_violation(check_no_invented_time)

    def test_canary_invented_timezone_detection(self):
        """
        Verify the canary actually detects when local_time_value is invented.
        """
        def mutated_parser_with_tz(text):
            """Broken parser that invents timezone."""
            deadline = parse_deadline(text)
            if deadline.precision == DeadlinePrecision.DATE_ONLY:
                return Deadline(
                    original_text=deadline.original_text,
                    date_value=deadline.date_value,
                    local_time_value="23:59",
                    timezone_name="UTC",  # INVENTED
                    utc_instant=datetime(
                        deadline.date_value.year,
                        deadline.date_value.month,
                        deadline.date_value.day,
                        23, 59, 0,
                        tzinfo=zoneinfo.ZoneInfo("UTC")
                    ),
                    precision=DeadlinePrecision.OFFSET_AWARE
                )
            return deadline

        def check_no_invented_tz():
            d = mutated_parser_with_tz("15 January 2027")
            assert d.timezone_name is None, "timezone_name should not be invented for date-only"

        # This check must also fail
        expect_violation(check_no_invented_tz)
