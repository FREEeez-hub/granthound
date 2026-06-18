import os, sqlite3, smtplib, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

PORT = int(os.environ.get('PORT', 10000))
DB_PATH = 'granthound.db'
GMAIL_USER = 'noahlatour77@gmail.com'
GMAIL_PASS = 'bvtciemwwxonfcmi'

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT, type TEXT, secteur TEXT, province TEXT,
        employes INTEGER, budget_annuel TEXT, annee_creation INTEGER,
        public_cible TEXT, projets TEXT, cofinancement INTEGER DEFAULT 0,
        email TEXT UNIQUE, contact TEXT,
        date_inscription TEXT DEFAULT CURRENT_TIMESTAMP,
        actif INTEGER DEFAULT 1
    )''')
    con.commit(); con.close()

def save_client(data):
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute('''INSERT INTO clients 
            (nom,type,secteur,province,employes,budget_annuel,annee_creation,
             public_cible,projets,cofinancement,email,contact)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (data.get('nom',''), data.get('type',''), data.get('secteur',''),
             data.get('province',''), int(data.get('employes',0) or 0),
             data.get('budget_annuel',''), int(data.get('annee_creation',2000) or 2000),
             data.get('public_cible',''), data.get('projets',''),
             1 if data.get('cofinancement') else 0,
             data.get('email',''), data.get('contact','')))
        con.commit(); return True, None
    except sqlite3.IntegrityError: return False, 'exists'
    finally: con.close()

def send_email(to, subject, body):
    def _send():
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = GMAIL_USER
            msg['To'] = to
            msg.attach(MIMEText(body, 'html'))
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as s:
                s.login(GMAIL_USER, GMAIL_PASS)
                s.sendmail(GMAIL_USER, to, msg.as_string())
            print(f'[EMAIL OK] {to}')
        except Exception as e:
            print(f'[EMAIL ERROR] {e}')
    threading.Thread(target=_send, daemon=True).start()

CSS = '''<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--navy:#0B1F3A;--green:#2D7A4F;--cream:#F7F6F2}
body{font-family:Inter,sans-serif;background:var(--cream);color:#1a1a1a}
h1,h2,h3{font-family:Sora,sans-serif}
nav{background:var(--navy);padding:0 5%;display:flex;align-items:center;justify-content:space-between;height:64px;position:sticky;top:0;z-index:100}
.logo{color:#fff;font-family:Sora,sans-serif;font-size:1.4rem;font-weight:800}.logo span{color:var(--green)}
.nav-links a{color:rgba(255,255,255,.8);font-size:.9rem;margin-left:24px;text-decoration:none}
.nav-links a:last-child{background:var(--green);color:#fff;padding:8px 18px;border-radius:6px}
.hero{background:var(--navy);padding:100px 5% 80px;text-align:center}
.hero h1{color:#fff;font-size:clamp(2rem,4vw,3.2rem);line-height:1.15;margin-bottom:20px}
.hero h1 em{color:var(--green);font-style:normal}
.hero p{color:rgba(255,255,255,.75);font-size:1.05rem;line-height:1.7;max-width:600px;margin:0 auto 36px}
.btn{display:inline-block;background:var(--green);color:#fff;padding:14px 32px;border-radius:8px;font-weight:700;font-size:1rem;text-decoration:none;border:none;cursor:pointer;transition:.2s}
.btn:hover{background:#3a9b63;transform:translateY(-2px)}
.btn-outline{background:transparent;border:2px solid rgba(255,255,255,.3);margin-left:12px;color:#fff}
.btn-outline:hover{border-color:#fff;background:rgba(255,255,255,.1)}
.ticker{background:var(--green);padding:10px 0;overflow:hidden;white-space:nowrap}
.ticker-inner{display:inline-flex;animation:ticker 28s linear infinite}
.ticker span{padding:0 32px;color:#fff;font-size:.85rem;font-weight:600}
@keyframes ticker{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.section{padding:70px 5%;max-width:1100px;margin:0 auto}
.section-tag{color:var(--green);font-size:.8rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px}
.section h2{font-size:clamp(1.7rem,3vw,2.4rem);color:var(--navy);margin-bottom:16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;margin-top:40px}
.card{background:#fff;border-radius:12px;padding:28px;border:1px solid #e8e6e0}
.card h3{color:var(--navy);margin-bottom:8px;font-size:1rem}
.card p{color:#666;font-size:.88rem;line-height:1.7}
.form-wrap{background:var(--navy);padding:70px 5%}
.form-inner{max-width:760px;margin:0 auto}
.form-inner h2{color:#fff;font-size:2rem;margin-bottom:8px}
.form-inner .sub{color:rgba(255,255,255,.6);margin-bottom:36px;font-size:.95rem}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.field{display:flex;flex-direction:column;gap:6px}
.field.full{grid-column:1/-1}
.field label{color:rgba(255,255,255,.85);font-size:.85rem;font-weight:600}
.field input,.field select{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#fff;padding:11px 14px;border-radius:8px;font-size:.92rem;font-family:Inter,sans-serif;outline:none;-webkit-appearance:none;appearance:none}
.field select option{background:#0B1F3A}
.field input:focus,.field select:focus{border-color:var(--green)}
.field input::placeholder{color:rgba(255,255,255,.35)}
.checks{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}
.checks label{display:flex;align-items:center;gap:8px;color:rgba(255,255,255,.85);font-size:.88rem;font-weight:400;cursor:pointer}
.checks input[type=checkbox]{width:16px;height:16px;accent-color:var(--green)}
.form-submit{margin-top:24px;text-align:center}
.form-note{color:rgba(255,255,255,.4);font-size:.78rem;margin-top:10px}
.alert{padding:14px 20px;border-radius:8px;margin-bottom:20px;font-weight:600;text-align:center}
.alert-ok{background:rgba(45,122,79,.15);border:1px solid var(--green);color:#2D7A4F}
.alert-err{background:rgba(180,30,30,.1);border:1px solid #c0392b;color:#c0392b}
footer{background:var(--navy);color:rgba(255,255,255,.5);padding:36px 5%;text-align:center;font-size:.84rem}
footer a{color:var(--green)}
@media(max-width:640px){.form-grid{grid-template-columns:1fr}.checks{grid-template-columns:1fr}}
</style>'''

