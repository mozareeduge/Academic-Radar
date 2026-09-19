"""Loader for versioned protocol definitions from protocols.yaml."""

import os
from pathlib import Path
import yaml
from academic_radar.domain.protocols import Protocol


def load_protocols() -> dict[str, Protocol]:
    """Load five versioned protocol definitions from protocols.yaml.

    Returns:
        Dictionary with keys: SUPERVISOR_FIRST_PHD, ADVERTISED_PHD,
        STRUCTURED_PHD, MA_PROGRAMME, FUNDING_ASSESSMENT.
        Values are Protocol objects with version '1.0.0'.

    Raises:
        FileNotFoundError: If protocols.yaml not found.
        KeyError: If route key not found in loaded protocols.
    """
    protocol_dir = Path(__file__).parent
    yaml_path = protocol_dir / "protocols.yaml"

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    protocols_data = data.get("protocols", {})
    protocols = {}

    for route_key, route_data in protocols_data.items():
        protocol = Protocol(
            application_route=route_data["application_route"],
            version=route_data["version"],
            mandatory=tuple(route_data.get("mandatory", [])),
            optional=tuple(route_data.get("optional", [])),
            allow_zero_result=route_data.get("allow_zero_result", False),
            allowed_unknowns=tuple(route_data.get("allowed_unknowns", [])),
            blocking_unknowns=tuple(route_data.get("blocking_unknowns", [])),
            freshness_days=route_data.get("freshness_days", {}),
        )
        protocols[route_key] = protocol

    return protocols
