"""Add radar watch, change events, and application briefs schema

Revision ID: r005_add_radar_watch_schema
Revises: r004_add_radar_claims_schema
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'r005_add_radar_watch_schema'
down_revision: Union[str, Sequence[str], None] = 'r004_add_radar_claims_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create radar_watch_targets
    op.create_table(
        'radar_watch_targets',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('target_id', sa.String(36), nullable=False),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('cadence', sa.String(64), nullable=False),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('ACTIVE', 'PAUSED', 'ERROR', 'RETIRED')", name='ck_radar_watch_targets_state'),
        sa.ForeignKeyConstraint(['target_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_radar_watch_targets_state', 'radar_watch_targets', ['state'], unique=False)
    op.create_index('ix_radar_watch_targets_target_id', 'radar_watch_targets', ['target_id'], unique=False)

    # Create radar_watch_checks
    op.create_table(
        'radar_watch_checks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('watch_target_id', sa.String(36), nullable=False),
        sa.Column('snapshot_id', sa.String(36), nullable=False),
        sa.Column('changed', sa.Boolean(), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['watch_target_id'], ['radar_watch_targets.id'], ),
        sa.ForeignKeyConstraint(['snapshot_id'], ['radar_source_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_radar_watch_checks_watch_target_id', 'radar_watch_checks', ['watch_target_id'], unique=False)
    op.create_index('ix_radar_watch_checks_snapshot_id', 'radar_watch_checks', ['snapshot_id'], unique=False)
    op.create_index('ix_radar_watch_checks_watch_target_at', 'radar_watch_checks', ['watch_target_id', 'at'], unique=False)
    op.create_index('ix_radar_watch_checks_at', 'radar_watch_checks', ['at'], unique=False)

    # Create radar_change_events
    op.create_table(
        'radar_change_events',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('watch_check_id', sa.String(36), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('material', sa.Boolean(), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['watch_check_id'], ['radar_watch_checks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_radar_change_events_watch_check_id', 'radar_change_events', ['watch_check_id'], unique=False)
    op.create_index('ix_radar_change_events_material_at', 'radar_change_events', ['material', 'at'], unique=False)
    op.create_index('ix_radar_change_events_at', 'radar_change_events', ['at'], unique=False)

    # Create radar_application_briefs
    op.create_table(
        'radar_application_briefs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('frozen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('content', sa.JSON(), nullable=True),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('superseded_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('DRAFT', 'REVIEWED', 'SUPERSEDED')", name='ck_radar_application_briefs_state'),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.ForeignKeyConstraint(['superseded_by'], ['radar_application_briefs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_radar_application_briefs_case_id', 'radar_application_briefs', ['case_id'], unique=False)
    op.create_index('ix_radar_application_briefs_state', 'radar_application_briefs', ['state'], unique=False)
    op.create_index('ix_radar_application_briefs_case_state', 'radar_application_briefs', ['case_id', 'state'], unique=False)
    op.create_index('ix_radar_application_briefs_superseded_by', 'radar_application_briefs', ['superseded_by'], unique=False)

    # Create radar_brief_dependencies
    op.create_table(
        'radar_brief_dependencies',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('brief_id', sa.String(36), nullable=False),
        sa.Column('dependency_kind', sa.String(64), nullable=False),
        sa.Column('dependency_id', sa.String(36), nullable=False),
        sa.Column('dependency_version', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['brief_id'], ['radar_application_briefs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_radar_brief_dependencies_brief_id', 'radar_brief_dependencies', ['brief_id'], unique=False)
    op.create_index('ix_radar_brief_dependencies_dependency_id', 'radar_brief_dependencies', ['dependency_id'], unique=False)
    op.create_index('ix_radar_brief_dependencies_brief_kind', 'radar_brief_dependencies', ['brief_id', 'dependency_kind'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('radar_brief_dependencies')
    op.drop_table('radar_application_briefs')
    op.drop_table('radar_change_events')
    op.drop_table('radar_watch_checks')
    op.drop_table('radar_watch_targets')
