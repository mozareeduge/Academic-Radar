import os
import time
import json
from typing import Callable, Optional, Dict, Any, List
from urllib.parse import urlencode

from academic_radar.security.fetch import safe_fetch


class OpenAIREClient:
    def __init__(
        self,
        http_get: Callable,
        base_url: Optional[str] = None,
        cache: Optional[Dict[str, Any]] = None,
        min_interval_s: float = 0.2,
        resolver: Optional[Callable] = None,
    ):
        if base_url is None:
            # Live-verified 2026-09-20 against https://api.openaire.eu/graph/v3/api-docs
            base_url = os.environ.get(
                "OPENAIRE_BASE_URL",
                "https://api.openaire.eu/graph/v3"
            )
        self.http_get = http_get
        self.base_url = base_url
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

    def search_persons(self, name: str) -> List[Dict[str, Any]]:
        """Search for persons by name."""
        params = {"search": name}
        url = f"{self.base_url}/persons?{urlencode(params)}"

        if url in self.cache:
            return self.cache[url]

        response = self._make_request(url)

        if "error" in response:
            return []

        persons = []
        for person_data in response.get("results", []):
            normalized = self._normalize_person(person_data)
            persons.append(normalized)

        self.cache[url] = persons
        return persons

    def search_projects(
        self, query: str, funder: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for projects by query, optionally filtered by funder.

        Live-verified 2026-09-20: the documented `funder` param returns 0
        results on the production Graph v3 API even with correct quoting;
        `fundingShortName` (e.g. "SNSF") is the filter that works.
        """
        params = {"search": query}
        if funder:
            params["fundingShortName"] = funder

        url = f"{self.base_url}/projects?{urlencode(params)}"

        if url in self.cache:
            return self.cache[url]

        response = self._make_request(url)

        if "error" in response:
            return []

        projects = []
        for project_data in response.get("results", []):
            normalized = self._normalize_project(project_data)
            projects.append(normalized)

        self.cache[url] = projects
        return projects

    def search_organizations(self, name: str) -> List[Dict[str, Any]]:
        """Search for organizations by name."""
        params = {"search": name}
        url = f"{self.base_url}/organizations?{urlencode(params)}"

        if url in self.cache:
            return self.cache[url]

        response = self._make_request(url)

        if "error" in response:
            return []

        organizations = []
        for org_data in response.get("results", []):
            normalized = self._normalize_organization(org_data)
            organizations.append(normalized)

        self.cache[url] = organizations
        return organizations

    def search_research_products(
        self, query: str, author_orcid: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for research products by query, optionally filtered by author ORCID."""
        params = {"search": query}
        if author_orcid:
            params["authorId"] = author_orcid

        url = f"{self.base_url}/research-products?{urlencode(params)}"

        if url in self.cache:
            return self.cache[url]

        response = self._make_request(url)

        if "error" in response:
            return []

        products = []
        for product_data in response.get("results", []):
            normalized = self._normalize_research_product(product_data)
            products.append(normalized)

        self.cache[url] = products
        return products

    def _normalize_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize person response to standard format (live Graph v3 shape)."""
        orcid = None
        for pid in person_data.get("pid") or []:
            if isinstance(pid, dict) and pid.get("typeCode") == "orcid":
                orcid = pid.get("value")
                break
        display_name = " ".join(
            part
            for part in (person_data.get("givenName"), person_data.get("familyName"))
            if part
        ) or None
        return {
            "openaire_id": person_data.get("id"),
            "display_name": display_name,
            "orcid": orcid,
            "research_products_count": person_data.get("research_products_count"),
        }

    def _normalize_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize project response to standard format (live Graph v3 shape)."""
        fundings = project_data.get("fundings") or []
        granted = project_data.get("granted") or {}
        start_date = project_data.get("startDate") or ""
        end_date = project_data.get("endDate") or ""
        return {
            "openaire_id": project_data.get("id"),
            "title": project_data.get("title"),
            "funder": (fundings[0].get("shortName") if fundings else None),
            "start_year": start_date[:4] or None,
            "end_year": end_date[:4] or None,
            "funding_amount": granted.get("fundedAmount"),
        }

    def _normalize_organization(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize organization response to standard format (live Graph v3 shape)."""
        ror = None
        for pid in org_data.get("pids") or []:
            if isinstance(pid, dict) and pid.get("scheme") == "ror":
                ror = pid.get("value")
                break
        country = org_data.get("country") or {}
        return {
            "openaire_id": org_data.get("id"),
            "display_name": org_data.get("legalName"),
            "ror": ror,
            "country": country.get("label") or country.get("code"),
        }

    def _normalize_research_product(
        self, product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize research product response to standard format (live Graph v3 shape)."""
        doi = None
        for pid in product_data.get("pids") or []:
            if isinstance(pid, dict) and pid.get("scheme") == "doi":
                doi = pid.get("value")
                break
        pub_date = product_data.get("publicationDate") or ""
        authors = [
            a.get("fullName")
            for a in (product_data.get("authors") or [])
            if isinstance(a, dict)
        ]
        return {
            "openaire_id": product_data.get("id"),
            "title": product_data.get("mainTitle"),
            "doi": doi,
            "publication_year": pub_date[:4] or None,
            "authors": authors,
        }