def page_home(alert=''):
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GrantHound — Veille automatique de subsides wallons</title>
<link href="https://fonts.bunny.net/css?family=sora:700,800|inter:400,500,600" rel="stylesheet">
{CSS}</head><body>
<nav><a class="logo" href="/">Grant<span>Hound</span></a>
<div class="nav-links"><a href="/apropos">A propos</a><a href="/contact">Contact</a><a href="/#inscription">S inscrire</a></div></nav>
<div class="hero">
  <h1>Trouvez les subsides qui<br><em>financent votre ASBL</em></h1>
  <p>GrantHound surveille automatiquement 297+ sources de financement wallonnes et vous alerte uniquement sur les aides qui correspondent a votre profil.</p>
  <a href="/#inscription" class="btn">S inscrire gratuitement</a>
  <a href="/apropos" class="btn btn-outline">En savoir plus</a>
</div>
<div class="ticker"><div class="ticker-inner">
<span>MIDAS Wallonie</span><span>FWB</span><span>Province de Liege</span><span>Province de Luxembourg</span>
<span>Fondation Roi Baudouin</span><span>Loterie Nationale</span><span>Interreg</span><span>CERV Europe</span>
<span>Erasmus+</span><span>LIFE</span><span>MIDAS Wallonie</span><span>FWB</span><span>Province de Liege</span>
<span>Province de Luxembourg</span><span>Fondation Roi Baudouin</span><span>Loterie Nationale</span>
<span>Interreg</span><span>CERV Europe</span><span>Erasmus+</span><span>LIFE</span>
</div></div>
<div class="section">
  <p class="section-tag">Pourquoi GrantHound</p>
  <h2>Ne manquez plus aucun subside adapte a votre structure</h2>
  <p style="color:#555;line-height:1.8">La veille manuelle des subsides est chronophage. GrantHound automatise tout.</p>
  <div class="cards">
    <div class="card"><h3>Detection automatique</h3><p>297+ sources officielles scrutees en continu.</p></div>
    <div class="card"><h3>Matching IA</h3><p>Gemini 2.5 Flash analyse votre profil et ne vous envoie que les aides pertinentes.</p></div>
    <div class="card"><h3>Alertes hebdo</h3><p>Chaque lundi matin, un rapport clair avec les aides ouvertes.</p></div>
    <div class="card"><h3>Aides meconnues</h3><p>On separe les aides connues des aides que vous ne connaissiez pas encore.</p></div>
  </div>
