from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from extensions import db
from models import Favorite, Room, Booking, TenantApplication, Conversation, Message, Report, ContactMessage, NewsletterSubscriber, SavedSearch, Role
from security import require_auth, sanitize_text, sanitize_email, validate_email, audit, current_user

social_bp = Blueprint('social', __name__)

def payload():
    return request.get_json(silent=True) or request.form.to_dict()

@social_bp.get('/favorites')
@require_auth
def favorites():
    rows = Favorite.query.filter_by(user_id=request.user.id).order_by(Favorite.created_at.desc()).all()
    return jsonify({'ok': True, 'favorites': [r.room.to_dict() for r in rows if r.room]})

@social_bp.post('/favorites/<int:room_id>')
@require_auth
def add_favorite(room_id):
    Room.query.get_or_404(room_id)
    if not Favorite.query.filter_by(user_id=request.user.id, room_id=room_id).first():
        db.session.add(Favorite(user_id=request.user.id, room_id=room_id))
        db.session.commit()
    return jsonify({'ok': True})

@social_bp.delete('/favorites/<int:room_id>')
@require_auth
def remove_favorite(room_id):
    fav = Favorite.query.filter_by(user_id=request.user.id, room_id=room_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return jsonify({'ok': True})

@social_bp.post('/bookings')
@require_auth
def create_booking():
    p = payload()
    room = Room.query.get_or_404(int(p.get('room_id')))
    try:
        visit_at = datetime.fromisoformat(p.get('visit_at'))
    except Exception:
        return jsonify({'ok': False, 'error': 'visit_at must be ISO datetime'}), 400
    booking = Booking(room_id=room.id, renter_id=request.user.id, owner_id=room.owner_id, visit_at=visit_at, message=sanitize_text(p.get('message'), max_len=1000))
    db.session.add(booking)
    db.session.commit()
    audit('booking_create', 'booking', booking.id, actor=request.user)
    return jsonify({'ok': True, 'booking': booking.to_dict()})

@social_bp.get('/bookings')
@require_auth
def list_bookings():
    u = request.user
    q = Booking.query.filter(or_(Booking.renter_id == u.id, Booking.owner_id == u.id)).order_by(Booking.created_at.desc())
    return jsonify({'ok': True, 'bookings': [b.to_dict() for b in q.all()]})

@social_bp.put('/bookings/<int:booking_id>')
@require_auth
def update_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if request.user.id != booking.owner_id and request.user.id != booking.renter_id and request.user.role != Role.ADMIN.value:
        return jsonify({'ok': False, 'error': 'Permission denied'}), 403
    status = sanitize_text(payload().get('status'), max_len=30)
    if status in {'requested', 'approved', 'rejected', 'cancelled', 'completed'}:
        booking.status = status
        db.session.commit()
    return jsonify({'ok': True, 'booking': booking.to_dict()})

@social_bp.post('/applications')
@require_auth
def apply_room():
    p = payload()
    room = Room.query.get_or_404(int(p.get('room_id')))
    app = TenantApplication(room_id=room.id, applicant_id=request.user.id, owner_id=room.owner_id, occupation=sanitize_text(p.get('occupation'), max_len=120), monthly_income=int(p.get('monthly_income') or 0), message=sanitize_text(p.get('message'), max_len=1500))
    if p.get('move_in_date'):
        from datetime import datetime
        app.move_in_date = datetime.strptime(p.get('move_in_date'), '%Y-%m-%d').date()
    db.session.add(app)
    db.session.commit()
    return jsonify({'ok': True, 'application': app.to_dict()})

@social_bp.get('/applications')
@require_auth
def applications():
    u = request.user
    q = TenantApplication.query.filter(or_(TenantApplication.applicant_id == u.id, TenantApplication.owner_id == u.id)).order_by(TenantApplication.created_at.desc())
    return jsonify({'ok': True, 'applications': [a.to_dict() for a in q.all()]})

@social_bp.get('/messages')
@require_auth
def conversations():
    u = request.user
    rows = Conversation.query.filter(or_(Conversation.renter_id == u.id, Conversation.owner_id == u.id)).order_by(Conversation.updated_at.desc()).all()
    return jsonify({'ok': True, 'conversations': [c.to_dict() for c in rows]})

@social_bp.get('/messages/<int:conversation_id>')
@require_auth
def conversation_detail(conversation_id):
    c = Conversation.query.get_or_404(conversation_id)
    if request.user.id not in {c.renter_id, c.owner_id} and request.user.role != Role.ADMIN.value:
        return jsonify({'ok': False, 'error': 'Permission denied'}), 403
    return jsonify({'ok': True, 'conversation': c.to_dict(), 'messages': [m.to_dict() for m in c.messages]})

@social_bp.post('/messages')
@require_auth
def send_message():
    p = payload()
    room = Room.query.get_or_404(int(p.get('room_id'))) if p.get('room_id') else None
    body = sanitize_text(p.get('body'), max_len=1500)
    if not body:
        return jsonify({'ok': False, 'error': 'Message body is required'}), 400
    other_id = int(p.get('to_user_id') or (room.owner_id if room and room.owner_id != request.user.id else 0))
    if not other_id:
        return jsonify({'ok': False, 'error': 'Recipient missing'}), 400
    renter_id, owner_id = (request.user.id, other_id) if request.user.role != Role.OWNER.value else (other_id, request.user.id)
    conv = Conversation.query.filter_by(room_id=room.id if room else None, renter_id=renter_id, owner_id=owner_id).first()
    if not conv:
        conv = Conversation(room_id=room.id if room else None, renter_id=renter_id, owner_id=owner_id)
        db.session.add(conv)
        db.session.flush()
    msg = Message(conversation_id=conv.id, sender_id=request.user.id, body=body)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'ok': True, 'message': msg.to_dict(), 'conversation': conv.to_dict()})

