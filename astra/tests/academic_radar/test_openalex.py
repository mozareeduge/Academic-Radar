import json
import os
import pytest
import socket
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from academic_radar.connectors.openalex import OpenAlexClient


def mock_resolver_public(hostname, family):
    """Mock resolver for public addresses."""
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]


def _get_fixture_path(filename):
    """Get absolute path to fixture file."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(test_dir, "fixtures", filename)


@pytest.fixture
def mock_http_get():
    """Mock HTTP GET function."""
    return Mock()


@pytest.fixture
def openalex_authors_fixture():
    """Load OpenAlex authors fixture."""
    with open(_get_fixture_path('openalex_authors.json')) as f:
        return json.load(f)


@pytest.fixture
def openalex_works_fixture():
    """Load OpenAlex works fixture."""
    with open(_get_fixture_path('openalex_works.json')) as f:
        return json.load(f)


class TestOpenAlexSearchAuthors:

    def test_select_fields_in_url(self, mock_http_get):
        """Test that select= parameter is present in URL."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"results": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        client.search_authors("Jane Smith")

        called_url = mock_http_get.call_args[0][0]
        assert "select=" in called_url
        assert "display_name" in called_url
        assert "orcid" in called_url
        assert "last_known_institutions" in called_url
        assert "works_count" in called_url

    def test_api_key_absent_when_unset(self, mock_http_get):
        """Test that api_key is not sent in URL when not set."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"results": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, api_key=None, resolver=mock_resolver_public)
        client.search_authors("Jane Smith")

        called_url = mock_http_get.call_args[0][0]
        assert "api_key" not in called_url

    def test_api_key_present_when_set(self, mock_http_get):
        """Test that api_key is sent in URL when set."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"results": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, api_key="test-key-123", resolver=mock_resolver_public)
        client.search_authors("Jane Smith")

        called_url = mock_http_get.call_args[0][0]
        assert "api_key=test-key-123" in called_url

    def test_cache_hit_avoids_second_call(self, mock_http_get, openalex_authors_fixture):
        """Test that cache hit avoids a second HTTP call."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openalex_authors_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)

        # First call
        results1 = client.search_authors("Jane Smith")
        assert len(results1) == 2
        assert mock_http_get.call_count == 1

        # Second call (should hit cache)
        results2 = client.search_authors("Jane Smith")
        assert len(results2) == 2
        assert mock_http_get.call_count == 1
        assert results1 == results2

    def test_same_display_name_different_institutions(
        self, mock_http_get, openalex_authors_fixture
    ):
        """Test that two authors with same name at different institutions are returned."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openalex_authors_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.search_authors("Jane Smith")

        assert len(results) == 2
        assert results[0]["display_name"] == "Jane Smith"
        assert results[1]["display_name"] == "Jane Smith"
        assert results[0]["last_known_institutions"][0]["display_name"] == "University of Oxford"
        assert results[1]["last_known_institutions"][0]["display_name"] == "University of Cambridge"
        assert results[0]["orcid"] == "https://orcid.org/0000-0001-2345-6789"
        assert results[1]["orcid"] == "https://orcid.org/0000-0005-9876-5432"

    def test_normalized_output_keys(self, mock_http_get, openalex_authors_fixture):
        """Test that output has expected normalized keys."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openalex_authors_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.search_authors("Jane Smith")

        assert len(results) > 0
        for author in results:
            assert "openalex_id" in author
            assert "display_name" in author
            assert "orcid" in author
            assert "last_known_institutions" in author
            assert "works_count" in author


class TestOpenAlexRetry:

    def test_429_twice_then_200_succeeds(self, mock_http_get, openalex_authors_fixture):
        """Test that 429 followed by eventual 200 succeeds with backoff."""
        mock_resp_429_1 = Mock()
        mock_resp_429_1.status_code = 429
        mock_resp_429_1.headers = {'content-type': 'application/json'}
        mock_resp_429_1.error = None

        mock_resp_429_2 = Mock()
        mock_resp_429_2.status_code = 429
        mock_resp_429_2.headers = {'content-type': 'application/json'}
        mock_resp_429_2.error = None

        mock_resp_200 = Mock()
        mock_resp_200.status_code = 200
        mock_resp_200.headers = {'content-type': 'application/json'}
        mock_resp_200.content = json.dumps(openalex_authors_fixture).encode('utf-8')

        mock_http_get.side_effect = [mock_resp_429_1, mock_resp_429_2, mock_resp_200]

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)

        with patch('academic_radar.connectors.openalex.time.sleep'):
            results = client.search_authors("Jane Smith")

        assert len(results) == 2
        assert mock_http_get.call_count == 3

    def test_429_four_times_returns_error(self, mock_http_get):
        """Test that 429 repeated 4+ times returns error result, not exception."""
        mock_resp_429 = Mock()
        mock_resp_429.status_code = 429
        mock_resp_429.headers = {'content-type': 'application/json'}
        mock_resp_429.error = None

        mock_http_get.side_effect = [mock_resp_429] * 4

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)

        with patch('academic_radar.connectors.openalex.time.sleep'):
            results = client.search_authors("Jane Smith")

        assert results == []
        assert mock_http_get.call_count == 3

    def test_500_error_retries_with_backoff(self, mock_http_get, openalex_authors_fixture):
        """Test that 500 errors trigger retry with backoff."""
        mock_resp_500 = Mock()
        mock_resp_500.status_code = 500
        mock_resp_500.headers = {'content-type': 'application/json'}
        mock_resp_500.error = None

        mock_resp_200 = Mock()
        mock_resp_200.status_code = 200
        mock_resp_200.headers = {'content-type': 'application/json'}
        mock_resp_200.content = json.dumps(openalex_authors_fixture).encode('utf-8')

        mock_http_get.side_effect = [mock_resp_500, mock_resp_200]

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)

        with patch('academic_radar.connectors.openalex.time.sleep'):
            results = client.search_authors("Jane Smith")

        assert len(results) == 2
        assert mock_http_get.call_count == 2


class TestOpenAlexGetAuthor:

    def test_get_author_by_id(self, mock_http_get):
        """Test fetching a single author by OpenAlex ID."""
        author_data = {
            "id": "https://openalex.org/A1234567890",
            "display_name": "Jane Smith",
            "orcid": "https://orcid.org/0000-0001-2345-6789",
            "last_known_institutions": [
                {
                    "id": "https://ror.org/03x3j6d52",
                    "ror": "03x3j6d52",
                    "display_name": "University of Oxford"
                }
            ],
            "works_count": 42
        }

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(author_data).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        result = client.get_author("A1234567890")

        assert result is not None
        assert result["display_name"] == "Jane Smith"
        assert result["works_count"] == 42

    def test_get_author_select_fields_in_url(self, mock_http_get):
        """Test that select= is present when fetching author."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        client.get_author("A1234567890")

        called_url = mock_http_get.call_args[0][0]
        assert "select=" in called_url
        assert "display_name" in called_url


