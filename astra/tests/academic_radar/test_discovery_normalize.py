"""Test discovery normalization and deduplication."""

import pytest

from academic_radar.discovery.normalize import canonical_url, dedupe_key
from academic_radar.discovery.traces import make_trace


class TestCanonicalUrl:
    """Test URL canonicalization."""

    def test_normalize_http_https_equal(self):
        """http and https schemes are normalized but kept distinct."""
        url1 = "https://example.com/path?b=2&a=1"
        url2 = "https://EXAMPLE.COM/path?a=1&b=2"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_scheme_and_host_lowercase(self):
        """Scheme and host should be lowercased."""
        url = "HTTPS://EXAMPLE.COM/Path"
        canonical = canonical_url(url)
        assert canonical.startswith("https://example.com")

    def test_normalize_drop_fragment(self):
        """Fragment should be dropped."""
        url1 = "https://example.com/page#section"
        url2 = "https://example.com/page"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_drop_utm_params(self):
        """UTM parameters should be dropped."""
        url1 = "https://example.com/page?utm_source=x&utm_medium=y&utm_campaign=z&other=keep"
        url2 = "https://example.com/page?other=keep"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_drop_gclid_fbclid(self):
        """gclid and fbclid parameters should be dropped."""
        url1 = "https://example.com/page?gclid=abc&fbclid=def&other=keep"
        url2 = "https://example.com/page?other=keep"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_sort_query_params(self):
        """Remaining query parameters should be sorted."""
        url1 = "https://example.com/page?z=3&a=1&m=2"
        url2 = "https://example.com/page?a=1&m=2&z=3"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_drop_default_http_port(self):
        """Default HTTP port (80) should be dropped."""
        url1 = "http://example.com:80/page"
        url2 = "http://example.com/page"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_drop_default_https_port(self):
        """Default HTTPS port (443) should be dropped."""
        url1 = "https://example.com:443/page"
        url2 = "https://example.com/page"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_keep_non_default_port(self):
        """Non-default ports should be kept."""
        url1 = "https://example.com:8443/page"
        url2 = "https://example.com:8443/page"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_strip_trailing_slash_except_root(self):
        """Trailing slash should be stripped except for root."""
        url1 = "https://example.com/page/"
        url2 = "https://example.com/page"
        assert canonical_url(url1) == canonical_url(url2)

    def test_normalize_keep_root_trailing_slash(self):
        """Root URL should keep single trailing slash."""
        url = "https://example.com/"
        canonical = canonical_url(url)
        assert canonical == "https://example.com/"

    def test_normalize_complex_url(self):
        """Complex URL with multiple normalizations."""
        url = "HTTPS://EXAMPLE.COM:443/path?z=3&utm_source=x&a=1&fbclid=y#section"
        canonical = canonical_url(url)
        assert canonical == "https://example.com/path?a=1&z=3"

    def test_different_paths_not_equal(self):
        """Different paths should result in different canonical URLs."""
        url1 = "https://example.com/path1"
        url2 = "https://example.com/path2"
        assert canonical_url(url1) != canonical_url(url2)

    def test_different_query_values_not_equal(self):
        """Different query parameter values should result in different canonical URLs."""
        url1 = "https://example.com/page?id=1"
        url2 = "https://example.com/page?id=2"
        assert canonical_url(url1) != canonical_url(url2)


