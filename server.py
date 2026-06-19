import os, sqlite3, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get('PORT', 10000))
DB_PATH = 'granthound.db'
RESEND_API_KEY = "re_SVfMy7i6_HMsxcvfodN8gQhcZTnzpym2L"
ADMIN_EMAIL = "noahlatour77@gmail.com"
GMAIL_USER = "noahlatour77@gmail.com"
GMAIL_PASS = "bvtciemwwxonfcmi"

# ── Database ──────────────────────────────────────────────────────────────────

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

# ── Email (Resend REST) ───────────────────────────────────────────────────────

BREVO_SMTP = "smtp-relay.brevo.com"
BREVO_PORT = 587
BREVO_LOGIN = "af3e1d001@smtp-brevo.com"
BREVO_KEY = os.environ.get('BREVO_KEY', '')

def send_email(to, subject, html_body):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = 'GrantHound <noahlatour77@gmail.com>'
        msg['To'] = to
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        with smtplib.SMTP(BREVO_SMTP, BREVO_PORT) as s:
            s.starttls()
            s.login(BREVO_LOGIN, BREVO_KEY)
            s.sendmail(BREVO_LOGIN, to, msg.as_string())
        print(f"[EMAIL OK] {to}", flush=True)
    except Exception as e:
        print(f"[EMAIL ERROR] {e}", flush=True)
    v
# ── Shared CSS + JS ───────────────────────────────────────────────────────────

