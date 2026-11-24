#!/usr/bin/env python
"""
Scheduled task: find users whose access is about to lapse or has just lapsed,
and email them. Run this daily via Railway's cron feature (or any scheduler):

    python scripts/renewal_check.py

This is intentionally a standalone script rather than a Flask route — it's
meant to be triggered by the platform's scheduler, not by a web request, and
keeping it separate means it can be cron'd without exposing an endpoint.

Two emails only, matching the agreed model (no auto-renewal — ever):
  1. Pre-expiry reminder, sent once, PRE_EXPIRY_REMINDER_DAYS before access_until.
     "Your access ends in N days."
  2. Lapsed-access offer, sent once, right after access_until passes (for anyone
     who hasn't already opted into the continuation).
     "Your access has ended — continue for £5/month, cancel any time."
"""
import os
import sys
from datetime import datetime, timedelta

from flask_mail import Message

# Allow running as `python scripts/renewal_check.py` from the repo root (as the
# README and Railway cron setup both do) without needing the package installed
# or PYTHONPATH set manually.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db, mail
from app.models import User


def run():
    app = create_app()
    with app.app_context():
        _send_pre_expiry_reminders(app)
        _send_lapsed_offers(app)


def _send_pre_expiry_reminders(app):
    now = datetime.utcnow()
    window_end = now + timedelta(days=app.config["PRE_EXPIRY_REMINDER_DAYS"])

    candidates = User.query.filter(
        User.access_until.isnot(None),
        User.access_until > now,
        User.access_until <= window_end,
        User.pre_expiry_reminder_sent_at.is_(None),
    ).all()

    for user in candidates:
        days_left = (user.access_until - now).days
        sent = _send(
            app,
            user,
            subject=f"Your {app.config['APP_NAME']} access ends in {days_left} days",
            template="pre_expiry_reminder",
            days_left=days_left,
        )
        if sent:
            user.pre_expiry_reminder_sent_at = now
            db.session.commit()
            print(f"Sent pre-expiry reminder to {user.email}")
        else:
            print(f"FAILED to send pre-expiry reminder to {user.email} — will retry next run")


def _send_lapsed_offers(app):
    now = datetime.utcnow()

    candidates = User.query.filter(
        User.access_until.isnot(None),
        User.access_until <= now,
        User.continuation_active.is_(False),
        User.lapsed_offer_sent_at.is_(None),
    ).all()

    for user in candidates:
        sent = _send(
            app,
            user,
            subject=f"Your {app.config['APP_NAME']} access has ended",
            template="lapsed_offer",
        )
        if sent:
            user.lapsed_offer_sent_at = now
            db.session.commit()
            print(f"Sent lapsed-access offer to {user.email}")
        else:
            print(f"FAILED to send lapsed-access offer to {user.email} — will retry next run")


def _send(app, user, subject, template, **context):
    continue_url = app.config["APP_URL"] + "/billing/pricing"
    if template == "pre_expiry_reminder":
        body = (
            f"Hi {user.full_name or ''},\n\n"
            f"Just a heads up — your {app.config['APP_NAME']} access ends in "
            f"{context['days_left']} days.\n\n"
            f"If you haven't passed all three TfL assessments yet, you can carry on "
            f"afterwards for £{app.config['CONTINUATION_PRICE_GBP']:.0f}/month — cancel "
            f"any time, no notice needed:\n\n{continue_url}\n\n"
            f"Nothing happens automatically — we won't charge you unless you choose to.\n"
        )
    else:  # lapsed_offer
        body = (
            f"Hi {user.full_name or ''},\n\n"
            f"Your {app.config['APP_NAME']} access has now ended. It was never set to "
            f"renew automatically, so you haven't been charged.\n\n"
            f"If you still need to pass one or more of the TfL assessments, you can "
            f"continue for £{app.config['CONTINUATION_PRICE_GBP']:.0f}/month — cancel "
            f"whenever you like, right from your account:\n\n{continue_url}\n\n"
            f"Good luck with the rest of your licence application either way.\n"
        )

    msg = Message(subject=subject, recipients=[user.email], body=body)
    try:
        mail.send(msg)
        return True
    except Exception:
        app.logger.exception("Failed to send '%s' email to %s", template, user.email)
        return False


if __name__ == "__main__":
    run()
