#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from passlib.hash import bcrypt

# Загружаем переменные окружения
load_dotenv()

# --- Пути ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

ALEMBIC_INI = os.path.join(BASE_DIR, "alembic.ini")

# --- Импорты ---
from src.extensions import db  # общий db
from src.models.user import User
from src.models.domain import Domain, Report

# --- Конфигурация ---
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Keyadmin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
DB_WAIT_RETRIES = int(os.environ.get("DB_WAIT_RETRIES", 30))
DB_WAIT_DELAY = float(os.environ.get("DB_WAIT_DELAY", 3.0))


def wait_for_db(uri, retries=DB_WAIT_RETRIES, delay=DB_WAIT_DELAY):
    """Ждём, пока БД станет доступна."""
    engine = create_engine(uri)
    for i in range(1, retries + 1):
        try:
            print(f"[db_init] Попытка подключения к БД ({i}/{retries})...")
            conn = engine.connect()
            conn.close()
            print("[db_init] Подключение к БД успешно.")
            return True
        except OperationalError as e:
            print(f"[db_init] БД недоступна: {e}. Ждём {delay} сек.")
            time.sleep(delay)
    return False


def run_alembic():
    """Запускаем миграции Alembic, если есть alembic.ini."""
    if not os.path.exists(ALEMBIC_INI):
        print(f"[db_init] alembic.ini не найден ({ALEMBIC_INI}). Пропускаем миграции.")
        return
    try:
        subprocess.run(["alembic", "-c", ALEMBIC_INI, "upgrade", "head"], check=True)
        print("[db_init] Alembic миграции применены.")
    except subprocess.CalledProcessError as e:
        print(f"[db_init] Alembic вернул ошибку: {e}")


def create_flask_app(uri):
    """Создаём Flask-приложение и подключаем db."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)  # используем общий db
    return app


def create_admin_and_seed(app):
    """Создаём администратора и тестовые данные."""
    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(username=ADMIN_USERNAME).first()
        if not admin:
            print(f"[db_init] Создаём админа '{ADMIN_USERNAME}'...")
            hashed = bcrypt.hash(ADMIN_PASSWORD)
            admin = User(username=ADMIN_USERNAME, password=hashed)
            db.session.add(admin)
            db.session.commit()
        else:
            print(f"[db_init] Админ '{ADMIN_USERNAME}' уже существует.")

        if not Domain.query.first():
            domain = Domain(name="example.com", long_live=True)
            db.session.add(domain)
            db.session.flush()
            report = Report(
                domain_id=domain.id,
                metrics={"seed": True},
                quality_score=90,
                category="Recommended"
            )
            db.session.add(report)
            db.session.commit()
            print("[db_init] Тестовые данные добавлены.")
        else:
            print("[db_init] Домены уже есть — пропускаем seed.")


def main():
    print("[db_init] Старт инициализации БД")

    if not DATABASE_URL:
        print("[db_init] DATABASE_URL не задан!")
        sys.exit(1)

    if not wait_for_db(DATABASE_URL):
        sys.exit(1)

    run_alembic()

    app = create_flask_app(DATABASE_URL)
    create_admin_and_seed(app)

    print("[db_init] Инициализация завершена.")


if __name__ == "__main__":
    main()