HEAD = '''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.bunny.net/css?family=sora:700,800|inter:400,500,600" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--navy:#0B1F3A;--green:#2D7A4F;--cream:#F7F6F2}
body{font-family:Inter,sans-serif;background:var(--cream);color:#1a1a1a;overflow-x:hidden}
h1,h2,h3{font-family:Sora,sans-serif}

/* NAV */
nav{position:fixed;top:0;left:0;right:0;z-index:200;padding:0 5%;display:flex;align-items:center;justify-content:space-between;height:64px;transition:background .3s,box-shadow .3s}
nav.solid{background:var(--navy);box-shadow:0 2px 16px rgba(0,0,0,.25)}
.logo{color:#fff;font-family:Sora,sans-serif;font-size:1.4rem;font-weight:800;text-decoration:none}
.logo span{color:var(--green)}
.nav-links a{color:rgba(255,255,255,.85);font-size:.9rem;margin-left:24px;text-decoration:none;transition:.2s}
.nav-links a:hover{color:#fff}
.nav-links a.cta{background:var(--green);color:#fff;padding:8px 18px;border-radius:6px}
.nav-links a.cta:hover{background:#3a9b63}

/* HERO */
.hero{position:relative;background:var(--navy);padding:130px 5% 100px;text-align:center;overflow:hidden;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center}
#particles{position:absolute;inset:0;pointer-events:none}
.hero-content{position:relative;z-index:1}
.hero h1{color:#fff;font-size:clamp(2rem,4.5vw,3.4rem);line-height:1.15;margin-bottom:20px}
.hero h1 em{color:var(--green);font-style:normal}
.hero p{color:rgba(255,255,255,.75);font-size:1.1rem;line-height:1.75;max-width:620px;margin:0 auto 38px}
.btn{display:inline-block;background:var(--green);color:#fff;padding:14px 32px;border-radius:8px;font-weight:700;font-size:1rem;text-decoration:none;border:none;cursor:pointer;transition:.2s}
.btn:hover{background:#3a9b63;transform:translateY(-2px)}
.btn-outline{background:transparent;border:2px solid rgba(255,255,255,.35);margin-left:12px;color:#fff}
.btn-outline:hover{border-color:#fff;background:rgba(255,255,255,.1);transform:translateY(-2px)}

/* TICKER */
.ticker{background:var(--green);padding:11px 0;overflow:hidden;white-space:nowrap}
.ticker-inner{display:inline-flex;animation:ticker 32s linear infinite}
.ticker span{padding:0 36px;color:#fff;font-size:.85rem;font-weight:600;letter-spacing:.5px}
@keyframes ticker{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* COUNTERS */
.counters{background:#fff;padding:50px 5%;display:flex;justify-content:center;gap:60px;flex-wrap:wrap}
.counter{text-align:center}
.counter-num{font-family:Sora,sans-serif;font-size:2.6rem;font-weight:800;color:var(--navy)}
.counter-num span{color:var(--green)}
.counter-label{color:#666;font-size:.88rem;margin-top:4px}

/* SECTIONS */
.section{padding:80px 5%;max-width:1100px;margin:0 auto}
.section-tag{color:var(--green);font-size:.8rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px}
.section h2{font-size:clamp(1.7rem,3vw,2.4rem);color:var(--navy);margin-bottom:16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:24px;margin-top:40px}
.card{background:#fff;border-radius:12px;padding:28px;border:1px solid #e8e6e0;transition:.25s}
.card:hover{transform:translateY(-4px);box-shadow:0 8px 30px rgba(11,31,58,.1)}
.card-icon{font-size:1.8rem;margin-bottom:12px}
.card h3{color:var(--navy);margin-bottom:8px;font-size:1rem}
.card p{color:#666;font-size:.88rem;line-height:1.7}

/* FORM */
.form-wrap{background:var(--navy);padding:80px 5%}
.form-inner{max-width:780px;margin:0 auto}
.form-inner h2{color:#fff;font-size:2rem;margin-bottom:8px}
.form-inner .sub{color:rgba(255,255,255,.6);margin-bottom:38px;font-size:.95rem}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.field{display:flex;flex-direction:column;gap:6px}
.field.full{grid-column:1/-1}
.field label{color:rgba(255,255,255,.85);font-size:.85rem;font-weight:600}
.field input,.field select,.field textarea{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#fff;padding:11px 14px;border-radius:8px;font-size:.92rem;font-family:Inter,sans-serif;outline:none;-webkit-appearance:none;appearance:none;transition:.2s}
.field select option{background:#0B1F3A;color:#fff}
.field input:focus,.field select:focus,.field textarea:focus{border-color:var(--green);background:rgba(255,255,255,.12)}
.field input::placeholder,.field textarea::placeholder{color:rgba(255,255,255,.35)}
.checks{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}
.checks label{display:flex;align-items:center;gap:8px;color:rgba(255,255,255,.85);font-size:.88rem;font-weight:400;cursor:pointer}
.checks input[type=checkbox]{width:16px;height:16px;accent-color:var(--green);flex-shrink:0}
.form-submit{margin-top:26px;text-align:center}
.form-note{color:rgba(255,255,255,.4);font-size:.78rem;margin-top:10px}
.alert{padding:14px 20px;border-radius:8px;margin-bottom:22px;font-weight:600;text-align:center}
.alert-ok{background:rgba(45,122,79,.15);border:1px solid var(--green);color:#2ecc71}
.alert-err{background:rgba(180,30,30,.1);border:1px solid #c0392b;color:#e74c3c}

/* FOOTER */
footer{background:var(--navy);color:rgba(255,255,255,.5);padding:40px 5%;text-align:center;font-size:.84rem}
footer .logo-foot{font-family:Sora,sans-serif;color:#fff;font-size:1.15rem;font-weight:800;margin-bottom:10px}
footer a{color:var(--green);text-decoration:none}
footer a:hover{text-decoration:underline}

/* REVEAL */
.reveal{opacity:0;transform:translateY(30px);transition:opacity .6s ease,transform .6s ease}
.reveal.visible{opacity:1;transform:none}

@media(max-width:640px){
  .form-grid{grid-template-columns:1fr}
  .checks{grid-template-columns:1fr}
  .counters{gap:30px}
  .nav-links a:not(.cta){display:none}
}
</style>'''

