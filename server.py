#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GrantHound — Serveur web principal
Usage: python3 server.py
"""

import sqlite3
import smtplib
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
PORT = 8000
DB_PATH = os.path.join(os.path.dirname(__file__), "granthound.db")
GMAIL_USER = "noahlatour77@gmail.com"
GMAIL_PASS = "bvtciemwwxonfcmi"

try:
    from granthound_matching import get_top_aides
except ImportError:
    def get_top_aides(secteur, province, type_org, n=3):
        return []

# ── Database ─────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            type_org TEXT,
            secteur TEXT,
            province TEXT,
            employes TEXT,
            email TEXT NOT NULL,
            contact TEXT,
            date_inscription TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS aides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            organisme TEXT,
            secteurs TEXT,
            provinces TEXT,
            types_org TEXT,
            montant_min INTEGER DEFAULT 0,
            montant_max INTEGER DEFAULT 0,
            deadline TEXT,
            description TEXT,
            url_officiel TEXT,
            date_ajout TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_aide(aide_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM aides WHERE id=?", (aide_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_client(data):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO clients (nom, type_org, secteur, province, employes, email, contact, date_inscription) VALUES (?,?,?,?,?,?,?,?)",
        (data.get("nom",""), data.get("type",""), data.get("secteur",""),
         data.get("province",""), data.get("employes",""), data.get("email",""),
         data.get("prenom",""), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

# ── Email ─────────────────────────────────────────────────────────────────────
def send_email(to, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, to, msg.as_string())
        return True
    except Exception as e:
        print(f"[Email error] {e}")
        return False

def email_bienvenue(client):
    aides = get_top_aides(client.get("secteur",""), client.get("province",""), client.get("type",""))
    aides_html = ""
    if aides:
        for a in aides[:3]:
            nom = a.get("nom","") or a.get("name","")
            desc = a.get("description","") or a.get("desc","")
            aides_html += f"<li style='margin-bottom:12px'><strong>{nom}</strong><br><span style='color:#6B7280'>{desc}</span></li>"
        aides_html = f"<ul style='padding-left:20px'>{aides_html}</ul>"
    else:
        aides_html = "<p style='color:#6B7280'>Votre rapport personnalisé sera envoyé dans quelques minutes.</p>"

    prenom = client.get("prenom","") or "cher(e) utilisateur(trice)"
    nom_org = client.get("nom","")
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:32px;color:#111827">
  <div style="border-left:4px solid #1E4D3A;padding-left:20px;margin-bottom:32px">
    <h1 style="font-family:Georgia,serif;color:#1E4D3A;font-size:28px;margin:0">GrantHound</h1>
    <p style="color:#6B7280;margin:4px 0 0">Veille automatique de subsides</p>
  </div>
  <p>Bonjour {prenom},</p>
  <p>Merci d'avoir rejoint GrantHound pour <strong>{nom_org}</strong>. Votre profil est enregistré.</p>
  <h2 style="font-family:Georgia,serif;color:#1E4D3A;font-size:20px">Premières pistes identifiées</h2>
  {aides_html}
  <p style="margin-top:32px;padding:16px;background:#F5F0E8;border-radius:8px;font-size:14px;color:#374151">
    <strong>Phase pilote :</strong> vous bénéficiez d'un accès gratuit. Votre premier rapport complet sera envoyé chaque semaine.
  </p>
  <p style="color:#6B7280;font-size:13px;margin-top:24px">Questions ? Répondez directement à cet email ou appelez le 0491 63 76 89.</p>
  <p style="color:#6B7280;font-size:13px">— Noah · GrantHound · Vielsalm</p>
</body></html>"""
    send_email(client["email"], f"Bienvenue sur GrantHound — {nom_org}", html)

def email_contact(data):
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:32px;color:#111827">
  <h2 style="color:#1E4D3A">Nouveau message GrantHound</h2>
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="padding:8px;border:1px solid #E5E7EB;background:#F9FAFB;width:120px"><strong>Nom</strong></td><td style="padding:8px;border:1px solid #E5E7EB">{data.get("nom","")}</td></tr>
    <tr><td style="padding:8px;border:1px solid #E5E7EB;background:#F9FAFB"><strong>Email</strong></td><td style="padding:8px;border:1px solid #E5E7EB">{data.get("email","")}</td></tr>
    <tr><td style="padding:8px;border:1px solid #E5E7EB;background:#F9FAFB"><strong>Sujet</strong></td><td style="padding:8px;border:1px solid #E5E7EB">{data.get("sujet","")}</td></tr>
    <tr><td style="padding:8px;border:1px solid #E5E7EB;background:#F9FAFB"><strong>Message</strong></td><td style="padding:8px;border:1px solid #E5E7EB">{data.get("message","").replace(chr(10),"<br>")}</td></tr>
  </table>
</body></html>"""
    send_email(GMAIL_USER, f"[GrantHound Contact] {data.get('sujet','')} — {data.get('nom','')}", html)

# ── CSS commun ────────────────────────────────────────────────────────────────
FONTS = """
  <link rel="preconnect" href="https://fonts.bunny.net">
  <link href="https://fonts.bunny.net/css?family=newsreader:400,500,600,700|inter:300,400,500,600&display=swap" rel="stylesheet">
