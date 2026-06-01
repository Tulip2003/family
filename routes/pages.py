from flask import Blueprint, render_template, redirect, request
from models import Room, ListingStatus

pages_bp = Blueprint('pages', __name__)

PAGES = {
    '/': 'index.html',
    '/search': 'search.html',
    '/post-room': 'post_room.html',
    '/dashboard': 'dashboard.html',
    '/favorites': 'favorites.html',
    '/messages': 'messages.html',
    '/listings': 'listings.html',
    '/profile': 'profile.html',
    '/login': 'login.html',
    '/signup': 'signup.html',
    '/contact': 'contact.html',
    '/bookings': 'bookings.html',
    '/applications': 'applications.html',
    '/saved-searches': 'saved_searches.html',
    '/compare': 'compare.html',
    '/verification': 'verification.html',
    '/safety': 'safety.html',
    '/admin': 'admin.html',
    '/moderation': 'moderation.html',
    '/map': 'map.html',
    '/how-it-works': 'how_it_works.html',
}

for path, template in list(PAGES.items()):
    pages_bp.add_url_rule(path, endpoint=template.replace('.html', '').replace('-', '_'), view_func=lambda template=template: render_template(template))

@pages_bp.get('/room/<int:room_id>')
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    room.view_count += 1
    from extensions import db
    db.session.commit()
    return render_template('room_detail.html', room=room)

@pages_bp.get('/room-details.html')
def old_room_detail():
    rid = request.args.get('id', '1')
    return redirect(f'/room/{rid}')

@pages_bp.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404
