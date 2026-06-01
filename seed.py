from __future__ import annotations
from datetime import date, datetime, timedelta
from flask import current_app
from extensions import db
from models import User, Room, RoomImage, Role, ListingStatus, Favorite, Booking, TenantApplication, Conversation, Message, Report

AREAS = ['Baneshwor', 'Putalisadak', 'Boudha', 'Patan', 'Kirtipur', 'Kalanki', 'Balaju', 'Bhaktapur', 'Lalitpur', 'Tokha', 'Chabahil', 'Kapan']
AMENITIES = ['WiFi', 'Water 24/7', 'Parking', 'Attached Bathroom', 'Kitchen', 'Balcony', 'Sunlight', 'CCTV', 'Laundry', 'Nearby Bus Stop']


def ensure_user(name, email, password, role, **extra):
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(name=name, email=email, role=role, **extra)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def seed_database(app=None):
    admin = ensure_user('Roomies Admin', current_app.config.get('ADMIN_EMAIL', 'admin@roomies.local'), current_app.config.get('ADMIN_PASSWORD', 'admin1234'), Role.ADMIN.value, email_verified=True, owner_verified=True, city='Kathmandu')
    owner = ensure_user('Sudeep Owner', 'demo@roomies.local', 'demo1234', Role.OWNER.value, phone='+9779800000001', email_verified=True, phone_verified=True, owner_verified=True, city='Kathmandu')
    renter = ensure_user('Nisha Renter', 'renter@roomies.local', 'renter1234', Role.RENTER.value, phone='+9779800000002', email_verified=True, phone_verified=True, city='Lalitpur')

    if Room.query.count() == 0:
        for idx, area in enumerate(AREAS, start=1):
            room = Room(
                owner_id=owner.id,
                title=f'{area} bright room near main road',
                description=f'A clean, sunny and secure room in {area}. Perfect for students, working people, and small families. Close to shops, bus stop, clinic, and daily services.',
                city='Kathmandu' if idx % 3 else 'Lalitpur',
                area=area,
                address=f'{area} chowk, Ring Road access',
                price=6500 + idx * 850,
                deposit=6500 + idx * 850,
                room_type=['Single room', 'Flat', 'Shared room', 'Studio'][idx % 4],
                furnishing=['Unfurnished', 'Semi furnished', 'Fully furnished'][idx % 3],
                available_from=date.today() + timedelta(days=idx),
                bedrooms=1 + (idx % 3 == 0),
                bathrooms=1,
                max_people=1 + idx % 3,
                latitude=27.70 + idx * 0.003,
                longitude=85.31 + idx * 0.004,
                amenities=', '.join(AMENITIES[: 5 + idx % 5]),
                rules='No loud music after 10 PM\nKeep common area clean\nID verification required',
                status=ListingStatus.APPROVED.value if idx < 11 else ListingStatus.PENDING.value,
                is_featured=idx in [1, 2, 5, 8],
                safety_score=70 + idx % 25,
                view_count=idx * 17,
            )
            db.session.add(room)
            db.session.flush()
            for j in range(1, 4):
                photo_no = ((idx + j - 2) % 12) + 1
                db.session.add(RoomImage(room_id=room.id, url=f'/static/demo-photos/room-{photo_no:02}.png', storage_key='', alt=f'{area} room photo {j}', sort_order=j))

    if Favorite.query.count() == 0:
        for room in Room.query.limit(3).all():
            db.session.add(Favorite(user_id=renter.id, room_id=room.id))
    if Booking.query.count() == 0:
        sample_room = Room.query.first()
        if sample_room:
            db.session.add(Booking(room_id=sample_room.id, renter_id=renter.id, owner_id=sample_room.owner_id, visit_at=datetime.utcnow()+timedelta(days=2), message='I want to visit this room after college.', status='requested'))
            db.session.add(TenantApplication(room_id=sample_room.id, applicant_id=renter.id, owner_id=sample_room.owner_id, move_in_date=date.today()+timedelta(days=15), occupation='Architecture student', monthly_income=18000, message='Looking for a quiet study-friendly room.'))
            conv = Conversation(room_id=sample_room.id, renter_id=renter.id, owner_id=sample_room.owner_id)
            db.session.add(conv)
            db.session.flush()
            db.session.add(Message(conversation_id=conv.id, sender_id=renter.id, body='Is the room still available?'))
            db.session.add(Message(conversation_id=conv.id, sender_id=sample_room.owner_id, body='Yes, you can visit this weekend.'))
    db.session.commit()
