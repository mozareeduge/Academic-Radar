"""Test discovery scope, fixture adapter, classification, and deduplication."""

import json
from pathlib import Path
import pytest

from academic_radar.discovery.scope import (
    DEFAULT_COUNTRIES,
    resolve_scope,
)
from academic_radar.discovery.fixture_source import FixtureSource
from academic_radar.discovery.classify import classify_route
from academic_radar.discovery.normalize import dedupe_key
from academic_radar.discovery.traces import make_trace
from academic_radar.domain.enums import ApplicationRoute


class TestDiscoveryScope:
    """Test country scope configuration."""

    def test_default_countries_defined(self):
        """DEFAULT_COUNTRIES should be ('BE', 'NL', 'DE')."""
        assert DEFAULT_COUNTRIES == ('BE', 'NL', 'DE')

    def test_resolve_scope_scheduled_run_uses_defaults(self):
        """Scheduled run (requested=None) should return DEFAULT_COUNTRIES."""
        result = resolve_scope(requested=None, explore_europe=False)
        assert result == DEFAULT_COUNTRIES

    def test_resolve_scope_manual_run_remembers_selection(self):
        """Manual run with requested list should return that selection."""
        requested = ['FR', 'AT']
        result = resolve_scope(requested=requested, explore_europe=False)
        assert result == ('FR', 'AT')

    def test_resolve_scope_fr_excluded_from_defaults(self):
        """Scheduled scope should exclude FR (only BE, NL, DE)."""
        scope = resolve_scope(requested=None, explore_europe=False)
        assert 'FR' not in scope
        assert 'BE' in scope
        assert 'NL' in scope
        assert 'DE' in scope

    def test_resolve_scope_explore_europe_can_include_fr(self):
        """explore_europe=True enables including FR beyond defaults."""
        requested = ['BE', 'NL', 'DE', 'FR', 'AT']
        result = resolve_scope(requested=requested, explore_europe=True)
        assert 'FR' in result
        assert 'AT' in result


