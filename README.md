# Fleet Dashboard for Vehicles Telemetry

Modern FastAPI + React TypeScript fleet dashboard for vehicles telemetry.

## Stack

- FastAPI backend managed with `uv`
- React TypeScript frontend built with Vite
- PostgreSQL and Redis for local development through Docker Compose
- SQLAlchemy and Alembic for database access and migrations

## Quick Start

Start Postgres and Redis:

```bash
docker compose up -d postgres redis
```

Run migrations and seed local vehicles:

```bash
uv run alembic upgrade head
uv run python -m backend.app.seed_vehicles
```

Start the API:

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173.

## Configuration

Copy the root `.env.example` to `.env` for backend settings.

Copy `frontend/.env.example` to `frontend/.env` for frontend settings.

## API

- `GET /` - API metadata
- `GET /api/health` - application health
- `GET /api/health/db` - PostgreSQL health
- `GET /api/health/redis` - Redis health

## Migrations

Create a migration:

```bash
uv run alembic revision -m "describe change"
```

Run migrations:

```bash
uv run alembic upgrade head
```

## Tests

Run backend tests:

```bash
uv run pytest
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Session History

See [opencode_session_history.md](opencode_session_history.md) for the development session log.
