# dropanalyzer-backend/src/main.py
import os
import sys
import datetime
import jwt
from functools import wraps

# Поддержка .env
from dotenv import load_dotenv
load_dotenv()

# Настим путь к корню проекта, чтобы импорты из src и корня работали
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

# Создаём Flask-приложение (static_folder — на тот случай, если frontend лежит в src/static)
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))

# Загружаем и проверяем SECRET_KEY (обязательное требование)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.getenv('SECRET_KEY')
if not app.config.get('SECRET_KEY'):
    # критически — завершаем запуск; в проде ключ должен быть задан через .env/secret manager
    print("FATAL: SECRET_KEY is not set. Set SECRET_KEY in your .env before starting.", file=sys.stderr)
    sys.exit(1)

# CORS: читаем список через запятую, если пусто — разрешаем ничего (пустой список)
cors_origins_raw = os.environ.get('CORS_ORIGINS', '').strip()
if cors_origins_raw:
    cors_origins = [o.strip() for o in cors_origins_raw.split(',') if o.strip()]
else:
    cors_origins = []
CORS(app, origins=cors_origins or None)

# --- Импорт моделей, blueprints и т.д. после создания app и настройки sys.path ---
from src.models.user import db
from src.routes.user import user_bp

# Регистрируем blueprint'ы
app.register_blueprint(user_bp, url_prefix='/api')

# Настройка SQLAlchemy: читать из окружения DATABASE_URL или SQLALCHEMY_DATABASE_URI,
# иначе использовать локальный sqlite (dev fallback)
db_url = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL") or ("postgresql://%s:%s@db:5432/%s" % (os.environ.get("POSTGRES_USER"), os.environ.get("POSTGRES_PASSWORD"), os.environ.get("POSTGRES_DB")))
if not db_url:
    # default dev sqlite (file inside src/database/app.db)
    db_file = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
    db_url = f"sqlite:///{db_file}"

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация БД
db.init_app(app)
with app.app_context():
    db.create_all()

# Импорт аналитики и задач Celery
from domain_analyzer import analyze_domain_sync, analyze_domains_batch_sync, LONG_LIVE_DOMAINS
from src.tasks.analyze_tasks import analyze_domain_task
from src.celery_app import celery as celery_app
from celery.result import AsyncResult

# ------ Аутентификация / декоратор токена ------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token_header = request.headers.get('Authorization')
        if not token_header:
            return jsonify({'message': 'Token is missing!'}), 401
        token = token_header
        if token.startswith('Bearer '):
            token = token[7:]
        try:
            # декодируем jwt
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            # можно поместить payload в g если нужно
        except Exception:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

# ------ Login endpoint ------
@app.route('/api/v1/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'username and password required'}), 400

    from src.models.user import User
    from passlib.hash import bcrypt

    def verify_password(raw, stored):
        # поддержка plaintext (legacy) и bcrypt
        try:
            return bcrypt.verify(raw, stored)
        except Exception:
            return raw == stored

    user = User.query.filter_by(username=username).first()
    if user and verify_password(password, user.password):
        token = jwt.encode({
            'user': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        # pyjwt может возвращать bytes на старых версиях
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return jsonify({'access_token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

# ------ Dashboard / reports for long-live domains ------
@app.route('/api/v1/dashboard', methods=['GET'])
@token_required
def dashboard():
    total_long_live = len(LONG_LIVE_DOMAINS)
    return jsonify({
        'total_domains': total_long_live,
        'domains_with_snapshots': total_long_live,
        'good_domains': total_long_live,
        'recommended_domains': total_long_live,
        'recently_active': total_long_live
    })

@app.route('/api/v1/reports', methods=['GET'])
@token_required
def reports():
    reports_data = []
    for domain in LONG_LIVE_DOMAINS:
        reports_data.append({
            'domain': domain,
            'quality_score': 100,
            'category': 'Recommended',
            'total_snapshots': 'N/A',
            'years_covered': 'N/A',
            'has_snapshots': True,
            'is_good': True,
            'recommended': True,
            'last_analyzed': datetime.datetime.utcnow().isoformat()
        })
    return jsonify({'data': reports_data})

# ------ Analyze single domain (enqueue) ------
@app.route('/api/v1/analyze_domain', methods=['POST'])
@token_required
def analyze_domain():
    data = request.get_json() or {}
    domain = data.get('domain')
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    try:
        task = analyze_domain_task.delay(domain)
        return jsonify({'task_id': task.id, 'status': 'queued'}), 202
    except Exception as e:
        return jsonify({
            'domain': domain,
            'error': str(e),
            'quality_score': 0,
            'category': 'Error',
            'total_snapshots': 0,
            'years_covered': 0,
            'has_snapshots': False,
            'is_good': False,
            'recommended': False,
            'message': f'Error analyzing domain: {str(e)}'
        }), 500

# ------ Batch analyze (sync fallback) ------
@app.route('/api/v1/batch_analyze', methods=['POST'])
@token_required
def batch_analyze():
    data = request.get_json() or {}
    domains = data.get('domains', [])
    if not domains:
        return jsonify({'error': 'Domains list is required'}), 400
    try:
        results = analyze_domains_batch_sync(domains)
        return jsonify({'data': results})
    except Exception as e:
        return jsonify({'error': f'Batch analysis failed: {str(e)}'}), 500

# ------ Static file serving (SPA fallback) ------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# ------ Task status and report endpoints ------
@app.route('/api/v1/task_status/<task_id>', methods=['GET'])
@token_required
def task_status(task_id):
    try:
        res = AsyncResult(task_id, app=celery_app)
        payload = {'task_id': task_id, 'state': res.state}
        if res.ready():
            try:
                payload['result'] = res.result
            except Exception:
                payload['result'] = str(res.result)
        return jsonify(payload)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/report/<domain>', methods=['GET'])
@token_required
def get_latest_report(domain):
    try:
        from src.models.domain import Domain, Report
        d = Domain.query.filter_by(name=domain).first()
        if not d:
            return jsonify({'error': 'Domain not found'}), 404
        r = Report.query.filter_by(domain_id=d.id).order_by(Report.created_at.desc()).first()
        if not r:
            return jsonify({'error': 'No report found for domain'}), 404
        return jsonify({
            'domain': d.name,
            'long_live': d.long_live,
            'report': {
                'quality_score': r.quality_score,
                'category': r.category,
                'metrics': r.metrics,
                'created_at': r.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Запуск приложения (локально)
if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host=host, port=port, debug=debug)