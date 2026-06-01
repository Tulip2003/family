from flask import Blueprint, jsonify, request
from sqlalchemy import func
from extensions import db
from models import User, Room, Report, ContactMessage, AuditLog, ListingStatus, Role
from security import require_role, sanitize_text, audit

admin_bp = Blueprint('admin', __name__)

@admin_bp.get('/stats')
@require_role(Role.ADMIN.value)
def stats():
    return jsonify({'ok': True, 'stats': {
        'users': User.query.count(),
        'rooms': Room.query.count(),
        'pending_rooms': Room.query.filter_by(status=ListingStatus.PENDING.value).count(),
        'reports': Report.query.filter_by(status='open').count(),
        'contacts': ContactMessage.query.filter_by(status='new').count(),
    }})

@admin_bp.get('/rooms')
@require_role(Role.ADMIN.value)
def rooms():
    status = request.args.get('status')
    q = Room.query
    if status:
        q = q.filter_by(status=status)
    rows = q.order_by(Room.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'rooms': [r.to_dict(detail=True) for r in rows]})

@admin_bp.put('/rooms/<int:room_id>/status')
@require_role(Role.ADMIN.value)
def room_status(room_id):
    room = Room.query.get_or_404(room_id)
    status = sanitize_text((request.get_json(silent=True) or {}).get('status'), max_len=30)
    if status not in {s.value for s in ListingStatus}:
        return jsonify({'ok': False, 'error': 'Invalid status'}), 400
    room.status = status
    db.session.commit()
    audit('admin_room_status', 'room', room.id, {'status': status}, actor=request.user)
    return jsonify({'ok': True, 'room': room.to_dict(detail=True)})

@admin_bp.get('/users')
@require_role(Role.ADMIN.value)
def users():
    rows = User.query.order_by(User.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'users': [u.public_dict() | {'is_active': u.is_active} for u in rows]})

@admin_bp.put('/users/<int:user_id>')
@require_role(Role.ADMIN.value)
def user_update(user_id):
    user = User.query.get_or_404(user_id)
    p = request.get_json(silent=True) or {}
    for key in ['is_active', 'email_verified', 'phone_verified', 'owner_verified']:
        if key in p:
            setattr(user, key, bool(p[key]))
    role = sanitize_text(p.get('role'), max_len=20)
    if role in {Role.RENTER.value, Role.OWNER.value, Role.ADMIN.value}:
        user.role = role
    db.session.commit()
    audit('admin_user_update', 'user', user.id, actor=request.user)
    return jsonify({'ok': True, 'user': user.public_dict()})

@admin_bp.get('/reports')
@require_role(Role.ADMIN.value)
def reports():
    rows = Report.query.order_by(Report.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'reports': [r.to_dict() for r in rows]})

@admin_bp.put('/reports/<int:report_id>')
@require_role(Role.ADMIN.value)
def report_update(report_id):
    row = Report.query.get_or_404(report_id)
    status = sanitize_text((request.get_json(silent=True) or {}).get('status'), max_len=30)
    if status in {'open', 'reviewing', 'resolved', 'dismissed'}:
        row.status = status
        db.session.commit()
    return jsonify({'ok': True, 'report': row.to_dict()})

@admin_bp.get('/audit-logs')
@require_role(Role.ADMIN.value)
def audit_logs():
    rows = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return jsonify({'ok': True, 'logs': [r.to_dict() for r in rows]})
