from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db

# The three TfL assessments this app prepares learners for. Keeping this as a
# plain string/enum (rather than a free-text name) makes it cheap to route,
# gate access, and tag questions consistently across the app.
MODULE_SLUGS = ("elr", "seru", "topographical")

MODULE_LABELS = {
    "elr": "English Language Requirement (ELR)",
    "seru": "SERU — Safety, Equality & Regulatory Understanding",
    "topographical": "Topographical Assessment",
}


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Access state ---
    # Phase 1: set when the one-off £36 payment succeeds. No Stripe subscription
    # object exists for this phase — access is just "now < access_until".
    access_until = db.Column(db.DateTime, nullable=True)

    # Phase 2: only populated if the user opts in to the £5/month continuation
    # after phase 1 lapses. A real, freely-cancellable Stripe subscription.
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    continuation_subscription_id = db.Column(db.String(255), nullable=True)
    continuation_active = db.Column(db.Boolean, default=False, nullable=False)

    # Tracks whether the pre-expiry and lapsed-access emails have already been
    # sent for the *current* access_until, so the renewal-check task never
    # double-sends if it runs more than once around the same date.
    pre_expiry_reminder_sent_at = db.Column(db.DateTime, nullable=True)
    lapsed_offer_sent_at = db.Column(db.DateTime, nullable=True)

    attempts = db.relationship(
        "Attempt", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def has_access(self) -> bool:
        """Single source of truth for "can this user use the paid content right now".
        True if still inside the initial paid window OR the opt-in continuation
        subscription is active. Admins always have access — they manage the
        question bank and shouldn't be paywalled out of the app they run."""
        if self.is_admin:
            return True
        if self.access_until and self.access_until > datetime.utcnow():
            return True
        return bool(self.continuation_active)

    def grant_initial_access(self, days: int) -> None:
        """Called from the Stripe webhook on successful one-off payment."""
        now = datetime.utcnow()
        base = self.access_until if (self.access_until and self.access_until > now) else now
        self.access_until = base + timedelta(days=days)
        # A fresh purchase means any previous reminder flags no longer apply.
        self.pre_expiry_reminder_sent_at = None
        self.lapsed_offer_sent_at = None

    def progress_for(self, module_slug: str) -> dict:
        """Lightweight progress summary for a module: best mock-exam score and
        total questions answered, used on the dashboard."""
        q = self.attempts.filter_by(module_slug=module_slug, is_mock_exam=True)
        best = None
        for attempt in q:
            if attempt.score_percent is not None and (best is None or attempt.score_percent > best):
                best = attempt.score_percent
        answered = (
            db.session.query(db.func.count(AttemptAnswer.id))
            .join(Attempt, Attempt.id == AttemptAnswer.attempt_id)
            .filter(Attempt.user_id == self.id, Attempt.module_slug == module_slug)
            .scalar()
        )
        return {"best_mock_score": best, "questions_answered": answered or 0}


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    module_slug = db.Column(db.String(32), nullable=False, index=True)
    topic = db.Column(db.String(120))  # e.g. "Safeguarding", "Compass directions"
    prompt = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)  # shown after answering, reinforces learning
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    choices = db.relationship(
        "Choice", backref="question", cascade="all, delete-orphan", order_by="Choice.id"
    )

    @property
    def correct_choice(self):
        return next((c for c in self.choices if c.is_correct), None)


class Choice(db.Model):
    __tablename__ = "choices"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)


class Attempt(db.Model):
    """One practice session or mock exam. is_mock_exam distinguishes a timed,
    scored run (used for dashboard progress) from casual practice."""
    __tablename__ = "attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    module_slug = db.Column(db.String(32), nullable=False, index=True)
    is_mock_exam = db.Column(db.Boolean, default=False, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    score_percent = db.Column(db.Float, nullable=True)

    answers = db.relationship("AttemptAnswer", backref="attempt", cascade="all, delete-orphan")

    def finalise(self) -> None:
        total = len(self.answers)
        if total:
            correct = sum(1 for a in self.answers if a.is_correct)
            self.score_percent = round(100 * correct / total, 1)
        self.finished_at = datetime.utcnow()


class AttemptAnswer(db.Model):
    __tablename__ = "attempt_answers"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    choice_id = db.Column(db.Integer, db.ForeignKey("choices.id"), nullable=True)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

    question = db.relationship("Question")
    choice = db.relationship("Choice")
