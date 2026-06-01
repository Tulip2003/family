# Roomies API

All write endpoints require `X-CSRF-Token` from the page meta tag.

## Auth

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `PUT /api/auth/profile`
- `PUT /api/auth/password`

## Rooms

- `GET /api/rooms?q=&city=&area=&min_price=&max_price=&room_type=&sort=`
- `GET /api/rooms/<id>`
- `POST /api/rooms` multipart or JSON
- `PUT /api/rooms/<id>`
- `DELETE /api/rooms/<id>`
- `POST /api/rooms/<id>/images`

## Social

- `GET /api/favorites`
- `POST /api/favorites/<room_id>`
- `DELETE /api/favorites/<room_id>`
- `POST /api/bookings`
- `GET /api/bookings`
- `PUT /api/bookings/<id>`
- `POST /api/applications`
- `GET /api/applications`
- `GET /api/messages`
- `GET /api/messages/<conversation_id>`
- `POST /api/messages`
- `POST /api/reports`
- `POST /api/contact`
- `POST /api/newsletter`
- `GET /api/saved-searches`
- `POST /api/saved-searches`

## Verification

- `POST /api/verify/email/request`
- `POST /api/verify/email/confirm`
- `POST /api/verify/phone/request`
- `POST /api/verify/phone/confirm`

## Admin

Admin role required.

- `GET /api/admin/stats`
- `GET /api/admin/rooms`
- `PUT /api/admin/rooms/<id>/status`
- `GET /api/admin/users`
- `PUT /api/admin/users/<id>`
- `GET /api/admin/reports`
- `PUT /api/admin/reports/<id>`
- `GET /api/admin/audit-logs`