"""

CSS_BASE = """
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  /* ── THÈME 1 : Vert Wallonie (défaut) ── forêt + ambre */
  :root, [data-theme="vert"] {
    --vert:       #1E4D3A;
    --vert-light: #2D6A4F;
    --vert-pale:  #EAF2EE;
    --ambre:      #D97706;
    --ambre-hover:#B45309;
    --beige:      #F5F0E8;
    --gris-pale:  #F9FAFB;
    --gris:       #6B7280;
    --gris-bord:  #E5E7EB;
    --noir:       #111827;
    --blanc:      #FFFFFF;
  }

  /* ── THÈME 2 : Marine & Or ── institutionnel belge / prestige */
  [data-theme="marine"] {
    --vert:       #1B3B6F;
    --vert-light: #234E8C;
    --vert-pale:  #E8EEF7;
    --ambre:      #C9960C;
    --ambre-hover:#A37A0A;
    --beige:      #F4F1E8;
    --gris-pale:  #F8F9FB;
    --gris:       #64748B;
    --gris-bord:  #E2E8F0;
    --noir:       #0F1F3D;
    --blanc:      #FFFFFF;
  }

  /* ── THÈME 3 : Ardoise & Terracotta ── éditorial moderne / chaleureux */
  [data-theme="ardoise"] {
    --vert:       #334155;
    --vert-light: #475569;
    --vert-pale:  #F1F5F9;
    --ambre:      #C2542A;
    --ambre-hover:#A34222;
    --beige:      #FBF7F4;
    --gris-pale:  #F8F9FA;
    --gris:       #64748B;
    --gris-bord:  #E2E8F0;
    --noir:       #1E293B;
    --blanc:      #FFFFFF;
  }

  /* ── Sélecteur de thème flottant ── */
  .theme-switcher {
    position: fixed; bottom: 28px; right: 28px;
    z-index: 8000;
    display: flex; flex-direction: column; align-items: flex-end; gap: 10px;
  }
  .theme-toggle-btn {
    width: 44px; height: 44px; border-radius: 50%;
    background: var(--vert); color: var(--blanc);
    border: none; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    transition: transform 200ms, background 200ms;
    font-size: 18px;
  }
  .theme-toggle-btn:hover { transform: scale(1.1) rotate(30deg); }
  .theme-options {
    display: flex; flex-direction: column; gap: 8px;
    opacity: 0; pointer-events: none;
    transform: translateY(8px) scale(0.96);
    transition: opacity 200ms, transform 200ms;
  }
  .theme-options.open {
    opacity: 1; pointer-events: all;
    transform: translateY(0) scale(1);
  }
  .theme-btn {
    display: flex; align-items: center; gap: 10px;
    background: var(--blanc); border: 2px solid var(--gris-bord);
    border-radius: 24px; padding: 6px 14px 6px 8px;
    cursor: pointer; font-size: 13px; font-weight: 600;
    color: var(--noir); white-space: nowrap;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: border-color 150ms, transform 150ms;
  }
  .theme-btn:hover { transform: translateX(-4px); }
  .theme-btn.active { border-color: var(--vert); }
  .theme-swatch {
    width: 20px; height: 20px; border-radius: 50%;
    flex-shrink: 0; border: 2px solid rgba(0,0,0,0.1);
  }
  html { scroll-behavior: smooth; }
  body {
    font-family: 'Inter', system-ui, sans-serif;
    color: var(--noir);
    background: var(--blanc);
    font-size: 16px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }
  h1,h2,h3,h4 { font-family: 'Newsreader', Georgia, serif; line-height: 1.2; }
  a { color: inherit; text-decoration: none; }
  img { max-width: 100%; }

  /* Navbar */
  .nav {
    position: sticky; top: 0; z-index: 50;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--gris-bord);
    padding: 0 24px;
  }
  .nav-inner {
    max-width: 1100px; margin: 0 auto;
    display: flex; align-items: center; justify-content: space-between;
    height: 64px;
  }
  .nav-logo {
    display: flex; align-items: center; gap: 10px;
    font-family: 'Newsreader', serif; font-size: 22px; font-weight: 700;
    color: var(--vert); letter-spacing: -0.5px;
  }
  .nav-logo svg { flex-shrink: 0; }
  .nav-links {
    display: flex; align-items: center; gap: 32px;
    list-style: none;
  }
  .nav-links a {
    font-size: 14px; font-weight: 500; color: var(--gris);
    transition: color 150ms;
  }
  .nav-links a:hover { color: var(--vert); }
  .btn-nav {
    background: var(--vert); color: var(--blanc);
    padding: 9px 20px; border-radius: 6px;
    font-size: 14px; font-weight: 600;
    transition: background 150ms;
    cursor: pointer; display: inline-block;
  }
  .btn-nav:hover { background: var(--vert-light); }
  .nav-burger { display: none; cursor: pointer; flex-direction: column; gap: 5px; }
  .nav-burger span { display: block; width: 24px; height: 2px; background: var(--noir); border-radius: 2px; }

  /* Buttons */
  .btn-primary {
    background: var(--ambre); color: var(--blanc);
    padding: 14px 28px; border-radius: 6px;
    font-size: 15px; font-weight: 600; border: none;
    cursor: pointer; display: inline-block;
    transition: background 150ms, transform 150ms;
  }
  .btn-primary:hover { background: var(--ambre-hover); transform: translateY(-1px); }
  .btn-secondary {
    background: transparent; color: var(--vert);
    padding: 14px 28px; border-radius: 6px;
    font-size: 15px; font-weight: 600;
    border: 2px solid var(--vert);
    cursor: pointer; display: inline-block;
    transition: background 150ms, color 150ms;
  }
  .btn-secondary:hover { background: var(--vert); color: var(--blanc); }

  /* Container */
  .container { max-width: 1100px; margin: 0 auto; padding: 0 24px; }

  /* Section spacing */
  .section { padding: 96px 0; }
  .section-sm { padding: 64px 0; }

  /* Section label */
  .section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: var(--ambre);
    margin-bottom: 12px; display: block;
  }
  .section-title {
    font-size: clamp(28px, 4vw, 42px);
    font-weight: 700; color: var(--noir);
    margin-bottom: 16px; line-height: 1.15;
  }
  .section-sub {
    font-size: 18px; color: var(--gris);
    max-width: 560px; line-height: 1.7;
  }

  /* Hero */
  .hero {
    background: var(--vert);
    padding: 100px 0 80px;
    position: relative; overflow: hidden;
  }
  .hero::before {
    content: "";
    position: absolute; top: -200px; right: -200px;
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(255,255,255,0.04) 0%, transparent 70%);
    pointer-events: none;
  }
  .hero-content { position: relative; z-index: 1; }
  .hero-tag {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.9); border-radius: 100px;
    padding: 6px 14px; font-size: 13px; font-weight: 500;
    margin-bottom: 28px;
  }
  .hero-tag span { width: 6px; height: 6px; background: #4ADE80; border-radius: 50%; display: inline-block; }
  .hero h1 {
    font-family: 'Newsreader', serif;
    font-size: clamp(38px, 6vw, 68px);
    font-weight: 700; color: var(--blanc);
    line-height: 1.08; letter-spacing: -1.5px;
    max-width: 760px; margin-bottom: 24px;
  }
  .hero h1 em { font-style: normal; color: #86EFAC; }
  .hero-sub {
    font-size: 18px; color: rgba(255,255,255,0.75);
    max-width: 520px; line-height: 1.7; margin-bottom: 40px;
  }
  .hero-actions { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 64px; }
  .hero-btn-primary {
    background: var(--ambre); color: var(--blanc);
    padding: 16px 32px; border-radius: 6px;
    font-size: 15px; font-weight: 700; border: none;
    cursor: pointer; display: inline-block;
    transition: background 150ms, transform 150ms;
    white-space: nowrap;
  }
  .hero-btn-primary:hover { background: var(--ambre-hover); transform: translateY(-1px); }
  .hero-btn-secondary {
    background: rgba(255,255,255,0.1); color: var(--blanc);
    padding: 16px 32px; border-radius: 6px;
    font-size: 15px; font-weight: 600;
    border: 1px solid rgba(255,255,255,0.25);
    cursor: pointer; display: inline-block;
    transition: background 150ms;
    white-space: nowrap;
  }
  .hero-btn-secondary:hover { background: rgba(255,255,255,0.18); }

  /* Stats bar */
  .stats-bar {
    display: grid; grid-template-columns: repeat(4, 1fr);
    border-top: 1px solid rgba(255,255,255,0.15);
    padding-top: 40px; gap: 24px;
  }
  .stat-item { }
  .stat-number {
    font-family: 'Newsreader', serif;
    font-size: 36px; font-weight: 700;
    color: var(--blanc); letter-spacing: -1px;
    display: block; line-height: 1;
  }
  .stat-number em { font-style: normal; color: #86EFAC; }
  .stat-label {
    font-size: 13px; color: rgba(255,255,255,0.6);
    margin-top: 6px; display: block; line-height: 1.4;
  }

  /* How it works */
  .steps-grid {
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 2px; background: var(--gris-bord);
    border: 1px solid var(--gris-bord); border-radius: 12px;
    overflow: hidden; margin-top: 56px;
  }
  .step-card {
    background: var(--blanc); padding: 40px;
    position: relative;
  }
  .step-card:hover { background: var(--gris-pale); }
  .step-num {
    font-family: 'Newsreader', serif;
    font-size: 72px; font-weight: 700;
    color: var(--vert-pale); line-height: 1;
    margin-bottom: 16px; letter-spacing: -3px;
    user-select: none;
  }
  .step-title {
    font-family: 'Newsreader', serif;
    font-size: 20px; font-weight: 600; color: var(--noir);
    margin-bottom: 8px;
  }
  .step-desc { font-size: 14px; color: var(--gris); line-height: 1.65; }

  /* ROI section */
  .roi-section { background: var(--beige); }
  .roi-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 80px; align-items: center;
  }
  .roi-quote {
    font-family: 'Newsreader', serif;
    font-size: clamp(22px, 3vw, 30px);
    font-weight: 500; color: var(--vert); line-height: 1.4;
    font-style: italic;
  }
  .roi-quote::before { content: "“"; }
  .roi-quote::after { content: "”"; }
  .roi-items { display: flex; flex-direction: column; gap: 28px; }
  .roi-item { display: flex; gap: 20px; align-items: flex-start; }
  .roi-icon {
    width: 44px; height: 44px; flex-shrink: 0;
    background: var(--vert); border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
  }
  .roi-item-title { font-size: 16px; font-weight: 600; color: var(--noir); margin-bottom: 4px; }
  .roi-item-desc { font-size: 14px; color: var(--gris); line-height: 1.6; }

  /* Pricing */
  .pricing-grid {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 24px; margin-top: 56px;
  }
  .price-card {
    border: 2px solid var(--gris-bord); border-radius: 12px;
    padding: 32px 28px; background: var(--blanc);
    display: flex; flex-direction: column;
    transition: box-shadow 200ms, border-color 200ms;
  }
  .price-card:hover { box-shadow: 0 8px 32px rgba(0,0,0,0.08); }
  .price-card.featured {
    border-color: var(--vert); background: var(--vert);
    color: var(--blanc); position: relative;
  }
  .price-badge {
    position: absolute; top: -13px; left: 50%; transform: translateX(-50%);
    background: var(--ambre); color: var(--blanc);
    font-size: 11px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; padding: 4px 14px; border-radius: 100px;
    white-space: nowrap;
  }
  .price-name {
    font-size: 13px; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--gris);
    margin-bottom: 8px;
  }
  .price-card.featured .price-name { color: rgba(255,255,255,0.65); }
  .price-amount {
    font-family: 'Newsreader', serif;
    font-size: 48px; font-weight: 700; letter-spacing: -2px;
    line-height: 1; color: var(--noir); margin-bottom: 4px;
  }
  .price-card.featured .price-amount { color: var(--blanc); }
  .price-period { font-size: 14px; color: var(--gris); margin-bottom: 24px; }
  .price-card.featured .price-period { color: rgba(255,255,255,0.6); }
  .price-desc { font-size: 14px; color: var(--gris); margin-bottom: 24px; line-height: 1.6; }
  .price-card.featured .price-desc { color: rgba(255,255,255,0.75); }
  .price-features { list-style: none; margin-bottom: 32px; flex: 1; }
  .price-features li {
    font-size: 14px; padding: 9px 0;
    border-bottom: 1px solid var(--gris-bord);
    display: flex; align-items: flex-start; gap: 10px; color: var(--noir);
  }
  .price-card.featured .price-features li {
    border-bottom-color: rgba(255,255,255,0.15); color: rgba(255,255,255,0.9);
  }
  .price-features li svg { flex-shrink: 0; margin-top: 2px; }
  .price-cta {
    display: block; text-align: center;
    padding: 13px 20px; border-radius: 6px;
    font-size: 14px; font-weight: 700;
    background: var(--vert-pale); color: var(--vert);
    border: none; cursor: pointer;
    transition: background 150ms;
  }
  .price-cta:hover { background: #d5e8df; }
  .price-card.featured .price-cta {
    background: var(--ambre); color: var(--blanc);
  }
  .price-card.featured .price-cta:hover { background: var(--ambre-hover); }

  /* Form section */
  .form-section { background: var(--gris-pale); }
  .form-wrap {
    max-width: 680px; margin: 0 auto;
    background: var(--blanc); border-radius: 16px;
    padding: 48px; box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    border: 1px solid var(--gris-bord);
  }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .form-full { grid-column: 1 / -1; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group label {
    font-size: 13px; font-weight: 600; color: var(--noir);
  }
  .form-group input, .form-group select, .form-group textarea {
    padding: 11px 14px; border: 1.5px solid var(--gris-bord);
    border-radius: 6px; font-size: 14px; font-family: inherit;
    color: var(--noir); background: var(--blanc);
    transition: border-color 150ms, box-shadow 150ms;
    width: 100%;
  }
  .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
    outline: none; border-color: var(--vert);
    box-shadow: 0 0 0 3px rgba(30,77,58,0.1);
  }
  .form-group textarea { resize: vertical; min-height: 120px; }
  .form-submit {
    width: 100%; padding: 16px; border-radius: 6px;
    background: var(--vert); color: var(--blanc);
    font-size: 15px; font-weight: 700; border: none;
    cursor: pointer; transition: background 150ms, transform 150ms;
    margin-top: 8px;
  }
  .form-submit:hover { background: var(--vert-light); transform: translateY(-1px); }
  .form-submit:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
  .form-disclaimer {
    font-size: 12px; color: var(--gris);
    text-align: center; margin-top: 14px; line-height: 1.6;
  }

  /* About page */
  .about-hero { background: var(--vert); padding: 80px 0 64px; }
  .about-hero h1 { font-family: 'Newsreader', serif; font-size: clamp(36px,5vw,54px); font-weight:700; color:var(--blanc); line-height:1.1; }
  .about-hero p { font-size:18px; color:rgba(255,255,255,0.75); margin-top:16px; max-width:560px; }
  .values-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:24px; margin-top:48px; }
  .value-card { background:var(--blanc); border:1px solid var(--gris-bord); border-radius:12px; padding:28px; }
  .value-icon { width:40px; height:40px; background:var(--vert-pale); border-radius:8px; display:flex; align-items:center; justify-content:center; margin-bottom:16px; }
  .value-title { font-family:'Newsreader',serif; font-size:18px; font-weight:600; color:var(--noir); margin-bottom:8px; }
  .value-desc { font-size:14px; color:var(--gris); line-height:1.65; }
  .compare-table { width:100%; border-collapse:collapse; margin-top:32px; }
  .compare-table th { text-align:left; padding:12px 16px; background:var(--gris-pale); font-size:13px; font-weight:700; border:1px solid var(--gris-bord); }
  .compare-table td { padding:12px 16px; border:1px solid var(--gris-bord); font-size:14px; }
  .compare-table tr:nth-child(even) td { background:var(--gris-pale); }
  .check { color:#16A34A; font-weight:700; }
  .cross { color:#DC2626; font-weight:700; }

  /* Contact page */
  .contact-grid { display:grid; grid-template-columns:1fr 2fr; gap:64px; align-items:start; }
  .contact-info h3 { font-family:'Newsreader',serif; font-size:22px; font-weight:600; color:var(--noir); margin-bottom:24px; }
  .contact-item { display:flex; gap:14px; align-items:flex-start; margin-bottom:20px; }
  .contact-icon { width:38px; height:38px; background:var(--vert-pale); border-radius:8px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
  .contact-item-title { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:var(--gris); margin-bottom:4px; }
  .contact-item-val { font-size:14px; color:var(--noir); line-height:1.5; }

  /* Merci page */
  .merci-page { min-height: 80vh; display:flex; align-items:center; justify-content:center; text-align:center; }
  .merci-wrap { max-width:520px; }
  .merci-icon { width:72px; height:72px; background:var(--vert); border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 32px; }
  .merci-title { font-family:'Newsreader',serif; font-size:clamp(28px,4vw,38px); font-weight:700; color:var(--vert); margin-bottom:16px; }
  .merci-sub { font-size:17px; color:var(--gris); line-height:1.7; margin-bottom:32px; }
  .merci-back { display:inline-block; padding:12px 28px; background:var(--vert); color:var(--blanc); border-radius:6px; font-weight:600; font-size:14px; cursor:pointer; }
  .merci-back:hover { background:var(--vert-light); }

  /* 404 */
  .page-404 { min-height:80vh; display:flex; align-items:center; justify-content:center; text-align:center; }
  .page-404-num { font-family:'Newsreader',serif; font-size:120px; font-weight:700; color:var(--vert-pale); line-height:1; }
  .page-404 h2 { font-family:'Newsreader',serif; font-size:28px; color:var(--vert); margin-bottom:12px; }
  .page-404 p { color:var(--gris); margin-bottom:32px; }

  /* Footer */
  .footer { background:var(--noir); color:rgba(255,255,255,0.7); padding:56px 0 32px; }
  .footer-grid { display:grid; grid-template-columns:2fr 1fr 1fr; gap:48px; margin-bottom:48px; }
  .footer-brand { font-family:'Newsreader',serif; font-size:22px; font-weight:700; color:var(--blanc); margin-bottom:12px; }
  .footer-tagline { font-size:14px; line-height:1.7; }
  .footer-col h4 { font-size:12px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:rgba(255,255,255,0.45); margin-bottom:16px; }
  .footer-col ul { list-style:none; }
  .footer-col li { margin-bottom:10px; }
  .footer-col a { font-size:14px; color:rgba(255,255,255,0.65); transition:color 150ms; }
  .footer-col a:hover { color:var(--blanc); }
  .footer-bottom { border-top:1px solid rgba(255,255,255,0.1); padding-top:24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; }
  .footer-bottom p { font-size:13px; }

  /* ── ANIMATIONS (Motion-Driven, Editorial Grid guidelines) ── */

  /* Scroll-reveal: éléments cachés initialement */
  .reveal {
    opacity: 0;
    transform: translateY(28px);
    transition: opacity 420ms cubic-bezier(.22,1,.36,1),
                transform 420ms cubic-bezier(.22,1,.36,1);
    will-change: transform, opacity;
  }
  .reveal.visible {
    opacity: 1;
    transform: translateY(0);
  }
  /* Délais en cascade pour les grilles */
  .reveal-delay-1 { transition-delay: 80ms; }
  .reveal-delay-2 { transition-delay: 160ms; }
  .reveal-delay-3 { transition-delay: 240ms; }
  .reveal-delay-4 { transition-delay: 320ms; }

  /* Fade-in latéral pour le hero */
  .reveal-left {
    opacity: 0;
    transform: translateX(-24px);
    transition: opacity 500ms cubic-bezier(.22,1,.36,1),
                transform 500ms cubic-bezier(.22,1,.36,1);
    will-change: transform, opacity;
  }
  .reveal-left.visible { opacity: 1; transform: translateX(0); }

  /* Counter animation pour les stats */
  .stat-number[data-count] { display: block; }

  /* Step cards : lift au hover (transform seul, perf OK) */
  .step-card {
    transition: transform 250ms ease, background 250ms ease;
    cursor: default;
  }
  .step-card:hover {
    transform: translateY(-4px);
    background: var(--gris-pale);
    box-shadow: 0 12px 40px rgba(30,77,58,0.08);
  }

  /* Price card lift */
  .price-card {
    transition: transform 250ms ease, box-shadow 250ms ease, border-color 250ms ease;
  }
  .price-card:hover { transform: translateY(-6px); box-shadow: 0 16px 48px rgba(0,0,0,0.1); }
  .price-card.featured:hover { box-shadow: 0 16px 48px rgba(30,77,58,0.25); }

  /* Underline animé sur les liens de nav */
  .nav-links a {
    position: relative;
  }
  .nav-links a::after {
    content: "";
    position: absolute; bottom: -2px; left: 0;
    width: 0; height: 2px;
    background: var(--vert);
    transition: width 200ms ease;
  }
  .nav-links a:hover::after { width: 100%; }

  /* Pulsation légère sur le badge "pilote actif" */
  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: .6; transform: scale(1.4); }
  }
  .hero-tag span { animation: pulse-dot 2s ease-in-out infinite; }

  /* Section hero : shimmer sur le titre */
  @keyframes shimmer-in {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .hero h1   { animation: shimmer-in 700ms cubic-bezier(.22,1,.36,1) both; }
  .hero-sub  { animation: shimmer-in 700ms 120ms cubic-bezier(.22,1,.36,1) both; }
  .hero-actions { animation: shimmer-in 700ms 240ms cubic-bezier(.22,1,.36,1) both; }
  .stats-bar { animation: shimmer-in 700ms 360ms cubic-bezier(.22,1,.36,1) both; }

  /* ROI items : trait gauche animé */
  .roi-item { transition: transform 200ms ease; }
  .roi-item:hover { transform: translateX(6px); }

  /* Bouton CTA : shimmer de lumière au hover */
  @keyframes btn-shine {
    from { background-position: -200% center; }
    to   { background-position: 200% center; }
  }
  .hero-btn-primary:hover, .btn-primary:hover {
    background-image: linear-gradient(90deg, var(--ambre) 40%, #f59e0b 50%, var(--ambre) 60%);
    background-size: 200% auto;
    animation: btn-shine 600ms linear;
  }

  /* ── Kinetic Typography keyframes (DB: Kinetic Typography style) ── */
  @keyframes wordUp {
    to { transform: translateY(0); }
  }

  /* ── Floating orbs décoratifs dans le hero (parallax layer 1) ── */
  .hero-orb {
    position: absolute; border-radius: 50%;
    pointer-events: none; will-change: transform;
  }
  .hero-orb-1 {
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(134,239,172,0.12) 0%, transparent 70%);
    top: -100px; right: -80px;
    animation: orbFloat 8s ease-in-out infinite;
  }
  .hero-orb-2 {
    width: 250px; height: 250px;
    background: radial-gradient(circle, rgba(217,119,6,0.08) 0%, transparent 70%);
    bottom: 40px; left: 10%;
    animation: orbFloat 12s ease-in-out infinite reverse;
  }
  @keyframes orbFloat {
    0%,100% { transform: translateY(0) scale(1); }
    50%      { transform: translateY(-24px) scale(1.04); }
  }

  /* ── Gradient text animé sur le hero ── */
  @keyframes gradShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  .hero h1 em {
    background: linear-gradient(90deg, #86EFAC, #4ADE80, #D97706, #86EFAC);
    background-size: 300% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradShift 4s ease infinite;
    font-style: normal;
  }

  /* ── Ligne animée sous la section-label ── */
  .section-label {
    position: relative; display: inline-block;
  }
  .section-label::after {
    content: '';
    position: absolute; bottom: -4px; left: 0;
    width: 0; height: 2px; background: var(--ambre);
    transition: width 600ms 200ms ease;
  }
  .section-label.visible::after { width: 100%; }

  /* ── Step number glow au hover ── */
  .step-card:hover .step-num {
    color: rgba(30,77,58,0.25);
    text-shadow: 0 0 40px rgba(30,77,58,0.15);
    transition: color 300ms, text-shadow 300ms;
  }

  /* ── Price card featured : border glow animé ── */
  @keyframes borderGlow {
    0%,100% { box-shadow: 0 0 0 0 rgba(30,77,58,0); }
    50%      { box-shadow: 0 0 32px 4px rgba(30,77,58,0.2); }
  }
  .price-card.featured {
    animation: borderGlow 3s ease-in-out infinite;
  }

  /* ── Scroll progress bar ── */
  /* (injecté via JS) */

  /* Respect prefers-reduced-motion (guideline db: CRITICAL) */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
    .reveal, .reveal-left { opacity: 1; transform: none; }
    .hero h1 em { -webkit-text-fill-color: #86EFAC; }
  }

  /* ── Canvas particles dans le hero ── */
  #hero-canvas {
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    pointer-events: none; z-index: 0;
    opacity: 0.45;
  }

  /* ── Ticker strip défilant ── */
  .ticker-wrap {
    background: var(--vert); color: rgba(255,255,255,0.85);
    overflow: hidden; white-space: nowrap;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    height: 36px; display: flex; align-items: center;
  }
  .ticker-track {
    display: inline-flex; gap: 0;
    animation: tickerScroll 38s linear infinite;
  }
  .ticker-wrap:hover .ticker-track { animation-play-state: paused; }
  .ticker-item {
    font-size: 12px; font-weight: 500; letter-spacing: 0.3px;
    padding: 0 40px; display: inline-flex; align-items: center; gap: 8px;
  }
  .ticker-dot { width: 5px; height: 5px; border-radius: 50%; background: #4ADE80; display: inline-block; flex-shrink: 0; }
  @keyframes tickerScroll {
    from { transform: translateX(0); }
    to   { transform: translateX(-50%); }
  }
  @media (prefers-reduced-motion: reduce) {
    .ticker-track { animation: none; }
  }

  /* ── Page aide ── */
  .aide-hero { background: var(--vert); padding: 64px 0 48px; }
  .aide-hero h1 { font-family:'Newsreader',serif; font-size:clamp(28px,4vw,44px); font-weight:700; color:var(--blanc); line-height:1.15; margin-bottom:16px; }
  .aide-meta { display:flex; flex-wrap:wrap; gap:12px; margin-top:20px; }
  .aide-badge {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.25);
    color:rgba(255,255,255,0.9); border-radius:100px;
    padding:5px 14px; font-size:12px; font-weight:600;
  }
  .aide-body { padding: 64px 0; }
  .aide-grid { display:grid; grid-template-columns:2fr 1fr; gap:56px; align-items:start; }
  .aide-desc { font-size:16px; color:var(--gris); line-height:1.8; }
  .aide-sidebar { background:var(--gris-pale); border:1px solid var(--gris-bord); border-radius:12px; padding:28px; }
  .aide-sidebar h3 { font-family:'Newsreader',serif; font-size:18px; font-weight:600; color:var(--noir); margin-bottom:20px; }
  .aide-info-row { display:flex; justify-content:space-between; align-items:flex-start; padding:10px 0; border-bottom:1px solid var(--gris-bord); font-size:14px; }
  .aide-info-row:last-child { border-bottom:none; }
  .aide-info-label { color:var(--gris); font-weight:500; }
  .aide-info-val { color:var(--noir); font-weight:600; text-align:right; max-width:60%; }
  .aide-cta-btn { display:block; text-align:center; padding:14px 20px; background:var(--ambre); color:var(--blanc); border-radius:6px; font-weight:700; font-size:14px; margin-top:20px; transition:background 150ms; }
  .aide-cta-btn:hover { background:var(--ambre-hover); }
  @media(max-width:768px){ .aide-grid{ grid-template-columns:1fr; } }

  /* Alerts */
  .alert { padding:12px 16px; border-radius:6px; font-size:14px; margin-bottom:16px; display:none; }
  .alert-error { background:#FEE2E2; color:#991B1B; border:1px solid #FECACA; }
  .alert-success { background:#DCFCE7; color:#166534; border:1px solid #BBF7D0; }

  /* Responsive */
  @media (max-width:768px) {
    .nav-links { display:none; }
    .nav-burger { display:flex; }
    .stats-bar { grid-template-columns:repeat(2,1fr); }
    .steps-grid { grid-template-columns:1fr; }
    .roi-grid { grid-template-columns:1fr; gap:40px; }
    .pricing-grid { grid-template-columns:1fr; max-width:400px; margin-left:auto; margin-right:auto; }
    .form-grid { grid-template-columns:1fr; }
    .footer-grid { grid-template-columns:1fr; }
    .contact-grid { grid-template-columns:1fr; }
    .values-grid { grid-template-columns:1fr; }
    .hero-actions { flex-direction:column; }
    .hero-btn-primary, .hero-btn-secondary { text-align:center; }
    .section { padding:64px 0; }
  }
</style>
"""

JS_ANIMATIONS = """
<script>
(function() {
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── 1. CANVAS PARTICLES dans le hero ── */
  (function(){
    var canvas = document.getElementById('hero-canvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var particles = [];
    function resize(){ canvas.width=canvas.offsetWidth; canvas.height=canvas.offsetHeight; }
    resize();
    window.addEventListener('resize', resize, {passive:true});
    for(var i=0;i<55;i++){
      particles.push({
        x: Math.random()*canvas.width,
        y: Math.random()*canvas.height,
        r: Math.random()*2+0.5,
        dx: (Math.random()-0.5)*0.35,
        dy: (Math.random()-0.5)*0.35,
        alpha: Math.random()*0.5+0.2
      });
    }
    function draw(){
      ctx.clearRect(0,0,canvas.width,canvas.height);
      particles.forEach(function(p){
        p.x+=p.dx; p.y+=p.dy;
        if(p.x<0)p.x=canvas.width; if(p.x>canvas.width)p.x=0;
        if(p.y<0)p.y=canvas.height; if(p.y>canvas.height)p.y=0;
        ctx.beginPath();
        ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
        ctx.fillStyle='rgba(134,239,172,'+p.alpha+')';
        ctx.fill();
      });
      /* lignes entre particules proches */
      for(var a=0;a<particles.length;a++){
        for(var b=a+1;b<particles.length;b++){
          var dx=particles[a].x-particles[b].x, dy=particles[a].y-particles[b].y;
          var dist=Math.sqrt(dx*dx+dy*dy);
          if(dist<90){
            ctx.beginPath();
            ctx.moveTo(particles[a].x,particles[a].y);
            ctx.lineTo(particles[b].x,particles[b].y);
            ctx.strokeStyle='rgba(134,239,172,'+(0.12*(1-dist/90))+')';
            ctx.lineWidth=0.6;
            ctx.stroke();
          }
        }
      }
      if(!reduced) requestAnimationFrame(draw);
    }
    if(!reduced) draw();
    else { /* dessine une frame statique */ draw(); }
  })();

  /* ── 2. SPLIT TEXT — Kinetic Typography sur le hero h1 ── */
  if (!reduced) {
    var h1 = document.querySelector('.hero h1');
    if (h1) {
      var words = h1.innerHTML.split(' ');
      h1.innerHTML = words.map(function(w,i){
        return '<span class="word" style="display:inline-block;overflow:hidden;margin-right:0.22em"><span class="word-inner" style="display:inline-block;transform:translateY(110%);animation:wordUp 700ms '+((i*80)+80)+'ms cubic-bezier(.22,1,.36,1) forwards">'+w+'</span></span>';
      }).join(' ');
    }
  }

  /* ── 3. SCROLL REVEAL (Intersection Observer) ── */
  var io = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -48px 0px' });
  document.querySelectorAll('.reveal, .reveal-left').forEach(function(el){ io.observe(el); });

  /* ── 4. PARALLAX multi-couches sur le hero ── */
  if (!reduced) {
    var hero = document.querySelector('.hero');
    var heroBg = document.querySelector('.hero-parallax-bg');
    var heroTag = document.querySelector('.hero-tag');
    window.addEventListener('scroll', function(){
      var sy = window.scrollY;
      if (hero && sy < window.innerHeight * 1.5) {
        if (heroBg) heroBg.style.transform = 'translateY('+sy*0.35+'px)';
        if (heroTag) heroTag.style.transform = 'translateY('+sy*0.08+'px)';
        var hc = hero.querySelector('.hero-content');
        if (hc) hc.style.transform = 'translateY('+sy*0.18+'px)';
      }
    }, { passive: true });
  }

  /* ── 5. MAGNETIC BUTTONS ── */
  if (!reduced && window.innerWidth > 768) {
    document.querySelectorAll('.hero-btn-primary,.hero-btn-secondary,.btn-nav,.price-cta').forEach(function(btn){
      btn.addEventListener('mousemove',function(e){
        var r=btn.getBoundingClientRect();
        var dx=(e.clientX-r.left-r.width/2)*0.22;
        var dy=(e.clientY-r.top-r.height/2)*0.22;
        btn.style.transform='translate('+dx+'px,'+dy+'px) scale(1.04)';
      });
      btn.addEventListener('mouseleave',function(){
        btn.style.transform='translate(0,0) scale(1)';
        btn.style.transition='transform 400ms cubic-bezier(.22,1,.36,1)';
      });
      btn.addEventListener('mouseenter',function(){
        btn.style.transition='transform 100ms ease';
      });
    });
  }

  /* ── 6. COUNTER animation sur les stats ── */
  document.querySelectorAll('.stat-number[data-count]').forEach(function(el) {
    var target = parseInt(el.dataset.count, 10);
    var suffix = el.dataset.suffix || '';
    var duration = reduced ? 0 : 1600;
    var start = null;
    function step(ts) {
      if (!start) start = ts;
      var pct = Math.min((ts - start) / duration, 1);
      var ease = 1 - Math.pow(1 - pct, 3);
      el.textContent = Math.round(ease * target) + suffix;
      if (pct < 1) requestAnimationFrame(step);
      else el.textContent = target + suffix;
    }
    if (duration === 0) { el.textContent = target + suffix; return; }
    var obs2 = new IntersectionObserver(function(ent) {
      if (ent[0].isIntersecting) { requestAnimationFrame(step); obs2.disconnect(); }
    }, { threshold: 0.5 });
    obs2.observe(el);
  });

  /* ── 7. TYPING EFFECT sur le hero-sub ── */
  if (!reduced) {
    var sub = document.querySelector('.hero-sub');
    if (sub) {
      var txt = sub.textContent;
      sub.textContent = '';
      sub.style.opacity = '1';
      sub.style.animation = 'none';
      var i = 0;
      setTimeout(function type(){
        if (i <= txt.length) {
          sub.textContent = txt.slice(0, i);
          i++;
          setTimeout(type, i < 20 ? 30 : 18);
        }
      }, 900);
    }
  }

  /* ── 8. PAGE TRANSITION (fade out au clic de lien) ── */
  if (!reduced) {
    var overlay = document.createElement('div');
    overlay.style.cssText='position:fixed;inset:0;background:var(--vert);z-index:9000;opacity:0;pointer-events:none;transition:opacity 350ms ease';
    document.body.appendChild(overlay);
    document.querySelectorAll('a[href]').forEach(function(a){
      var href = a.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('mailto') || href.startsWith('tel') || href.startsWith('http')) return;
      a.addEventListener('click',function(e){
        e.preventDefault();
        overlay.style.opacity='1';
        overlay.style.pointerEvents='all';
        setTimeout(function(){ window.location.href=href; }, 340);
      });
    });
    window.addEventListener('pageshow',function(){
      overlay.style.opacity='0';
      overlay.style.pointerEvents='none';
    });
  }

  /* ── 9. STAGGER sur les step-cards au scroll ── */
  if (!reduced) {
    var steps = document.querySelectorAll('.step-card');
    if (steps.length) {
      steps.forEach(function(el,i){
        el.style.opacity='0';
        el.style.transform='translateY(40px)';
        el.style.transition='opacity 500ms '+(i*100+80)+'ms cubic-bezier(.22,1,.36,1), transform 500ms '+(i*100+80)+'ms cubic-bezier(.22,1,.36,1)';
      });
      var stepsObs = new IntersectionObserver(function(entries){
        entries.forEach(function(e){
          if(e.isIntersecting){
            e.target.style.opacity='1';
            e.target.style.transform='translateY(0)';
            stepsObs.unobserve(e.target);
          }
        });
      },{threshold:0.15});
      steps.forEach(function(el){ stepsObs.observe(el); });
    }
  }

  /* ── 10. SCROLL PROGRESS BAR en haut de page ── */
  if (!reduced) {
    var bar = document.createElement('div');
    bar.style.cssText='position:fixed;top:0;left:0;height:3px;width:0%;background:linear-gradient(90deg,var(--vert),var(--ambre));z-index:9999;transition:width 80ms linear';
    document.body.appendChild(bar);
    window.addEventListener('scroll',function(){
      var pct=(window.scrollY/(document.documentElement.scrollHeight-window.innerHeight))*100;
      bar.style.width=Math.min(pct,100)+'%';
    },{passive:true});
  }

  /* ── 11. SÉLECTEUR DE THÈME ── */
  (function(){
    var themes = [
      {key:'vert',    label:'Vert Wallonie', c1:'#1E4D3A', c2:'#D97706'},
      {key:'marine',  label:'Marine & Or',   c1:'#1B3B6F', c2:'#C9960C'},
      {key:'ardoise', label:'Ardoise & Terracotta', c1:'#334155', c2:'#C2542A'}
    ];
    var saved = localStorage.getItem('gh-theme') || 'vert';
    document.documentElement.setAttribute('data-theme', saved);

    var sw = document.createElement('div');
    sw.className = 'theme-switcher';
    var opts = document.createElement('div');
    opts.className = 'theme-options';

    themes.forEach(function(t){
      var btn = document.createElement('button');
      btn.className = 'theme-btn' + (saved===t.key?' active':'');
      btn.innerHTML = '<span class="theme-swatch" style="background:linear-gradient(135deg,'+t.c1+' 50%,'+t.c2+' 50%)"></span>'+t.label;
      btn.addEventListener('click',function(){
        document.documentElement.setAttribute('data-theme',t.key);
        localStorage.setItem('gh-theme',t.key);
        document.querySelectorAll('.theme-btn').forEach(function(b){b.classList.remove('active');});
        btn.classList.add('active');
        opts.classList.remove('open');
      });
      opts.appendChild(btn);
    });

    var toggleBtn = document.createElement('button');
    toggleBtn.className = 'theme-toggle-btn';
    toggleBtn.setAttribute('aria-label','Changer de thème');
    toggleBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="5" stroke="white" stroke-width="1.8"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M4.2 15.8l1.4-1.4M14.4 5.6l1.4-1.4" stroke="white" stroke-width="1.5" stroke-linecap="round"/></svg>';
    toggleBtn.addEventListener('click',function(e){
      e.stopPropagation();
      opts.classList.toggle('open');
    });
    document.addEventListener('click',function(){ opts.classList.remove('open'); });

    sw.appendChild(opts);
    sw.appendChild(toggleBtn);
    document.body.appendChild(sw);
  })();

})();
</script>
"""

SVG_CHECK = """<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="8" fill="#22C55E" opacity="0.15"/><path d="M5 8l2 2 4-4" stroke="#16A34A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>"""
SVG_CHECK_WHITE = """<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="8" fill="rgba(255,255,255,0.15)"/><path d="M5 8l2 2 4-4" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>"""
SVG_LOGO = """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="8" stroke="#1E4D3A" stroke-width="2.5"/><path d="M18 18L24 24" stroke="#1E4D3A" stroke-width="2.5" stroke-linecap="round"/><circle cx="12" cy="12" r="3" fill="#D97706"/></svg>"""
SVG_LOGO_WHITE = """<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="8" stroke="white" stroke-width="2.5"/><path d="M18 18L24 24" stroke="white" stroke-width="2.5" stroke-linecap="round"/><circle cx="12" cy="12" r="3" fill="#86EFAC"/></svg>"""

def navbar(active="accueil"):
    links = [("Accueil","/","accueil"),("À propos","/apropos","apropos"),("Contact","/contact","contact")]
    items = ""
    for label,href,key in links:
        style = "color:var(--vert);font-weight:700;" if key==active else ""
        items += f'<li><a href="{href}" style="{style}">{label}</a></li>'
    return f"""
<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="nav-logo">{SVG_LOGO} GrantHound</a>
    <ul class="nav-links">{items}
      <li><a href="/#inscription" class="btn-nav">Essai gratuit</a></li>
    </ul>
    <button class="nav-burger" onclick="document.getElementById('mob-menu').classList.toggle('open')" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
  </div>
  <div id="mob-menu" style="display:none;padding:16px 24px;border-top:1px solid var(--gris-bord);background:var(--blanc)">
    {" ".join(f'<a href="{href}" style="display:block;padding:10px 0;font-size:15px;font-weight:500;border-bottom:1px solid var(--gris-bord)">{label}</a>' for label,href,_ in links)}
    <a href="/#inscription" class="btn-nav" style="display:block;text-align:center;margin-top:16px">Essai gratuit</a>
  </div>
</nav>
<script>
  var m=document.getElementById('mob-menu');
  document.querySelector('.nav-burger').addEventListener('click',function(){{
    m.style.display=m.style.display==='none'?'block':'none';
  }});
</script>"""

def footer():
    return """
<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand">GrantHound</div>
        <p class="footer-tagline">Veille automatique de subsides pour les ASBL wallonnes.<br>220+ sources surveillées. Un email par semaine.</p>
      </div>
      <div class="footer-col">
        <h4>Navigation</h4>
        <ul>
          <li><a href="/">Accueil</a></li>
          <li><a href="/apropos">À propos</a></li>
          <li><a href="/contact">Contact</a></li>
          <li><a href="/#inscription">Essai gratuit</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Contact</h4>
        <ul>
          <li><a href="mailto:noahlatour77@gmail.com">noahlatour77@gmail.com</a></li>
          <li><a href="tel:+32491637689">0491 63 76 89</a></li>
          <li style="color:rgba(255,255,255,0.65);font-size:14px">Vielsalm, Province de Luxembourg</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2025 GrantHound &middot; Tous droits réservés</p>
      <p>Conçu pour la Wallonie &middot; Pilote gratuit en cours</p>
    </div>
  </div>
</footer>"""

# ── Pages HTML ─────────────────────────────────────────────────────────────────
def page_accueil():
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="GrantHound surveille 220+ sources de subsides et envoie chaque semaine les aides qui correspondent à votre ASBL wallonne.">
  <title>GrantHound — Veille automatique de subsides pour ASBL wallonnes</title>
  {FONTS}
  {CSS_BASE}
</head>
<body>

{navbar("accueil")}

<!-- TICKER STRIP -->
<div class="ticker-wrap" aria-hidden="true">
  <div class="ticker-track">
    <span class="ticker-item"><span class="ticker-dot"></span>Nouveau : subside MIDAS « Emploi et Inclusion » · deadline 30 juin 2025</span>
    <span class="ticker-item"><span class="ticker-dot"></span>FWB : appel à projets « Jeunesse &amp; Numérique » ouvert · max 15 000 €</span>
    <span class="ticker-item"><span class="ticker-dot"></span>Province de Liège : soutien aux ASBL culturelles · dépôt avant le 15 juillet</span>
    <span class="ticker-item"><span class="ticker-dot"></span>FEDER Wallonie : 220+ M€ disponibles pour les projets innovants 2025-2027</span>
    <span class="ticker-item"><span class="ticker-dot"></span>Nouveau : subside MIDAS « Emploi et Inclusion » · deadline 30 juin 2025</span>
    <span class="ticker-item"><span class="ticker-dot"></span>FWB : appel à projets « Jeunesse &amp; Numérique » ouvert · max 15 000 €</span>
    <span class="ticker-item"><span class="ticker-dot"></span>Province de Liège : soutien aux ASBL culturelles · dépôt avant le 15 juillet</span>
    <span class="ticker-item"><span class="ticker-dot"></span>FEDER Wallonie : 220+ M€ disponibles pour les projets innovants 2025-2027</span>
  </div>
</div>

<!-- HERO -->
<section class="hero">
  <canvas id="hero-canvas"></canvas>
  <div class="hero-parallax-bg" style="position:absolute;inset:0;pointer-events:none"></div>
  <div class="hero-orb hero-orb-1"></div>
  <div class="hero-orb hero-orb-2"></div>
  <div class="container hero-content">
    <div class="hero-tag"><span></span> Phase pilote · Accès gratuit</div>
    <h1>Les subsides que votre ASBL <em>rate</em> chaque mois.</h1>
    <p class="hero-sub">GrantHound surveille 220+ sources de financement wallonnes et vous envoie chaque semaine uniquement les aides qui correspondent à votre profil.</p>
    <div class="hero-actions">
      <a href="#inscription" class="hero-btn-primary">Recevoir mon premier rapport</a>
      <a href="#comment" class="hero-btn-secondary">Comment ça marche</a>
    </div>
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-number" data-count="220" data-suffix="+">220+</span>
        <span class="stat-label">Sources surveillées en continu</span>
      </div>
      <div class="stat-item">
        <span class="stat-number" data-count="5">5</span>
        <span class="stat-label">Niveaux de financement (MIDAS, FWB, provinces, Europe…)</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">1×</span>
        <span class="stat-label">Rapport personnalisé par semaine</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">0€</span>
        <span class="stat-label">Pendant le pilote · Sans carte</span>
      </div>
    </div>
  </div>
</section>

<!-- COMMENT ÇA MARCHE -->
<section class="section" id="comment">
  <div class="container">
    <span class="section-label reveal">Processus</span>
    <h2 class="section-title reveal reveal-delay-1">Simple comme un email</h2>
    <p class="section-sub reveal reveal-delay-2">Pas d'interface complexe. Pas de formation. Quatre étapes et vous recevez des alertes personnalisées.</p>
    <div class="steps-grid">
      <div class="step-card reveal reveal-delay-1">
        <div class="step-num">01</div>
        <div class="step-title">Décrivez votre structure</div>
        <p class="step-desc">Secteur, province, taille, type d'organisation. Deux minutes maximum. GrantHound construit votre profil de financement.</p>
      </div>
      <div class="step-card reveal reveal-delay-2">
        <div class="step-num">02</div>
        <div class="step-title">GrantHound surveille</div>
        <p class="step-desc">Notre moteur parcourt MIDAS Wallonie, la FWB, les quatre provinces, les fonds européens et 200+ autres sources — 24h/24.</p>
      </div>
      <div class="step-card reveal reveal-delay-3">
        <div class="step-num">03</div>
        <div class="step-title">Recevez les alertes</div>
        <p class="step-desc">Chaque semaine, un email clair : les aides qui correspondent à votre profil, avec les deadlines et les liens officiels. Rien d'autre.</p>
      </div>
      <div class="step-card reveal reveal-delay-4">
        <div class="step-num">04</div>
        <div class="step-title">Déposez les dossiers</div>
        <p class="step-desc">Vous choisissez, vous déposez. GrantHound ne fait pas le dossier à votre place — il vous assure de ne plus en rater un seul.</p>
      </div>
    </div>
  </div>
</section>

<!-- POURQUOI PAYER -->
<section class="section roi-section">
  <div class="container">
    <div class="roi-grid">
      <div class="reveal-left">
        <span class="section-label">Pourquoi 19€ / mois</span>
        <p class="roi-quote">Un subside moyen en Wallonie vaut entre 5&nbsp;000 et 50&nbsp;000&nbsp;€. En rater un seul coûte cent fois le prix d'un abonnement.</p>
        <p style="margin-top:24px;font-size:14px;color:var(--gris);line-height:1.7">Un consultant spécialisé en recherche de subsides facture 500 à 800€ la journée. GrantHound fait cette veille en continu, pour le prix d'un repas par mois.</p>
      </div>
      <div class="roi-items">
        <div class="roi-item reveal reveal-delay-1">
          <div class="roi-icon">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2v16M6 6h8M6 14h8" stroke="white" stroke-width="1.8" stroke-linecap="round"/></svg>
          </div>
          <div>
            <div class="roi-item-title">ROI dès le premier mois</div>
            <p class="roi-item-desc">Une seule alerte pertinente par an couvre 30+ années d'abonnement. Le calcul est simple.</p>
          </div>
        </div>
        <div class="roi-item reveal reveal-delay-2">
          <div class="roi-icon">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="white" stroke-width="1.8"/><path d="M10 7v3l2 2" stroke="white" stroke-width="1.8" stroke-linecap="round"/></svg>
          </div>
          <div>
            <div class="roi-item-title">Votre temps est précieux</div>
            <p class="roi-item-desc">Surveiller MIDAS manuellement prend 2 à 3 heures par semaine. GrantHound le fait pour vous, sans fatigue et sans oubli.</p>
          </div>
        </div>
        <div class="roi-item reveal reveal-delay-3">
          <div class="roi-icon">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10l4 4 8-8" stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div>
            <div class="roi-item-title">Toujours la source officielle</div>
            <p class="roi-item-desc">Chaque aide signalée pointe vers sa source officielle. Pas de synthèse approximative, pas d'intermédiaire.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- TARIFS -->
<section class="section" id="tarifs">
  <div class="container" style="text-align:center">
    <span class="section-label reveal">Tarifs</span>
    <h2 class="section-title reveal reveal-delay-1">Transparent, sans surprise</h2>
    <p class="section-sub reveal reveal-delay-2" style="margin:0 auto">Phase pilote actuellement gratuite pour les premiers inscrits.</p>
    <div class="pricing-grid">
      <!-- Veille -->
      <div class="price-card reveal reveal-delay-1">
        <div class="price-name">Veille</div>
        <div class="price-amount">19€</div>
        <div class="price-period">/ mois · après le pilote</div>
        <p class="price-desc">Pour les petites ASBL qui veulent ne plus rater aucune opportunité.</p>
        <ul class="price-features">
          <li>{SVG_CHECK} Surveillance 220+ sources</li>
          <li>{SVG_CHECK} 1 rapport email / semaine</li>
          <li>{SVG_CHECK} Matching sur votre profil</li>
          <li>{SVG_CHECK} Liens officiels inclus</li>
          <li>{SVG_CHECK} Désinscription en 1 clic</li>
        </ul>
        <a href="#inscription" class="price-cta">Démarrer gratuitement</a>
      </div>
      <!-- Pro -->
      <div class="price-card featured reveal reveal-delay-2">
        <div class="price-badge">Le plus populaire</div>
        <div class="price-name">Pro</div>
        <div class="price-amount">35€</div>
        <div class="price-period">/ mois · après le pilote</div>
        <p class="price-desc">Pour les ASBL actives avec plusieurs dossiers en cours et besoin de suivi.</p>
        <ul class="price-features">
          <li>{SVG_CHECK_WHITE} Tout de Veille</li>
          <li>{SVG_CHECK_WHITE} Alertes en temps réel (deadlines)</li>
          <li>{SVG_CHECK_WHITE} Matching étendu multi-profil</li>
          <li>{SVG_CHECK_WHITE} Historique 12 mois</li>
          <li>{SVG_CHECK_WHITE} Support prioritaire &lt;24h</li>
          <li>{SVG_CHECK_WHITE} Export PDF des rapports</li>
        </ul>
        <a href="#inscription" class="price-cta">Démarrer gratuitement</a>
      </div>
      <!-- Cabinet -->
      <div class="price-card reveal reveal-delay-3">
        <div class="price-name">Cabinet</div>
        <div class="price-amount">89€</div>
        <div class="price-period">/ mois · après le pilote</div>
        <p class="price-desc">Pour les bureaux qui accompagnent plusieurs ASBL et veulent un outil professionnel.</p>
        <ul class="price-features">
          <li>{SVG_CHECK} Tout de Pro</li>
          <li>{SVG_CHECK} Jusqu'à 10 profils clients</li>
          <li>{SVG_CHECK} Dashboard multi-organisations</li>
          <li>{SVG_CHECK} Rapports personnalisables</li>
          <li>{SVG_CHECK} Accès API (bêta)</li>
          <li>{SVG_CHECK} Support dédié téléphone</li>
        </ul>
        <a href="/contact" class="price-cta">Nous contacter</a>
      </div>
    </div>
  </div>
</section>

<!-- FORMULAIRE INSCRIPTION -->
<section class="section form-section" id="inscription">
  <div class="container">
    <div style="text-align:center;margin-bottom:48px">
      <span class="section-label">Inscription pilote</span>
      <h2 class="section-title">Recevez votre premier rapport</h2>
      <p class="section-sub" style="margin:0 auto">Gratuit pendant la phase pilote. Aucune carte bancaire requise.</p>
    </div>
    <div class="form-wrap">
      <div class="alert alert-error" id="form-error"></div>
      <div class="alert alert-success" id="form-success"></div>
      <form id="form-inscription">
        <div class="form-grid">
          <div class="form-group">
            <label for="nom">Nom de la structure *</label>
            <input type="text" id="nom" name="nom" placeholder="ASBL Les Amis du Quartier" required>
          </div>
          <div class="form-group">
            <label for="type">Type d'organisation *</label>
            <select id="type" name="type" required>
              <option value="">Choisir…</option>
              <option value="ASBL">ASBL</option>
              <option value="Indépendant">Indépendant</option>
              <option value="PME">PME</option>
              <option value="Autre">Autre</option>
            </select>
          </div>
          <div class="form-group">
            <label for="secteur">Secteur d'activité *</label>
            <select id="secteur" name="secteur" required>
              <option value="">Choisir…</option>
              <option>Culture &amp; arts</option>
              <option>Jeunesse &amp; éducation</option>
              <option>Environnement</option>
              <option>Action sociale</option>
              <option>Tourisme &amp; patrimoine</option>
              <option>Formation professionnelle</option>
              <option>Sport</option>
              <option>Santé</option>
              <option>Numérique &amp; innovation</option>
              <option>Autre</option>
            </select>
          </div>
          <div class="form-group">
            <label for="province">Province *</label>
            <select id="province" name="province" required>
              <option value="">Choisir…</option>
              <option>Hainaut</option>
              <option>Liège</option>
              <option>Luxembourg</option>
              <option>Namur</option>
              <option>Brabant wallon</option>
            </select>
          </div>
          <div class="form-group">
            <label for="employes">Nombre d'employés (ETP)</label>
            <select id="employes" name="employes">
              <option value="">Choisir…</option>
              <option>0 (bénévoles)</option>
              <option>1–5</option>
              <option>6–20</option>
              <option>21–50</option>
              <option>50+</option>
            </select>
          </div>
          <div class="form-group">
            <label for="prenom">Votre prénom *</label>
            <input type="text" id="prenom" name="prenom" placeholder="Marie" required>
          </div>
          <div class="form-group form-full">
            <label for="email">Adresse email *</label>
            <input type="email" id="email" name="email" placeholder="marie@monasbl.be" required>
          </div>
        </div>
        <button type="submit" class="form-submit" id="form-btn">Recevoir mon premier rapport</button>
        <p class="form-disclaimer">Gratuit pendant le pilote · Pas de carte bancaire · Désinscription en 1 clic</p>
      </form>
    </div>
  </div>
</section>

{footer()}

<script>
document.getElementById('form-inscription').addEventListener('submit', async function(e) {{

  e.preventDefault();
  var btn = document.getElementById('form-btn');
  var errEl = document.getElementById('form-error');
  var okEl = document.getElementById('form-success');
  errEl.style.display = 'none'; okEl.style.display = 'none';
  btn.disabled = true; btn.textContent = 'Envoi en cours…';
  var data = {{}};
  new FormData(this).forEach(function(v,k){{ data[k]=v; }});
  try {{
    var r = await fetch('/inscrire', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
    var j = await r.json();
    if (j.ok) {{ window.location.href = '/merci'; }}
    else {{ errEl.textContent = j.error || 'Une erreur est survenue.'; errEl.style.display='block'; btn.disabled=false; btn.textContent='Recevoir mon premier rapport'; }}
  }} catch(ex) {{ errEl.textContent = 'Erreur réseau. Réessayez.'; errEl.style.display='block'; btn.disabled=false; btn.textContent='Recevoir mon premier rapport'; }}
}});
</script>
{JS_ANIMATIONS}
</body>
</html>"""

def page_apropos():
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>À propos — GrantHound</title>
  {FONTS}
  {CSS_BASE}
</head>
<body>
{navbar("apropos")}

<section class="about-hero">
  <div class="container">
    <h1>Connecter l'argent public<br>avec ceux qui en ont besoin.</h1>
    <p>Des millions d'euros de subsides ne sont jamais réclamés en Wallonie — faute de temps pour surveiller les sources. GrantHound est là pour changer ça.</p>
  </div>
</section>

<section class="section">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:start">
      <div>
        <span class="section-label">L'histoire</span>
        <h2 class="section-title" style="font-size:clamp(24px,3vw,34px)">Qui est derrière GrantHound ?</h2>
        <p style="color:var(--gris);line-height:1.75;margin-bottom:20px">Je m'appelle Noah, j'ai 17 ans et je vis à Vielsalm, en Province de Luxembourg. Développeur autodidacte, j'ai déjà construit <strong>FindrBot</strong> — un outil de veille automatique pour le marché du resell.</p>
        <p style="color:var(--gris);line-height:1.75;margin-bottom:20px">En travaillant avec des ASBL locales, j'ai découvert un problème récurrent : des coordinateurs surchargés qui passent des heures à chercher des subsides sur MIDAS, FWB et les sites provinciaux — ou qui abandonnent et ratent des aides auxquelles ils avaient droit.</p>
        <p style="color:var(--gris);line-height:1.75">GrantHound automatise cette veille. Le résultat : un email hebdomadaire avec uniquement ce qui est pertinent pour votre structure.</p>
        <div style="margin-top:32px;padding:20px 24px;background:var(--vert-pale);border-left:3px solid var(--vert);border-radius:0 8px 8px 0">
          <p style="font-size:14px;color:var(--vert);font-weight:500;line-height:1.65">Je réponds personnellement à chaque message. Si GrantHound ne répond pas à un besoin précis, je préfère le dire clairement.</p>
          <p style="font-size:13px;color:var(--gris);margin-top:8px">— Noah · 0491 63 76 89</p>
        </div>
      </div>
      <div>
        <span class="section-label">Nos valeurs</span>
        <div class="values-grid" style="margin-top:12px">
          <div class="value-card">
            <div class="value-icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2l1.5 4.5H16l-3.5 2.5 1.5 4.5L10 11l-4 2.5 1.5-4.5L4 6.5h4.5z" stroke="#1E4D3A" stroke-width="1.5" stroke-linejoin="round"/></svg></div>
            <div class="value-title">Précision</div>
            <p class="value-desc">Uniquement les aides pertinentes pour votre profil. Pas de bruit, pas de spam — chaque alerte a une raison d'être là.</p>
          </div>
          <div class="value-card">
            <div class="value-icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="#1E4D3A" stroke-width="1.5"/><path d="M10 7v3l2 2" stroke="#1E4D3A" stroke-width="1.5" stroke-linecap="round"/></svg></div>
            <div class="value-title">Rapidité</div>
            <p class="value-desc">Les alertes arrivent avant les deadlines, pas après. La surveillance est continue — 7j/7, 24h/24.</p>
          </div>
          <div class="value-card">
            <div class="value-icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10l4 4 8-8" stroke="#1E4D3A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
            <div class="value-title">Transparence</div>
            <p class="value-desc">Toujours la source officielle. Chaque aide signalée inclut le lien direct vers l'organisme émetteur.</p>
          </div>
          <div class="value-card">
            <div class="value-icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 3C6.1 3 3 6.1 3 10s3.1 7 7 7 7-3.1 7-7" stroke="#1E4D3A" stroke-width="1.5" stroke-linecap="round"/><path d="M14 3v4h4" stroke="#1E4D3A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
            <div class="value-title">Local</div>
            <p class="value-desc">Conçu spécifiquement pour la Wallonie. Pas un outil générique reconditionné — une solution pensée pour votre réalité.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section" style="background:var(--gris-pale)">
  <div class="container">
    <span class="section-label">Comparaison</span>
    <h2 class="section-title">GrantHound vs MIDAS gratuit</h2>
    <p class="section-sub">MIDAS Wallonie est une excellente ressource — mais c'est une base de données, pas un système de veille.</p>
    <div style="overflow-x:auto;margin-top:32px">
      <table class="compare-table">
        <thead>
          <tr>
            <th>Fonctionnalité</th>
            <th>MIDAS Wallonie (gratuit)</th>
            <th style="color:var(--vert)">GrantHound</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>Accès aux données de subsides</td><td class="check">✓</td><td class="check">✓</td></tr>
          <tr><td>Alertes automatiques par email</td><td class="cross">✗</td><td class="check">✓</td></tr>
          <tr><td>Matching sur votre profil</td><td class="cross">✗</td><td class="check">✓</td></tr>
          <tr><td>Surveillance continue 24h/24</td><td class="cross">✗ (manuel)</td><td class="check">✓</td></tr>
          <tr><td>Agrégation multi-sources (FWB, provinces, Europe)</td><td class="cross">Partiel</td><td class="check">✓ 220+ sources</td></tr>
          <tr><td>Alertes avant deadline</td><td class="cross">✗</td><td class="check">✓</td></tr>
          <tr><td>Temps passé par semaine</td><td class="cross">2–3 heures</td><td class="check">0 min (email lu en 5 min)</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<section class="section-sm" style="text-align:center;background:var(--vert)">
  <div class="container">
    <h2 class="reveal" style="font-family:'Newsreader',serif;font-size:clamp(24px,3vw,36px);color:var(--blanc);margin-bottom:20px">Prêt à ne plus rater un subside ?</h2>
    <a href="/#inscription" class="hero-btn-primary reveal reveal-delay-1">Essai gratuit — sans carte</a>
  </div>
</section>

{footer()}
{JS_ANIMATIONS}
</body>
</html>"""

def page_contact():
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Contact — GrantHound</title>
  {FONTS}
  {CSS_BASE}
</head>
<body>
{navbar("contact")}

<section class="about-hero">
  <div class="container">
    <h1>Je réponds personnellement<br>à chaque message.</h1>
    <p>Une question, une demande de pilote, ou simplement envie d'échanger — je suis disponible.</p>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="contact-grid">
      <div>
        <h3 class="contact-info">Coordonnées</h3>
        <div class="contact-item">
          <div class="contact-icon"><svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M3 5l6 4 6-4M3 5h12v8H3V5z" stroke="#1E4D3A" stroke-width="1.5" stroke-linejoin="round"/></svg></div>
          <div><div class="contact-item-title">Email</div><div class="contact-item-val"><a href="mailto:noahlatour77@gmail.com" style="color:var(--vert);font-weight:500">noahlatour77@gmail.com</a></div></div>
        </div>
        <div class="contact-item">
          <div class="contact-icon"><svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M15 12.5c0 .3-.1.6-.2.9-1.4 3-9-1-11.5-3.5S-.4 2.6 2.6 1.2c.3-.1.6-.1.9-.1.3 0 .5.1.7.3l2 2.7c.2.3.2.7 0 1l-1 1c.7 1.4 1.7 2.7 3 3.8l1-1c.3-.2.7-.2 1 0l2.7 2c.2.2.3.4.1.6z" stroke="#1E4D3A" stroke-width="1.5" stroke-linejoin="round"/></svg></div>
          <div><div class="contact-item-title">Téléphone</div><div class="contact-item-val"><a href="tel:+32491637689" style="color:var(--vert);font-weight:500">0491 63 76 89</a></div></div>
        </div>
        <div class="contact-item">
          <div class="contact-icon"><svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2a5 5 0 0 1 5 5c0 3.5-5 9-5 9S4 10.5 4 7a5 5 0 0 1 5-5z" stroke="#1E4D3A" stroke-width="1.5"/><circle cx="9" cy="7" r="1.5" stroke="#1E4D3A" stroke-width="1.5"/></svg></div>
          <div><div class="contact-item-title">Localisation</div><div class="contact-item-val">Vielsalm, Province de Luxembourg<br><span style="font-size:13px;color:var(--gris)">Belgique</span></div></div>
        </div>
        <div class="contact-item">
          <div class="contact-icon"><svg width="18" height="18" viewBox="0 0 18 18" fill="none"><circle cx="9" cy="9" r="6" stroke="#1E4D3A" stroke-width="1.5"/><path d="M9 6v3l2 2" stroke="#1E4D3A" stroke-width="1.5" stroke-linecap="round"/></svg></div>
          <div><div class="contact-item-title">Délai de réponse</div><div class="contact-item-val">Sous 24h en semaine</div></div>
        </div>
      </div>
      <div>
        <div class="form-wrap" style="box-shadow:none;border:1px solid var(--gris-bord);padding:40px">
          <div class="alert alert-error" id="contact-error"></div>
          <div class="alert alert-success" id="contact-success"></div>
          <form id="form-contact">
            <div class="form-grid">
              <div class="form-group">
                <label for="c-nom">Nom *</label>
                <input type="text" id="c-nom" name="nom" placeholder="Marie Dupont" required>
              </div>
              <div class="form-group">
                <label for="c-email">Email *</label>
                <input type="email" id="c-email" name="email" placeholder="marie@asbl.be" required>
              </div>
              <div class="form-group form-full">
                <label for="c-sujet">Sujet *</label>
                <select id="c-sujet" name="sujet" required>
                  <option value="">Choisir…</option>
                  <option>Question sur le service</option>
                  <option>Demande pilote gratuit</option>
                  <option>Proposition de partenariat</option>
                  <option>Autre</option>
                </select>
              </div>
              <div class="form-group form-full">
                <label for="c-message">Message *</label>
                <textarea id="c-message" name="message" placeholder="Votre message…" required></textarea>
              </div>
            </div>
            <button type="submit" class="form-submit" id="contact-btn">Envoyer le message</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</section>

{footer()}

<script>
document.getElementById('form-contact').addEventListener('submit', async function(e) {{

  e.preventDefault();
  var btn = document.getElementById('contact-btn');
  var errEl = document.getElementById('contact-error');
  var okEl = document.getElementById('contact-success');
  errEl.style.display='none'; okEl.style.display='none';
  btn.disabled=true; btn.textContent='Envoi en cours…';
  var data={{}};
  new FormData(this).forEach(function(v,k){{data[k]=v;}});
  try {{
    var r=await fetch('/message',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
    var j=await r.json();
    if(j.ok){{okEl.textContent='Message envoyé ! Je vous réponds sous 24h.';okEl.style.display='block';this.reset();}}
    else{{errEl.textContent=j.error||'Erreur lors de l\\'envoi.';errEl.style.display='block';}}
  }} catch(ex){{errEl.textContent='Erreur réseau. Réessayez.';errEl.style.display='block';}}
  btn.disabled=false; btn.textContent='Envoyer le message';
}});
</script>
{JS_ANIMATIONS}
</body>
</html>"""

def page_merci():
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Merci — GrantHound</title>
  {FONTS}
  {CSS_BASE}
</head>
<body>
{navbar()}
<div class="container merci-page">
  <div class="merci-wrap">
    <div class="merci-icon">
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none"><path d="M9 18l6 6 12-12" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </div>
    <h1 class="merci-title">Votre inscription est confirmée !</h1>
    <p class="merci-sub">Votre premier rapport personnalisé arrive dans quelques minutes dans votre boîte mail.<br><br>Regardez dans vos spams si vous ne le voyez pas d'ici 5 minutes.</p>
    <a href="/" class="merci-back">Retour à l'accueil</a>
  </div>
</div>
{footer()}
</body>
</html>"""

def page_aide(aide_id):
    aide = get_aide(aide_id)
    if not aide:
        return None
    nom = aide.get("nom","Aide sans titre")
    organisme = aide.get("organisme","Non précisé")
    description = aide.get("description","") or "Description non disponible."
    deadline = aide.get("deadline","") or "Non précisée"
    url = aide.get("url_officiel","") or ""
    montant_min = aide.get("montant_min",0) or 0
    montant_max = aide.get("montant_max",0) or 0
    if montant_min and montant_max:
        montant_str = f"{montant_min:,} – {montant_max:,} €".replace(",",".")
    elif montant_max:
        montant_str = f"Jusqu'à {montant_max:,} €".replace(",",".")
    else:
        montant_str = "Non précisé"
    secteurs = aide.get("secteurs","") or "Tous secteurs"
    provinces = aide.get("provinces","") or "Toute la Wallonie"
    types_org = aide.get("types_org","") or "Tous types"
    url_btn = f'<a href="{url}" target="_blank" rel="noopener" class="aide-cta-btn">Voir la source officielle →</a>' if url else ""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{nom} — GrantHound</title>
  {FONTS}
  {CSS_BASE}
</head>
<body>
{navbar()}

<section class="aide-hero">
  <div class="container">
    <div style="margin-bottom:12px">
      <a href="/" style="font-size:13px;color:rgba(255,255,255,0.65);display:inline-flex;align-items:center;gap:6px">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M9 2L4 7l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Retour à l'accueil
      </a>
    </div>
    <h1>{nom}</h1>
    <div class="aide-meta">
      <span class="aide-badge">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1v2M6 9v2M1 6h2M9 6h2" stroke="white" stroke-width="1.2" stroke-linecap="round"/></svg>
        {organisme}
      </span>
      <span class="aide-badge">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="6" r="4.5" stroke="white" stroke-width="1.2"/><path d="M6 4v2l1.5 1.5" stroke="white" stroke-width="1.2" stroke-linecap="round"/></svg>
        Deadline : {deadline}
      </span>
      <span class="aide-badge">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 10l3-3 2 2 3-5" stroke="white" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        {montant_str}
      </span>
    </div>
  </div>
</section>

<section class="aide-body">
  <div class="container">
    <div class="aide-grid">
      <div>
        <h2 style="font-family:'Newsreader',serif;font-size:22px;font-weight:600;color:var(--noir);margin-bottom:20px">Description</h2>
        <div class="aide-desc">{description.replace(chr(10),'<br>')}</div>
        <div style="margin-top:40px;padding:20px 24px;background:var(--vert-pale);border-left:3px solid var(--vert);border-radius:0 8px 8px 0">
          <p style="font-size:14px;color:var(--vert);font-weight:600;margin-bottom:6px">Cette aide vous correspond ?</p>
          <p style="font-size:13px;color:var(--gris);line-height:1.65">Inscrivez-vous à GrantHound pour recevoir des alertes automatiques sur les subsides qui correspondent à votre profil.</p>
          <a href="/#inscription" style="display:inline-block;margin-top:12px;padding:9px 18px;background:var(--vert);color:var(--blanc);border-radius:6px;font-size:13px;font-weight:600">S'inscrire gratuitement</a>
        </div>
      </div>
      <div>
        <div class="aide-sidebar">
          <h3>Informations clés</h3>
          <div class="aide-info-row">
            <span class="aide-info-label">Organisme</span>
            <span class="aide-info-val">{organisme}</span>
          </div>
          <div class="aide-info-row">
            <span class="aide-info-label">Montant</span>
            <span class="aide-info-val">{montant_str}</span>
          </div>
          <div class="aide-info-row">
            <span class="aide-info-label">Deadline</span>
            <span class="aide-info-val">{deadline}</span>
          </div>
          <div class="aide-info-row">
            <span class="aide-info-label">Secteurs</span>
            <span class="aide-info-val">{secteurs}</span>
          </div>
          <div class="aide-info-row">
            <span class="aide-info-label">Provinces</span>
            <span class="aide-info-val">{provinces}</span>
          </div>
          <div class="aide-info-row">
            <span class="aide-info-label">Types d'org.</span>
            <span class="aide-info-val">{types_org}</span>
          </div>
          {url_btn}
        </div>
      </div>
    </div>
  </div>
</section>

{footer()}
{JS_ANIMATIONS}
</body>
</html>"""

def page_404():
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page introuvable — GrantHound</title>
  {FONTS}
  {CSS_BASE}
</head>
<body>
{navbar()}
<div class="container page-404">
  <div>
    <div class="page-404-num">404</div>
    <h2>Page introuvable</h2>
    <p>La page que vous cherchez n'existe pas ou a été déplacée.</p>
    <a href="/" class="btn-primary">Retour à l'accueil</a>
  </div>
</div>
{footer()}
</body>
</html>"""

# ── Request Handler ────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

    def send_html(self, html, code=200):
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        routes = {
            "/": page_accueil,
            "/apropos": page_apropos,
            "/contact": page_contact,
            "/merci": page_merci,
        }
        if path in routes:
            self.send_html(routes[path]())
        elif path.startswith("/aide/"):
            try:
                aide_id = int(path.split("/aide/")[1])
                html = page_aide(aide_id)
                if html:
                    self.send_html(html)
                else:
                    self.send_html(page_404(), 404)
            except (ValueError, IndexError):
                self.send_html(page_404(), 404)
        else:
            self.send_html(page_404(), 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.read_json_body()
        except Exception:
            self.send_json({"ok": False, "error": "JSON invalide"}, 400)
            return

        if path == "/inscrire":
            required = ["nom", "type", "secteur", "province", "prenom", "email"]
            missing = [f for f in required if not data.get(f,"").strip()]
            if missing:
                self.send_json({"ok": False, "error": f"Champs manquants : {', '.join(missing)}"}, 400)
                return
            try:
                save_client(data)
                email_bienvenue(data)
                self.send_json({"ok": True})
            except Exception as e:
                print(f"[Error /inscrire] {e}")
                self.send_json({"ok": False, "error": "Erreur serveur. Réessayez."}, 500)

        elif path == "/message":
            required = ["nom", "email", "sujet", "message"]
            missing = [f for f in required if not data.get(f,"").strip()]
            if missing:
                self.send_json({"ok": False, "error": f"Champs manquants : {', '.join(missing)}"}, 400)
                return
            try:
                email_contact(data)
                self.send_json({"ok": True})
            except Exception as e:
                print(f"[Error /message] {e}")
                self.send_json({"ok": False, "error": "Erreur lors de l'envoi."}, 500)
        else:
            self.send_json({"ok": False, "error": "Route inconnue"}, 404)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print(f"GrantHound démarré sur http://localhost:{PORT}")
    print(f"Base de données : {DB_PATH}")
    HTTPServer(("", PORT), Handler).serve_forever()
