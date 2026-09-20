import json
import os
import pytest
import socket
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from academic_radar.connectors.openaire import OpenAIREClient


def mock_resolver_public(hostname, family):
    """Mock resolver for public addresses."""
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]


@pytest.fixture
def mock_http_get():
    """Mock HTTP GET function."""
    return Mock()


def _get_fixture_path(filename):
    """Get absolute path to fixture file."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(test_dir, "fixtures", filename)


@pytest.fixture
def openaire_persons_fixture():
    """Load OpenAIRE persons fixture."""
    with open(_get_fixture_path('openaire_persons.json')) as f:
        return json.load(f)


@pytest.fixture
def openaire_projects_fixture():
    """Load OpenAIRE projects fixture."""
    with open(_get_fixture_path('openaire_projects.json')) as f:
        return json.load(f)


@pytest.fixture
def openaire_organizations_fixture():
    """Load OpenAIRE organizations fixture."""
    with open(_get_fixture_path('openaire_organizations.json')) as f:
        return json.load(f)


@pytest.fixture
def openaire_research_products_fixture():
    """Load OpenAIRE research products fixture."""
    with open(_get_fixture_path('openaire_research_products.json')) as f:
        return json.load(f)


class TestOpenAIRESearchPersons:

    def test_url_contains_graph_v3(self, mock_http_get):
        """Test that URLs contain /graph/v3."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        client.search_persons("Alice Johnson")

        called_url = mock_http_get.call_args[0][0]
        assert "/graph/v3" in called_url
        assert "beta" not in called_url
        assert "/v4" not in called_url

    def test_env_override_respected(self, mock_http_get):
        """Test that OPENAIRE_BASE_URL environment variable is respected."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        custom_url = "https://custom.openaire.eu/api/v3"
        client = OpenAIREClient(
            http_get=mock_http_get,
            base_url=custom_url,
            resolver=mock_resolver_public
        )
        client.search_persons("Alice Johnson")

        called_url = mock_http_get.call_args[0][0]
        assert called_url.startswith(custom_url)

    def test_cache_hit_avoids_second_call(self, mock_http_get, openaire_persons_fixture):
        """Test that cache hit avoids a second HTTP call."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openaire_persons_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)

        # First call
        results1 = client.search_persons("Alice Johnson")
        assert len(results1) == 2
        assert mock_http_get.call_count == 1

        # Second call (should hit cache)
        results2 = client.search_persons("Alice Johnson")
        assert len(results2) == 2
        assert mock_http_get.call_count == 1
        assert results1 == results2

    def test_same_display_name_different_orcid(
        self, mock_http_get, openaire_persons_fixture
    ):
        """Test that two persons with same name but different ORCID are returned."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openaire_persons_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.search_persons("Alice Johnson")

        assert len(results) == 2
        assert results[0]["display_name"] == "Jane Smith"
        assert results[1]["display_name"] == "Jane Smith"
        assert results[0]["orcid"] == "0000-0002-4728-5184"
        assert results[1]["orcid"] == "0000-0001-2345-6789"

    def test_normalized_output_keys(self, mock_http_get, openaire_persons_fixture):
        """Test that output has expected normalized keys."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openaire_persons_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.search_persons("Alice Johnson")

        assert len(results) > 0
        for person in results:
            assert "openaire_id" in person
            assert "display_name" in person
            assert "orcid" in person
            assert "research_products_count" in person


class TestOpenAIRESearchProjects:

    def test_projects_search_url(self, mock_http_get):
        """Test that projects search URL is correct."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        client.search_projects("machine learning")

        called_url = mock_http_get.call_args[0][0]
        assert "/graph/v3" in called_url
        assert "search=" in called_url

    def test_projects_with_funder_filter(self, mock_http_get, openaire_projects_fixture):
        """Test that funder filter is included when specified."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openaire_projects_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.search_projects("ML", funder="ERC")

        called_url = mock_http_get.call_args[0][0]
        assert "fundingShortName=ERC" in called_url


class TestOpenAIRESearchOrganizations:

    def test_organizations_search_url(self, mock_http_get):
        """Test that organizations search URL is correct."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        client.search_organizations("Manchester")

        called_url = mock_http_get.call_args[0][0]
        assert "/graph/v3" in called_url
        assert "/organizations?" in called_url

    def test_organizations_normalized_output(
        self, mock_http_get, openaire_organizations_fixture
    ):
        """Test normalized organization output."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openaire_organizations_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.search_organizations("Manchester")

        assert len(results) > 0
        for org in results:
            assert "openaire_id" in org
            assert "display_name" in org
            assert "ror" in org
            assert "country" in org


