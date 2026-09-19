"""Profile and route seed importer.

Imports candidate profile and MozareRoute definitions from YAML fixture.
Enforces provenance on every fact and validates state enums.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4
from datetime import datetime, timezone

import yaml
from sqlalchemy import text
from sqlalchemy.orm import Session

from academic_radar.domain.enums import RouteState, ProfileState


@dataclass
class ImportReport:
    """Result of an import operation."""
    profiles_created: int
    profiles_updated: int
    routes_created: int
    routes_updated: int
    errors: list[str]


def _validate_provenance(fact: Any, fact_name: str) -> dict[str, Any]:
    """Extract and validate provenance from a fact dict.

    Raises ValueError if provenance is missing.
    """
    if not isinstance(fact, dict):
        raise ValueError(f"{fact_name}: must be a dict, got {type(fact).__name__}")

    provenance = fact.get("provenance")
    if not provenance:
        raise ValueError(f"{fact_name}: missing required 'provenance' field")

    if not isinstance(provenance, dict):
        raise ValueError(f"{fact_name}: provenance must be a dict, got {type(provenance).__name__}")

    source = provenance.get("source")
    if not source:
        raise ValueError(f"{fact_name}: provenance.source is required")

    verified = provenance.get("verified")
    if verified is None:
        raise ValueError(f"{fact_name}: provenance.verified is required")

    return provenance


def import_seed(path: str | Path, session: Session) -> ImportReport:
    """Import candidate profile and routes from YAML seed file.

    Args:
        path: Path to YAML file
        session: SQLAlchemy session

    Returns:
        ImportReport with counts and errors

    Raises:
        ValueError: If provenance is missing or state values are invalid
        FileNotFoundError: If seed file does not exist
        yaml.YAMLError: If YAML is malformed
    """
    report = ImportReport(
        profiles_created=0,
        profiles_updated=0,
        routes_created=0,
        routes_updated=0,
        errors=[],
    )

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Seed file must contain a YAML dict at root level")

    # Process candidate profile
    candidate_data = data.get("candidate")
    if candidate_data:
        report = _import_candidate_profile(candidate_data, session, report)

    # Process routes
    routes = data.get("routes", [])
    for route_data in routes:
        report = _import_route(route_data, session, report)

    session.commit()
    return report


def _import_candidate_profile(
    candidate_data: dict[str, Any], session: Session, report: ImportReport
) -> ImportReport:
    """Import or update candidate profile."""

    # Validate state if present
    state = candidate_data.get("state", "ACTIVE")
    try:
        ProfileState(state)
    except ValueError:
        raise ValueError(f"Invalid profile state: {state}")

    # For idempotency, there is only one active profile at a time
    # Find existing active profile
    existing = session.execute(
        text("SELECT id FROM radar_candidate_profiles WHERE state = 'ACTIVE' LIMIT 1")
    ).scalar()

    profile_id = str(uuid4()) if not existing else existing
    now = datetime.now(timezone.utc)

    # Prepare profile data
    profile_data = {
        "id": profile_id,
        "state": state,
        "created_at": now,
        "updated_at": now,
    }

    # Validate and store constraints
    if "fixed_constraints" in candidate_data:
        _validate_provenance(candidate_data["fixed_constraints"], "candidate.fixed_constraints")
        profile_data["fixed_constraints"] = candidate_data["fixed_constraints"].get("value")

    # Validate and store education
    education = candidate_data.get("education", [])
    for i, edu in enumerate(education):
        _validate_provenance(edu, f"candidate.education[{i}]")
    profile_data["education"] = json.dumps(education) if education else None

    # Validate and store language evidence
    language_evidence = candidate_data.get("language_evidence", [])
    for i, lang in enumerate(language_evidence):
        _validate_provenance(lang, f"candidate.language_evidence[{i}]")
    profile_data["language_evidence"] = json.dumps(language_evidence) if language_evidence else None

    # Validate and store scholarly work
    scholarly = candidate_data.get("scholarly", [])
    for i, work in enumerate(scholarly):
        _validate_provenance(work, f"candidate.scholarly[{i}]")
    profile_data["scholarly_work"] = json.dumps(scholarly) if scholarly else None

    # Validate and store artistic work
    artistic = candidate_data.get("artistic", [])
    for i, work in enumerate(artistic):
        _validate_provenance(work, f"candidate.artistic[{i}]")
    profile_data["artistic_curatorial_work"] = json.dumps(artistic) if artistic else None

    # Validate and store professional work
    professional = candidate_data.get("professional", [])
    for i, work in enumerate(professional):
        _validate_provenance(work, f"candidate.professional[{i}]")
    profile_data["professional_technical_evidence"] = json.dumps(professional) if professional else None

    # Upsert profile
    if existing:
        session.execute(
            text("""
                UPDATE radar_candidate_profiles
                SET state = :state,
                    fixed_constraints = :fixed_constraints,
                    education = :education,
                    language_evidence = :language_evidence,
                    scholarly_work = :scholarly_work,
                    artistic_curatorial_work = :artistic_curatorial_work,
                    professional_technical_evidence = :professional_technical_evidence,
                    updated_at = :updated_at
                WHERE id = :id
            """),
            profile_data,
        )
        report.profiles_updated += 1
    else:
        session.execute(
            text("""
                INSERT INTO radar_candidate_profiles
                (id, state, fixed_constraints, education, language_evidence,
                 scholarly_work, artistic_curatorial_work,
                 professional_technical_evidence, created_at, updated_at)
                VALUES (:id, :state, :fixed_constraints, :education, :language_evidence,
                        :scholarly_work, :artistic_curatorial_work,
                        :professional_technical_evidence, :created_at, :updated_at)
            """),
            profile_data,
        )
        report.profiles_created += 1

    return report


def _import_route(route_data: dict[str, Any], session: Session, report: ImportReport) -> ImportReport:
    """Import or update a MozareRoute."""

    # seed_key is required for idempotency
    seed_key = route_data.get("seed_key")
    if not seed_key:
        raise ValueError("routes: every route must have a seed_key for idempotency")

    # Validate state
    state = route_data.get("state", "ACTIVE")
    try:
        RouteState(state)
    except ValueError:
        raise ValueError(f"Invalid route state: {state}")

    # Find existing route by seed_key
    existing = session.execute(
        text("SELECT id FROM radar_mozare_routes WHERE name = :seed_key LIMIT 1"),
        {"seed_key": seed_key},
    ).scalar()

    route_id = str(uuid4()) if not existing else existing
    now = datetime.now(timezone.utc)

    # Build route data with JSON serialization for list fields
    route_data_db = {
        "id": route_id,
        "name": seed_key,
        "state": state,
        "route_statement": route_data.get("statement"),
        "core_problem": route_data.get("core_problem"),
        "operations_methods": json.dumps(route_data.get("methods")) if route_data.get("methods") else None,
        "relevant_corpora_material": json.dumps(route_data.get("corpora")) if route_data.get("corpora") else None,
        "target_disciplines": json.dumps(route_data.get("target_disciplines")) if route_data.get("target_disciplines") else None,
        "prohibited_overclaims": json.dumps(route_data.get("prohibited_overclaims")) if route_data.get("prohibited_overclaims") else None,
        "maturity": route_data.get("maturity"),
        "created_at": now,
        "updated_at": now,
    }

    # Upsert route
    if existing:
        session.execute(
            text("""
                UPDATE radar_mozare_routes
                SET state = :state,
                    route_statement = :route_statement,
                    core_problem = :core_problem,
                    operations_methods = :operations_methods,
                    relevant_corpora_material = :relevant_corpora_material,
                    target_disciplines = :target_disciplines,
                    prohibited_overclaims = :prohibited_overclaims,
                    maturity = :maturity,
                    updated_at = :updated_at
                WHERE id = :id
            """),
            route_data_db,
        )
        report.routes_updated += 1
    else:
        session.execute(
            text("""
                INSERT INTO radar_mozare_routes
                (id, name, state, route_statement, core_problem,
                 operations_methods, relevant_corpora_material,
                 target_disciplines, prohibited_overclaims, maturity,
                 created_at, updated_at)
                VALUES (:id, :name, :state, :route_statement, :core_problem,
                        :operations_methods, :relevant_corpora_material,
                        :target_disciplines, :prohibited_overclaims, :maturity,
                        :created_at, :updated_at)
            """),
            route_data_db,
        )
        report.routes_created += 1

    return report
