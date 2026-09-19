from pydantic import BaseModel, Field
from typing import Optional
from academic_radar.domain.enums import ClaimType, CoverageStatus


class ClaimOut(BaseModel):
    statement: str
    claim_type: ClaimType
    evidence_ids: list[str]
    protocol_class: str
    unknowns: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)


class NodeOutput(BaseModel):
    schema_version: str
    node: str
    claims: list[ClaimOut]
    coverage: dict[str, CoverageStatus]