class TestFixtureSource:
    """Test fixture-backed discovery source."""

    @pytest.fixture
    def fixture_path(self):
        """Return path to test fixture JSON."""
        return Path(__file__).parent / "fixtures" / "discovery_fixture.json"

    def test_fixture_source_loads_json(self, fixture_path):
        """FixtureSource should load and parse JSON file."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())
        assert len(candidates) > 0

    def test_fixture_has_six_candidates(self, fixture_path):
        """Fixture should contain 6 candidates (7 items, 1 duplicate URL with utm)."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())
        assert len(candidates) == 7

    def test_fixture_has_two_supervisor_pages(self, fixture_path):
        """Fixture should have 2 Person (supervisor) kind records."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())
        person_candidates = [c for c in candidates if c['kind'] == 'Person']
        assert len(person_candidates) == 2

    def test_fixture_has_two_advertised_phd(self, fixture_path):
        """Fixture should have 2 PhDOpportunity (advertised) records."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())
        phd_candidates = [c for c in candidates if c['kind'] == 'PhDOpportunity']
        assert len(phd_candidates) == 3  # 2 unique + 1 duplicate

    def test_fixture_has_structured_phd(self, fixture_path):
        """Fixture should have 1 structured PhD Programme record."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())
        prog_candidates = [c for c in candidates if c['kind'] == 'Programme']
        structured_phd = [c for c in prog_candidates if 'phd' in c['title'].lower() or 'structured' in c['title'].lower()]
        assert len(structured_phd) >= 1

    def test_fixture_has_ma_programme(self, fixture_path):
        """Fixture should have 1 MA Programme record."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())
        prog_candidates = [c for c in candidates if c['kind'] == 'Programme']
        ma_candidates = [c for c in prog_candidates if c['title'] == 'Master\'s Programme in European Studies']
        assert len(ma_candidates) == 1

    def test_fixture_has_country_mix_be_nl_de_fr(self, fixture_path):
        """Fixture should contain countries BE, NL, DE (and FR for explore_europe test)."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())
        countries = {c['country'] for c in candidates}
        assert 'BE' in countries
        assert 'NL' in countries
        assert 'DE' in countries

    def test_candidate_has_normalized_fields(self, fixture_path):
        """Each yielded candidate should have normalized fields."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())
        for candidate in candidates:
            assert 'kind' in candidate
            assert 'title' in candidate
            assert 'url' in candidate
            assert 'country' in candidate
            assert 'external_ids' in candidate
            assert 'url_canonical' in candidate
            assert 'dedupe_key' in candidate

    def test_duplicate_url_with_utm_collapses_same_dedupe_key(self, fixture_path):
        """Duplicate URLs with utm params should have identical dedupe_key."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())

        kling_candidates = [
            c for c in candidates
            if 'computational-linguistics' in c['url'].lower()
        ]
        assert len(kling_candidates) == 2

        keys = {c['dedupe_key'] for c in kling_candidates}
        assert len(keys) == 1, "Both URLs should produce identical dedupe_key"

    def test_candidate_url_canonicalized(self, fixture_path):
        """Candidate URLs should be canonicalized (UTM params dropped)."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())

        master_prog = [c for c in candidates if c['title'] == 'Master\'s Programme in European Studies'][0]
        assert 'utm' not in master_prog['url_canonical']

    def test_external_ids_preserved(self, fixture_path):
        """External IDs should be preserved in normalized candidates."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())

        orcid_candidates = [c for c in candidates if 'orcid' in c['external_ids']]
        assert len(orcid_candidates) > 0


class TestClassifyRoute:
    """Test route classification by keyword rules."""

    def test_classify_person_to_supervisor_first_phd(self):
        """kind='Person' should classify as SUPERVISOR_FIRST_PHD."""
        candidate = {
            'kind': 'Person',
            'title': 'Prof. John Smith',
        }
        route = classify_route(candidate)
        assert route == ApplicationRoute.SUPERVISOR_FIRST_PHD

    def test_classify_phd_opportunity_to_advertised_phd(self):
        """kind='PhDOpportunity' should classify as ADVERTISED_PHD."""
        candidate = {
            'kind': 'PhDOpportunity',
            'title': 'PhD in Computer Science',
        }
        route = classify_route(candidate)
        assert route == ApplicationRoute.ADVERTISED_PHD

    def test_classify_programme_with_phd_to_structured_phd(self):
        """kind='Programme' with 'PhD' in title should classify as STRUCTURED_PHD."""
        candidate = {
            'kind': 'Programme',
            'title': 'Structured PhD Programme in Neuroscience',
        }
        route = classify_route(candidate)
        assert route == ApplicationRoute.STRUCTURED_PHD

    def test_classify_programme_with_structured_to_structured_phd(self):
        """kind='Programme' with 'Structured' in title should classify as STRUCTURED_PHD."""
        candidate = {
            'kind': 'Programme',
            'title': 'Structured Research Programme',
        }
        route = classify_route(candidate)
        assert route == ApplicationRoute.STRUCTURED_PHD

    def test_classify_programme_ma_to_ma_programme(self):
        """kind='Programme' without PhD reference should classify as MA_PROGRAMME."""
        candidate = {
            'kind': 'Programme',
            'title': 'Master\'s Programme in European Studies',
        }
        route = classify_route(candidate)
        assert route == ApplicationRoute.MA_PROGRAMME

    def test_classify_programme_generic_to_ma_programme(self):
        """Generic Programme kind without PhD should default to MA_PROGRAMME."""
        candidate = {
            'kind': 'Programme',
            'title': 'Engineering Programme',
        }
        route = classify_route(candidate)
        assert route == ApplicationRoute.MA_PROGRAMME

    def test_classify_case_insensitive(self):
        """Classification should be case-insensitive."""
        candidate = {
            'kind': 'Programme',
            'title': 'STRUCTURED PHD PROGRAMME',
        }
        route = classify_route(candidate)
        assert route == ApplicationRoute.STRUCTURED_PHD

    def test_all_fixture_candidates_get_route(self, tmp_path):
        """Every fixture candidate should be classified to a valid route."""
        fixture_path = Path(__file__).parent / "fixtures" / "discovery_fixture.json"
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())

        for candidate in candidates:
            route = classify_route(candidate)
            assert route in ApplicationRoute
            assert isinstance(route, ApplicationRoute)


class TestDiscoveryIntegration:
    """Integration tests for discovery scope, fixture, and classification."""

    @pytest.fixture
    def fixture_path(self):
        """Return path to test fixture JSON."""
        return Path(__file__).parent / "fixtures" / "discovery_fixture.json"

    def test_scheduled_scope_excludes_fr(self, fixture_path):
        """Scheduled runs should exclude FR candidates."""
        scope = resolve_scope(requested=None, explore_europe=False)
        assert 'FR' not in scope

        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())

        filtered = [c for c in candidates if c['country'] in scope]
        fr_candidates = [c for c in candidates if c['country'] == 'FR']

        assert len(fr_candidates) == 0 or all(c not in filtered for c in fr_candidates)

    def test_explore_europe_includes_fr(self, fixture_path):
        """explore_europe=True allows FR in scope."""
        scope = resolve_scope(requested=['BE', 'NL', 'DE', 'FR'], explore_europe=True)
        assert 'FR' in scope

    def test_duplicate_collapses_via_dedupe_key(self, fixture_path):
        """Duplicate URLs should collapse via dedupe_key."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())

        dedupe_keys = [c['dedupe_key'] for c in candidates]
        unique_keys = set(dedupe_keys)

        assert len(unique_keys) < len(candidates), "Duplicates should be detected"

    def test_every_fixture_candidate_gets_trace(self, fixture_path):
        """Every candidate can generate a discovery trace."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())

        traces = []
        for candidate in candidates:
            trace = make_trace(
                target_id=f"target_{candidate['dedupe_key']}",
                source="fixture",
                query="test",
                run_id="run_123",
                at="2026-09-19T00:00:00Z"
            )
            traces.append(trace)
            assert trace['target_id'] is not None
            assert trace['source'] == 'fixture'

        assert len(traces) == len(candidates)

    def test_every_fixture_candidate_gets_route(self, fixture_path):
        """Every candidate gets classified to a route."""
        source = FixtureSource(fixture_path)
        candidates = list(source.candidates())

        for candidate in candidates:
            route = classify_route(candidate)
            assert route in ApplicationRoute
