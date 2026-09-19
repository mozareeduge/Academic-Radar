"""Fixture-backed discovery source adapter."""

import json
from pathlib import Path
from academic_radar.discovery.normalize import canonical_url, dedupe_key


class FixtureSource:
    """Load and yield normalised candidates from a JSON fixture file."""

    def __init__(self, path):
        """
        Initialize fixture source with a JSON file path.

        Args:
            path: Path to a JSON file containing candidate records.
        """
        self.path = Path(path)

    def candidates(self):
        """
        Load and yield normalised candidate dicts from fixture.

        Each candidate is normalised with canonical_url and dedupe_key.

        Yields:
            dict with keys: kind, url, external_ids, dedupe_key, title, country, url_canonical
        """
        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for candidate in data:
            url = candidate.get('url', '')
            external_ids = candidate.get('external_ids', {})
            url_canonical = canonical_url(url) if url else ''
            dedupe = dedupe_key(candidate.get('kind', ''), url_canonical, external_ids)

            yield {
                'kind': candidate.get('kind', ''),
                'url': url,
                'url_canonical': url_canonical,
                'external_ids': external_ids,
                'dedupe_key': dedupe,
                'title': candidate.get('title', ''),
                'country': candidate.get('country', ''),
            }
