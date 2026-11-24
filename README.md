# PCO Driver Prep

Subscription e-learning app for new London PCO (private hire) drivers preparing for
the three TfL assessments: the English Language Requirement, SERU (Safety, Equality
and Regulatory Understanding), and the Topographical assessment.

Built on the same stack as the rest of the app suite: Flask + PostgreSQL, deployable
to Railway.

**This is an independent exam-preparation product. It is not affiliated with,
endorsed by, or run on behalf of Transport for London.**

## Pricing model

- **£36 for the first 90 days** (set via `INITIAL_ACCESS_DAYS`/`INITIAL_ACCESS_PRICE_GBP`) —
  a one-off Stripe payment, not a subscription. No card is charged again automatically.
- **Access simply ends** after that — nothing auto-renews.
- A scheduled task (`scripts/renewal_check.py`) emails the user a few days before
  expiry, and again right after it lapses, offering to **continue at £5/month**
  if they choose to. That's an ordinary, freely-cancellable Stripe subscription,
  only ever created if the user clicks through and opts in.
- Cancellation is one click, from the pricing page, at any time.

## Local setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real values
export FLASK_APP=run.py

flask db init          # first time only
flask db migrate -m "initial schema"
flask db upgrade

python seed_data.py    # sample questions + an admin user (admin@example.com / change-this-password)

flask run
```

Visit `http://localhost:5000`. Log in as the seeded admin to manage questions at `/admin`.
**Change the seeded admin password immediately** — `seed_data.py` prints a reminder.

## Stripe setup

1. In the Stripe dashboard, create two Prices:
   - A one-off ("one time") price for £36 → copy its ID into `STRIPE_INITIAL_PRICE_ID`.
   - A recurring monthly price for £5 → copy its ID into `STRIPE_CONTINUATION_PRICE_ID`.
2. Add a webhook endpoint pointing at `https://your-domain/billing/webhook`, subscribed to:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
3. Copy the webhook signing secret into `STRIPE_WEBHOOK_SECRET`.

Test end-to-end with Stripe's test card `4242 4242 4242 4242` before going live.

## Deploying to Railway

1. New Railway project → deploy from this repo (or `railway up` from this folder).
2. Attach a PostgreSQL plugin — Railway sets `DATABASE_URL` automatically.
3. Set the remaining environment variables from `.env.example` in the Railway service settings.
4. The `release` phase in the `Procfile` runs `flask db upgrade` automatically on each deploy.
5. **Set up the renewal-check cron job**: in Railway, add a second service (or a Railway
   Cron Job pointed at this same repo) running:
   ```
   python scripts/renewal_check.py
   ```
   once a day. This is the only thing that triggers the £5/month continuation offer —
   nothing else in the app does this automatically, by design.

## Project layout

```
app/
  __init__.py       app factory
  models.py         User, Question, Choice, Attempt, AttemptAnswer
  auth.py           register / login / logout / password reset
  learning.py       dashboard, modules, practice mode, timed mock exams
  billing.py        Stripe checkout (one-off + opt-in subscription) and webhook
  admin.py          question bank CRUD, gated on User.is_admin
  templates/, static/
scripts/
  renewal_check.py  daily cron: pre-expiry reminder + lapsed-access offer emails
seed_data.py        sample questions + admin user for a fresh database
```

## Content maintenance

TfL's rules for these three assessments have changed more than once in the last few
years (safeguarding content added to SERU in 2021, topographical rule changes in 2024,
fee changes in 2026). Treat the question bank as something to actively maintain, not a
one-off build — check TfL's Taxi & Private Hire notices periodically and update content
via `/admin` as rules shift.

## Not yet built (intentionally out of MVP scope)

- A fully interactive map-reading widget for the topographical module (it currently uses
  multiple-choice questions, same format as the other two modules). Flagged in the
  research doc as the strongest v2 differentiator versus competitor apps.
- Video/explainer lesson content per topic (currently text-only explanations after each
  practice question).
- Operator/fleet partnership tooling (bulk seats, branded sub-pages).