PARTICLES_JS = '''
<canvas id="particles"></canvas>
<script>
(function(){
  const c=document.getElementById('particles');
  const ctx=c.getContext('2d');
  let pts=[];
  function resize(){c.width=c.offsetWidth;c.height=c.offsetHeight;pts=[];for(let i=0;i<90;i++)pts.push({x:Math.random()*c.width,y:Math.random()*c.height,vx:(Math.random()-.5)*.4,vy:(Math.random()-.5)*.4,r:Math.random()*2+.5})}
  function draw(){
    ctx.clearRect(0,0,c.width,c.height);
    pts.forEach(p=>{
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0||p.x>c.width)p.vx*=-1;
      if(p.y<0||p.y>c.height)p.vy*=-1;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle='rgba(45,122,79,.55)';ctx.fill();
    });
    pts.forEach((a,i)=>pts.slice(i+1).forEach(b=>{
      const d=Math.hypot(a.x-b.x,a.y-b.y);
      if(d<120){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
      ctx.strokeStyle=`rgba(45,122,79,${.18*(1-d/120)})`;ctx.lineWidth=.7;ctx.stroke();}
    }));
    requestAnimationFrame(draw);
  }
  resize();draw();
  window.addEventListener('resize',resize);
})();
</script>'''

NAV_SCROLL_JS = '''<script>
(function(){
  const nav=document.querySelector('nav');
  function update(){nav.classList.toggle('solid',scrollY>40)}
  window.addEventListener('scroll',update,{passive:true});update();
})();
</script>'''

COUNTER_JS = '''<script>
(function(){
  const els=document.querySelectorAll('[data-count]');
  const io=new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(!e.isIntersecting)return;
      const el=e.target,target=+el.dataset.count,suffix=el.dataset.suffix||'';
      let start=0,dur=1600,t0=null;
      (function step(ts){if(!t0)t0=ts;const p=Math.min((ts-t0)/dur,1);
        el.textContent=Math.round(p*target)+suffix;if(p<1)requestAnimationFrame(step);
      })(performance.now());
      io.unobserve(el);
    });
  },{threshold:.4});
  els.forEach(el=>io.observe(el));
})();
</script>'''

REVEAL_JS = '''<script>
(function(){
  const io=new IntersectionObserver(entries=>{
    entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible')});
  },{threshold:.12});
  document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
})();
</script>'''

def nav(active=''):
    return f'''<nav id="main-nav">
  <a class="logo" href="/">Grant<span>Hound</span></a>
  <div class="nav-links">
    <a href="/apropos">À propos</a>
    <a href="/contact">Contact</a>
    <a href="/#inscription" class="cta">S\'inscrire</a>
  </div>
</nav>'''

def footer():
    return '''<footer>
  <p class="logo-foot">Grant<span style="color:#2D7A4F">Hound</span></p>
  <p>Veille automatique de subsides pour structures wallonnes</p>
  <p style="margin-top:12px"><a href="/apropos">À propos</a> &nbsp;·&nbsp; <a href="/contact">Contact</a></p>
</footer>'''

def ticker():
    items = ['MIDAS Wallonie','FWB','Province de Liège','Province de Luxembourg',
             'Fondation Roi Baudouin','Loterie Nationale','Interreg','CERV','Erasmus+',
             'LIFE','Province de Namur','Province du Hainaut']
    double = items * 2
    spans = ''.join(f'<span>{i}</span>' for i in double)
    return f'<div class="ticker"><div class="ticker-inner">{spans}</div></div>'

# ── Pages ─────────────────────────────────────────────────────────────────────