class TestOpenAIRESearchResearchProducts:

    def test_research_products_search_url(self, mock_http_get):
        """Test that research products search URL is correct."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        client.search_research_products("deep learning")

        called_url = mock_http_get.call_args[0][0]
        assert "/graph/v3" in called_url
        assert "/research-products?" in called_url

    def test_research_products_with_author_orcid(
        self, mock_http_get, openaire_research_products_fixture
    ):
        """Test that author_orcid filter is included when specified."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps(openaire_research_products_fixture).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)
        results = client.search_research_products(
            "neural networks",
            author_orcid="0000-0001-2345-6789"
        )

        called_url = mock_http_get.call_args[0][0]
        assert "authorId=0000-0001-2345-6789" in called_url


class TestOpenAIRERetry:

    def test_429_twice_then_200_succeeds(self, mock_http_get, openaire_persons_fixture):
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
        mock_resp_200.content = json.dumps(openaire_persons_fixture).encode('utf-8')

        mock_http_get.side_effect = [mock_resp_429_1, mock_resp_429_2, mock_resp_200]

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)

        with patch('academic_radar.connectors.openaire.time.sleep'):
            results = client.search_persons("Alice Johnson")

        assert len(results) == 2
        assert mock_http_get.call_count == 3

    def test_429_four_times_returns_error(self, mock_http_get):
        """Test that 429 repeated 4+ times returns error result, not exception."""
        mock_resp_429 = Mock()
        mock_resp_429.status_code = 429
        mock_resp_429.headers = {'content-type': 'application/json'}
        mock_resp_429.error = None

        mock_http_get.side_effect = [mock_resp_429] * 4

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)

        with patch('academic_radar.connectors.openaire.time.sleep'):
            results = client.search_persons("Alice Johnson")

        assert results == []
        assert mock_http_get.call_count == 3

    def test_500_error_retries_with_backoff(self, mock_http_get, openaire_persons_fixture):
        """Test that 500 errors trigger retry with backoff."""
        mock_resp_500 = Mock()
        mock_resp_500.status_code = 500
        mock_resp_500.headers = {'content-type': 'application/json'}
        mock_resp_500.error = None

        mock_resp_200 = Mock()
        mock_resp_200.status_code = 200
        mock_resp_200.headers = {'content-type': 'application/json'}
        mock_resp_200.content = json.dumps(openaire_persons_fixture).encode('utf-8')

        mock_http_get.side_effect = [mock_resp_500, mock_resp_200]

        client = OpenAIREClient(http_get=mock_http_get, resolver=mock_resolver_public)

        with patch('academic_radar.connectors.openaire.time.sleep'):
            results = client.search_persons("Alice Johnson")

        assert len(results) == 2
        assert mock_http_get.call_count == 2


class TestOpenAIREMinInterval:

    def test_min_interval_enforced(self, mock_http_get):
        """Test that minimum interval between requests is enforced."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(
            http_get=mock_http_get,
            resolver=mock_resolver_public,
            min_interval_s=0.2,
        )

        with patch('academic_radar.connectors.openaire.time.sleep') as mock_sleep:
            client.search_persons("Person 1")
            client.search_persons("Person 2")

            mock_sleep.assert_called()


class TestOpenAIRECacheCustom:

    def test_custom_cache_provided(self, mock_http_get):
        """Test that a custom cache dict can be provided."""
        custom_cache = {}
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(
            http_get=mock_http_get,
            resolver=mock_resolver_public,
            cache=custom_cache,
        )

        client.search_persons("Alice Johnson")

        assert len(custom_cache) > 0


class TestOpenAIREBaseURLDefaults:

    def test_default_base_url_when_none_provided(self, mock_http_get):
        """Test that default base URL is used when none provided."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        client = OpenAIREClient(http_get=mock_http_get, base_url=None, resolver=mock_resolver_public)
        client.search_persons("Test")

        called_url = mock_http_get.call_args[0][0]
        assert "https://api.openaire.eu/graph/v3" in called_url

    def test_env_variable_overrides_default(self, mock_http_get):
        """Test that OPENAIRE_BASE_URL environment variable overrides default."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.headers = {'content-type': 'application/json'}
        mock_resp.content = json.dumps({"data": []}).encode('utf-8')
        mock_http_get.return_value = mock_resp

        with patch.dict(os.environ, {"OPENAIRE_BASE_URL": "https://custom.example.com/api"}):
            client = OpenAIREClient(http_get=mock_http_get, base_url=None, resolver=mock_resolver_public)
            client.search_persons("Test")

            called_url = mock_http_get.call_args[0][0]
            assert "https://custom.example.com/api" in called_url
