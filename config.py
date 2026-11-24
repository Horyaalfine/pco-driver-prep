import os
from datetime import timedelta


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL", "sqlite:///dev.db")
        # Railway/Heroku-style URLs sometimes come as postgres:// — SQLAlchemy needs postgresql://
        .replace("postgres://", "postgresql://", 1)
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Access / pricing model ---
    # First purchase: a one-off charge that grants N days of access. No subscription object
    # is created for this phase — it's a flat payment, tracked via User.access_until.
    INITIAL_ACCESS_PRICE_GBP = float(os.environ.get("INITIAL_ACCESS_PRICE_GBP", "36.00"))
    INITIAL_ACCESS_DAYS = int(os.environ.get("INITIAL_ACCESS_DAYS", "90"))  # ~3 months

    # Continuation: only created if the user opts in after their initial access lapses.
    # An ordinary, freely-cancellable Stripe subscription.
    CONTINUATION_PRICE_GBP = float(os.environ.get("CONTINUATION_PRICE_GBP", "5.00"))

    # --- Stripe ---
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    # Price IDs set up in the Stripe dashboard: one "payment" price for the £36 initial
    # block, one recurring monthly price for the £5 continuation.
    STRIPE_INITIAL_PRICE_ID = os.environ.get("STRIPE_INITIAL_PRICE_ID", "")
    STRIPE_CONTINUATION_PRICE_ID = os.environ.get("STRIPE_CONTINUATION_PRICE_ID", "")

    # --- Email (reuses the same pattern as FlexLog: SMTP via Namecheap Private Email,
    # or any standard SMTP provider — just set these env vars) ---
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "mail.privateemail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # --- Misc ---
    APP_NAME = os.environ.get("APP_NAME", "PCO Driver Prep")
    APP_URL = os.environ.get("APP_URL", "http://localhost:5000")
    # Used by the renewal-email task to avoid re-sending the same reminder.
    PRE_EXPIRY_REMINDER_DAYS = int(os.environ.get("PRE_EXPIRY_REMINDER_DAYS", "5"))

    REMEMBER_COOKIE_DURATION = timedelta(days=30)
