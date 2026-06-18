import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import config
import database
import mailer

BASE_DIR = os.path.dirname(__file__)


class Handler(BaseHTTPRequestHandler):
    ROUTES = {
        "/": "index.html",
        "/comment-ca-marche": "how_it_works.html",
        "/tarifs": "pricing.html",
        "/inscription": "signup.html",
        "/a-propos": "about.html",
        "/contact": "contact.html",
    }

    MIME = {
        ".css": "text/css",
        ".js": "application/javascript",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff2": "font/woff2",
    }

    # ------------------------------------------------------------------ GET
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"
        qs = urllib.parse.parse_qs(self.path.split("?")[1]) if "?" in self.path else {}

        if path.startswith("/static/"):
            self._serve_static(path)
        elif path in self.ROUTES:
            self._serve_template(self.ROUTES[path], query=qs)
        else:
            self._send_404()

    # ----------------------------------------------------------------- POST
    def do_POST(self):
        body = self._read_body()
        if self.path == "/api/signup":
            self._handle_signup(body)
        elif self.path == "/api/contact":
            self._handle_contact(body)
        else:
            self._send_404()

    # ------------------------------------------------------------ internals
    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))

    def _serve_static(self, path):
        fpath = os.path.join(BASE_DIR, path.lstrip("/").replace("/", os.sep))
        if not os.path.isfile(fpath):
            self._send_404()
            return
        ext = os.path.splitext(fpath)[1]
        ctype = self.MIME.get(ext, "application/octet-stream")
        with open(fpath, "rb") as f:
            data = f.read()
        self._respond(200, ctype, data)

    def _serve_template(self, name: str, query: dict = None):
        fpath = os.path.join(BASE_DIR, "templates", name)
        with open(fpath, "r", encoding="utf-8") as f:
            html = f.read()
        # Inject flash messages
        success = bool(query and query.get("success"))
        error = bool(query and query.get("error"))
        html = html.replace("{{FLASH_SUCCESS}}", "flash-show" if success else "")
        html = html.replace("{{FLASH_ERROR}}", "flash-show" if error else "")
        self._respond(200, "text/html; charset=utf-8", html.encode("utf-8"))

    def _handle_signup(self, data):
        name = data.get("name", [""])[0].strip()
        email = data.get("email", [""])[0].strip()
        plan = data.get("plan", ["starter"])[0].strip()
        asbl = data.get("asbl", [""])[0].strip()
        if not name or not email:
            self._redirect("/inscription?error=1")
            return
        try:
            database.save_signup(name, email, plan, asbl)
            try:
                mailer.send_confirmation(email, name, plan)
            except Exception:
                pass  # don't block on mail failure
            self._redirect("/inscription?success=1")
        except Exception:
            self._redirect("/inscription?error=1")

    def _handle_contact(self, data):
        name = data.get("name", [""])[0].strip()
        email = data.get("email", [""])[0].strip()
        subject = data.get("subject", [""])[0].strip()
        message = data.get("message", [""])[0].strip()
        if not name or not email or not message:
            self._redirect("/contact?error=1")
            return
        try:
            database.save_contact(name, email, message, subject)
            try:
                mailer.send_contact_notification(name, email, message, subject)
            except Exception:
                pass
            self._redirect("/contact?success=1")
        except Exception:
            self._redirect("/contact?error=1")

    def _redirect(self, url: str):
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

    def _respond(self, code: int, ctype: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self):
        body = "<h1>404 &mdash; Page introuvable</h1>".encode("utf-8")
        self._respond(404, "text/html", body)

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    database.init_db()
    srv = HTTPServer(("0.0.0.0", config.PORT), Handler)
    print(f"\n  GrantHound  →  http://localhost:{config.PORT}\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Arrêt du serveur.")