@social_bp.post('/reports')
def report_room():
    p = payload()
    room = Room.query.get_or_404(int(p.get('room_id')))
    report = Report(room_id=room.id, reporter_id=current_user().id if current_user() else None, reason=sanitize_text(p.get('reason'), max_len=120) or 'Suspicious listing', detail=sanitize_text(p.get('detail'), max_len=1500))
    db.session.add(report)
    db.session.commit()
    return jsonify({'ok': True})

@social_bp.post('/contact')
def contact():
    p = payload()
    email = sanitize_email(p.get('email'))
    if not validate_email(email):
        return jsonify({'ok': False, 'error': 'Valid email required'}), 400
    row = ContactMessage(name=sanitize_text(p.get('name'), max_len=120), email=email, subject=sanitize_text(p.get('subject'), max_len=160), message=sanitize_text(p.get('message'), max_len=4000))
    db.session.add(row)
    db.session.commit()
    return jsonify({'ok': True})

@social_bp.post('/newsletter')
def newsletter():
    email = sanitize_email(payload().get('email'))
    if not validate_email(email):
        return jsonify({'ok': False, 'error': 'Valid email required'}), 400
    row = NewsletterSubscriber.query.filter_by(email=email).first()
    if not row:
        db.session.add(NewsletterSubscriber(email=email))
    else:
        row.active = True
    db.session.commit()
    return jsonify({'ok': True})

@social_bp.get('/saved-searches')
@require_auth
def saved_searches():
    rows = SavedSearch.query.filter_by(user_id=request.user.id).order_by(SavedSearch.created_at.desc()).all()
    return jsonify({'ok': True, 'saved_searches': [r.to_dict() for r in rows]})

@social_bp.post('/saved-searches')
@require_auth
def save_search():
    p = payload()
    row = SavedSearch(user_id=request.user.id, name=sanitize_text(p.get('name'), max_len=120) or 'My search', query_json=p.get('query') if isinstance(p.get('query'), dict) else p, alert_enabled=bool(p.get('alert_enabled')))
    db.session.add(row)
    db.session.commit()
    return jsonify({'ok': True, 'saved_search': row.to_dict()})
