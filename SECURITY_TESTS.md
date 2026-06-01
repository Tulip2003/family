# Security Testing Checklist

Run the automated tests first:

```bash
pytest
```

Then test manually before launch:

1. Create account with weak passwords and confirm weak passwords are rejected.
2. Try repeated wrong logins and confirm temporary lockout.
3. Request email verification and confirm only the latest unexpired code works.
4. Request phone verification and confirm OTP expiry works.
5. Upload `.svg`, `.php`, renamed `.exe`, and oversized image files. They must be rejected.
6. Upload a valid JPG/PNG/WEBP and confirm EXIF is stripped and file name is randomized.
7. Post a room as an unverified owner. It should go to `pending`.
8. Verify owner or approve listing from admin. It should become public.
9. Try editing another owner’s room. It must return 403.
10. Try calling admin endpoints as renter/owner. They must return 403.
11. Submit contact form rapidly. Rate limit must trigger.
12. Confirm HTTPS is active on production and secure headers are present.
13. Check that `.env`, backups, and database URLs are never publicly served.
14. Review admin moderation and report handling before opening signups.

Recommended external checks:

- OWASP ZAP baseline scan
- Dependency scan: `pip-audit`
- Secret scan: `gitleaks detect`
- Database backup restore drill
