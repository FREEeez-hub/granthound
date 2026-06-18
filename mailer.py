import smtplib
import config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _send(to: str, subject: str, html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"GrantHound <{config.GMAIL_USER}>"
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
        s.sendmail(config.GMAIL_USER, to, msg.as_string())


def send_confirmation(email: str, name: str, plan: str):
    plan_info = config.PLANS.get(plan, {"name": plan, "price": ""})
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto;background:#f7f3ec;padding:40px;border-radius:12px">
      <h1 style="font-family:Georgia,serif;color:#1a2e1e;font-size:32px;margin-bottom:8px">Bienvenue dans la meute 🐾</h1>
      <p style="color:#2a5738;font-size:18px;margin-bottom:24px">Bonjour {name},</p>
      <p style="color:#3a3a3a;line-height:1.7">
        Votre inscription au plan <strong>{plan_info['name']}</strong> ({plan_info['price']}) est bien reçue.<br>
        Notre équipe vous contacte sous 24h pour finaliser l'activation de votre compte.
      </p>
      <div style="background:#1a2e1e;border-radius:8px;padding:24px;margin:32px 0">
        <p style="color:#c9943a;font-size:13px;text-transform:uppercase;letter-spacing:2px;margin:0 0 8px">Prochaine étape</p>
        <p style="color:#f0ead6;margin:0;line-height:1.6">
          Vous recevrez un email de configuration avec vos identifiants d'accès et les premières alertes subsides pour votre ASBL.
        </p>
      </div>
      <p style="color:#666;font-size:13px">— L'équipe GrantHound</p>
    </div>
    """
    _send(email, "Votre inscription GrantHound est confirmée ✓", html)


def send_contact_notification(name: str, email: str, message: str, subject: str = ""):
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto">
      <h2 style="color:#1a2e1e">Nouveau message via GrantHound</h2>
      <p><strong>De :</strong> {name} ({email})</p>
      {"<p><strong>Sujet :</strong> " + subject + "</p>" if subject else ""}
      <div style="background:#f7f3ec;padding:20px;border-radius:8px;border-left:4px solid #c9943a">
        <p style="margin:0;white-space:pre-wrap">{message}</p>
      </div>
    </div>
    """
    _send(config.NOTIFY_EMAIL, f"[GrantHound Contact] {name}", html)
    # Confirmation to sender
    confirm_html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto;background:#f7f3ec;padding:40px;border-radius:12px">
      <h2 style="font-family:Georgia,serif;color:#1a2e1e">Message bien reçu</h2>
      <p style="color:#3a3a3a">Bonjour {name}, nous avons bien reçu votre message et vous répondrons dans les plus brefs délais.</p>
      <p style="color:#666;font-size:13px">— L'équipe GrantHound</p>
    </div>
    """
    _send(email, "Nous avons bien reçu votre message — GrantHound", confirm_html)