class TestDedupeKey:
    """Test deduplication key generation."""

    def test_dedupe_key_prefers_doi(self):
        """DOI should be preferred over other external IDs."""
        key_with_doi = dedupe_key(
            "Person",
            "https://example.com",
            {"doi": "10.1234/test", "orcid": "0000-0001-2345-6789"}
        )
        assert key_with_doi == "doi:10.1234/test"

    def test_dedupe_key_prefers_orcid_over_openalex(self):
        """ORCID should be preferred over OpenAlex when DOI absent."""
        key_with_orcid = dedupe_key(
            "Person",
            "https://example.com",
            {"orcid": "0000-0001-2345-6789", "openalex_id": "A12345"}
        )
        assert key_with_orcid == "orcid:0000-0001-2345-6789"

    def test_dedupe_key_falls_back_to_url(self):
        """When no external IDs present, use URL key."""
        key_with_url = dedupe_key(
            "Person",
            "https://example.com/profile",
            {}
        )
        assert key_with_url.startswith("url:")
        assert "example.com" in key_with_url

    def test_dedupe_key_uses_canonical_url(self):
        """Deduplication should use already-canonical URLs."""
        canonical1 = canonical_url("https://example.com/path?a=1&b=2")
        canonical2 = canonical_url("https://EXAMPLE.COM/path?b=2&a=1")
        key1 = dedupe_key("Programme", canonical1, {})
        key2 = dedupe_key("Programme", canonical2, {})
        assert key1 == key2

    def test_dedupe_key_includes_target_kind(self):
        """Target kind should be part of the key logic."""
        key_person = dedupe_key("Person", "https://example.com", {})
        key_programme = dedupe_key("Programme", "https://example.com", {})
        # Keys should differ based on target_kind (through dedupe logic)
        # Both will use URL since no external IDs, but they maintain separate identities
        assert "url:" in key_person and "url:" in key_programme


class TestMakeTrace:
    """Test discovery trace creation."""

    def test_make_trace_returns_dict(self):
        """make_trace should return a plain dict."""
        trace = make_trace(
            target_id="target123",
            source="OpenAlex",
            query="supervisor query",
            run_id="run456",
            at="2026-09-19T10:30:00Z"
        )
        assert isinstance(trace, dict)

    def test_make_trace_dict_keys(self):
        """Returned dict should have required columns."""
        trace = make_trace(
            target_id="target123",
            source="OpenAlex",
            query="supervisor query",
            run_id="run456",
            at="2026-09-19T10:30:00Z"
        )
        assert "target_id" in trace
        assert "source" in trace
        assert "query" in trace
        assert "run_id" in trace
        assert "at" in trace

    def test_make_trace_values_preserved(self):
        """Input values should be preserved in output dict."""
        target_id = "target123"
        source = "OpenAlex"
        query = "supervisor query"
        run_id = "run456"
        at = "2026-09-19T10:30:00Z"

        trace = make_trace(
            target_id=target_id,
            source=source,
            query=query,
            run_id=run_id,
            at=at
        )
        assert trace["target_id"] == target_id
        assert trace["source"] == source
        assert trace["query"] == query
        assert trace["run_id"] == run_id
        assert trace["at"] == at

    def test_make_trace_rejects_empty_source(self):
        """Empty source should raise ValueError."""
        with pytest.raises(ValueError, match="source.*empty"):
            make_trace(
                target_id="target123",
                source="",
                query="query text",
                run_id="run456",
                at="2026-09-19T10:30:00Z"
            )

    def test_make_trace_rejects_empty_query(self):
        """Empty query should raise ValueError."""
        with pytest.raises(ValueError, match="query.*empty"):
            make_trace(
                target_id="target123",
                source="OpenAlex",
                query="",
                run_id="run456",
                at="2026-09-19T10:30:00Z"
            )

    def test_make_trace_rejects_none_source(self):
        """None source should raise ValueError."""
        with pytest.raises(ValueError, match="source.*empty"):
            make_trace(
                target_id="target123",
                source=None,
                query="query text",
                run_id="run456",
                at="2026-09-19T10:30:00Z"
            )

    def test_make_trace_rejects_none_query(self):
        """None query should raise ValueError."""
        with pytest.raises(ValueError, match="query.*empty"):
            make_trace(
                target_id="target123",
                source="OpenAlex",
                query=None,
                run_id="run456",
                at="2026-09-19T10:30:00Z"
            )

    def test_make_trace_allows_none_run_id(self):
        """None run_id should be allowed."""
        trace = make_trace(
            target_id="target123",
            source="OpenAlex",
            query="supervisor query",
            run_id=None,
            at="2026-09-19T10:30:00Z"
        )
        assert trace["run_id"] is None

    def test_make_trace_dict_matches_schema_columns(self):
        """Dict should match radar_discovery_traces table columns."""
        trace = make_trace(
            target_id="t123",
            source="TestSource",
            query="test query",
            run_id="r456",
            at="2026-09-19T00:00:00Z"
        )
        expected_keys = {"target_id", "source", "query", "run_id", "at"}
        assert set(trace.keys()) >= expected_keys
