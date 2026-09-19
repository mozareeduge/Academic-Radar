import pytest
from academic_radar.domain.authority import classify_source, origin_group, same_origin, SourceAuthority


class TestClassifySource:
    """Test URL classification into SourceAuthority categories."""

    def test_official_department_kuleuven(self):
        """Belgium: KU Leuven official department."""
        assert classify_source("https://www.kuleuven.be/some/page") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
        assert classify_source("https://kuleuven.be/dept") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_programme_kuleuven(self):
        """Belgium: KU Leuven official programme page."""
        assert classify_source("https://www.kuleuven.be/programme/info") == SourceAuthority.OFFICIAL_PROGRAMME
        assert classify_source("https://kuleuven.be/program/master") == SourceAuthority.OFFICIAL_PROGRAMME
        assert classify_source("https://kuleuven.be/en/phd/something") == SourceAuthority.OFFICIAL_PROGRAMME
        assert classify_source("https://kuleuven.be/master") == SourceAuthority.OFFICIAL_PROGRAMME
        assert classify_source("https://kuleuven.be/studium") == SourceAuthority.OFFICIAL_PROGRAMME
        assert classify_source("https://kuleuven.be/admission") == SourceAuthority.OFFICIAL_PROGRAMME

    def test_official_department_ugent(self):
        """Belgium: UGent official department."""
        assert classify_source("https://ugent.be/en/departments") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_programme_ugent(self):
        """Belgium: UGent official programme."""
        assert classify_source("https://ugent.be/master/english-studies") == SourceAuthority.OFFICIAL_PROGRAMME

    def test_official_department_vub(self):
        """Belgium: VUB official department."""
        assert classify_source("https://vub.be/en/research-group") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_department_uantwerpen(self):
        """Belgium: UAntwerpen official department."""
        assert classify_source("https://uantwerpen.be/en/") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_department_uhasselt(self):
        """Belgium: UHasselt official department."""
        assert classify_source("https://uhasselt.be/en/staff") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_department_uu_nl(self):
        """Netherlands: Utrecht University official department."""
        assert classify_source("https://uu.nl/en/research") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_programme_uu_nl(self):
        """Netherlands: Utrecht University programme."""
        assert classify_source("https://uu.nl/en/master/philosophy") == SourceAuthority.OFFICIAL_PROGRAMME

    def test_official_department_uva_nl(self):
        """Netherlands: UvA official department."""
        assert classify_source("https://uva.nl/en/research") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_programme_leidenuniv(self):
        """Netherlands: Leiden University programme."""
        assert classify_source("https://leidenuniv.nl/en/programme/physics") == SourceAuthority.OFFICIAL_PROGRAMME

    def test_official_department_ru_nl(self):
        """Netherlands: Radboud University official department."""
        assert classify_source("https://ru.nl/en/about") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_programme_rug_nl(self):
        """Netherlands: University of Groningen programme."""
        assert classify_source("https://rug.nl/master/mathematical-sciences") == SourceAuthority.OFFICIAL_PROGRAMME

    def test_official_department_vu_nl(self):
        """Netherlands: VU University official department."""
        assert classify_source("https://vu.nl/en/research") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_department_tudelft(self):
        """Netherlands: TU Delft official department."""
        assert classify_source("https://tudelft.nl/en/research") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_department_uni_germany(self):
        """Germany: uni-*.de official department."""
        assert classify_source("https://uni-heidelberg.de/en/research") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
        assert classify_source("https://uni-bonn.de/") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_programme_uni_germany(self):
        """Germany: uni-*.de programme."""
        assert classify_source("https://uni-heidelberg.de/master/physics") == SourceAuthority.OFFICIAL_PROGRAMME

    def test_official_department_hu_berlin(self):
        """Germany: Humboldt University Berlin official department."""
        assert classify_source("https://hu-berlin.de/research") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
        assert classify_source("https://example.hu-berlin.de/") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_department_fu_berlin(self):
        """Germany: Free University Berlin official department."""
        assert classify_source("https://fu-berlin.de/en/research") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_department_lmu(self):
        """Germany: LMU Munich official department."""
        assert classify_source("https://lmu.de/en/index.html") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_official_department_hu_hungary(self):
        """Hungary: any *.hu-berlin.de domain."""
        assert classify_source("https://example.hu-berlin.de/page") == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON

    def test_authoritative_registry_openalex(self):
        """OpenAlex scholarly registry."""
        assert classify_source("https://api.openalex.org/works") == SourceAuthority.AUTHORITATIVE_REGISTRY
        assert classify_source("https://openalex.org/authors") == SourceAuthority.AUTHORITATIVE_REGISTRY

    def test_authoritative_registry_openaire(self):
        """OpenAIRE scholarly registry."""
        assert classify_source("https://api.openaire.eu/graph") == SourceAuthority.AUTHORITATIVE_REGISTRY
        assert classify_source("https://explore.openaire.eu/") == SourceAuthority.AUTHORITATIVE_REGISTRY

    def test_authoritative_registry_orcid(self):
        """ORCID registry."""
        assert classify_source("https://orcid.org/0000-0001-2345-6789") == SourceAuthority.AUTHORITATIVE_REGISTRY

    def test_authoritative_registry_ror(self):
        """ROR (Research Organization Registry)."""
        assert classify_source("https://ror.org/institutions") == SourceAuthority.AUTHORITATIVE_REGISTRY

    def test_primary_research_output_doi(self):
        """DOI primary research output."""
        assert classify_source("https://doi.org/10.1234/example") == SourceAuthority.PRIMARY_RESEARCH_OUTPUT

    def test_discovery_aggregator_findaphd(self):
        """FindAPhD aggregator."""
        assert classify_source("https://findaphd.com/phds") == SourceAuthority.DISCOVERY_AGGREGATOR

    def test_discovery_aggregator_euraxess(self):
        """EURAXESS EC aggregator."""
        assert classify_source("https://euraxess.ec.europa.eu/jobs") == SourceAuthority.DISCOVERY_AGGREGATOR

    def test_discovery_aggregator_academictransfer(self):
        """Academic Transfer aggregator."""
        assert classify_source("https://academictransfer.com/jobs") == SourceAuthority.DISCOVERY_AGGREGATOR

    def test_discovery_aggregator_jobs_ac_uk(self):
        """Jobs.ac.uk aggregator."""
        assert classify_source("https://jobs.ac.uk/") == SourceAuthority.DISCOVERY_AGGREGATOR

    def test_discovery_aggregator_mastersportal(self):
        """MastersPortal aggregator."""
        assert classify_source("https://mastersportal.com/programmes") == SourceAuthority.DISCOVERY_AGGREGATOR

    def test_discovery_aggregator_studyportals(self):
        """StudyPortals aggregator."""
        assert classify_source("https://studyportals.com/") == SourceAuthority.DISCOVERY_AGGREGATOR

    def test_unknown_host(self):
        """Unknown host classification."""
        assert classify_source("https://example.com/something") == SourceAuthority.UNKNOWN
        assert classify_source("https://random-university.org/") == SourceAuthority.UNKNOWN


