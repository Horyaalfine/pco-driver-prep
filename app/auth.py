from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.extensions import db, mail
from app.models import User
from flask_mail import Message

auth_bp = Blueprint("auth", __name__)

RESET_SALT = "password-reset"
RESET_MAX_AGE_SECONDS = 60 * 60  # 1 hour


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("learning.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()

        if not email or "@" not in email:
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(email=email, full_name=full_name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome! Let's get you set up.", "success")
            return redirect(url_for("billing.pricing"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("learning.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("learning.dashboard"))
        flash("Incorrect email or password.", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        # Always show the same message, whether or not the account exists,
        # so we don't leak which emails are registered.
        if user:
            token = _serializer().dumps(user.email, salt=RESET_SALT)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            _send_reset_email(user, reset_url)
        flash("If that email is registered, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = _serializer().loads(token, salt=RESET_SALT, max_age=RESET_MAX_AGE_SECONDS)
    except SignatureExpired:
        flash("That reset link has expired. Please request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("That reset link is invalid.", "error")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("That reset link is invalid.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        else:
            user.set_password(password)
            db.session.commit()
            flash("Password updated. You can now log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """Change password while logged in — doesn't depend on email being
    configured, unlike the forgot-password flow."""
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "error")
        elif len(new_password) < 8:
            flash("New password must be at least 8 characters.", "error")
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("auth.account"))

    return render_template("auth/account.html")


def _send_reset_email(user: User, reset_url: str) -> None:
    msg = Message(
        subject=f"Reset your {current_app.config['APP_NAME']} password",
        recipients=[user.email],
        body=(
            f"Hi {user.full_name or ''},\n\n"
            f"Click the link below to reset your password. This link expires in 1 hour.\n\n"
            f"{reset_url}\n\n"
            f"If you didn't request this, you can ignore this email."
        ),
    )
    try:
        mail.send(msg)
    except Exception:
        current_app.logger.exception("Failed to send password reset email to %s", user.email)
