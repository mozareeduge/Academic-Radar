"""Add radar evidence schema (protocols, runs, evidence, snapshots, dependencies)

Revision ID: r003_add_radar_evidence_schema
Revises: r002_add_radar_cases_schema
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'r003_add_radar_evidence_schema'
down_revision: Union[str, Sequence[str], None] = 'r002_add_radar_cases_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create radar_research_protocols
    op.create_table(
        'radar_research_protocols',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('application_route', sa.String(32), nullable=False),
        sa.Column('protocol_version', sa.String(64), nullable=False),
        sa.Column('definition', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "application_route IN ('SUPERVISOR_FIRST_PHD', 'ADVERTISED_PHD', 'STRUCTURED_PHD', 'MA_PROGRAMME')",
            name='ck_radar_research_protocols_application_route'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_route', 'protocol_version', name='uq_radar_research_protocols_route_version'),
    )
    op.create_index('ix_radar_research_protocols_application_route', 'radar_research_protocols', ['application_route'])

    # Create radar_source_snapshots
    op.create_table(
        'radar_source_snapshots',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('fingerprint', sa.String(128), nullable=True),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('content_ref', sa.Text(), nullable=True),
        sa.Column('captured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('CAPTURED', 'UNCHANGED', 'CHANGED', 'FETCH_FAILED')",
            name='ck_radar_source_snapshots_state'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_source_snapshots_source_url', 'radar_source_snapshots', ['source_url'])
    op.create_index('ix_radar_source_snapshots_captured_at', 'radar_source_snapshots', ['captured_at'])

    # Create radar_research_runs
    op.create_table(
        'radar_research_runs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('protocol_version', sa.String(64), nullable=False),
        sa.Column('model_id', sa.String(128), nullable=True),
        sa.Column('provider_id', sa.String(128), nullable=True),
        sa.Column('prompt_hash', sa.String(64), nullable=True),
        sa.Column('schema_version', sa.String(64), nullable=True),
        sa.Column('run_identity', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'CANCELLING', 'COMPLETED', 'PARTIAL', 'FAILED', 'CANCELLED')",
            name='ck_radar_research_runs_status'
        ),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_research_runs_case_id', 'radar_research_runs', ['case_id'])
    op.create_index('ix_radar_research_runs_status', 'radar_research_runs', ['status'])

    # Create radar_evidence_artifacts
    op.create_table(
        'radar_evidence_artifacts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(64), nullable=True),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('structured_extraction', sa.JSON(), nullable=True),
        sa.Column('snapshot_id', sa.String(36), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_authority', sa.String(32), nullable=False),
        sa.Column('canonical_origin', sa.String(512), nullable=True),
        sa.Column('identity_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_authority IN ('OFFICIAL_REGULATION', 'OFFICIAL_PROGRAMME', 'OFFICIAL_DEPARTMENT_OR_PERSON', "
            "'AUTHORITATIVE_REGISTRY', 'PRIMARY_RESEARCH_OUTPUT', 'REPUTABLE_SECONDARY', 'DISCOVERY_AGGREGATOR', 'UNKNOWN')",
            name='ck_radar_evidence_artifacts_source_authority'
        ),
        sa.ForeignKeyConstraint(['snapshot_id'], ['radar_source_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_evidence_artifacts_source_url', 'radar_evidence_artifacts', ['source_url'])
    op.create_index('ix_radar_evidence_artifacts_snapshot_id', 'radar_evidence_artifacts', ['snapshot_id'])
    op.create_index('ix_radar_evidence_artifacts_canonical_origin', 'radar_evidence_artifacts', ['canonical_origin'])

    # Create radar_research_coverage
    op.create_table(
        'radar_research_coverage',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('run_id', sa.String(36), nullable=False),
        sa.Column('evidence_class', sa.String(64), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('evidence_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('SEARCHED_FOUND', 'SEARCHED_NONE_FOUND', 'NOT_SEARCHED', 'BLOCKED')",
            name='ck_radar_research_coverage_status'
        ),
        sa.ForeignKeyConstraint(['run_id'], ['radar_research_runs.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_research_coverage_run_id', 'radar_research_coverage', ['run_id'])
    op.create_index('ix_radar_research_coverage_evidence_class', 'radar_research_coverage', ['evidence_class'])

    # Create radar_source_authorities
    op.create_table(
        'radar_source_authorities',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('host_pattern', sa.String(255), nullable=False),
        sa.Column('authority', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "authority IN ('OFFICIAL_REGULATION', 'OFFICIAL_PROGRAMME', 'OFFICIAL_DEPARTMENT_OR_PERSON', "
            "'AUTHORITATIVE_REGISTRY', 'PRIMARY_RESEARCH_OUTPUT', 'REPUTABLE_SECONDARY', 'DISCOVERY_AGGREGATOR', 'UNKNOWN')",
            name='ck_radar_source_authorities_authority'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('host_pattern', name='uq_radar_source_authorities_host_pattern'),
    )
    op.create_index('ix_radar_source_authorities_host_pattern', 'radar_source_authorities', ['host_pattern'])

    # Create radar_discovery_traces
    op.create_table(
        'radar_discovery_traces',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('target_id', sa.String(36), nullable=False),
        sa.Column('source', sa.String(128), nullable=True),
        sa.Column('query', sa.Text(), nullable=True),
        sa.Column('run_id', sa.String(36), nullable=True),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['target_id'], ['radar_target_entities.id'], ),
        sa.ForeignKeyConstraint(['run_id'], ['radar_research_runs.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_discovery_traces_target_id', 'radar_discovery_traces', ['target_id'])
    op.create_index('ix_radar_discovery_traces_run_id', 'radar_discovery_traces', ['run_id'])
    op.create_index('ix_radar_discovery_traces_at', 'radar_discovery_traces', ['at'])

    # Create radar_evidence_dependencies
    op.create_table(
        'radar_evidence_dependencies',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('upstream_kind', sa.String(64), nullable=False),
        sa.Column('upstream_id', sa.String(36), nullable=False),
        sa.Column('downstream_kind', sa.String(64), nullable=False),
        sa.Column('downstream_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_evidence_dependencies_upstream', 'radar_evidence_dependencies', ['upstream_kind', 'upstream_id'])
    op.create_index('ix_radar_evidence_dependencies_downstream', 'radar_evidence_dependencies', ['downstream_kind', 'downstream_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('radar_evidence_dependencies')
    op.drop_table('radar_discovery_traces')
    op.drop_table('radar_source_authorities')
    op.drop_table('radar_research_coverage')
    op.drop_table('radar_evidence_artifacts')
    op.drop_table('radar_research_runs')
    op.drop_table('radar_source_snapshots')
    op.drop_table('radar_research_protocols')
