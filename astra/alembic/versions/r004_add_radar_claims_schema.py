"""Add radar claims and assessments schema

Revision ID: r004_add_radar_claims_schema
Revises: r003_add_radar_evidence_schema
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'r004_add_radar_claims_schema'
down_revision: Union[str, Sequence[str], None] = 'r003_add_radar_evidence_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create radar_claims
    op.create_table(
        'radar_claims',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('claim_type', sa.String(32), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('generated_by', sa.String(128), nullable=True),
        sa.Column('run_id', sa.String(36), nullable=True),
        sa.Column('protocol_version', sa.String(64), nullable=True),
        sa.Column('reviewed_by_user', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "claim_type IN ('EXTERNAL_FACT', 'OBSERVED_RELATION', 'INFERENCE', 'USER_DECISION')",
            name='ck_radar_claims_claim_type'
        ),
        sa.CheckConstraint(
            "status IN ('SUPPORTED', 'PARTIAL', 'CONTRADICTED', 'UNKNOWN', 'STALE')",
            name='ck_radar_claims_status'
        ),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.ForeignKeyConstraint(['run_id'], ['radar_research_runs.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_claims_case_id', 'radar_claims', ['case_id'])
    op.create_index('ix_radar_claims_run_id', 'radar_claims', ['run_id'])

    # Create radar_claim_evidence
    op.create_table(
        'radar_claim_evidence',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('claim_id', sa.String(36), nullable=False),
        sa.Column('evidence_artifact_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['radar_claims.id'], ),
        sa.ForeignKeyConstraint(['evidence_artifact_id'], ['radar_evidence_artifacts.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_claim_evidence_claim_id', 'radar_claim_evidence', ['claim_id'])
    op.create_index('ix_radar_claim_evidence_evidence_artifact_id', 'radar_claim_evidence', ['evidence_artifact_id'])

    # Create radar_gate_assessments
    op.create_table(
        'radar_gate_assessments',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('requirement', sa.Text(), nullable=False),
        sa.Column('source_authority', sa.String(32), nullable=False),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('evaluation_rule', sa.Text(), nullable=True),
        sa.Column('result', sa.String(32), nullable=False),
        sa.Column('evidence_ids', sa.JSON(), nullable=True),
        sa.Column('provenance', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_authority IN ('OFFICIAL_REGULATION', 'OFFICIAL_PROGRAMME', 'OFFICIAL_DEPARTMENT_OR_PERSON', "
            "'AUTHORITATIVE_REGISTRY', 'PRIMARY_RESEARCH_OUTPUT', 'REPUTABLE_SECONDARY', 'DISCOVERY_AGGREGATOR', 'UNKNOWN')",
            name='ck_radar_gate_assessments_source_authority'
        ),
        sa.CheckConstraint(
            "result IN ('PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE', 'STALE')",
            name='ck_radar_gate_assessments_result'
        ),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_gate_assessments_case_id', 'radar_gate_assessments', ['case_id'])

    # Create radar_dimension_assessments
    op.create_table(
        'radar_dimension_assessments',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('dimension_id', sa.String(64), nullable=False),
        sa.Column('scale', sa.String(64), nullable=False),
        sa.Column('value', sa.Integer(), nullable=True),
        sa.Column('unknowns', sa.JSON(), nullable=True),
        sa.Column('reviewer_status', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "value IS NULL OR (value >= 0 AND value <= 3)",
            name='ck_radar_dimension_assessments_value'
        ),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_dimension_assessments_case_id', 'radar_dimension_assessments', ['case_id'])

    # Create radar_funding_assessments
    op.create_table(
        'radar_funding_assessments',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('funding_route_id', sa.String(36), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('award_amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('tuition_amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('duration_months', sa.Integer(), nullable=True),
        sa.Column('known_costs', sa.JSON(), nullable=True),
        sa.Column('unknown_costs', sa.JSON(), nullable=True),
        sa.Column('uncovered_gap', sa.Numeric(14, 2), nullable=True),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('ELIGIBLE', 'FUNDING_GAP', 'ELIGIBILITY_UNKNOWN', 'FORMALLY_BLOCKED')",
            name='ck_radar_funding_assessments_state'
        ),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.ForeignKeyConstraint(['funding_route_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_funding_assessments_case_id', 'radar_funding_assessments', ['case_id'])
    op.create_index('ix_radar_funding_assessments_funding_route_id', 'radar_funding_assessments', ['funding_route_id'])

    # Create radar_supervision_precedents
    op.create_table(
        'radar_supervision_precedents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('person_target_id', sa.String(36), nullable=True),
        sa.Column('project_target_id', sa.String(36), nullable=True),
        sa.Column('role', sa.String(128), nullable=False),
        sa.Column('fields', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.ForeignKeyConstraint(['person_target_id'], ['radar_target_entities.id'], ),
        sa.ForeignKeyConstraint(['project_target_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_supervision_precedents_case_id', 'radar_supervision_precedents', ['case_id'])
    op.create_index('ix_radar_supervision_precedents_person_target_id', 'radar_supervision_precedents', ['person_target_id'])
    op.create_index('ix_radar_supervision_precedents_project_target_id', 'radar_supervision_precedents', ['project_target_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('radar_supervision_precedents')
    op.drop_table('radar_funding_assessments')
    op.drop_table('radar_dimension_assessments')
    op.drop_table('radar_gate_assessments')
    op.drop_table('radar_claim_evidence')
    op.drop_table('radar_claims')