class TestOpenAlexAuthorWorks:

    def test_author_works_retrieves_works(self, mock_http_get, openalex_works_fixture):
        """Test fetching works for an author."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openalex_works_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.author_works("A1234567890")

        assert len(results) == 2
        assert results[0]["title"] == "Machine Learning in Academic Research"
        assert results[1]["title"] == "Neural Networks and Deep Learning"

    def test_author_works_select_fields_in_url(self, mock_http_get):
        """Test that select= is present in author works URL."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"results": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        client.author_works("A1234567890")

        called_url = mock_http_get.call_args[0][0]
        assert "select=" in called_url
        assert "doi" in called_url
        assert "title" in called_url
        assert "publication_year" in called_url
        assert "topics" in called_url

    def test_normalized_work_output_keys(self, mock_http_get, openalex_works_fixture):
        """Test that work output has expected normalized keys."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openalex_works_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.author_works("A1234567890")

        assert len(results) > 0
        for work in results:
            assert "id" in work
            assert "doi" in work
            assert "title" in work
            assert "publication_year" in work
            assert "topics" in work

    def test_author_works_cache_hit(self, mock_http_get, openalex_works_fixture):
        """Test that cache hit avoids second call for works."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openalex_works_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)

        results1 = client.author_works("A1234567890")
        assert mock_http_get.call_count == 1

        results2 = client.author_works("A1234567890")
        assert mock_http_get.call_count == 1
        assert results1 == results2


class TestOpenAlexMinInterval:

    def test_min_interval_enforced(self, mock_http_get):
        """Test that minimum interval between requests is enforced."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"results": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(
            http_get=mock_http_get,
            resolver=mock_resolver_public,
            min_interval_s=0.1,
        )

        with patch('academic_radar.connectors.openalex.time.sleep') as mock_sleep:
            client.search_authors("Author 1")
            client.search_authors("Author 2")

            mock_sleep.assert_called()


class TestOpenAlexCacheCustom:

    def test_custom_cache_provided(self, mock_http_get):
        """Test that a custom cache dict can be provided."""
        custom_cache = {}
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"results": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAlexClient(
            http_get=mock_http_get,
            resolver=mock_resolver_public,
            cache=custom_cache,
        )

        client.search_authors("Jane Smith")

        assert len(custom_cache) > 0


class TestOpenAlexIntegration:

    def test_safe_fetch_integration(self, openalex_authors_fixture):
        """Test that OpenAlexClient properly integrates with safe_fetch."""
        from academic_radar.security.fetch import safe_fetch

        def mock_http_get(url, **kwargs):
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.headers = {'content-type': 'application/json'}
            mock_resp.content = json.dumps(openalex_authors_fixture).encode('utf-8')
            return mock_resp

        client = OpenAlexClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.search_authors("Jane Smith")

        assert len(results) == 2