</div>
<div class="form-wrap" id="inscription">
<div class="form-inner">
  <h2>Creez votre profil subsides</h2>
  <p class="sub">Inscription gratuite - Pas de carte - Premier rapport sous 7 jours</p>
  {alert}
  <form method="POST" action="/inscrire">
  <div class="form-grid">
    <div class="field full"><label>Nom de la structure *</label>
      <input type="text" name="nom" placeholder="Ex : ASBL Horizon Vert" required></div>
    <div class="field"><label>Type *</label>
      <select name="type" required><option value="" disabled selected>Choisissez...</option>
      <option>ASBL</option><option>Independant</option><option>PME</option><option>Autre</option></select></div>
    <div class="field"><label>Secteur *</label>
      <select name="secteur" required><option value="" disabled selected>Choisissez...</option>
      <option>Culture et Arts</option><option>Jeunesse</option><option>Environnement</option>
      <option>Social</option><option>Tourisme</option><option>Formation</option>
      <option>Agriculture</option><option>Autre</option></select></div>
    <div class="field"><label>Province *</label>
      <select name="province" required><option value="" disabled selected>Choisissez...</option>
      <option>Province de Liege</option><option>Province de Luxembourg</option>
      <option>Province de Namur</option><option>Province du Hainaut</option>
      <option>Province du Brabant wallon</option><option>Bruxelles</option></select></div>
    <div class="field"><label>Employes</label>
      <input type="number" name="employes" min="0" placeholder="Ex : 5"></div>
    <div class="field"><label>Budget annuel</label>
      <select name="budget_annuel"><option value="" disabled selected>Choisissez...</option>
      <option>Moins de 50000 euros</option><option>50000 a 200000 euros</option>
      <option>200000 a 500000 euros</option><option>Plus de 500000 euros</option></select></div>
    <div class="field"><label>Annee de creation</label>
      <input type="number" name="annee_creation" min="1900" max="2026" placeholder="Ex : 2005"></div>
    <div class="field"><label>Public cible</label>
      <select name="public_cible"><option value="" disabled selected>Choisissez...</option>
      <option>Grand public</option><option>Jeunes</option><option>Personnes handicapees</option>
      <option>Demandeurs d emploi</option><option>Artistes</option>
      <option>Agriculteurs</option><option>Entreprises</option><option>Autre</option></select></div>
    <div class="field full"><label>Projets en cours</label>
      <div class="checks">
        <label><input type="checkbox" name="projets" value="Recrutement"> Recrutement</label>
        <label><input type="checkbox" name="projets" value="Formation"> Formation</label>
        <label><input type="checkbox" name="projets" value="Investissement"> Investissement</label>
        <label><input type="checkbox" name="projets" value="Projet culturel"> Projet culturel</label>
        <label><input type="checkbox" name="projets" value="Projet environnemental"> Projet environnemental</label>
        <label><input type="checkbox" name="projets" value="Projet jeunesse"> Projet jeunesse</label>
      </div></div>
    <div class="field full">
      <label style="display:flex;align-items:center;gap:10px;font-weight:400;cursor:pointer">
        <input type="checkbox" name="cofinancement" value="1">
        Je cherche des fonds complementaires (cofinancement)
      </label></div>
    <div class="field"><label>Prenom *</label>
      <input type="text" name="contact" placeholder="Ex : Marie" required></div>
    <div class="field"><label>Email *</label>
      <input type="email" name="email" placeholder="marie@structure.be" required></div>
  </div>
  <div class="form-submit">
    <button type="submit" class="btn" style="font-size:1.05rem;padding:16px 40px">Creer mon profil</button>
    <p class="form-note">Acces gratuit pendant le pilote - Pas de carte - Desinscription en 1 clic</p>
  </div>
  </form>
</div></div>
<footer>
  <p style="font-family:Sora,sans-serif;color:#fff;font-size:1.1rem;font-weight:700;margin-bottom:10px">Grant<span style="color:#2D7A4F">Hound</span></p>
  <p>Veille automatique de subsides pour ASBL wallonnes</p>
  <p style="margin-top:12px"><a href="/apropos">A propos</a> - <a href="/contact">Contact</a></p>
</footer></body></html>'''

def page_apropos():
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A propos - GrantHound</title>
<link href="https://fonts.bunny.net/css?family=sora:700,800|inter:400,500,600" rel="stylesheet">
{CSS}</head><body>
<nav><a class="logo" href="/">Grant<span>Hound</span></a>
<div class="nav-links"><a href="/">Accueil</a><a href="/contact">Contact</a><a href="/#inscription">S inscrire</a></div></nav>
<div class="hero" style="padding:80px 5%">
  <h1>A propos de <em>GrantHound</em></h1>
  <p>Developpe par Noah Latour, 17 ans, Vielsalm.</p>
</div>
<div class="section">
  <div class="cards">
    <div class="card"><h3>297+ aides</h3><p>MIDAS, FWB, 5 provinces wallonnes, Europe, Fondation Roi Baudouin, Loterie Nationale.</p></div>
    <div class="card"><h3>IA Gemini 2.5 Flash</h3><p>Chaque aide est analysee pour evaluer sa pertinence par rapport a votre profil.</p></div>
    <div class="card"><h3>Rapport hebdo</h3><p>Chaque lundi : les aides pertinentes, separees entre connues et inconnues.</p></div>
  </div>
  <div style="margin-top:48px;background:#fff;border-radius:12px;padding:32px;border:1px solid #e8e6e0">
    <h3 style="color:var(--navy);margin-bottom:12px">Contact</h3>
    <p style="color:#555;line-height:1.8">
      Email : noahlatour77@gmail.com<br>
      Tel : 0491 63 76 89<br>
      Vielsalm, Province de Luxembourg, Belgique
    </p>
  </div>
</div>
<footer><p><a href="/">Accueil</a> - <a href="/contact">Contact</a></p></footer>
</body></html>'''

