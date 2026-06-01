from datetime import datetime
from flask import Blueprint, jsonify, request
from extensions import db, limiter
from models import User, Role, VerificationToken
from security import sanitize_text, sanitize_email, validate_email, validate_phone, validate_password, login_user, logout_user, current_user, is_locked, register_failed_login, audit, require_auth
from notify import send_verification_email

auth_bp = Blueprint('auth', __name__)


def payload():
    return request.get_json(silent=True) or request.form.to_dict()


@auth_bp.post('/signup')
@limiter.limit(lambda: '10 per hour')
def signup():
    data = payload()
    name = sanitize_text(data.get('name'), max_len=120)
    email = sanitize_email(data.get('email'))
    phone = sanitize_text(data.get('phone'), max_len=40) or None
    password = data.get('password') or ''
    role = sanitize_text(data.get('role'), max_len=20) or Role.RENTER.value
    if role not in {Role.RENTER.value, Role.OWNER.value}:
        role = Role.RENTER.value
    if not name:
        return jsonify({'ok': False, 'error': 'Name is required'}), 400
    if not validate_email(email):
        return jsonify({'ok': False, 'error': 'Valid email is required'}), 400
    if not validate_phone(phone):
        return jsonify({'ok': False, 'error': 'Valid phone is required'}), 400
    ok, msg = validate_password(password)
    if not ok:
        return jsonify({'ok': False, 'error': msg}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'ok': False, 'error': 'Email already registered'}), 409
    if phone and User.query.filter_by(phone=phone).first():
        return jsonify({'ok': False, 'error': 'Phone already registered'}), 409

    user = User(name=name, email=email, phone=phone, role=role, city=sanitize_text(data.get('city'), max_len=100) or 'Kathmandu')
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    token_obj, token = VerificationToken.make(user.id, 'email')
    db.session.add(token_obj)
    db.session.commit()
    send_verification_email(user, token)
    login_user(user)
    audit('signup', 'user', user.id, actor=user)
    return jsonify({'ok': True, 'user': user.public_dict(), 'message': 'Account created. Check email for verification code.'})


@auth_bp.post('/login')
@limiter.limit(lambda: '5 per minute')
def login():
    data = payload()
    email = sanitize_email(data.get('email'))
    password = data.get('password') or ''
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'ok': False, 'error': 'Invalid login'}), 401
    if is_locked(user):
        return jsonify({'ok': False, 'error': 'Account locked for 15 minutes due to failed attempts'}), 423
    if not user.check_password(password):
        register_failed_login(user)
        return jsonify({'ok': False, 'error': 'Invalid login'}), 401
    if not user.is_active:
        return jsonify({'ok': False, 'error': 'Account disabled'}), 403
    login_user(user)
    audit('login', 'user', user.id, actor=user)
    return jsonify({'ok': True, 'user': user.public_dict()})


@auth_bp.post('/logout')
def logout():
    audit('logout')
    logout_user()
    return jsonify({'ok': True})


@auth_bp.get('/me')
def me():
    user = current_user()
    return jsonify({'ok': True, 'user': user.public_dict() if user else None})


@auth_bp.put('/profile')
@require_auth
def update_profile():
    user = request.user
    data = payload()
    user.name = sanitize_text(data.get('name', user.name), max_len=120) or user.name
    user.city = sanitize_text(data.get('city', user.city), max_len=100)
    user.bio = sanitize_text(data.get('bio', user.bio), max_len=800)
    phone = sanitize_text(data.get('phone', user.phone), max_len=40) or None
    if phone != user.phone:
        if not validate_phone(phone):
            return jsonify({'ok': False, 'error': 'Invalid phone'}), 400
        user.phone = phone
        user.phone_verified = False
    db.session.commit()
    audit('profile_update', 'user', user.id, actor=user)
    return jsonify({'ok': True, 'user': user.public_dict()})


@auth_bp.put('/password')
@require_auth
def change_password():
    user = request.user
    data = payload()
    current = data.get('current_password') or ''
    new = data.get('new_password') or ''
    if not user.check_password(current):
        return jsonify({'ok': False, 'error': 'Current password is wrong'}), 400
    ok, msg = validate_password(new)
    if not ok:
        return jsonify({'ok': False, 'error': msg}), 400
    user.set_password(new)
    db.session.commit()
    audit('password_change', 'user', user.id, actor=user)
    return jsonify({'ok': True})
