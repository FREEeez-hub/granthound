"""
Quick launcher — sets env vars then starts the server.
Edit GMAIL_USER and GMAIL_APP_PASSWORD before first run.
"""
import os
os.environ.setdefault("GMAIL_USER",         "votre@gmail.com")
os.environ.setdefault("GMAIL_APP_PASSWORD", "xxxx xxxx xxxx xxxx")
os.environ.setdefault("NOTIFY_EMAIL",       "votre@gmail.com")
os.environ.setdefault("PORT",               "8000")

import server  # noqa: E402  (runs __main__ block)