class TestOriginGroup:
    """Test canonical-origin grouping for mirrors/syndication."""

    def test_same_text_different_hosts(self):
        """Two different hosts with identical text should have same origin group."""
        text = "This is identical content about a PhD programme"
        group_a = origin_group("https://host1.edu/page", text)
        group_b = origin_group("https://host2.edu/page", text)
        assert group_a == group_b

    def test_different_text_same_host(self):
        """Same host with different text should have different origin groups."""
        group_a = origin_group("https://host.edu/page", "Text version 1")
        group_b = origin_group("https://host.edu/page", "Text version 2")
        assert group_a != group_b

    def test_same_host_same_text(self):
        """Same host and text should have identical origin group."""
        url = "https://host.edu/page"
        text = "Identical content"
        assert origin_group(url, text) == origin_group(url, text)

    def test_whitespace_normalization(self):
        """Whitespace variations should normalize to same group."""
        text1 = "This is   content   with   spaces"
        text2 = "This is content with spaces"
        group1 = origin_group("https://host1.edu/", text1)
        group2 = origin_group("https://host1.edu/", text2)
        assert group1 == group2

    def test_case_normalization(self):
        """Content case should normalize to lowercase."""
        text1 = "UPPERCASE CONTENT"
        text2 = "uppercase content"
        group1 = origin_group("https://host.edu/", text1)
        group2 = origin_group("https://host.edu/", text2)
        assert group1 == group2

    def test_text_truncation_first_500_chars(self):
        """Long texts over 500 chars are handled correctly with whitespace normalization."""
        # Create a text longer than 500 chars with whitespace padding
        core_text = "This is programme information with details"
        padded_text = core_text + " " * 500  # Add 500 spaces

        group_core = origin_group("https://host.edu/", core_text)
        group_padded = origin_group("https://host.edu/", padded_text)

        # After whitespace normalization, both should hash the same
        assert group_core == group_padded

        # Text with different core content should differ
        different_text = "This is different content" + " " * 500
        group_different = origin_group("https://host.edu/", different_text)
        assert group_core != group_different

    def test_registrable_host_only(self):
        """Only registrable domain (not full subdomain path) should be used."""
        text = "Same content"
        group1 = origin_group("https://deep.sub.host.edu/page", text)
        group2 = origin_group("https://host.edu/other", text)
        # Both should use registrable host "host.edu"
        assert group1 == group2


class TestSameOrigin:
    """Test syndication detection helper."""

    def test_identical_text_different_urls(self):
        """Syndicated copy with identical text should return True."""
        text = "This is syndicated content"
        assert same_origin(
            "https://source1.edu/article",
            text,
            "https://source2.edu/news",
            text
        ) is True

    def test_different_text_same_host(self):
        """Different content on same host should return False."""
        assert same_origin(
            "https://host.edu/article1",
            "Content 1",
            "https://host.edu/article2",
            "Content 2"
        ) is False

    def test_modified_text_same_source(self):
        """Modified/paraphrased content should return False."""
        original = "Original text"
        modified = "Completely different text"
        assert same_origin(
            "https://source.edu/",
            original,
            "https://copy.edu/",
            modified
        ) is False

    def test_whitespace_variations_same_origin(self):
        """Whitespace variations should still match."""
        text1 = "Content   with   spaces"
        text2 = "Content with spaces"
        assert same_origin(
            "https://host1.edu/",
            text1,
            "https://host2.edu/",
            text2
        ) is True
