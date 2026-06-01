from __future__ import annotations
from functools import wraps
from datetime import datetime, timedelta
import re, secrets, hmac, hashlib
from flask import current_app, request, session, jsonify
from werkzeug.utils import secure_filename
import bleach
from extensions import db
from models import User, AuditLog

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^\+?[0-9][0-9\-\s]{6,18}$')
PASSWORD_MIN_LENGTH = 8


def sanitize_text(value: str | None, *, max_len: int = 10000) -> str:
    text = (value or '').strip()[:max_len]
    return bleach.clean(text, tags=[], attributes={}, strip=True)


def sanitize_email(email: str | None) -> str:
    return sanitize_text(email, max_len=255).lower()


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ''))


def validate_phone(phone: str | None) -> bool:
    if not phone:
        return True
    return bool(PHONE_RE.match(phone))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password or '') < PASSWORD_MIN_LENGTH:
        return False, f'Password must be at least {PASSWORD_MIN_LENGTH} characters.'
    if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
        return False, 'Password must include letters and numbers.'
    return True, 'ok'


def allowed_file(filename: str) -> bool:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in current_app.config['ALLOWED_IMAGE_EXTENSIONS']


def safe_storage_name(filename: str) -> str:
    name = secure_filename(filename or 'upload')
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else 'bin'
    return f'{datetime.utcnow().strftime("%Y/%m/%d")}/{secrets.token_hex(16)}.{ext}'


def current_user() -> User | None:
    uid = session.get('user_id')
    if not uid:
        return None
    return db.session.get(User, uid)


def login_user(user: User):
    session.clear()
    session['user_id'] = user.id
    session['role'] = user.role
    session.permanent = True
    user.last_login_at = datetime.utcnow()
    user.failed_login_count = 0
    user.locked_until = None
    db.session.commit()


def logout_user():
    session.clear()


def is_locked(user: User) -> bool:
    return bool(user.locked_until and user.locked_until > datetime.utcnow())


def register_failed_login(user: User):
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= 5:
        user.locked_until = datetime.utcnow() + timedelta(minutes=15)
    db.session.commit()


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({'ok': False, 'error': 'Authentication required'}), 401
        if not user.is_active:
            return jsonify({'ok': False, 'error': 'Account disabled'}), 403
        request.user = user
        return fn(*args, **kwargs)
    return wrapper


def require_role(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({'ok': False, 'error': 'Authentication required'}), 401
            if user.role not in roles:
                return jsonify({'ok': False, 'error': 'Permission denied'}), 403
            request.user = user
            return fn(*args, **kwargs)
        return wrapper
    return deco


def csrf_token() -> str:
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


def verify_csrf() -> bool:
    if not current_app.config.get('WTF_CSRF_ENABLED'):
        return True
    if request.method in {'GET', 'HEAD', 'OPTIONS'}:
        return True
    sent = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    return bool(sent and hmac.compare_digest(sent, session.get('_csrf_token', '')))


def audit(action: str, entity: str = '', entity_id: str = '', meta: dict | None = None, actor: User | None = None):
    try:
        log = AuditLog(
            actor_id=(actor.id if actor else session.get('user_id')),
            action=action,
            entity=entity,
            entity_id=str(entity_id or ''),
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr or '')[:80],
            user_agent=(request.headers.get('User-Agent') or '')[:300],
            meta_json=meta or {},
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


def sign_value(value: str) -> str:
    secret = current_app.config['SECRET_KEY'].encode()
    digest = hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()
    return f'{value}.{digest}'


def unsign_value(signed: str) -> str | None:
    try:
        value, digest = signed.rsplit('.', 1)
    except ValueError:
        return None
    expected = hmac.new(current_app.config['SECRET_KEY'].encode(), value.encode(), hashlib.sha256).hexdigest()
    return value if hmac.compare_digest(expected, digest) else None
