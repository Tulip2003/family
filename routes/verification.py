from datetime import datetime
from flask import Blueprint, jsonify, request
from extensions import db, limiter
from models import VerificationToken, User
from security import require_auth, sanitize_email, sanitize_text, current_user
from notify import send_verification_email, send_phone_otp

verification_bp = Blueprint('verification', __name__)

def payload():
    return request.get_json(silent=True) or request.form.to_dict()

@verification_bp.post('/email/request')
@require_auth
@limiter.limit(lambda: '3 per hour')
def request_email_code():
    user = request.user
    token_obj, raw = VerificationToken.make(user.id, 'email')
    db.session.add(token_obj)
    db.session.commit()
    send_verification_email(user, raw)
    return jsonify({'ok': True, 'message': 'Verification email sent'})

@verification_bp.post('/email/confirm')
def confirm_email():
    p = payload()
    email = sanitize_email(p.get('email'))
    token = sanitize_text(p.get('token'), max_len=20)
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'ok': False, 'error': 'Invalid verification'}), 400
    row = VerificationToken.query.filter_by(user_id=user.id, channel='email').order_by(VerificationToken.created_at.desc()).first()
    if not row or not row.verify(token):
        return jsonify({'ok': False, 'error': 'Invalid or expired code'}), 400
    row.used_at = datetime.utcnow()
    user.email_verified = True
    db.session.commit()
    return jsonify({'ok': True})

@verification_bp.post('/phone/request')
@require_auth
@limiter.limit(lambda: '3 per hour')
def request_phone_code():
    user = request.user
    if not user.phone:
        return jsonify({'ok': False, 'error': 'Add phone number first'}), 400
    token_obj, raw = VerificationToken.make(user.id, 'phone')
    db.session.add(token_obj)
    db.session.commit()
    send_phone_otp(user.phone, raw)
    return jsonify({'ok': True, 'message': 'Phone code sent'})

@verification_bp.post('/phone/confirm')
@require_auth
def confirm_phone():
    token = sanitize_text(payload().get('token'), max_len=20)
    row = VerificationToken.query.filter_by(user_id=request.user.id, channel='phone').order_by(VerificationToken.created_at.desc()).first()
    if not row or not row.verify(token):
        return jsonify({'ok': False, 'error': 'Invalid or expired code'}), 400
    row.used_at = datetime.utcnow()
    request.user.phone_verified = True
    db.session.commit()
    return jsonify({'ok': True})
