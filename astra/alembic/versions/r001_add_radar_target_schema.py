"""Add radar target schema (profiles, routes, targets, identities)

Revision ID: r001_add_radar_target_schema
Revises: d9c4b1a7e230
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'r001_add_radar_target_schema'
down_revision: Union[str, Sequence[str], None] = 'd9c4b1a7e230'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create radar_candidate_profiles
    op.create_table(
        'radar_candidate_profiles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('fixed_constraints', sa.Text(), nullable=True),
        sa.Column('education', sa.JSON(), nullable=True),
        sa.Column('language_evidence', sa.JSON(), nullable=True),
        sa.Column('scholarly_work', sa.JSON(), nullable=True),
        sa.Column('artistic_curatorial_work', sa.JSON(), nullable=True),
        sa.Column('professional_technical_evidence', sa.JSON(), nullable=True),
        sa.Column('verification_status', sa.Text(), nullable=True),
        sa.Column('documents', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('ACTIVE', 'NEEDS_VERIFICATION', 'SUPERSEDED')", name='ck_radar_candidate_profiles_state'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_candidate_profiles_id', 'radar_candidate_profiles', ['id'])

    # Create radar_candidate_evidence
    op.create_table(
        'radar_candidate_evidence',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('candidate_profile_id', sa.String(36), nullable=False),
        sa.Column('evidence_type', sa.String(64), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('content', sa.JSON(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['candidate_profile_id'], ['radar_candidate_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_candidate_evidence_candidate_profile_id', 'radar_candidate_evidence', ['candidate_profile_id'])

    # Create radar_mozare_routes
    op.create_table(
        'radar_mozare_routes',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('state', sa.String(32), nullable=False),
        sa.Column('route_statement', sa.Text(), nullable=True),
        sa.Column('core_problem', sa.Text(), nullable=True),
        sa.Column('operations_methods', sa.JSON(), nullable=True),
        sa.Column('relevant_corpora_material', sa.JSON(), nullable=True),
        sa.Column('supporting_evidence', sa.JSON(), nullable=True),
        sa.Column('target_disciplines', sa.JSON(), nullable=True),
        sa.Column('prohibited_overclaims', sa.JSON(), nullable=True),
        sa.Column('maturity', sa.String(32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('ACTIVE', 'EXPLORATORY', 'DORMANT', 'RETIRED')", name='ck_radar_mozare_routes_state'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_mozare_routes_name', 'radar_mozare_routes', ['name'])

    # Create radar_target_entities
    op.create_table(
        'radar_target_entities',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('kind', sa.String(32), nullable=False),
        sa.Column('display_name', sa.String(512), nullable=False),
        sa.Column('canonical_url', sa.Text(), nullable=True),
        sa.Column('doi', sa.String(256), nullable=True),
        sa.Column('orcid', sa.String(64), nullable=True),
        sa.Column('openalex_id', sa.String(256), nullable=True),
        sa.Column('openaire_id', sa.String(256), nullable=True),
        sa.Column('ror', sa.String(64), nullable=True),
        sa.Column('attributes', sa.JSON(), nullable=True),
        sa.Column('source_authority', sa.String(32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('Person', 'Programme', 'PhDOpportunity', 'FundedProject', 'Institution', 'FundingRoute', 'SupervisedProject', 'Work')",
            name='ck_radar_target_entities_kind'
        ),
        sa.CheckConstraint(
            "source_authority IN ('OFFICIAL_REGULATION', 'OFFICIAL_PROGRAMME', 'OFFICIAL_DEPARTMENT_OR_PERSON', 'AUTHORITATIVE_REGISTRY', 'PRIMARY_RESEARCH_OUTPUT', 'REPUTABLE_SECONDARY', 'DISCOVERY_AGGREGATOR', 'UNKNOWN')",
            name='ck_radar_target_entities_source_authority'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('orcid', name='uq_radar_target_entities_orcid'),
    )
    op.create_index('ix_radar_target_entities_kind', 'radar_target_entities', ['kind'])
    op.create_index('ix_radar_target_entities_display_name', 'radar_target_entities', ['display_name'])
    op.create_index('ix_radar_target_entities_canonical_url', 'radar_target_entities', ['canonical_url'])
    op.create_index('ix_radar_target_entities_doi', 'radar_target_entities', ['doi'])
    op.create_index('ix_radar_target_entities_orcid', 'radar_target_entities', ['orcid'])
    op.create_index('ix_radar_target_entities_openalex_id', 'radar_target_entities', ['openalex_id'])
    op.create_index('ix_radar_target_entities_openaire_id', 'radar_target_entities', ['openaire_id'])
    op.create_index('ix_radar_target_entities_ror', 'radar_target_entities', ['ror'])

    # Create radar_person_identities
    op.create_table(
        'radar_person_identities',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('target_entity_id', sa.String(36), nullable=False),
        sa.Column('identity_status', sa.String(32), nullable=False),
        sa.Column('resolution_basis', sa.Text(), nullable=True),
        sa.Column('candidate_set', sa.JSON(), nullable=True),
        sa.Column('institution_target_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "identity_status IN ('RESOLVED', 'UNRESOLVED', 'CANDIDATE')",
            name='ck_radar_person_identities_status'
        ),
        sa.ForeignKeyConstraint(['target_entity_id'], ['radar_target_entities.id'], ),
        sa.ForeignKeyConstraint(['institution_target_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_person_identities_target_entity_id', 'radar_person_identities', ['target_entity_id'])
    op.create_index('ix_radar_person_identities_institution_target_id', 'radar_person_identities', ['institution_target_id'])

    # Create radar_programmes
    op.create_table(
        'radar_programmes',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('target_entity_id', sa.String(36), nullable=False),
        sa.Column('display_name', sa.String(512), nullable=False),
        sa.Column('level', sa.String(64), nullable=True),
        sa.Column('duration_months', sa.Integer(), nullable=True),
        sa.Column('languages', sa.JSON(), nullable=True),
        sa.Column('admission_gates', sa.JSON(), nullable=True),
        sa.Column('contact_details', sa.JSON(), nullable=True),
        sa.Column('deadline_original_text', sa.Text(), nullable=True),
        sa.Column('deadline_date', sa.Date(), nullable=True),
        sa.Column('deadline_local_time', sa.Time(), nullable=True),
        sa.Column('deadline_timezone', sa.String(64), nullable=True),
        sa.Column('deadline_utc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deadline_precision', sa.String(32), nullable=True),
        sa.Column('deadline_evidence_id', sa.String(36), nullable=True),
        sa.Column('deadline_last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "deadline_precision IN ('DATE_ONLY', 'LOCAL_TIME', 'OFFSET_AWARE', 'AMBIGUOUS')",
            name='ck_radar_programmes_deadline_precision'
        ),
        sa.ForeignKeyConstraint(['target_entity_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_programmes_target_entity_id', 'radar_programmes', ['target_entity_id'])

    # Create radar_opportunities
    op.create_table(
        'radar_opportunities',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('target_entity_id', sa.String(36), nullable=False),
        sa.Column('display_name', sa.String(512), nullable=False),
        sa.Column('application_route', sa.String(32), nullable=False),
        sa.Column('project_description', sa.Text(), nullable=True),
        sa.Column('supervisor_info', sa.JSON(), nullable=True),
        sa.Column('funding_status', sa.String(64), nullable=True),
        sa.Column('estimated_stipend', sa.String(64), nullable=True),
        sa.Column('deadline_original_text', sa.Text(), nullable=True),
        sa.Column('deadline_date', sa.Date(), nullable=True),
        sa.Column('deadline_local_time', sa.Time(), nullable=True),
        sa.Column('deadline_timezone', sa.String(64), nullable=True),
        sa.Column('deadline_utc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deadline_precision', sa.String(32), nullable=True),
        sa.Column('deadline_evidence_id', sa.String(36), nullable=True),
        sa.Column('deadline_last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "application_route IN ('SUPERVISOR_FIRST_PHD', 'ADVERTISED_PHD', 'STRUCTURED_PHD', 'MA_PROGRAMME')",
            name='ck_radar_opportunities_application_route'
        ),
        sa.CheckConstraint(
            "deadline_precision IN ('DATE_ONLY', 'LOCAL_TIME', 'OFFSET_AWARE', 'AMBIGUOUS')",
            name='ck_radar_opportunities_deadline_precision'
        ),
        sa.ForeignKeyConstraint(['target_entity_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_opportunities_target_entity_id', 'radar_opportunities', ['target_entity_id'])

    # Create radar_funding_routes
    op.create_table(
        'radar_funding_routes',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('target_entity_id', sa.String(36), nullable=False),
        sa.Column('display_name', sa.String(512), nullable=False),
        sa.Column('funder', sa.String(256), nullable=True),
        sa.Column('award_amount', sa.String(64), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('eligibility_criteria', sa.JSON(), nullable=True),
        sa.Column('nomination_process', sa.Text(), nullable=True),
        sa.Column('deadline_original_text', sa.Text(), nullable=True),
        sa.Column('deadline_date', sa.Date(), nullable=True),
        sa.Column('deadline_local_time', sa.Time(), nullable=True),
        sa.Column('deadline_timezone', sa.String(64), nullable=True),
        sa.Column('deadline_utc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deadline_precision', sa.String(32), nullable=True),
        sa.Column('deadline_evidence_id', sa.String(36), nullable=True),
        sa.Column('deadline_last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "deadline_precision IN ('DATE_ONLY', 'LOCAL_TIME', 'OFFSET_AWARE', 'AMBIGUOUS')",
            name='ck_radar_funding_routes_deadline_precision'
        ),
        sa.ForeignKeyConstraint(['target_entity_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_funding_routes_target_entity_id', 'radar_funding_routes', ['target_entity_id'])

    # Create radar_entity_relations
    op.create_table(
        'radar_entity_relations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('subject_id', sa.String(36), nullable=False),
        sa.Column('predicate', sa.String(256), nullable=False),
        sa.Column('object_id', sa.String(36), nullable=False),
        sa.Column('evidence_ids', sa.JSON(), nullable=True),
        sa.Column('identity_resolved', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['radar_target_entities.id'], ),
        sa.ForeignKeyConstraint(['object_id'], ['radar_target_entities.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_radar_entity_relations_subject_id', 'radar_entity_relations', ['subject_id'])
    op.create_index('ix_radar_entity_relations_object_id', 'radar_entity_relations', ['object_id'])
    op.create_index('ix_radar_entity_relations_predicate', 'radar_entity_relations', ['predicate'])
    op.create_index('ix_radar_entity_relations_subject_predicate', 'radar_entity_relations', ['subject_id', 'predicate'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('radar_entity_relations')
    op.drop_table('radar_funding_routes')
    op.drop_table('radar_opportunities')
    op.drop_table('radar_programmes')
    op.drop_table('radar_person_identities')
    op.drop_table('radar_target_entities')
    op.drop_table('radar_mozare_routes')
    op.drop_table('radar_candidate_evidence')
    op.drop_table('radar_candidate_profiles')
