import hmac
import secrets
from functools import wraps

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db, mail
from app.models import User, Question, Choice, MODULE_SLUGS, MODULE_LABELS
from app.seed import run_seed
from flask_mail import Message

admin_bp = Blueprint("admin", __name__)


def _check_seed_token():
    token = request.args.get("token", "")
    expected = current_app.config.get("SEED_TOKEN") or current_app.config["SECRET_KEY"]
    if not token or not expected or not hmac.compare_digest(token, expected):
        abort(404)


@admin_bp.route("/seed")
def seed_once():
    """One-time bootstrap for a freshly-deployed database with no shell access
    (e.g. Railway). Protected by the app's SECRET_KEY as a bearer token rather
    than a login, since there's no admin account to log in with yet on a brand
    new database. Safe to call more than once — it only adds what's missing."""
    _check_seed_token()
    summary, admin_created = run_seed()
    lines = list(summary)
    if admin_created:
        lines.append("Created admin user admin@example.com / change-this-password — log in and change this immediately.")
    else:
        lines.append("Admin user already existed — left as-is.")
    return "<br>".join(lines), 200


@admin_bp.route("/create-admin")
def create_admin():
    """Create (or promote) an admin account by email, for when there's no
    shell access to run this by hand. Same token-protected pattern as
    /admin/seed. If the email already has an account, it's promoted to admin
    in place and its password is left untouched — unless ?reset=1 is passed,
    in which case a fresh password is generated and shown once, overwriting
    whatever was there before. If the account doesn't exist yet, it's created
    with a randomly generated password shown once in the response — nowhere
    else, so copy it immediately and change it after logging in."""
    _check_seed_token()
    email = (request.args.get("email") or "").strip().lower()
    reset = request.args.get("reset") == "1"
    if not email or "@" not in email:
        return "Missing or invalid ?email=", 400

    user = User.query.filter_by(email=email).first()
    if user:
        changed = []
        if not user.is_admin:
            user.is_admin = True
            changed.append("promoted to admin")
        if reset:
            generated_password = secrets.token_urlsafe(12)
            user.set_password(generated_password)
            changed.append("password reset")
        db.session.commit()
        if not changed:
            return f"{email} is already an admin. No changes made.", 200
        msg = f"{email}: {', '.join(changed)}."
        if reset:
            msg += (
                f"<br>New password: {generated_password}"
                "<br><br>This password is shown once and not stored anywhere else."
            )
        else:
            msg += " Existing password unchanged."
        return msg, 200

    generated_password = secrets.token_urlsafe(12)
    user = User(email=email, full_name="Admin", is_admin=True)
    user.set_password(generated_password)
    db.session.add(user)
    db.session.commit()
    return (
        f"Created admin account.<br>Email: {email}<br>Password: {generated_password}"
        "<br><br>This password is shown once and not stored anywhere else — "
        "log in now and change it from your account settings.",
        200,
    )


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/")
@admin_required
def index():
    counts = {
        slug: Question.query.filter_by(module_slug=slug).count() for slug in MODULE_SLUGS
    }
    return render_template("admin/index.html", modules=MODULE_LABELS, counts=counts)


@admin_bp.route("/module/<module_slug>")
@admin_required
def module_questions(module_slug):
    if module_slug not in MODULE_SLUGS:
        abort(404)
    questions = (
        Question.query.filter_by(module_slug=module_slug)
        .order_by(Question.created_at.desc())
        .all()
    )
    return render_template(
        "admin/module_questions.html",
        module_slug=module_slug,
        module_label=MODULE_LABELS[module_slug],
        questions=questions,
    )


@admin_bp.route("/module/<module_slug>/question/new", methods=["GET", "POST"])
@admin_required
def new_question(module_slug):
    if module_slug not in MODULE_SLUGS:
        abort(404)

    if request.method == "POST":
        question = _save_question_form(module_slug, None)
        flash("Question added.", "success")
        return redirect(url_for("admin.module_questions", module_slug=module_slug))

    return render_template(
        "admin/question_form.html",
        module_slug=module_slug,
        module_label=MODULE_LABELS[module_slug],
        question=None,
    )


