# Roomies Cloud Production Upgrade

This version upgrades the Roomies website from local SQLite demo code into a production-style backend with:

- PostgreSQL or MySQL through SQLAlchemy
- Real email verification through SMTP
- Real phone verification through Twilio-compatible SMS
- Cloud image storage through S3-compatible storage
- Safer image upload handling with format validation, size limits, metadata stripping, and random storage names
- Rate limiting, secure headers, account lockout, audit logs, spam honeypot, admin moderation, and report workflows
- Pytest security tests and deployment-ready Docker files

The frontend pages from the Roomies Pro version are included, and the API keeps the same `/api/...` paths used by `js/app.js`.

## 1. Local setup

```bash
cd roomies_website_cloud_production
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

For quick local testing, keep the default SQLite fallback by removing/commenting `DATABASE_URL`, or run PostgreSQL with Docker.

```bash
python -m flask --app app init-db
python -m flask --app app seed-db
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Demo accounts after seed:

```text
Admin:  admin@roomies.local / admin1234
Owner:  demo@roomies.local / demo1234
Renter: renter@roomies.local / renter1234
```

## 2. PostgreSQL cloud database

Set this in `.env`:

```env
DATABASE_URL=postgresql+psycopg://roomies:STRONG_PASSWORD@HOST:5432/roomies
```

Then:

```bash
python -m flask --app app init-db
python -m flask --app app seed-db
```

For Render, Railway, Supabase, Neon, DigitalOcean, or any hosted PostgreSQL provider, paste their connection string into `DATABASE_URL`. If they provide `postgres://`, change it to `postgresql+psycopg://`.

## 3. MySQL cloud database

Set this in `.env`:

```env
DATABASE_URL=mysql+pymysql://roomies:STRONG_PASSWORD@HOST:3306/roomies?charset=utf8mb4
```

Then:

```bash
python -m flask --app app init-db
python -m flask --app app seed-db
```

## 4. Real email verification

Set SMTP values in `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM="Roomies <your-email@gmail.com>"
SMTP_USE_TLS=true
DEBUG_VERIFICATION_OUTPUT=false
```

For Gmail, use an App Password, not your normal password. SendGrid, Mailgun, Zoho, Brevo, and other SMTP providers also work.

## 5. Real phone verification

Set Twilio values in `.env`:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_FROM_PHONE=+1XXXXXXXXXX
DEBUG_VERIFICATION_OUTPUT=false
```

The app sends a 6-digit OTP and stores only the hashed code in the database.

## 6. Cloud image storage

This supports AWS S3, Cloudflare R2, DigitalOcean Spaces, Wasabi, or MinIO.

```env
S3_BUCKET=roomies-uploads
S3_REGION=ap-south-1
S3_ENDPOINT_URL=
S3_PUBLIC_BASE_URL=https://cdn.yourdomain.com
AWS_ACCESS_KEY_ID=xxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxx
MAX_IMAGE_MB=8
```

If `S3_BUCKET` is blank, uploads are stored locally in `/uploads`. When `S3_BUCKET` is configured, the same upload code stores images in the cloud.

## 7. Security features already coded

- Password hashing with Werkzeug scrypt
- Bearer auth tokens stored as SHA-256 hashes
- Login lockout after repeated failures
- Email and phone OTP codes stored only as hashes
- Rate limits on login, signup, verification, uploads, contact, and messages
- Secure response headers
- Upload validation with Pillow
- SVG upload disabled for user uploads to avoid script injection
- EXIF stripping and image resizing
- Spam honeypot on contact form
- Admin moderation for pending listings and reports
- Audit logs for key actions
- Cloud-safe JSON export for admin backups

## 8. Run tests

```bash
pytest
```

## 9. Production run

```bash
gunicorn "app:create_app('production')" --bind 0.0.0.0:$PORT --workers 3
```

Set a strong `SECRET_KEY`, use HTTPS, and set `FLASK_ENV=production`.
