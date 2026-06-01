import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


def _bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {'1', 'true', 'yes', 'on'}


def _csv(name: str, default: str = '') -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(',') if x.strip()]


class Config:
    APP_NAME = os.getenv('APP_NAME', 'Roomies')
    APP_ENV = os.getenv('APP_ENV', 'development')
    DEBUG = _bool('DEBUG', APP_ENV != 'production')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-me')
    JWT_LIKE_TOKEN_SALT = os.getenv('JWT_LIKE_TOKEN_SALT', 'dev-salt')
    APP_BASE_URL = os.getenv('APP_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
    ALLOWED_ORIGINS = _csv('ALLOWED_ORIGINS', APP_BASE_URL)

    @staticmethod
    def _database_uri() -> str:
        """Return a SQLAlchemy database URI that works well on Windows and Neon.

        Neon commonly gives URLs like:
            postgresql://user:pass@host/db?sslmode=require

        SQLAlchemy uses the installed driver. This project uses psycopg v3
        because it installs cleanly on modern Windows/Python versions.
        Therefore plain postgresql:// and postgres:// URLs are normalized to
        postgresql+psycopg:// automatically.
        """
        url = os.getenv('DATABASE_URL', 'sqlite:///roomies_dev.sqlite').strip()
        if url.startswith('postgres://'):
            return 'postgresql+psycopg://' + url[len('postgres://'):]
        if url.startswith('postgresql://'):
            return 'postgresql+psycopg://' + url[len('postgresql://'):]
        return url

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = _bool('SQLALCHEMY_ECHO')
    DIRECT_DATABASE_URL = os.getenv('DIRECT_DATABASE_URL', '')

    EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'brevo')
    EMAIL_VERIFICATION_ENABLED = _bool('EMAIL_VERIFICATION_ENABLED')
    BREVO_SMTP_HOST = os.getenv('BREVO_SMTP_HOST', 'smtp-relay.brevo.com')
    BREVO_SMTP_PORT = int(os.getenv('BREVO_SMTP_PORT', '587'))
    BREVO_SMTP_USER = os.getenv('BREVO_SMTP_USER', '')
    BREVO_SMTP_PASSWORD = os.getenv('BREVO_SMTP_PASSWORD', '')
    MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME', 'Roomies')
    MAIL_FROM_EMAIL = os.getenv('MAIL_FROM_EMAIL', 'no-reply@example.com')
    SMTP_USE_TLS = _bool('SMTP_USE_TLS', True)
    SMTP_USE_SSL = _bool('SMTP_USE_SSL')

    PHONE_VERIFICATION_ENABLED = _bool('PHONE_VERIFICATION_ENABLED')
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID', '')
    TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '')

    STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 'local')
    LOCAL_UPLOAD_FOLDER = os.getenv('LOCAL_UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH_MB = int(os.getenv('MAX_CONTENT_LENGTH_MB', '8'))
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_MB * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = set(_csv('ALLOWED_IMAGE_EXTENSIONS', 'jpg,jpeg,png,webp'))
    CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID', '')
    CLOUDFLARE_R2_ENDPOINT_URL = os.getenv('CLOUDFLARE_R2_ENDPOINT_URL', '')
    CLOUDFLARE_R2_BUCKET = os.getenv('CLOUDFLARE_R2_BUCKET', '')
    CLOUDFLARE_R2_ACCESS_KEY_ID = os.getenv('CLOUDFLARE_R2_ACCESS_KEY_ID', '')
    CLOUDFLARE_R2_SECRET_ACCESS_KEY = os.getenv('CLOUDFLARE_R2_SECRET_ACCESS_KEY', '')
    CLOUDFLARE_R2_PUBLIC_URL = os.getenv('CLOUDFLARE_R2_PUBLIC_URL', '').rstrip('/')

    SESSION_COOKIE_SECURE = _bool('SESSION_COOKIE_SECURE', APP_ENV == 'production')
    SESSION_COOKIE_HTTPONLY = _bool('SESSION_COOKIE_HTTPONLY', True)
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    WTF_CSRF_ENABLED = _bool('WTF_CSRF_ENABLED', True)
    RATE_LIMIT_ENABLED = _bool('RATE_LIMIT_ENABLED', True)
    LOGIN_RATE_LIMIT = os.getenv('LOGIN_RATE_LIMIT', '5 per minute')
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '200 per hour')
    UPLOAD_RATE_LIMIT = os.getenv('UPLOAD_RATE_LIMIT', '20 per hour')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@roomies.local')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin1234')
    SEED_DEMO_DATA = _bool('SEED_DEMO_DATA', True)
