from datetime import datetime

import stripe
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User

billing_bp = Blueprint("billing", __name__)


def _stripe():
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    return stripe


@billing_bp.route("/pricing")
@login_required
def pricing():
    cfg = current_app.config
    return render_template(
        "learning/pricing.html",
        initial_price=cfg["INITIAL_ACCESS_PRICE_GBP"],
        initial_days=cfg["INITIAL_ACCESS_DAYS"],
        continuation_price=cfg["CONTINUATION_PRICE_GBP"],
        has_access=current_user.has_access,
        ever_purchased=current_user.access_until is not None,
    )


# ---------------------------------------------------------------------------
# Phase 1 — one-off payment, no subscription object. Stripe Checkout in
# "payment" mode. The webhook (checkout.session.completed) is what actually
# grants access; the success_url is just where the user lands.
# ---------------------------------------------------------------------------

@billing_bp.route("/checkout/initial", methods=["POST"])
@login_required
def checkout_initial():
    client = _stripe()
    cfg = current_app.config

    if not current_user.stripe_customer_id:
        customer = client.Customer.create(email=current_user.email)
        current_user.stripe_customer_id = customer.id
        db.session.commit()

    checkout_session = client.checkout.Session.create(
        mode="payment",
        customer=current_user.stripe_customer_id,
        line_items=[{"price": cfg["STRIPE_INITIAL_PRICE_ID"], "quantity": 1}],
        success_url=cfg["APP_URL"] + url_for("billing.success"),
        cancel_url=cfg["APP_URL"] + url_for("billing.pricing"),
        metadata={"user_id": current_user.id, "kind": "initial_access"},
    )
    return redirect(checkout_session.url, code=303)


# ---------------------------------------------------------------------------
# Phase 2 — only ever reached when the user explicitly clicks through
# (from the pricing page, or the lapsed-access email) to opt in. An ordinary,
# freely-cancellable monthly subscription; cancellation is self-serve below.
# ---------------------------------------------------------------------------

@billing_bp.route("/checkout/continue", methods=["POST"])
@login_required
def checkout_continuation():
    client = _stripe()
    cfg = current_app.config

    if not current_user.stripe_customer_id:
        customer = client.Customer.create(email=current_user.email)
        current_user.stripe_customer_id = customer.id
        db.session.commit()

    checkout_session = client.checkout.Session.create(
        mode="subscription",
        customer=current_user.stripe_customer_id,
        line_items=[{"price": cfg["STRIPE_CONTINUATION_PRICE_ID"], "quantity": 1}],
        success_url=cfg["APP_URL"] + url_for("billing.success"),
        cancel_url=cfg["APP_URL"] + url_for("billing.pricing"),
        metadata={"user_id": current_user.id, "kind": "continuation"},
    )
    return redirect(checkout_session.url, code=303)


@billing_bp.route("/cancel-continuation", methods=["POST"])
@login_required
def cancel_continuation():
    """Self-serve cancellation — kept to one click, per the 'tell them clearly
    how to cancel whenever they wish' decision."""
    if current_user.continuation_subscription_id:
        client = _stripe()
        try:
            client.Subscription.delete(current_user.continuation_subscription_id)
        except stripe.error.StripeError:
            current_app.logger.exception("Failed to cancel subscription for user %s", current_user.id)
            flash("Something went wrong cancelling — please try again or email us.", "error")
            return redirect(url_for("billing.pricing"))

    current_user.continuation_active = False
    current_user.continuation_subscription_id = None
    db.session.commit()
    flash("Your subscription has been cancelled. You won't be charged again.", "success")
    return redirect(url_for("billing.pricing"))


@billing_bp.route("/success")
@login_required
def success():
    flash("Payment received — thanks!", "success")
    return redirect(url_for("learning.dashboard"))


# ---------------------------------------------------------------------------
# Webhook — the only place access is actually granted/revoked. Everything
# above just starts a Checkout Session; Stripe telling us it succeeded is
# what's authoritative.
# ---------------------------------------------------------------------------

@billing_bp.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    cfg = current_app.config

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, cfg["STRIPE_WEBHOOK_SECRET"])
    except (ValueError, stripe.error.SignatureVerificationError):
        current_app.logger.warning("Stripe webhook signature verification failed")
        return "invalid signature", 400

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(data, cfg)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(data)
    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(data)

    return "", 200


def _user_from_session(data) -> User | None:
    user_id = (data.get("metadata") or {}).get("user_id")
    if user_id:
        return User.query.get(int(user_id))
    customer_id = data.get("customer")
    if customer_id:
        return User.query.filter_by(stripe_customer_id=customer_id).first()
    return None


def _handle_checkout_completed(data, cfg):
    user = _user_from_session(data)
    if not user:
        current_app.logger.warning("Webhook: no matching user for checkout session %s", data.get("id"))
        return

    kind = (data.get("metadata") or {}).get("kind")
    if kind == "initial_access" or data.get("mode") == "payment":
        user.grant_initial_access(cfg["INITIAL_ACCESS_DAYS"])
        db.session.commit()
    elif kind == "continuation" or data.get("mode") == "subscription":
        user.continuation_active = True
        user.continuation_subscription_id = data.get("subscription")
        db.session.commit()


def _handle_subscription_deleted(data):
    user = User.query.filter_by(continuation_subscription_id=data.get("id")).first()
    if user:
        user.continuation_active = False
        user.continuation_subscription_id = None
        db.session.commit()


def _handle_subscription_updated(data):
    # Covers e.g. a failed renewal payment eventually cancelling the
    # subscription — Stripe's status field is authoritative.
    user = User.query.filter_by(continuation_subscription_id=data.get("id")).first()
    if user:
        user.continuation_active = data.get("status") == "active"
        db.session.commit()
