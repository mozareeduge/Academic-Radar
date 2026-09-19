import pytest
from tests.academic_radar.canary import expect_violation
from academic_radar.domain.identity import (
    PersonRecord,
    Resolution,
    IdentityStatus,
    resolve,
    can_merge_relation,
    check_no_same_name_merge,
)


class TestIdentityResolutionByExternalId:
    """Test resolution by explicit external IDs (Rule 1 & 2)."""

    def test_same_orcid_resolves(self):
        a = PersonRecord(
            name='John Smith',
            institution='Oxford',
            orcid='0000-0001-2345-6789',
        )
        b = PersonRecord(
            name='J. Smith',
            institution='Cambridge',
            orcid='0000-0001-2345-6789',
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED
        assert 'external_id:orcid' in resolution.basis

    def test_same_openalex_id_resolves(self):
        a = PersonRecord(
            name='Jane Doe',
            institution='MIT',
            openalex_id='A987654',
        )
        b = PersonRecord(
            name='Jane D.',
            institution='Stanford',
            openalex_id='A987654',
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED
        assert 'external_id:openalex_id' in resolution.basis

    def test_same_openaire_id_resolves(self):
        a = PersonRecord(
            name='Bob Johnson',
            institution='KU Leuven',
            openaire_id='O111222',
        )
        b = PersonRecord(
            name='B. Johnson',
            institution='Ghent',
            openaire_id='O111222',
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED
        assert 'external_id:openaire_id' in resolution.basis

    def test_different_orcid_unresolved_different(self):
        a = PersonRecord(
            name='Alice Brown',
            institution='Oxford',
            orcid='0000-0001-1111-1111',
        )
        b = PersonRecord(
            name='Alice Brown',
            institution='Oxford',
            orcid='0000-0001-2222-2222',
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.UNRESOLVED_DIFFERENT
        assert 'different_orcid' in resolution.basis

    def test_different_openalex_id_unresolved_different(self):
        a = PersonRecord(
            name='Charlie Davis',
            institution='MIT',
            openalex_id='A111111',
        )
        b = PersonRecord(
            name='Charlie Davis',
            institution='MIT',
            openalex_id='A222222',
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.UNRESOLVED_DIFFERENT
        assert 'different_openalex_id' in resolution.basis

    def test_different_openaire_id_unresolved_different(self):
        a = PersonRecord(
            name='Eva White',
            institution='Ghent',
            openaire_id='O333333',
        )
        b = PersonRecord(
            name='Eva White',
            institution='Ghent',
            openaire_id='O444444',
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.UNRESOLVED_DIFFERENT
        assert 'different_openaire_id' in resolution.basis


class TestIdentityResolutionByOfficialUrl:
    """Test resolution by official URL + institution (Rule 3)."""

    def test_same_official_url_and_institution_resolves(self):
        a = PersonRecord(
            name='Frank Miller',
            institution='KU Leuven',
            official_url='https://scholar.ku-leuven.be/frank-miller',
        )
        b = PersonRecord(
            name='F. Miller',
            institution='ku leuven',  # Different case/formatting
            official_url='https://scholar.ku-leuven.be/frank-miller',
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED
        assert 'official_url+institution' in resolution.basis

    def test_different_official_url_does_not_resolve_by_url_alone(self):
        a = PersonRecord(
            name='George Brown',
            institution='Oxford',
            official_url='https://oxford.ac.uk/george-brown',
        )
        b = PersonRecord(
            name='George Brown',
            institution='Oxford',
            official_url='https://oxford.ac.uk/g-brown',
        )
        resolution = resolve(a, b)
        # Without corroboration, should be CANDIDATE
        assert resolution.status == IdentityStatus.CANDIDATE


class TestIdentityResolutionByNameInstitutionCorroboration:
    """Test resolution by name + institution + corroboration (Rule 4)."""

    def test_same_name_institution_with_work_overlap_resolves(self):
        a = PersonRecord(
            name='Henry Chang',
            institution='Stanford',
            works={'paper-1', 'paper-2', 'paper-3'},
            topics={'ML', 'AI'},
        )
        b = PersonRecord(
            name='Henry Chang',
            institution='stanford',  # Case-insensitive
            works={'paper-2', 'paper-4'},  # One overlap: paper-2
            topics={'AI', 'NLP'},
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED
        assert 'name+institution+corroboration' in resolution.basis

    def test_same_name_institution_with_topic_overlap_resolves(self):
        a = PersonRecord(
            name='Iris Lopez',
            institution='MIT',
            works={'work-1'},
            topics={'quantum', 'physics'},
        )
        b = PersonRecord(
            name='Iris Lopez',
            institution='mit',
            works={'work-2'},
            topics={'physics', 'photonics'},  # One overlap: physics
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED
        assert 'name+institution+corroboration' in resolution.basis

    def test_same_name_institution_no_corroboration_candidate(self):
        a = PersonRecord(
            name='Jack Wilson',
            institution='Cambridge',
            works={'paper-1'},
            topics={'biology'},
        )
        b = PersonRecord(
            name='Jack Wilson',
            institution='Cambridge',
            works={'paper-2'},  # No overlap
            topics={'chemistry'},  # No overlap
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.CANDIDATE


class TestIdentityResolutionDifferentInstitution:
    """Test that different institutions with same name stay separate (Rule 5)."""

    def test_same_name_different_institutions_no_shared_id_candidate(self):
        a = PersonRecord(
            name='Jan Peeters',
            institution='KU Leuven',
            works={'paper-1'},
            topics={'ML'},
        )
        b = PersonRecord(
            name='Jan Peeters',
            institution='Ghent University',
            works={'paper-2'},
            topics={'AI'},
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.CANDIDATE
        # Must never RESOLVE
        assert resolution.status != IdentityStatus.RESOLVED

    def test_same_name_different_institutions_with_different_orcids_unresolved_different(self):
        a = PersonRecord(
            name='Alice Johnson',
            institution='Oxford',
            orcid='0000-0001-1111-1111',
        )
        b = PersonRecord(
            name='Alice Johnson',
            institution='Cambridge',
            orcid='0000-0001-2222-2222',
        )
        resolution = resolve(a, b)
        # Different IDs take precedence
        assert resolution.status == IdentityStatus.UNRESOLVED_DIFFERENT


class TestCanMergeRelation:
    """Test can_merge_relation function."""

    def test_can_merge_relation_with_resolved(self):
        resolution = Resolution(IdentityStatus.RESOLVED, 'test_basis')
        assert can_merge_relation(resolution) is True

    def test_cannot_merge_relation_with_candidate(self):
        resolution = Resolution(IdentityStatus.CANDIDATE, 'unresolved')
        assert can_merge_relation(resolution) is False

    def test_cannot_merge_relation_with_unresolved_different(self):
        resolution = Resolution(IdentityStatus.UNRESOLVED_DIFFERENT, 'different_id')
        assert can_merge_relation(resolution) is False


class TestCanaryTests:
    """Canary/negative-proof tests to ensure guards work."""

    @pytest.mark.canary
    def test_canary_same_name_identity_mutatation_detection(self):
        """
        Canary test: a mutated resolve function that ignores institution
        should be detected by check_no_same_name_merge.

        This test deliberately breaks the resolve logic and verifies
        that the canary catches it.
        """

        def mutated_resolve(a: PersonRecord, b: PersonRecord) -> Resolution:
            """Intentionally broken: ignores institution check."""
            a_name = a.name.lower().strip() if a.name else None
            b_name = b.name.lower().strip() if b.name else None

            if a_name and b_name and a_name == b_name:
                # Broken: always resolve same-name without checking institution
                return Resolution(IdentityStatus.RESOLVED, 'name_only_broken')

            return Resolution(IdentityStatus.CANDIDATE, 'unresolved')

        # expect_violation returns None if check() raises AssertionError
        # and raises CanaryNotDetected if check() does not raise
        expect_violation(check_no_same_name_merge, mutated_resolve)

    def test_canary_check_no_same_name_merge_with_correct_resolve(self):
        """
        Verify that check_no_same_name_merge passes with the correct resolve function.
        """
        # Should not raise
        check_no_same_name_merge(resolve)


class TestEdgeCases:
    """Test edge cases and normalization."""

    def test_name_normalization_case_insensitive(self):
        a = PersonRecord(
            name='JOHN SMITH',
            institution='Oxford',
            works={'paper-1'},
            topics={'AI'},
        )
        b = PersonRecord(
            name='john smith',
            institution='oxford',
            works={'paper-1'},
            topics={'AI'},
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED

    def test_name_normalization_with_whitespace(self):
        a = PersonRecord(
            name='  Jane Doe  ',
            institution='MIT',
            works={'work-1'},
            topics={'ML'},
        )
        b = PersonRecord(
            name='Jane Doe',
            institution='  mit  ',
            works={'work-1'},
            topics={'ML'},
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED

    def test_none_values_handled_gracefully(self):
        a = PersonRecord(
            name='Bob Test',
            institution='Stanford',
            orcid=None,
            official_url=None,
            works=set(),
            topics=set(),
        )
        b = PersonRecord(
            name='Bob Test',
            institution='Stanford',
            orcid=None,
            official_url=None,
            works=set(),
            topics=set(),
        )
        # Same name, institution, but no works/topics overlap -> CANDIDATE
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.CANDIDATE

    def test_empty_works_and_topics(self):
        a = PersonRecord(
            name='Test Person',
            institution='Univ A',
            works=set(),
            topics=set(),
        )
        b = PersonRecord(
            name='Test Person',
            institution='Univ A',
            works=set(),
            topics=set(),
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.CANDIDATE

    def test_single_element_sets(self):
        a = PersonRecord(
            name='Carol Reed',
            institution='Yale',
            works={'single-paper'},
        )
        b = PersonRecord(
            name='Carol Reed',
            institution='Yale',
            works={'single-paper'},
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED

    def test_multiple_works_overlap(self):
        a = PersonRecord(
            name='David Stone',
            institution='Harvard',
            works={'paper-1', 'paper-2', 'paper-3'},
            topics=set(),
        )
        b = PersonRecord(
            name='David Stone',
            institution='Harvard',
            works={'paper-2', 'paper-3', 'paper-4'},
            topics=set(),
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED

    def test_multiple_topics_overlap(self):
        a = PersonRecord(
            name='Emma Green',
            institution='Princeton',
            works=set(),
            topics={'biology', 'genetics', 'medicine'},
        )
        b = PersonRecord(
            name='Emma Green',
            institution='Princeton',
            works=set(),
            topics={'genetics', 'neurobiology'},
        )
        resolution = resolve(a, b)
        assert resolution.status == IdentityStatus.RESOLVED
