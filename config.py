import os
import re
from datetime import timedelta


def _normalize_database_url(raw: str) -> str:
    """Force the psycopg2 dialect explicitly, regardless of what scheme the host hands us.

    Heroku/Railway-style URLs sometimes arrive as postgres://, and some Railway
    Postgres templates hand out postgresql+psycopg:// (psycopg3) or an
    unqualified postgresql://. This app installs psycopg2-binary only (matching
    the rest of the app suite's stack) — and newer SQLAlchemy versions default
    an unqualified postgresql:// to the psycopg3 driver rather than psycopg2,
    so every variant is normalized to an explicit postgresql+psycopg2:// scheme
    rather than relying on whatever the installed SQLAlchemy's default is.
    SQLite URLs (used for local dev when DATABASE_URL is unset) pass through
    unchanged.
    """
    if raw.startswith("sqlite"):
        return raw
    return re.sub(r"^postgres(ql)?(\+\w+)?://", "postgresql+psycopg2://", raw, count=1)


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    # One-time token for GET /admin/seed (see app/admin.py). Not required —
    # falls back to SECRET_KEY if unset — but set independently is cleaner,
    # since it can be removed/rotated without touching the app's real secret.
    SEED_TOKEN = os.environ.get("SEED_TOKEN", "")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.environ.get("DATABASE_URL", "sqlite:///dev.db")
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

    # --- AI speaking feedback (ELR) ---
    # Transcribes a learner's recorded speaking answer and grades it against a
    # rubric via the OpenAI API. Entirely optional at runtime: if OPENAI_API_KEY
    # is unset, the feature degrades to a clear "not available" message rather
    # than erroring, so the rest of the app is unaffected. Model names are
    # configurable because OpenAI periodically retires models (e.g. whisper-1
    # and gpt-4o-mini-transcribe are both scheduled for shutdown Feb 2027) —
    # swapping the replacement in is then just an env var change, no deploy.
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_TRANSCRIBE_MODEL = os.environ.get("OPENAI_TRANSCRIBE_MODEL", "gpt-transcribe")
    OPENAI_GRADING_MODEL = os.environ.get("OPENAI_GRADING_MODEL", "gpt-4o-mini")
    # Reads each speaking prompt's question aloud (an "examiner" voice), so
    # practice matches the real interview's listen-then-speak format rather
    # than the learner reading the question themselves. Cached per prompt
    # (see SpeakingPrompt.question_audio) so this runs once per question ever,
    # not once per playback — at $15/1M characters and ~100-150 characters a
    # question, the one-off cost for the whole prompt bank is a few cents.
    OPENAI_TTS_MODEL = os.environ.get("OPENAI_TTS_MODEL", "tts-1")
    OPENAI_TTS_VOICE = os.environ.get("OPENAI_TTS_VOICE", "onyx")
    # Cost/abuse safeguard: a hard cap on graded recordings per user per day.
    # At ~$0.005/recording this is pennies even at the cap, but prevents a
    # runaway script (or a bug) from generating an unbounded API bill.
    SPEAKING_GRADING_DAILY_LIMIT = int(os.environ.get("SPEAKING_GRADING_DAILY_LIMIT", "20"))

    # --- Misc ---
    APP_NAME = os.environ.get("APP_NAME", "PCO Driver Prep")
    APP_URL = os.environ.get("APP_URL", "http://localhost:5000")
    # Used by the renewal-email task to avoid re-sending the same reminder.
    PRE_EXPIRY_REMINDER_DAYS = int(os.environ.get("PRE_EXPIRY_REMINDER_DAYS", "5"))

    REMEMBER_COOKIE_DURATION = timedelta(days=30)
