from datetime import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from extensions import db, limiter
from models import Room, RoomImage, ListingStatus, Favorite, Role
from security import sanitize_text, require_auth, audit, current_user
from storage import save_room_image, UploadError

rooms_bp = Blueprint('rooms', __name__)


def data():
    return request.get_json(silent=True) or request.form.to_dict()


def int_arg(name, default=None):
    val = request.args.get(name)
    try:
        return int(val) if val not in [None, ''] else default
    except ValueError:
        return default


@rooms_bp.get('')
def list_rooms():
    q = Room.query.filter(Room.status == ListingStatus.APPROVED.value)
    keyword = sanitize_text(request.args.get('q'), max_len=100)
    city = sanitize_text(request.args.get('city'), max_len=100)
    area = sanitize_text(request.args.get('area'), max_len=100)
    room_type = sanitize_text(request.args.get('room_type'), max_len=60)
    min_price = int_arg('min_price')
    max_price = int_arg('max_price')
    if keyword:
        like = f'%{keyword}%'
        q = q.filter(or_(Room.title.ilike(like), Room.description.ilike(like), Room.area.ilike(like), Room.city.ilike(like)))
    if city:
        q = q.filter(Room.city.ilike(f'%{city}%'))
    if area:
        q = q.filter(Room.area.ilike(f'%{area}%'))
    if room_type:
        q = q.filter(Room.room_type == room_type)
    if min_price is not None:
        q = q.filter(Room.price >= min_price)
    if max_price is not None:
        q = q.filter(Room.price <= max_price)
    sort = request.args.get('sort', 'newest')
    if sort == 'price_low':
        q = q.order_by(Room.price.asc())
    elif sort == 'price_high':
        q = q.order_by(Room.price.desc())
    elif sort == 'popular':
        q = q.order_by(Room.view_count.desc())
    else:
        q = q.order_by(Room.is_featured.desc(), Room.created_at.desc())
    page = int_arg('page', 1) or 1
    per_page = min(int_arg('per_page', 12) or 12, 50)
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({'ok': True, 'rooms': [r.to_dict() for r in pagination.items], 'total': pagination.total, 'page': page, 'pages': pagination.pages})


@rooms_bp.get('/<int:room_id>')
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    if room.status != ListingStatus.APPROVED.value:
        user = current_user()
        if not user or (user.id != room.owner_id and user.role != Role.ADMIN.value):
            return jsonify({'ok': False, 'error': 'Room not available'}), 404
    room.view_count += 1
    db.session.commit()
    return jsonify({'ok': True, 'room': room.to_dict(detail=True)})


@rooms_bp.post('')
@require_auth
@limiter.limit(lambda: '25 per hour')
def create_room():
    user = request.user
    if user.role not in {Role.OWNER.value, Role.ADMIN.value}:
        return jsonify({'ok': False, 'error': 'Only owners can post rooms'}), 403
    p = data()
    required = ['title', 'description', 'city', 'area', 'price']
    if any(not sanitize_text(p.get(k), max_len=300) for k in required):
        return jsonify({'ok': False, 'error': 'Title, description, city, area, and price are required'}), 400
    try:
        price = int(p.get('price'))
    except Exception:
        return jsonify({'ok': False, 'error': 'Price must be a number'}), 400
    room = Room(
        owner_id=user.id,
        title=sanitize_text(p.get('title'), max_len=180),
        description=sanitize_text(p.get('description'), max_len=4000),
        city=sanitize_text(p.get('city'), max_len=100),
        area=sanitize_text(p.get('area'), max_len=120),
        address=sanitize_text(p.get('address'), max_len=255),
        price=price,
        deposit=int(p.get('deposit') or 0),
        room_type=sanitize_text(p.get('room_type'), max_len=60) or 'Single room',
        furnishing=sanitize_text(p.get('furnishing'), max_len=60) or 'Semi furnished',
        bedrooms=int(p.get('bedrooms') or 1),
        bathrooms=int(p.get('bathrooms') or 1),
        max_people=int(p.get('max_people') or 1),
        latitude=float(p.get('latitude')) if p.get('latitude') else None,
        longitude=float(p.get('longitude')) if p.get('longitude') else None,
        amenities=sanitize_text(p.get('amenities'), max_len=1000),
        rules=sanitize_text(p.get('rules'), max_len=1500),
        status=ListingStatus.APPROVED.value if user.role == Role.ADMIN.value else ListingStatus.PENDING.value,
    )
    if p.get('available_from'):
        try:
            room.available_from = datetime.strptime(p.get('available_from'), '%Y-%m-%d').date()
        except ValueError:
            pass
    db.session.add(room)
    db.session.flush()
    # Attach uploaded images if present.
    for idx, file in enumerate(request.files.getlist('images')[:8]):
        try:
            saved = save_room_image(file)
            db.session.add(RoomImage(room_id=room.id, url=saved['url'], storage_key=saved['storage_key'], sort_order=idx))
        except UploadError:
            db.session.rollback()
            raise
    db.session.commit()
    audit('room_create', 'room', room.id, actor=user)
    return jsonify({'ok': True, 'room': room.to_dict(detail=True)})


@rooms_bp.put('/<int:room_id>')
@require_auth
def update_room(room_id):
    user = request.user
    room = Room.query.get_or_404(room_id)
    if user.id != room.owner_id and user.role != Role.ADMIN.value:
        return jsonify({'ok': False, 'error': 'Permission denied'}), 403
    p = data()
    for key, max_len in [('title', 180), ('description', 4000), ('city', 100), ('area', 120), ('address', 255), ('room_type', 60), ('furnishing', 60), ('amenities', 1000), ('rules', 1500)]:
        if key in p:
            setattr(room, key, sanitize_text(p.get(key), max_len=max_len))
    for key in ['price', 'deposit', 'bedrooms', 'bathrooms', 'max_people']:
        if key in p and p.get(key) != '':
            setattr(room, key, int(p.get(key)))
    if user.role != Role.ADMIN.value:
        room.status = ListingStatus.PENDING.value
    db.session.commit()
    audit('room_update', 'room', room.id, actor=user)
    return jsonify({'ok': True, 'room': room.to_dict(detail=True)})


@rooms_bp.delete('/<int:room_id>')
@require_auth
def delete_room(room_id):
    user = request.user
    room = Room.query.get_or_404(room_id)
    if user.id != room.owner_id and user.role != Role.ADMIN.value:
        return jsonify({'ok': False, 'error': 'Permission denied'}), 403
    room.status = ListingStatus.ARCHIVED.value
    db.session.commit()
    audit('room_archive', 'room', room.id, actor=user)
    return jsonify({'ok': True})


@rooms_bp.post('/<int:room_id>/images')
@require_auth
@limiter.limit(lambda: '20 per hour')
def upload_room_images(room_id):
    user = request.user
    room = Room.query.get_or_404(room_id)
    if user.id != room.owner_id and user.role != Role.ADMIN.value:
        return jsonify({'ok': False, 'error': 'Permission denied'}), 403
    images = []
    try:
        for idx, file in enumerate(request.files.getlist('images')[:8]):
            saved = save_room_image(file)
            img = RoomImage(room_id=room.id, url=saved['url'], storage_key=saved['storage_key'], sort_order=len(room.images) + idx)
            db.session.add(img)
            images.append(img)
        db.session.commit()
    except UploadError as exc:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(exc)}), 400
    audit('room_images_upload', 'room', room.id, {'count': len(images)}, actor=user)
    return jsonify({'ok': True, 'images': [i.to_dict() for i in images]})
