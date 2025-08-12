
# DropAnalyzer — Installation Guide

This document explains how to deploy DropAnalyzer on a server using Docker (recommended) and directly on Ubuntu 22.04 (systemd).

## Prerequisites
- A server with at least 2 CPU cores, 4GB RAM (for small setups).
- Domain name pointing to server (if you want public access).
- Docker & docker-compose (for Docker deployment) OR Python 3.11 and system packages (for manual deployment).
- PostgreSQL and Redis for production use. SQLite can be used for local testing only.

---
## A. Docker-based deployment (recommended)

1. Clone repository to server:
```
git clone <your-repo-url> dropanalyzer
cd dropanalyzer
```
2. Create `.env` file in repo root with values:
```
SECRET_KEY=supersecretreplace
SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@db:5432/dropanalyzer
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```
3. Build and start services:
```
docker compose build
docker compose up -d
```
This will start Postgres, Redis, the web service and a worker.

4. Apply migrations (inside web container or locally):
```
docker compose exec web bash
# inside container:
alembic -c dropanalyzer-backend/alembic/env.py upgrade head
# or run: python scripts/db_init.py (for sqlite or quick seed)
```

5. Seed long-live domains (inside container or locally):
```
python scripts/db_init.py
```

6. Access the app:
- Web API: `http://<server-ip-or-domain>:5000`
- Enqueue analysis: `POST /api/v1/analyze_domain` with JSON `{"domain":"example.com"}` and header `Authorization: Bearer <token>`.

---
## B. Manual deployment on Ubuntu 22.04 (systemd)

1. Install system deps:
```
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip build-essential libpq-dev
```
2. Create a user and app directory:
```
sudo useradd -m -s /bin/bash dropuser
sudo mkdir -p /opt/dropanalyzer && sudo chown dropuser:dropuser /opt/dropanalyzer
sudo -u dropuser bash
cd /opt/dropanalyzer
git clone <your-repo-url> .
python3.11 -m venv venv
source venv/bin/activate
pip install -r dropanalyzer-backend/requirements.txt
```
3. Configure environment variables (example use systemd env file `/etc/sysconfig/dropanalyzer`):
```
SECRET_KEY=replace_with_secure_key
SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/dropanalyzer
CELERY_BROKER_URL=redis://localhost:6379/0
```
4. Set up PostgreSQL and Redis (install and create DB/user). Example for Postgres:
```
sudo apt install -y postgresql redis-server
sudo -u postgres psql -c "CREATE DATABASE dropanalyzer; CREATE USER dropuser WITH PASSWORD 'password'; GRANT ALL PRIVILEGES ON DATABASE dropanalyzer TO dropuser;"
```
5. Apply migrations:
```
cd dropanalyzer-backend
alembic -c alembic/env.py upgrade head
# or python ../scripts/db_init.py for sqlite testing
```
6. Start services:
- Start web with gunicorn (example):
```
source venv/bin/activate
cd dropanalyzer-backend
gunicorn --bind 0.0.0.0:5000 src.main:app --workers 3
```
- Start worker (in separate terminal / systemd unit):
```
celery -A src.celery_app.celery worker --loglevel=info
```
You may create systemd unit files for web and worker for autorun.

---
## Notes & Security
- Always set `SECRET_KEY` via environment/secret manager.
- Use TLS/HTTPS (nginx reverse proxy + TLS certbot) for production.
- Run SAST/SCA in CI (provided GitHub Actions workflow).
