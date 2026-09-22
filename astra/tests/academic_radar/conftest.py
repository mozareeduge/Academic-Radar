"""Radar API tests use one explicitly configured workspace owner."""

import pytest


@pytest.fixture(autouse=True)
def _configured_radar_owner(monkeypatch):
    monkeypatch.setenv("RADAR_OWNER_EMAIL", "alice@example.com")