def page_contact(alert=''):
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Contact - GrantHound</title>
<link href="https://fonts.bunny.net/css?family=sora:700,800|inter:400,500,600" rel="stylesheet">
{CSS}</head><body>
<nav><a class="logo" href="/">Grant<span>Hound</span></a>
<div class="nav-links"><a href="/">Accueil</a><a href="/apropos">A propos</a><a href="/#inscription">S inscrire</a></div></nav>
<div class="form-wrap" style="padding-top:100px">
<div class="form-inner">
  <h2 style="color:#fff;margin-bottom:8px">Contactez-nous</h2>
  <p class="sub">Reponse sous 24h - noahlatour77@gmail.com - 0491 63 76 89</p>
  {alert}
  <form method="POST" action="/message">
  <div class="form-grid">
    <div class="field"><label>Nom *</label><input type="text" name="nom" placeholder="Marie Dupont" required></div>
    <div class="field"><label>Email *</label><input type="email" name="email" placeholder="marie@structure.be" required></div>
    <div class="field full"><label>Sujet *</label><input type="text" name="sujet" placeholder="Votre sujet..." required></div>
    <div class="field full"><label>Message *</label>
      <textarea name="message" rows="6" placeholder="Votre message..." required
        style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#fff;padding:11px 14px;border-radius:8px;font-size:.92rem;font-family:Inter,sans-serif;outline:none;resize:vertical"></textarea></div>
  </div>
  <div class="form-submit"><button type="submit" class="btn">Envoyer</button></div>
  </form>
</div></div>
<footer><p><a href="/">Accueil</a> - <a href="/apropos">A propos</a></p></footer>
</body></html>'''

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): print(f'[{self.address_string()}] {fmt % args}')

    def send_html(self, html, code=200):
        body = html.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/': self.send_html(page_home())
        elif path == '/apropos': self.send_html(page_apropos())
        elif path == '/contact': self.send_html(page_contact())
        else: self.send_html('<h1>404</h1>', 404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length).decode('utf-8')
        parsed = parse_qs(raw, keep_blank_values=True)
        data = {k: (v if len(v) > 1 else v[0]) for k, v in parsed.items()}

        if path == '/inscrire':
            projets = data.get('projets', [])
            if isinstance(projets, str): projets = [projets]
            data['projets'] = ', '.join(projets)
            ok, err = save_client(data)
            if ok:
                send_email(data.get('email',''), 'Bienvenue sur GrantHound !',
                    f'<p>Bonjour {data.get("contact","")}, votre profil <strong>{data.get("nom","")}</strong> est cree.</p>')
                send_email(GMAIL_USER, f'[GrantHound] Nouvelle inscription : {data.get("nom","")}',
                    f'<p>Email : {data.get("email","")}</p><p>Province : {data.get("province","")}</p>')
                self.send_html(page_home('<div class="alert alert-ok">Inscription reussie ! Consultez votre boite mail.</div>'))
            elif err == 'exists':
                self.send_html(page_home('<div class="alert alert-err">Cet email est deja inscrit.</div>'))
            else:
                self.send_html(page_home('<div class="alert alert-err">Erreur. Reessayez.</div>'))

        elif path == '/message':
            data2 = {k: (v[0] if isinstance(v, list) else v) for k, v in data.items()}
            if all(data2.get(f,'').strip() for f in ['nom','email','sujet','message']):
                send_email(GMAIL_USER, f'[GrantHound Contact] {data2.get("sujet","")}',
                    f'<p>De : {data2.get("nom","")} ({data2.get("email","")})</p><p>{data2.get("message","")}</p>')
                self.send_html(page_contact('<div class="alert alert-ok">Message envoye !</div>'))
            else:
                self.send_html(page_contact('<div class="alert alert-err">Remplissez tous les champs.</div>'))
        else:
            self.send_html('<h1>404</h1>', 404)

if __name__ == '__main__':
    init_db()
    print(f'[GrantHound] http://0.0.0.0:{PORT}')
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
