# Radar Release-Candidate Runbook

This runbook covers local development and release-candidate deployment of the Mozare Academic Radar using Docker Compose.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.12+ (for local development)
- PostgreSQL 16+ (if using external DB)

### Environment Setup

1. Copy `.env.example` to `.env` and fill in required values:
   ```bash
   cp .env.example .env
   ```

2. Required environment variables:
   - `ASTRA_SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
   - `CORS_ORIGINS`: Set to `http://localhost:3000` for local development
   - `RADAR_FIXTURE_MODE`: Set to `1` to enable fixture-backed testing

## Starting Services

### Docker Compose Stack (Recommended for RC)

All services in one command:

```bash
docker compose up -d --build
```

This starts:
- PostgreSQL (profile: postgres) — optional, omit to use SQLite
- Redis (profile: redis) — required for jobs
- FastAPI backend (8000)
- Radar worker (job processor)
- Next.js dashboard (3000)

Check health:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### Local Development (API only)

```bash
cd astra
python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

### Local Development (Dashboard only)

```bash
cd dashboard
npm run dev
```

## Database Migrations

Migrations run automatically on API startup via Alembic (see `astra/alembic/`).

### Manual migration (if needed):

```bash
cd astra
alembic upgrade head
```

### Testing migration from clean DB:

```bash
DATABASE_URL=sqlite:////tmp/test.db python -m alembic upgrade head
```

## Importing Seed Data

For fixture-mode testing, import the synthetic seed profile:

```bash
curl -X POST http://localhost:8000/api/radar/dev/import-seed \
  -H "Content-Type: application/json" \
  -d '{"seed_path": "astra/tests/academic_radar/fixtures/synthetic_seed.yaml"}'
```

Required: `RADAR_FIXTURE_MODE=1`

## Running the RC Smoke Test

The smoke test verifies end-to-end flow: import, discovery, case research, watch, brief freeze, and durability.

### Local smoke test (no Docker required):

This starts a local API in fixture mode, runs the smoke test, restarts the API, and verifies durability on the same database:

```bash
python scripts/local_smoke.py
```

Success output:
```
LOCAL SMOKE OK (fresh run + restart + durable check)
```

### Without restart (Docker):

```bash
python scripts/rc_smoke.py
```

### With restart verification (Docker):

```bash
# Run initial test
python scripts/rc_smoke.py

# Restart services
docker compose restart

# Verify durable state
python scripts/rc_smoke.py --verify-durable
```

### In CI:

The `compose-smoke` job in `.github/workflows/ci.yml` runs automatically on every push.

## Backup and Restore

### PostgreSQL Dump (before migration or deployment):

```bash
docker compose exec postgres pg_dump -U astra astra > astra_backup.sql
```

### Restore from dump:

```bash
docker compose exec -T postgres psql -U astra astra < astra_backup.sql
```

### SQLite Backup (local dev):

```bash
cp astra/astra.db astra/astra.db.backup
```

## Troubleshooting

### API not starting

Check logs:
```bash
docker compose logs api
docker compose logs radar-worker
```

Verify database connectivity:
```bash
curl http://localhost:8000/ready
```

### Worker not processing jobs

Ensure Redis is healthy:
```bash
docker compose logs redis
redis-cli -u redis://localhost:6379/0 ping
```

Restart worker:
```bash
docker compose restart radar-worker
```

### Dashboard not connecting to API

Verify CORS and API URL:
```bash
curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

Check dashboard logs:
```bash
docker compose logs dashboard
```

### Database lock or corruption

Reset to clean state:
```bash
docker compose down
rm -rf astra_pgdata/  # if using postgres profile
docker compose up -d --build
```

## Monitoring

### Health checks

- API liveness: `GET /health` (no auth)
- API readiness: `GET /ready` (checks DB, LLM config)

### Logs

View all services:
```bash
docker compose logs -f
```

View specific service:
```bash
docker compose logs -f api
docker compose logs -f radar-worker
```

### Metrics (if enabled)

Set `ASTRA_JSON_LOGS=1` for structured JSON logs.

## Stopping Services

```bash
docker compose down
```

This removes all containers but preserves volumes (`astra-pgdata`, `astra-data`).

To also remove volumes:
```bash
docker compose down -v
```

## Production Considerations

- Set `ASTRA_COOKIE_SECURE=1` (default) for HTTPS deployments
- Set `ASTRA_SSRF_GUARD=1` (default) to block internal/private URL access
- Use `API_WORKERS>1` for horizontal scaling (set `ASTRA_SCHEDULER_ENABLED=0` on extra workers)
- Configure external database URL and Redis for multi-node deployments
- Use secrets manager for credentials in production
- See `docs/DEPLOYMENT.md` for full production setup

## Support

- Check `docs/` for architecture and security details
- Run full test suite: `cd astra && python -m pytest tests/academic_radar -q`
- File issues with exact error messages and reproduction steps
