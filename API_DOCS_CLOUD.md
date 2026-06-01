# Roomies Cloud API Summary

All API routes are under `/api` and return JSON with `ok: true` or `ok: false`.

## Auth

- `POST /api/signup`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`
- `PUT /api/profile`
- `POST /api/profile/password`
- `POST /api/verification/request`
- `POST /api/verification/confirm`

Use auth header:

```http
Authorization: Bearer YOUR_TOKEN
```

## Rooms

- `GET /api/rooms`
- `POST /api/rooms`
- `GET /api/rooms/:id`
- `PUT /api/rooms/:id`
- `DELETE /api/rooms/:id`
- `GET /api/rooms/compare?ids=1,2,3`
- `POST /api/uploads/images`

Room creation supports:

```json
{
  "title": "Sunny private room",
  "location": "Putalisadak, Kathmandu",
  "city": "kathmandu",
  "price": 9500,
  "deposit": 9500,
  "room_type": "Private Room",
  "bedrooms": 1,
  "bathrooms": 1,
  "description": "Bright and safe room",
  "amenities": ["WiFi", "CCTV"],
  "image_data_list": [{"name": "room.jpg", "data": "data:image/jpeg;base64,..."}]
}
```

## Favorites, bookings, applications

- `POST /api/favorites/:room_id`
- `GET /api/favorites`
- `POST /api/bookings`
- `GET /api/bookings/my`
- `POST /api/bookings/:id/status`
- `POST /api/applications`
- `GET /api/applications/my`
- `POST /api/applications/:id/status`

## Messages and public forms

- `POST /api/messages`
- `GET /api/messages`
- `GET /api/messages/threads`
- `POST /api/contact`
- `POST /api/newsletter`

## Admin

- `GET /api/admin/overview`
- `GET /api/admin/moderation`
- `POST /api/admin/rooms/:id/status`
- `POST /api/admin/reports/:id/status`
- `POST /api/admin/users/:id/verify`
- `POST /api/admin/backup`