def page_home(alert=''):
    return f'''<!DOCTYPE html>
<html lang="fr"><head>
<title>GrantHound — Veille automatique de subsides wallons</title>
{HEAD}</head><body>
{nav()}
<div class="hero">
  {PARTICLES_JS}
  <div class="hero-content">
    <h1>Trouvez les subsides qui<br><em>financent votre structure</em></h1>
    <p>GrantHound surveille automatiquement 297+ sources de financement wallonnes et vous alerte uniquement sur les aides qui correspondent à votre profil.</p>
    <a href="/#inscription" class="btn">S'inscrire gratuitement</a>
    <a href="/apropos" class="btn btn-outline">En savoir plus</a>
  </div>
</div>
{ticker()}
<div class="counters">
  <div class="counter reveal">
    <div class="counter-num"><span data-count="297" data-suffix="+">0+</span></div>
    <div class="counter-label">Sources de financement</div>
  </div>
  <div class="counter reveal">
    <div class="counter-num"><span data-count="10" data-suffix="+">0+</span></div>
    <div class="counter-label">Réseaux de veille</div>
  </div>
  <div class="counter reveal">
    <div class="counter-num"><span data-count="7" data-suffix="j">0j</span></div>
    <div class="counter-label">Premier rapport</div>
  </div>
</div>
<div class="section">
  <p class="section-tag reveal">Pourquoi GrantHound</p>
  <h2 class="reveal">Ne manquez plus aucun subside adapté à votre structure</h2>
  <p class="reveal" style="color:#555;line-height:1.8">La veille manuelle des subsides est chronophage et incomplète. GrantHound automatise tout — de la détection à l'alerte ciblée.</p>
  <div class="cards">
    <div class="card reveal"><div class="card-icon">🔍</div><h3>Détection automatique</h3><p>297+ sources officielles scrutées en continu : MIDAS, FWB, provinces, Europe.</p></div>
    <div class="card reveal"><div class="card-icon">🤖</div><h3>Matching IA</h3><p>Gemini 2.5 Flash analyse votre profil et ne vous envoie que les aides pertinentes.</p></div>
    <div class="card reveal"><div class="card-icon">📬</div><h3>Alertes hebdo</h3><p>Chaque lundi matin, un rapport clair avec les aides ouvertes, classées par pertinence.</p></div>
    <div class="card reveal"><div class="card-icon">💎</div><h3>Aides méconnues</h3><p>On sépare les aides connues des aides que vous ne connaissiez pas encore.</p></div>
  </div>
</div>
<div class="form-wrap" id="inscription">
  <div class="form-inner">
    <h2>Créez votre profil subsides</h2>
    <p class="sub">Inscription gratuite · Pas de carte · Premier rapport sous 7 jours</p>
    {alert}
    <form method="POST" action="/inscrire">
    <div class="form-grid">
      <div class="field full"><label>Nom de la structure *</label>
        <input type="text" name="nom" placeholder="Ex : ASBL Horizon Vert" required></div>
      <div class="field"><label>Type *</label>
        <select name="type" required>
          <option value="" disabled selected>Choisissez...</option>
          <option>ASBL</option><option>Indépendant</option><option>PME</option><option>Autre</option>
        </select></div>
      <div class="field"><label>Secteur *</label>
        <select name="secteur" required>
          <option value="" disabled selected>Choisissez...</option>
          <option>Culture &amp; Arts</option><option>Jeunesse</option><option>Environnement</option>
          <option>Social</option><option>Tourisme</option><option>Formation</option>
          <option>Agriculture</option><option>Autre</option>
        </select></div>
      <div class="field"><label>Province *</label>
        <select name="province" required>
          <option value="" disabled selected>Choisissez...</option>
          <option>Province de Liège</option><option>Province de Luxembourg</option>
          <option>Province de Namur</option><option>Province du Hainaut</option>
          <option>Province du Brabant wallon</option><option>Bruxelles</option>
        </select></div>
      <div class="field"><label>Nombre d'employés</label>
        <input type="number" name="employes" min="0" placeholder="Ex : 5"></div>
      <div class="field"><label>Budget annuel</label>
        <select name="budget_annuel">
          <option value="" disabled selected>Choisissez...</option>
          <option>Moins de 50 000 €</option><option>50 000 € à 200 000 €</option>
          <option>200 000 € à 500 000 €</option><option>Plus de 500 000 €</option>
        </select></div>
      <div class="field"><label>Année de création</label>
        <input type="number" name="annee_creation" min="1900" max="2026" placeholder="Ex : 2005"></div>
      <div class="field"><label>Public cible</label>
        <select name="public_cible">
          <option value="" disabled selected>Choisissez...</option>
          <option>Grand public</option><option>Jeunes</option><option>Personnes handicapées</option>
          <option>Demandeurs d'emploi</option><option>Artistes</option>
          <option>Agriculteurs</option><option>Entreprises</option><option>Autre</option>
        </select></div>
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
          <input type="checkbox" name="cofinancement" value="1" style="width:18px;height:18px;accent-color:#2D7A4F;flex-shrink:0">
          Je cherche des fonds complémentaires (cofinancement)
        </label></div>
      <div class="field"><label>Prénom *</label>
        <input type="text" name="contact" placeholder="Ex : Marie" required></div>
      <div class="field"><label>Email *</label>
        <input type="email" name="email" placeholder="marie@structure.be" required></div>
    </div>
    <div class="form-submit">
      <button type="submit" class="btn" style="font-size:1.05rem;padding:16px 44px">Créer mon profil</button>
      <p class="form-note">Accès gratuit pendant le pilote · Pas de carte · Désinscription en 1 clic</p>
    </div>
    </form>
  </div>
</div>
{footer()}
{NAV_SCROLL_JS}
{COUNTER_JS}
{REVEAL_JS}
</body></html>'''

