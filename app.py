from __future__ import annotations
from datetime import timedelta
from pathlib import Path
from flask import Flask, jsonify, request, session, send_from_directory
from config import Config
from extensions import db, migrate, limiter, cors
from security import csrf_token, verify_csrf, current_user


def create_app(config_object=Config):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_object)
    app.permanent_session_lifetime = timedelta(days=14)

    Path(app.root_path, app.config['LOCAL_UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    if app.config.get('RATE_LIMIT_ENABLED'):
        limiter.init_app(app)
    cors.init_app(app, origins=app.config['ALLOWED_ORIGINS'], supports_credentials=True)

    register_blueprints(app)
    register_hooks(app)
    register_commands(app)
    return app


def register_blueprints(app: Flask):
    from routes.pages import pages_bp
    from routes.auth import auth_bp
    from routes.rooms import rooms_bp
    from routes.social import social_bp
    from routes.admin import admin_bp
    from routes.verification import verification_bp
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(rooms_bp, url_prefix='/api/rooms')
    app.register_blueprint(social_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(verification_bp, url_prefix='/api/verify')


def register_hooks(app: Flask):
    @app.before_request
    def guard_csrf_and_https():
        if request.path.startswith('/api/') and not verify_csrf():
            return jsonify({'ok': False, 'error': 'Bad CSRF token'}), 400

    @app.after_request
    def security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        if app.config['APP_ENV'] == 'production':
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        return response

    @app.context_processor
    def inject_globals():
        user = current_user()
        return {
            'csrf_token': csrf_token,
            'current_user': user,
            'app_name': app.config['APP_NAME'],
        }

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(Path(app.root_path) / app.config['LOCAL_UPLOAD_FOLDER'], filename)

    @app.get('/api/health')
    def health():
        return jsonify({'ok': True, 'app': app.config['APP_NAME'], 'env': app.config['APP_ENV']})


def register_commands(app: Flask):
    @app.cli.command('init-db')
    def init_db():
        from models import User
        db.create_all()
        print('Database tables created.')

    @app.cli.command('seed-db')
    def seed_db():
        from seed import seed_database
        seed_database(app)
        print('Database seeded.')

    @app.cli.command('reset-db')
    def reset_db():
        db.drop_all()
        db.create_all()
        from seed import seed_database
        seed_database(app)
        print('Database reset and seeded.')


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
