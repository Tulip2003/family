from __future__ import annotations

from flask import Blueprint, current_app, jsonify, send_from_directory

from extensions import db
from models import Room, User
from storage import serve_local_upload

core_bp = Blueprint("core", __name__)


@core_bp.get("/api/health")
def health():
    db.session.execute(db.text("SELECT 1"))
    return jsonify(ok=True, status="healthy", database="connected")


@core_bp.get("/api/dashboard/stats")
def dashboard_stats():
    return jsonify(
        ok=True,
        stats={
            "rooms": Room.query.count(),
            "active_rooms": Room.query.filter_by(status="active").count(),
            "pending_rooms": Room.query.filter_by(status="pending").count(),
            "users": User.query.count(),
        },
    )


@core_bp.get("/uploads/<path:path>")
def uploads(path: str):
    return serve_local_upload(path)
