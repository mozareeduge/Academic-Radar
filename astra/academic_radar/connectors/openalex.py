import time
import json
from typing import Callable, Optional, Dict, Any, List
from urllib.parse import urlencode

from academic_radar.security.fetch import safe_fetch


class OpenAlexClient:
    def __init__(
        self,
        http_get: Callable,
        base_url: str = "https://api.openalex.org",
        api_key: Optional[str] = None,
        cache: Optional[Dict[str, Any]] = None,
        min_interval_s: float = 0.1,
        resolver: Optional[Callable] = None,
    ):
        self.http_get = http_get
        self.base_url = base_url
        self.api_key = api_key
        self.cache = cache if cache is not None else {}
        self.min_interval_s = min_interval_s
        self.last_request_time = 0
        self.resolver = resolver

    def _sleep_before_request(self) -> None:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval_s:
            time.sleep(self.min_interval_s - elapsed)

    def _make_request(
        self, url: str, retries: int = 3
    ) -> Dict[str, Any]:
        """Make HTTP request with exponential backoff retry on 429/5xx."""
        for attempt in range(retries):
            self._sleep_before_request()
            self.last_request_time = time.time()

            fetch_kwargs = {"http_get": self.http_get}
            if self.resolver:
                fetch_kwargs["resolver"] = self.resolver

            result = safe_fetch(url, **fetch_kwargs)

            if result.error is None and result.status == 200:
                try:
                    return json.loads(result.body_bytes.decode('utf-8'))
                except (json.JSONDecodeError, AttributeError):
                    return {"error": "Failed to parse JSON response"}

            if result.status in (429, 500, 502, 503, 504):
                if attempt < retries - 1:
                    backoff = 2 ** attempt
                    time.sleep(backoff)
                    continue
                else:
                    return {"error": f"HTTP {result.status} after {retries} retries"}

            if result.error:
                return {"error": result.error}

            return {"error": f"HTTP {result.status}"}

        return {"error": "Max retries exceeded"}

    def search_authors(
        self,
        name: str,
        institution_ror: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for authors by name, optionally filtered by institution ROR."""
        select_fields = [
            "id",
            "display_name",
            "orcid",
            "last_known_institutions",
            "works_count",
        ]

        params = {
            "search": name,
            "select": ",".join(select_fields),
        }

        if institution_ror:
            params["filter"] = f"last_known_institutions.ror:{institution_ror}"

        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.base_url}/authors?{urlencode(params)}"

        if url in self.cache:
            return self.cache[url]

        response = self._make_request(url)

        if "error" in response:
            return []

        authors = []
        for author_data in response.get("results", []):
            normalized = self._normalize_author(author_data)
            authors.append(normalized)

        self.cache[url] = authors
        return authors

    def get_author(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """Get author details by OpenAlex ID."""
        select_fields = [
            "id",
            "display_name",
            "orcid",
            "last_known_institutions",
            "works_count",
        ]

        params = {"select": ",".join(select_fields)}

        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.base_url}/authors/{openalex_id}?{urlencode(params)}"

        if url in self.cache:
            return self.cache[url]

        response = self._make_request(url)

        if "error" in response:
            return None

        normalized = self._normalize_author(response)
        self.cache[url] = normalized
        return normalized

    def author_works(
        self,
        openalex_id: str,
        since_year: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get works for an author."""
        select_fields = [
            "id",
            "doi",
            "title",
            "publication_year",
            "topics",
        ]

        params = {
            "select": ",".join(select_fields),
            "limit": str(limit),
        }

        if since_year:
            params["filter"] = f"publication_year:>{since_year - 1}"

        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{self.base_url}/works?{urlencode(params)}&filter=author.id:{openalex_id}"

        if url in self.cache:
            return self.cache[url]

        response = self._make_request(url)

        if "error" in response:
            return []

        works = []
        for work_data in response.get("results", []):
            normalized = self._normalize_work(work_data)
            works.append(normalized)

        self.cache[url] = works
        return works

    def _normalize_author(
        self, author_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize author response to standard format."""
        institutions = []
        for inst in author_data.get("last_known_institutions", []):
            institutions.append({
                "ror": inst.get("ror"),
                "display_name": inst.get("display_name"),
            })

        return {
            "openalex_id": author_data.get("id"),
            "display_name": author_data.get("display_name"),
            "orcid": author_data.get("orcid"),
            "last_known_institutions": institutions,
            "works_count": author_data.get("works_count"),
        }

    def _normalize_work(self, work_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize work response to standard format."""
        topics = []
        for topic in work_data.get("topics", []):
            topics.append(topic.get("display_name") if isinstance(topic, dict) else topic)

        return {
            "id": work_data.get("id"),
            "doi": work_data.get("doi"),
            "title": work_data.get("title"),
            "publication_year": work_data.get("publication_year"),
            "topics": topics,
        }