def page_apropos():
    return f'''<!DOCTYPE html>
<html lang="fr"><head>
<title>À propos — GrantHound</title>
{HEAD}</head><body>
{nav('apropos')}
<div class="hero" style="min-height:50vh;padding:130px 5% 80px">
  {PARTICLES_JS}
  <div class="hero-content">
    <h1>À propos de <em>GrantHound</em></h1>
    <p>Développé par Noah Latour, 17 ans, Vielsalm.</p>
  </div>
</div>
{ticker()}
<div class="section">
  <p class="section-tag reveal">Notre mission</p>
  <h2 class="reveal">Démocratiser l'accès aux subsides wallons</h2>
  <p class="reveal" style="color:#555;line-height:1.8;max-width:700px">
    Des centaines d'ASBL passent à côté de financements faute de temps pour surveiller les appels à projets.
    GrantHound automatise cette veille et livre chaque semaine un rapport personnalisé.
  </p>
  <div class="cards" style="margin-top:40px">
    <div class="card reveal"><div class="card-icon">📊</div><h3>297+ aides surveillées</h3><p>MIDAS, FWB, 5 provinces wallonnes, Europe, Fondation Roi Baudouin, Loterie Nationale.</p></div>
    <div class="card reveal"><div class="card-icon">🤖</div><h3>IA Gemini 2.5 Flash</h3><p>Chaque aide est analysée pour évaluer sa pertinence par rapport à votre profil unique.</p></div>
    <div class="card reveal"><div class="card-icon">📅</div><h3>Rapport hebdomadaire</h3><p>Chaque lundi : les aides pertinentes, séparées entre connues et méconnues.</p></div>
  </div>
  <div style="margin-top:48px;background:#fff;border-radius:12px;padding:32px;border:1px solid #e8e6e0" class="reveal">
    <h3 style="color:var(--navy);margin-bottom:12px">Contact</h3>
    <p style="color:#555;line-height:1.9">
      Email : noahlatour77@gmail.com<br>
      Tél : 0491 63 76 89<br>
      Vielsalm, Province de Luxembourg, Belgique
    </p>
  </div>
</div>
{footer()}
{NAV_SCROLL_JS}
{REVEAL_JS}
</body></html>'''

def page_contact(alert=''):
    return f'''<!DOCTYPE html>
<html lang="fr"><head>
<title>Contact — GrantHound</title>
{HEAD}</head><body>
{nav('contact')}
<div class="form-wrap" style="padding-top:120px;min-height:100vh">
  <div class="form-inner">
    <h2>Contactez-nous</h2>
    <p class="sub">Réponse sous 24h · noahlatour77@gmail.com · 0491 63 76 89</p>
    {alert}
    <form method="POST" action="/message">
    <div class="form-grid">
      <div class="field"><label>Nom *</label>
        <input type="text" name="nom" placeholder="Marie Dupont" required></div>
      <div class="field"><label>Email *</label>
        <input type="email" name="email" placeholder="marie@structure.be" required></div>
      <div class="field full"><label>Sujet *</label>
        <input type="text" name="sujet" placeholder="Votre sujet..." required></div>
      <div class="field full"><label>Message *</label>
        <textarea name="message" rows="6" placeholder="Votre message..." required></textarea></div>
    </div>
    <div class="form-submit">
      <button type="submit" class="btn" style="font-size:1.05rem;padding:14px 40px">Envoyer</button>
    </div>
    </form>
  </div>
</div>
{footer()}
{NAV_SCROLL_JS}
</body></html>'''

