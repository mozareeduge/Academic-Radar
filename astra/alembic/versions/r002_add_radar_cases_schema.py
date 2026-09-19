"""Add radar cases schema (evaluation cases and history)

Revision ID: r002_add_radar_cases_schema
Revises: r001_add_radar_target_schema
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'r002_add_radar_cases_schema'
down_revision: Union[str, Sequence[str], None] = 'r001_add_radar_target_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create radar_evaluation_cases
    op.create_table(
        'radar_evaluation_cases',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('route_id', sa.String(36), nullable=False),
        sa.Column('target_id', sa.String(36), nullable=False),
        sa.Column('application_route', sa.String(32), nullable=False),
        sa.Column('research_state', sa.String(32), nullable=False),
        sa.Column('user_disposition', sa.String(32), nullable=False),
        sa.Column('suggested_disposition', sa.String(32), nullable=True),
        sa.Column('application_stage', sa.String(32), nullable=False),
        sa.Column('next_action', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "application_route IN ('SUPERVISOR_FIRST_PHD', 'ADVERTISED_PHD', 'STRUCTURED_PHD', 'MA_PROGRAMME')",
            name='ck_radar_evaluation_cases_application_route'
        ),
        sa.CheckConstraint(
            "research_state IN ('DISCOVERED', 'TRIAGED', 'RESEARCHING', 'EVIDENCE_READY', 'STALE', 'FAILED', 'ARCHIVED')",
            name='ck_radar_evaluation_cases_research_state'
        ),
        sa.CheckConstraint(
            "user_disposition IN ('UNDECIDED', 'STRONG', 'WATCH', 'ACT', 'REJECTED')",
            name='ck_radar_evaluation_cases_user_disposition'
        ),
        sa.CheckConstraint(
            "suggested_disposition IS NULL OR suggested_disposition IN ('UNDECIDED', 'STRONG', 'WATCH', 'ACT', 'REJECTED')",
            name='ck_radar_evaluation_cases_suggested_disposition'
        ),
        sa.CheckConstraint(
            "application_stage IN ('NOT_STARTED', 'PREPARING', 'CONTACTED', 'APPLICATION_OPEN', 'APPLIED', 'INTERVIEW', 'OFFER', 'DECLINED', 'CLOSED')",
            name='ck_radar_evaluation_cases_application_stage'
        ),
        sa.ForeignKeyConstraint(['route_id'], ['radar_mozare_routes.id'], ),
        sa.ForeignKeyConstraint(['target_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('route_id', 'target_id', 'application_route', name='uq_radar_evaluation_cases_identity'),
    )
    op.create_index('ix_radar_evaluation_cases_route_id', 'radar_evaluation_cases', ['route_id'])
    op.create_index('ix_radar_evaluation_cases_target_id', 'radar_evaluation_cases', ['target_id'])

    # Create radar_case_disposition_history
    op.create_table(
        'radar_case_disposition_history',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('previous', sa.String(32), nullable=True),
        sa.Column('new', sa.String(32), nullable=False),
        sa.Column('actor', sa.String(32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "previous IS NULL OR previous IN ('UNDECIDED', 'STRONG', 'WATCH', 'ACT', 'REJECTED')",
            name='ck_radar_case_disposition_history_previous'
        ),
        sa.CheckConstraint(
            "new IN ('UNDECIDED', 'STRONG', 'WATCH', 'ACT', 'REJECTED')",
            name='ck_radar_case_disposition_history_new'
        ),
        sa.CheckConstraint(
            "actor IN ('USER', 'SYSTEM_SUGGESTION')",
            name='ck_radar_case_disposition_history_actor'
        ),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_case_disposition_history_case_id', 'radar_case_disposition_history', ['case_id'])

    # Create radar_application_stage_history
    op.create_table(
        'radar_application_stage_history',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('previous', sa.String(32), nullable=True),
        sa.Column('new', sa.String(32), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "previous IS NULL OR previous IN ('NOT_STARTED', 'PREPARING', 'CONTACTED', 'APPLICATION_OPEN', 'APPLIED', 'INTERVIEW', 'OFFER', 'DECLINED', 'CLOSED')",
            name='ck_radar_application_stage_history_previous'
        ),
        sa.CheckConstraint(
            "new IN ('NOT_STARTED', 'PREPARING', 'CONTACTED', 'APPLICATION_OPEN', 'APPLIED', 'INTERVIEW', 'OFFER', 'DECLINED', 'CLOSED')",
            name='ck_radar_application_stage_history_new'
        ),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_application_stage_history_case_id', 'radar_application_stage_history', ['case_id'])

    # Create radar_user_notes
    op.create_table(
        'radar_user_notes',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['radar_evaluation_cases.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_user_notes_case_id', 'radar_user_notes', ['case_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('radar_user_notes')
    op.drop_table('radar_application_stage_history')
    op.drop_table('radar_case_disposition_history')
    op.drop_table('radar_evaluation_cases')
