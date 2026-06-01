# Roomies Enterprise Full Website

This is a full Flask + SQLAlchemy room-rent website with multi-page frontend, backend API, cloud database support, real email verification, optional phone OTP, Cloudflare R2 image storage, admin moderation, favorites, bookings, tenant applications, saved searches, messages, reports, and security controls.

## Quick local run

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python scripts/create_env.py
python -m flask --app app reset-db
python app.py
```

Open `http://127.0.0.1:5000`.

Demo accounts after seed:

- Admin: `admin@roomies.local` / `admin1234`
- Owner: `demo@roomies.local` / `demo1234`
- Renter: `renter@roomies.local` / `renter1234`

## Production stack

Recommended free/low-cost stack:

- Database: Neon PostgreSQL, use the pooled `DATABASE_URL`.
- Email: Brevo SMTP key for verification email.
- Storage: Cloudflare R2 bucket for room photos.
- Phone: Twilio or Nepal SMS provider, optional. You can launch with email verification first.
- Hosting: Render, Railway, Fly.io, PythonAnywhere, or VPS.

## Important security note

Do not paste secret keys into chat or GitHub. If you already pasted a password or API key anywhere public, regenerate it in that provider dashboard. Store secrets only in `.env` on your machine or hosting dashboard.

## Major features

- Secure signup/login with hashed passwords
- Account lockout after repeated failed login
- CSRF protection for API writes
- Rate limits on login, signup, upload
- Multi-image upload with validation and WEBP normalization
- Local or Cloudflare R2 storage
- PostgreSQL, MySQL, or SQLite support through SQLAlchemy
- Email verification and phone verification hooks
- Owner room CRUD
- Admin approval/rejection
- Favorites, compare rooms, saved searches
- Visit booking requests
- Tenant applications
- User-to-user messaging
- Fake listing reports
- Contact form and newsletter storage
- Audit logs
- PWA manifest and service worker

## Cloud `.env` outline

```env
APP_ENV=production
DEBUG=false
APP_BASE_URL=https://your-domain.com
ALLOWED_ORIGINS=https://your-domain.com
SECRET_KEY=generate-long-secret
DATABASE_URL=postgresql://USER:PASSWORD@POOLER_HOST/DB?sslmode=require
EMAIL_VERIFICATION_ENABLED=true
BREVO_SMTP_USER=your-brevo-login
BREVO_SMTP_PASSWORD=your-brevo-smtp-key
MAIL_FROM_EMAIL=verified-sender@example.com
STORAGE_PROVIDER=r2
CLOUDFLARE_R2_ENDPOINT_URL=https://ACCOUNT_ID.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET=roomies-uploads
CLOUDFLARE_R2_ACCESS_KEY_ID=...
CLOUDFLARE_R2_SECRET_ACCESS_KEY=...
SESSION_COOKIE_SECURE=true
```

## Deployment

For Render:

1. Push the project to a private GitHub repo without `.env`.
2. Create Web Service.
3. Set build command: `pip install -r requirements.txt`.
4. Set start command: `gunicorn -w 3 -b 0.0.0.0:$PORT app:app`.
5. Add environment variables in Render dashboard.
6. Run `python -m flask --app app init-db` and `python -m flask --app app seed-db` from a shell/job.

## API docs

See `docs/API.md` for endpoint list.
