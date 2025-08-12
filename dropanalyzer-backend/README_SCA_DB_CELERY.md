
DropAnalyzer — security & infra upgrades (auto-generated)
Generated: 2025-08-10T08:40:06.670146

Included changes:
- SAST/SCA CI workflow (.github/workflows/sast.yml) runs bandit/semgrep/safety.
- Dependabot configured to check pip dependencies weekly.
- Alembic scaffolding in dropanalyzer-backend/alembic/ with initial migration 0001_create_tables.py.
- SQLAlchemy models for Domain and Report in src/models/domain.py.
- DB init script: scripts/db_init.py (reads long_live_domains.txt and seeds it).
- Celery scaffolding: src/celery_app.py and a sample background task src/tasks/analyze_tasks.py.
- Docker Compose template to bring up Postgres and Redis for development (docker-compose.yml).
- Helper scripts to run bandit/semgrep/safety locally in scripts/

How to use (dev):
1. Create a python venv and install requirements: pip install -r dropanalyzer-backend/requirements.txt
2. Start Postgres and Redis (docker-compose up -d)
3. Set environment variables:
   - SQLALCHEMY_DATABASE_URI or DATABASE_URL (e.g. postgresql://postgres:postgres@localhost:5432/dropanalyzer)
   - SECRET_KEY (required)
   - CELERY_BROKER_URL (redis://localhost:6379/0)
4. Run alembic migrations (example):
   - pip install alembic
   - cd dropanalyzer-backend
   - alembic -c alembic/env.py upgrade head
   (or use scripts/db_init.py for sqlite during dev)
5. Seed long-live domains: python scripts/db_init.py
6. Start web and worker (example):
   - celery -A src.celery_app.celery worker --loglevel=info
   - python -m src.main

Notes:
- The scaffolding provided needs to be adjusted to your infra and tested before production deployment.
- I cannot run scans or migrations in this environment; the repository contains config + scripts so you can run SAST/SCA and DB migrations in CI or locally.
