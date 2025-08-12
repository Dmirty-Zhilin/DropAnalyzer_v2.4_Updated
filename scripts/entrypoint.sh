#!/bin/bash
set -e

echo "👷 Running db init (waits for DB & runs alembic if available)..."
python /app/dropanalyzer-backend/scripts/db_init.py || { echo "❌ db_init failed"; exit 1; }

if [ "$SERVICE_ROLE" = "web" ]; then
    echo "🌍 Запуск web-сервера..."
    exec gunicorn --bind 0.0.0.0:5000 src.main:app --workers 3
elif [ "$SERVICE_ROLE" = "worker" ]; then
    echo "⚙ Запуск Celery worker..."
    exec celery -A src.celery_app.celery worker --loglevel=info
else
    echo "❌ Unknown SERVICE_ROLE: $SERVICE_ROLE"
    exit 1
fi