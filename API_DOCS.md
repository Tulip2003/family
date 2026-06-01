# Roomies Pro API Docs

Base URL:

```text
/api
```

Use `Authorization: Bearer <token>` for private endpoints.

## Auth

```text
POST /api/signup
POST /api/login
POST /api/logout
GET  /api/me
PATCH /api/profile
PATCH /api/profile/password
```

## Rooms

```text
GET    /api/rooms
POST   /api/rooms
GET    /api/rooms/:id
PUT    /api/rooms/:id
DELETE /api/rooms/:id
GET    /api/rooms/compare?ids=1,2,3
```

Room filters:

```text
q, location, city, min_price, max_price, budget, type, bedrooms, bathrooms, furnished, wifi, amenities, preferred_tenant, verified, lat, lng, radius, sort, page, limit, status
```

Sort values can include:

```text
recommended, low price, high price, newest, rating, popular, nearest
```

## Favorites

```text
GET    /api/favorites
POST   /api/favorites/:room_id
DELETE /api/favorites/:room_id
```

## Bookings and visits

```text
POST  /api/bookings
GET   /api/bookings/my
PATCH /api/bookings/:id/status
```

## Tenant applications

```text
POST  /api/applications
GET   /api/applications/my
PATCH /api/applications/:id/status
```

Statuses:

```text
submitted, shortlisted, accepted, declined, withdrawn
```

## Messages

```text
GET  /api/messages/threads
GET  /api/messages?with_user=:id&room_id=:id
POST /api/messages
```

## Saved searches

```text
GET    /api/saved-searches
POST   /api/saved-searches
DELETE /api/saved-searches/:id
```

## Reports

```text
POST /api/reports
```

## Verification

```text
POST /api/verification/request
POST /api/verification/confirm
```

Local development returns `dev_code` so you can test without SMS/email.

## Notifications

```text
GET          /api/notifications
POST/PATCH   /api/notifications/read
```

## Admin

```text
GET   /api/admin/overview
GET   /api/admin/moderation
PATCH /api/admin/rooms/:id/status
PATCH /api/admin/reports/:id/status
PATCH /api/admin/users/:id/verify
POST  /api/admin/backup
```

## Public stats

```text
GET /api/public/stats
GET /api/health
```
