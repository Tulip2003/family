from app import create_app
from extensions import db
from sqlalchemy import text
from notify import send_email

app=create_app()
with app.app_context():
    print('Checking database...')
    db.session.execute(text('SELECT 1'))
    print('Database OK')
    print('Storage provider:', app.config['STORAGE_PROVIDER'])
    print('Email verification enabled:', app.config['EMAIL_VERIFICATION_ENABLED'])
    if app.config['EMAIL_VERIFICATION_ENABLED'] and app.config['MAIL_FROM_EMAIL']:
        print('Email config present. Send test manually from admin page or shell.')
    print('All basic integration checks passed.')
