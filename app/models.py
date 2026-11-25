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

    # The real SERU exam mixes multiple-choice with sentence-completion
    # ("fill_blank") and short reading-and-understanding passages ("reading")
    # — see app/learning.py's SERU mock-exam composition. "mcq" (the
    # original/default type) and "reading" are both graded via Choice rows;
    # "fill_blank" has no choices at all and is graded against
    # accepted_answers instead.
    question_type = db.Column(db.String(20), default="mcq", nullable=False)
    # For fill_blank: list of acceptable answer strings (matched
    # case-insensitively, whitespace-trimmed). Null/unused for mcq/reading.
    accepted_answers = db.Column(db.JSON, nullable=True)
    # For reading: the shared passage text, shown once above the question.
    # Null/unused for mcq/fill_blank.
    passage = db.Column(db.Text, nullable=True)

    choices = db.relationship(
        "Choice", backref="question", cascade="all, delete-orphan", order_by="Choice.id"
    )

    @property
    def correct_choice(self):
        return next((c for c in self.choices if c.is_correct), None)

    def grade_text_answer(self, raw_answer: str) -> bool:
        """Grading for fill_blank questions: case-insensitive, trimmed match
        against any of the accepted answers."""
        if not raw_answer or not self.accepted_answers:
            return False
        normalised = raw_answer.strip().lower()
        return any(normalised == accepted.strip().lower() for accepted in self.accepted_answers)


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
    # Used instead of choice_id for fill_blank questions, which have no Choice rows.
    text_answer = db.Column(db.String(500), nullable=True)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

    question = db.relationship("Question")
    choice = db.relationship("Choice")


# ---------------------------------------------------------------------------
# Topographical route-planning exercises. The real TfL topographical
# assessment weights its 4 route-planning questions at 75% of the total
# score (the multiple-choice questions above are only 25%), so this is a
# separate, purpose-built exercise type rather than another Question row:
# the student is shown a schematic map and has to build a legal route
# themselves, rather than pick from 4 pre-written options.
#
# Maps are entirely original/fictional layouts (not real London streets or
# any licensed map data) built to practise the underlying skill — reading
# one-way restrictions and planning the most direct legal route — without
# any copyright or factual-currency risk from depicting real junctions.
# ---------------------------------------------------------------------------

class RouteMap(db.Model):
    __tablename__ = "route_maps"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    # {"nodes": {"A": {"label": str, "x": int, "y": int}, ...},
    #  "edges": [{"from": "A", "to": "B", "name": str,
    #             "oneway": null|"forward"|"reverse", "weight": number}, ...]}
    # oneway "forward" means only from->to is legal; "reverse" means only
    # to->from is legal; null/absent means the street is two-way.
    data = db.Column(db.JSON, nullable=False)

    scenarios = db.relationship(
        "RouteScenario", backref="route_map", cascade="all, delete-orphan"
    )


class RouteScenario(db.Model):
    __tablename__ = "route_scenarios"

    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey("route_maps.id"), nullable=False)
    module_slug = db.Column(db.String(32), nullable=False, default="topographical", index=True)
    topic = db.Column(db.String(120))
    start_node = db.Column(db.String(32), nullable=False)
    end_node = db.Column(db.String(32), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    attempts = db.relationship(
        "RouteAttempt", backref="scenario", cascade="all, delete-orphan"
    )


class RouteAttempt(db.Model):
    __tablename__ = "route_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    scenario_id = db.Column(db.Integer, db.ForeignKey("route_scenarios.id"), nullable=False)
    submitted_path = db.Column(db.JSON, nullable=False)  # list of node ids, in order
    is_legal = db.Column(db.Boolean, nullable=False)
    is_optimal = db.Column(db.Boolean, nullable=False)
    score_percent = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