@admin_bp.route("/question/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.question_type != "mcq":
        # This form only knows how to author plain multiple-choice questions
        # (it always requires 2+ choice fields). Fill-in-the-blank and
        # reading-passage questions are authored in app/seed.py for now —
        # editing one here would just dead-end on the required choice fields.
        flash(
            "This question type (fill-in-the-blank / reading passage) isn't editable "
            "in the admin UI yet — update it in app/seed.py and redeploy, or deactivate "
            "it below and add a replacement.",
            "info",
        )
        return redirect(url_for("admin.module_questions", module_slug=question.module_slug))

    if request.method == "POST":
        _save_question_form(question.module_slug, question)
        flash("Question updated.", "success")
        return redirect(url_for("admin.module_questions", module_slug=question.module_slug))

    return render_template(
        "admin/question_form.html",
        module_slug=question.module_slug,
        module_label=MODULE_LABELS[question.module_slug],
        question=question,
    )


@admin_bp.route("/question/<int:question_id>/delete", methods=["POST"])
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    module_slug = question.module_slug
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.", "info")
    return redirect(url_for("admin.module_questions", module_slug=module_slug))


@admin_bp.route("/question/<int:question_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_active(question_id):
    question = Question.query.get_or_404(question_id)
    question.is_active = not question.is_active
    db.session.commit()
    return redirect(url_for("admin.module_questions", module_slug=question.module_slug))


@admin_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@admin_required
def new_user():
    """Create a customer account directly from the admin panel — useful for
    comp accounts, pilot learners, or support, without waiting on Stripe or
    asking the learner to self-register. An admin can type a specific password
    (e.g. one agreed with the learner over the phone) or leave it blank to
    auto-generate one, shown once on-screen."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        full_name = (request.form.get("full_name") or "").strip()
        grant_days = request.form.get("grant_days", type=int)
        chosen_password = (request.form.get("password") or "").strip()

        if not email or "@" not in email:
            flash("Enter a valid email address.", "error")
        elif chosen_password and len(chosen_password) < 8:
            flash("Password must be at least 8 characters, or leave it blank to auto-generate one.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            password = chosen_password or secrets.token_urlsafe(12)
            was_generated = not chosen_password
            user = User(email=email, full_name=full_name)
            user.set_password(password)
            if grant_days:
                user.grant_initial_access(grant_days)
            db.session.add(user)
            db.session.commit()

            email_sent = _send_welcome_email(user, password)

            msg = f"Account created for {email}."
            if grant_days:
                msg += f" Access granted for {grant_days} days."
            if email_sent:
                msg += " Login details were emailed to them."
            elif was_generated:
                msg += (
                    f" One-time password (not stored anywhere else — copy it now): "
                    f"{password}"
                )
            else:
                msg += " They can log in with the password you set."
            flash(msg, "success")
            return redirect(url_for("admin.users"))

    return render_template("admin/user_form.html")


@admin_bp.route("/users/<int:user_id>/grant-access", methods=["POST"])
@admin_required
def grant_access(user_id):
    user = User.query.get_or_404(user_id)
    days = request.form.get("days", type=int)
    if not days or days <= 0:
        flash("Enter a valid number of days.", "error")
    else:
        user.grant_initial_access(days)
        db.session.commit()
        flash(f"Granted {user.email} {days} more days of access.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def reset_user_password(user_id):
    """Set a customer account's password — either to a specific value the
    admin types in, or auto-generated (shown on-screen) if left blank.
    Doesn't rely on email delivery, which may not be configured."""
    user = User.query.get_or_404(user_id)
    chosen_password = (request.form.get("password") or "").strip()

    if chosen_password and len(chosen_password) < 8:
        flash("Password must be at least 8 characters, or leave it blank to auto-generate one.", "error")
        return redirect(url_for("admin.users"))

    password = chosen_password or secrets.token_urlsafe(12)
    was_generated = not chosen_password
    user.set_password(password)
    db.session.commit()

    email_sent = _send_welcome_email(user, password)
    if email_sent:
        flash(f"Password reset for {user.email} and emailed to them.", "success")
    elif was_generated:
        flash(
            f"Password reset for {user.email}. New password (not stored anywhere "
            f"else — copy it now): {password}",
            "success",
        )
    else:
        flash(f"Password set for {user.email}. They can log in with the password you chose.", "success")
    return redirect(url_for("admin.users"))


def _send_welcome_email(user: User, password: str) -> bool:
    msg = Message(
        subject=f"Your {current_app.config['APP_NAME']} account",
        recipients=[user.email],
        body=(
            f"Hi {user.full_name or ''},\n\n"
            f"An account has been set up for you on {current_app.config['APP_NAME']}.\n\n"
            f"Email: {user.email}\n"
            f"Temporary password: {password}\n\n"
            f"Log in and change your password from your account settings once you're in."
        ),
    )
    try:
        mail.send(msg)
        return True
    except Exception:
        current_app.logger.exception("Failed to send welcome email to %s", user.email)
        return False


def _save_question_form(module_slug: str, question):
    """Shared create/update logic. The form submits up to 5 choice rows
    (choice_1..choice_5) and a single correct_choice radio value."""
    prompt = request.form.get("prompt", "").strip()
    topic = request.form.get("topic", "").strip()
    explanation = request.form.get("explanation", "").strip()
    correct_index = request.form.get("correct_choice")

    if question is None:
        question = Question(module_slug=module_slug)
        db.session.add(question)
    else:
        # Replace choices wholesale on edit — simpler and safe since choices
        # have no other foreign keys pointing at them once an attempt exists
        # (AttemptAnswer stores the historical choice_id separately and a
        # question shouldn't normally be edited after it's been answered —
        # prefer deactivating + creating a new question for substantive changes).
        for c in list(question.choices):
            db.session.delete(c)

    question.prompt = prompt
    question.topic = topic or None
    question.explanation = explanation or None

    for i in range(1, 6):
        text = request.form.get(f"choice_{i}", "").strip()
        if not text:
            continue
        db.session.add(
            Choice(question=question, text=text, is_correct=(correct_index == str(i)))
        )

    db.session.commit()
    return question