# ── HTTP Handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f'[{self.address_string()}] {fmt % args}')

    def send_html(self, html, code=200):
        body = html.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/':
            self.send_html(page_home())
        elif path == '/apropos':
            self.send_html(page_apropos())
        elif path == '/contact':
            self.send_html(page_contact())
        else:
            self.send_html('<h1 style="font-family:sans-serif;padding:40px">404 — Page introuvable</h1>', 404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length).decode('utf-8')
        parsed = parse_qs(raw, keep_blank_values=True)
        data = {k: (v if len(v) > 1 else v[0]) for k, v in parsed.items()}

        if path == '/inscrire':
            projets = data.get('projets', [])
            if isinstance(projets, str):
                projets = [projets]
            data['projets'] = ', '.join(projets)
            ok, err = save_client(data)
            if ok:
                prenom = data.get('contact', '')
                nom = data.get('nom', '')
                email = data.get('email', '')
                province = data.get('province', '')
                send_email(
                    email,
                    'Bienvenue sur GrantHound !',
                    f'''<div style="font-family:Inter,sans-serif;max-width:600px;margin:auto;padding:32px">
                      <h2 style="color:#0B1F3A;font-family:Sora,sans-serif">Bienvenue, {prenom} !</h2>
                      <p style="color:#444;line-height:1.8;margin-top:16px">
                        Votre profil <strong>{nom}</strong> a bien été créé sur GrantHound.<br>
                        Vous recevrez votre premier rapport de subsides personnalisé sous 7 jours.
                      </p>
                      <p style="color:#888;font-size:.85rem;margin-top:32px">GrantHound — Vielsalm, Belgique</p>
                    </div>'''
                )
                send_email(
                    ADMIN_EMAIL,
                    f'[GrantHound] Nouvelle inscription : {nom}',
                    f'''<p>Nouvelle inscription :</p>
                      <ul>
                        <li>Structure : {nom}</li>
                        <li>Email : {email}</li>
                        <li>Province : {province}</li>
                        <li>Type : {data.get("type","")}</li>
                        <li>Secteur : {data.get("secteur","")}</li>
                      </ul>'''
                )
                self.send_html(page_home(
                    '<div class="alert alert-ok">✓ Inscription réussie ! Consultez votre boîte mail.</div>'
                ))
            elif err == 'exists':
                self.send_html(page_home(
                    '<div class="alert alert-err">Cet email est déjà inscrit.</div>'
                ))
            else:
                self.send_html(page_home(
                    '<div class="alert alert-err">Erreur serveur. Réessayez.</div>'
                ))

        elif path == '/message':
            d = {k: (v[0] if isinstance(v, list) else v) for k, v in data.items()}
            if all(d.get(f, '').strip() for f in ['nom', 'email', 'sujet', 'message']):
                send_email(
                    ADMIN_EMAIL,
                    f'[GrantHound Contact] {d.get("sujet","")}',
                    f'''<p>De : {d.get("nom","")} ({d.get("email","")})</p>
                      <p style="margin-top:12px">{d.get("message","")}</p>'''
                )
                self.send_html(page_contact(
                    '<div class="alert alert-ok">✓ Message envoyé ! Réponse sous 24h.</div>'
                ))
            else:
                self.send_html(page_contact(
                    '<div class="alert alert-err">Veuillez remplir tous les champs.</div>'
                ))
        else:
            self.send_html('<h1>404</h1>', 404)

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'[GrantHound] démarré sur http://0.0.0.0:{PORT}')
    server.serve_forever()