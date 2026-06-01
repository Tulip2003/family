from pathlib import Path
import secrets

root=Path(__file__).resolve().parents[1]
tpl=(root/'.env.example').read_text()
secret=secrets.token_urlsafe(64)
salt=secrets.token_urlsafe(32)
out=tpl.replace('change-me-generate-with-python-c-import-secrets-print-secrets-token-urlsafe-64',secret).replace('change-me-too',salt)
path=root/'.env'
if path.exists():
    print('.env already exists. Delete it first if you want a new one.')
else:
    path.write_text(out)
    print('Created .env. Now add your Neon, Brevo, Twilio, and Cloudflare R2 credentials locally.')
