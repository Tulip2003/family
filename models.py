from __future__ import annotations
from datetime import datetime, timedelta
from enum import Enum
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, UniqueConstraint
from extensions import db


class Role(str, Enum):
    RENTER = 'renter'
    OWNER = 'owner'
    ADMIN = 'admin'


class ListingStatus(str, Enum):
    DRAFT = 'draft'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    ARCHIVED = 'archived'


class BookingStatus(str, Enum):
    REQUESTED = 'requested'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'


class ApplicationStatus(str, Enum):
    SUBMITTED = 'submitted'
    REVIEWING = 'reviewing'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(TimestampMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(40), unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default=Role.RENTER.value, nullable=False, index=True)
    city = db.Column(db.String(100), default='Kathmandu')
    bio = db.Column(db.Text, default='')
    avatar_url = db.Column(db.String(800), default='')
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    phone_verified = db.Column(db.Boolean, default=False, nullable=False)
    owner_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)

    rooms = db.relationship('Room', back_populates='owner', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def public_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'city': self.city,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'email_verified': self.email_verified,
            'phone_verified': self.phone_verified,
            'owner_verified': self.owner_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Room(TimestampMixin, db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    area = db.Column(db.String(120), nullable=False, index=True)
    address = db.Column(db.String(255), default='')
    price = db.Column(db.Integer, nullable=False, index=True)
    deposit = db.Column(db.Integer, default=0)
    room_type = db.Column(db.String(60), default='Single room', index=True)
    furnishing = db.Column(db.String(60), default='Semi furnished')
    available_from = db.Column(db.Date)
    bedrooms = db.Column(db.Integer, default=1)
    bathrooms = db.Column(db.Integer, default=1)
    max_people = db.Column(db.Integer, default=1)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    amenities = db.Column(db.Text, default='')
    rules = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default=ListingStatus.PENDING.value, nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    safety_score = db.Column(db.Integer, default=70, nullable=False)

    owner = db.relationship('User', back_populates='rooms')
    images = db.relationship('RoomImage', back_populates='room', cascade='all, delete-orphan', order_by='RoomImage.sort_order')

    __table_args__ = (
        Index('ix_rooms_city_area_price', 'city', 'area', 'price'),
    )

    def amenity_list(self) -> list[str]:
        return [x.strip() for x in (self.amenities or '').split(',') if x.strip()]

    def rules_list(self) -> list[str]:
        return [x.strip() for x in (self.rules or '').split('\n') if x.strip()]

    def cover_url(self) -> str:
        return self.images[0].url if self.images else '/static/demo-photos/room-01.png'

    def to_dict(self, detail: bool = False) -> dict:
        data = {
            'id': self.id,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else '',
            'owner_verified': bool(self.owner and self.owner.owner_verified),
            'title': self.title,
            'description': self.description,
            'city': self.city,
            'area': self.area,
            'address': self.address,
            'price': self.price,
            'deposit': self.deposit,
            'room_type': self.room_type,
            'furnishing': self.furnishing,
            'available_from': self.available_from.isoformat() if self.available_from else None,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'max_people': self.max_people,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'amenities': self.amenity_list(),
            'status': self.status,
            'is_featured': self.is_featured,
            'view_count': self.view_count,
            'safety_score': self.safety_score,
            'cover_url': self.cover_url(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if detail:
            data['rules'] = self.rules_list()
            data['images'] = [img.to_dict() for img in self.images]
            data['owner'] = self.owner.public_dict() if self.owner else None
        return data


class RoomImage(TimestampMixin, db.Model):
    __tablename__ = 'room_images'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False, index=True)
    url = db.Column(db.String(1000), nullable=False)
    storage_key = db.Column(db.String(1000), default='')
    alt = db.Column(db.String(200), default='Room photo')
    sort_order = db.Column(db.Integer, default=0)
    room = db.relationship('Room', back_populates='images')

    def to_dict(self):
        return {'id': self.id, 'url': self.url, 'alt': self.alt, 'sort_order': self.sort_order}


class Favorite(TimestampMixin, db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    room = db.relationship('Room')
    __table_args__ = (UniqueConstraint('user_id', 'room_id', name='uq_favorite_user_room'),)


class SavedSearch(TimestampMixin, db.Model):
    __tablename__ = 'saved_searches'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    query_json = db.Column(db.JSON, nullable=False, default=dict)
    alert_enabled = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'query': self.query_json, 'alert_enabled': self.alert_enabled}


class Booking(TimestampMixin, db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False, index=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    visit_at = db.Column(db.DateTime, nullable=False)
    message = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default=BookingStatus.REQUESTED.value, nullable=False, index=True)
    room = db.relationship('Room')
    renter = db.relationship('User', foreign_keys=[renter_id])
    owner = db.relationship('User', foreign_keys=[owner_id])

    def to_dict(self):
        return {
            'id': self.id, 'room': self.room.to_dict() if self.room else None,
            'renter': self.renter.public_dict() if self.renter else None,
            'owner': self.owner.public_dict() if self.owner else None,
            'visit_at': self.visit_at.isoformat() if self.visit_at else None,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TenantApplication(TimestampMixin, db.Model):
    __tablename__ = 'tenant_applications'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False, index=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    move_in_date = db.Column(db.Date)
    occupation = db.Column(db.String(120), default='')
    monthly_income = db.Column(db.Integer, default=0)
    message = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default=ApplicationStatus.SUBMITTED.value, index=True)
    room = db.relationship('Room')
    applicant = db.relationship('User', foreign_keys=[applicant_id])
    owner = db.relationship('User', foreign_keys=[owner_id])

    def to_dict(self):
        return {
            'id': self.id, 'room': self.room.to_dict() if self.room else None,
            'applicant': self.applicant.public_dict() if self.applicant else None,
            'move_in_date': self.move_in_date.isoformat() if self.move_in_date else None,
            'occupation': self.occupation,
            'monthly_income': self.monthly_income,
            'message': self.message,
            'status': self.status,
        }


class Conversation(TimestampMixin, db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True, index=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    room = db.relationship('Room')
    messages = db.relationship('Message', back_populates='conversation', cascade='all, delete-orphan')

    def to_dict(self):
        last = self.messages[-1] if self.messages else None
        return {
            'id': self.id,
            'room': self.room.to_dict() if self.room else None,
            'renter_id': self.renter_id,
            'owner_id': self.owner_id,
            'last_message': last.body if last else '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Message(TimestampMixin, db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    read_at = db.Column(db.DateTime)
    conversation = db.relationship('Conversation', back_populates='messages')
    sender = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender': self.sender.public_dict() if self.sender else None,
            'body': self.body,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Report(TimestampMixin, db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    reason = db.Column(db.String(120), nullable=False)
    detail = db.Column(db.Text, default='')
    status = db.Column(db.String(30), default='open', nullable=False, index=True)
    room = db.relationship('Room')
    reporter = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id, 'room': self.room.to_dict() if self.room else None,
            'reporter': self.reporter.public_dict() if self.reporter else None,
            'reason': self.reason, 'detail': self.detail, 'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ContactMessage(TimestampMixin, db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='new', index=True)


class NewsletterSubscriber(TimestampMixin, db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    active = db.Column(db.Boolean, default=True, nullable=False)


class VerificationToken(TimestampMixin, db.Model):
    __tablename__ = 'verification_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    channel = db.Column(db.String(20), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    user = db.relationship('User')

    @staticmethod
    def make(user_id: int, channel: str, ttl_minutes: int = 30):
        raw = f'{secrets.randbelow(1000000):06d}'
        obj = VerificationToken(
            user_id=user_id,
            channel=channel,
            token_hash=generate_password_hash(raw, method='scrypt'),
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        )
        return obj, raw

    def verify(self, token: str) -> bool:
        if self.used_at or datetime.utcnow() > self.expires_at:
            return False
        return check_password_hash(self.token_hash, token)


class AuditLog(TimestampMixin, db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(120), nullable=False, index=True)
    entity = db.Column(db.String(120), default='')
    entity_id = db.Column(db.String(80), default='')
    ip_address = db.Column(db.String(80), default='')
    user_agent = db.Column(db.String(300), default='')
    meta_json = db.Column(db.JSON, default=dict)
    actor = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'actor': self.actor.public_dict() if self.actor else None,
            'action': self.action,
            'entity': self.entity,
            'entity_id': self.entity_id,
            'ip_address': self.ip_address,
            'meta': self.meta_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
