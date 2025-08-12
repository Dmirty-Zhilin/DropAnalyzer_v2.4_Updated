import os
import json
from src.celery_app import celery
from src.models.domain import db, Domain, Report
from domain_analyzer import analyze_domain_sync
from sqlalchemy.exc import IntegrityError
from flask import Flask

@celery.task(bind=True, acks_late=True)
def analyze_domain_task(self, domain_name):
    """Background task: analyze a domain and store report in DB."""
    try:
        # Выполняем синхронный анализ
        result = analyze_domain_sync(domain_name)

        # Отбираем сериализуемые метрики
        metrics = {
            k: v
            for k, v in result.items()
            if k not in ('category', 'quality', 'recommended', 'is_good', 'analysis_time_sec')
        }

        # Создаём временное Flask-приложение, чтобы инициализировать SQLAlchemy
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            os.environ.get('DATABASE_URL')
            or os.environ.get('SQLALCHEMY_DATABASE_URI')
            or 'sqlite:///data/app.db'
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

        with app.app_context():
            d = Domain.query.filter_by(name=domain_name).first()
            if not d:
                d = Domain(name=domain_name, long_live=(domain_name in set()))
                db.session.add(d)
                db.session.commit()

            r = Report(
                domain_id=d.id,
                metrics=metrics,
                quality_score=int(result.get('quality_score', 0)),
                category=result.get('category')
            )
            db.session.add(r)
            db.session.commit()

        return {'status': 'ok', 'domain': domain_name, 'score': result.get('quality_score')}

    except Exception as e:
        raise self.retry(exc=e, countdown=30, max_retries=3)