# Radar Migrations and Rollback

## Pre-Migration Backup

Before running any migration on a production PostgreSQL database, create a full backup:

```bash
pg_dump -U <username> -h <hostname> -d <database_name> -F custom > radar_backup_$(date +%Y%m%d_%H%M%S).dump
```

For local development with PostgreSQL:

```bash
pg_dump -U postgres -h localhost radar > radar_backup_local.sql
```

## Migration Procedure

From the `astra/` directory:

```bash
.venv/Scripts/python -m alembic upgrade head
```

This runs all pending migrations in sequence. To upgrade to a specific revision:

```bash
.venv/Scripts/python -m alembic upgrade <revision_id>
```

To verify the current state:

```bash
.venv/Scripts/python -m alembic current
```

## Downgrade and Restore

Downgrade is supported **only** for revisions `r001` through `r005` on empty or testing data. Downgrade destroys all tables; it is intended only for development and testing.

To downgrade one revision:

```bash
.venv/Scripts/python -m alembic downgrade -1
```

To downgrade to a specific revision (e.g., `r003`):

```bash
.venv/Scripts/python -m alembic downgrade r003
```

**Warning:** Downgrade will drop all tables created after the target revision. Do not use on production data except when restoring from backup.

## Restore from Backup

If a migration fails or corrupts data, restore the database from the pre-migration backup:

```bash
pg_restore -U <username> -h <hostname> -d <database_name> --clean --if-exists radar_backup_YYYYMMDD_HHMMSS.dump
```

For local development:

```bash
psql -U postgres -h localhost -d postgres -c "DROP DATABASE IF EXISTS radar;"
psql -U postgres -h localhost -d postgres -c "CREATE DATABASE radar;"
pg_restore -U postgres -h localhost -d radar < radar_backup_local.sql
```

## Migration Revisions

### r001 — Target schema (profiles, routes, targets, identities)

Tables:
- `radar_candidate_profiles`
- `radar_candidate_evidence`
- `radar_mozare_routes`
- `radar_target_entities`
- `radar_person_identities`
- `radar_programmes`
- `radar_opportunities`
- `radar_funding_routes`
- `radar_entity_relations`

### r002 — Cases and application stages

Tables:
- `radar_evaluation_cases`
- `radar_case_disposition_history`
- `radar_application_stage_history`
- `radar_user_notes`

### r003 — Evidence and discovery

Tables:
- `radar_research_protocols`
- `radar_research_runs`
- `radar_research_coverage`
- `radar_evidence_artifacts`
- `radar_source_snapshots`
- `radar_source_authorities`
- `radar_discovery_traces`
- `radar_evidence_dependencies`

### r004 — Claims and assessments

Tables:
- `radar_claims`
- `radar_claim_evidence`
- `radar_gate_assessments`
- `radar_dimension_assessments`
- `radar_funding_assessments`
- `radar_supervision_precedents`

### r005 — Watch, briefs, and change events

Tables:
- `radar_watch_targets`
- `radar_watch_checks`
- `radar_change_events`
- `radar_application_briefs`
- `radar_brief_dependencies`

## Development Workflow

For local SQLite testing, migrations are applied automatically when tests run. To manually test migrations:

```bash
# Create a clean test database
rm -f test_radar.db
export DATABASE_URL="sqlite:///test_radar.db"

# Run migrations
.venv/Scripts/python -m alembic upgrade head

# Verify all tables exist
.venv/Scripts/python -c "from db.models import Base; import db.radar_models_watch; ..."
```

## Verification

After migration, verify the schema is complete:

```bash
# Check migration history
.venv/Scripts/python -m alembic history

# Verify current revision
.venv/Scripts/python -m alembic current

# List all migration heads (should be exactly 1)
.venv/Scripts/python -m alembic heads
```

All migration tests are part of the CI suite and validate:
- Empty DB upgrade to head
- All required tables and columns exist
- CheckConstraints are in place
- ForeignKey relationships are valid
- Indexes are created
- Single migration head
