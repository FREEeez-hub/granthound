import os

PORT = int(os.environ.get("PORT", 8000))
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "granthound.db")

GMAIL_USER         = os.environ.get("GMAIL_USER",         "noahlatour77@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "bvtc iemw wxon fcmi")
NOTIFY_EMAIL       = os.environ.get("NOTIFY_EMAIL",       "noahlatour77@gmail.com")

PLANS = {
    "veille":  {"name": "Veille Active",  "price": "19€/mois"},
    "pro":     {"name": "Pro",            "price": "35€/mois"},
    "cabinet": {"name": "Cabinet",        "price": "89€/mois"},
    # compat ancien
    "starter": {"name": "Veille Active",  "price": "19€/mois"},
    "expert":  {"name": "Cabinet",        "price": "89€/mois"},
}
