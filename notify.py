from __future__ import annotations
import smtplib
from email.message import EmailMessage
from flask import current_app


def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    cfg = current_app.config
    if not cfg.get('EMAIL_VERIFICATION_ENABLED'):
        current_app.logger.info('EMAIL DEV MODE to=%s subject=%s body=%s', to, subject, text or html)
        return True
    if not (cfg.get('BREVO_SMTP_USER') and cfg.get('BREVO_SMTP_PASSWORD')):
        current_app.logger.warning('Email credentials missing; skipping email to %s', to)
        return False

    msg = EmailMessage()
    msg['From'] = f"{cfg.get('MAIL_FROM_NAME')} <{cfg.get('MAIL_FROM_EMAIL')}>"
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(text or 'Open this email in HTML view.')
    msg.add_alternative(html, subtype='html')

    smtp_cls = smtplib.SMTP_SSL if cfg.get('SMTP_USE_SSL') else smtplib.SMTP
    with smtp_cls(cfg.get('BREVO_SMTP_HOST'), cfg.get('BREVO_SMTP_PORT'), timeout=15) as smtp:
        if cfg.get('SMTP_USE_TLS') and not cfg.get('SMTP_USE_SSL'):
            smtp.starttls()
        smtp.login(cfg.get('BREVO_SMTP_USER'), cfg.get('BREVO_SMTP_PASSWORD'))
        smtp.send_message(msg)
    return True


def send_verification_email(user, token: str):
    app_url = current_app.config['APP_BASE_URL']
    link = f'{app_url}/verify-email?email={user.email}&token={token}'
    html = f'''
    <div style="font-family:Inter,Arial,sans-serif;line-height:1.6">
      <h2>Verify your Roomies email</h2>
      <p>Hello {user.name}, use this code to verify your email:</p>
      <div style="font-size:28px;font-weight:800;letter-spacing:4px;background:#f3f5ff;padding:16px;border-radius:12px;display:inline-block">{token}</div>
      <p>Or open <a href="{link}">this verification link</a>.</p>
      <p>This code expires soon.</p>
    </div>
    '''
    return send_email(user.email, 'Verify your Roomies email', html, f'Your Roomies verification code is {token}')


def send_phone_otp(phone: str, token: str) -> bool:
    cfg = current_app.config
    if not cfg.get('PHONE_VERIFICATION_ENABLED'):
        current_app.logger.info('SMS DEV MODE to=%s token=%s', phone, token)
        return True
    from twilio.rest import Client
    client = Client(cfg.get('TWILIO_ACCOUNT_SID'), cfg.get('TWILIO_AUTH_TOKEN'))
    if cfg.get('TWILIO_VERIFY_SERVICE_SID'):
        client.verify.v2.services(cfg.get('TWILIO_VERIFY_SERVICE_SID')).verifications.create(to=phone, channel='sms')
    else:
        client.messages.create(to=phone, from_=cfg.get('TWILIO_FROM_NUMBER'), body=f'Your Roomies code is {token}')
    return True
