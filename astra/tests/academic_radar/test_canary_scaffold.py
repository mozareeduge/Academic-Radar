import json
import pytest
from tests.academic_radar.canary import CanaryNotDetected, expect_violation


class TestCanaryHelper:
    def test_expect_violation_returns_none_on_assertion_error(self):
        def check_raises():
            raise AssertionError("expected failure")
        
        result = expect_violation(check_raises)
        assert result is None

    def test_expect_violation_raises_canary_not_detected_on_normal_return(self):
        def check_passes():
            pass
        
        with pytest.raises(CanaryNotDetected) as exc_info:
            expect_violation(check_passes)
        assert "canary not detected: check_passes" in str(exc_info.value)


class TestCanariesJson:
    def test_canaries_json_has_exactly_8_entries(self):
        with open("tests/academic_radar/canaries.json") as f:
            canaries = json.load(f)
        assert len(canaries) == 8

    def test_canaries_json_has_correct_ids(self):
        with open("tests/academic_radar/canaries.json") as f:
            canaries = json.load(f)
        expected_ids = [f"CANARY-{i:02d}" for i in range(1, 9)]
        actual_ids = [c["id"] for c in canaries]
        assert actual_ids == expected_ids

    def test_canaries_json_entries_have_required_fields(self):
        with open("tests/academic_radar/canaries.json") as f:
            canaries = json.load(f)
        for canary in canaries:
            assert "id" in canary
            assert "slug" in canary
            assert "text" in canary
            assert "status" in canary
            assert canary["status"] == "implemented"
            assert "test_path" in canary


class TestPackageImport:
    def test_import_academic_radar_succeeds(self):
        import academic_radar
        assert academic_radar is not None
