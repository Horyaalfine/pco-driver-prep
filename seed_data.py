"""
Seeds a handful of sample questions per module so the app is demoable and the
admin UI has something to show, and creates a first admin user if one
doesn't exist yet. Replace/expand the real question bank via the admin
panel — this is not meant to be the final question bank, just a realistic
starting shape.

Usage: python seed_data.py

(For seeding a live deployment with no shell access — e.g. Railway — see
the one-time /admin/seed?token=... route in app/admin.py instead, which
calls the same app.seed.run_seed() function.)
"""
from app import create_app
from app.seed import run_seed


def run():
    app = create_app()
    with app.app_context():
        summary, admin_created = run_seed()
        for line in summary:
            print(f"Seeded {line}")
        if admin_created:
            print("Created admin user admin@example.com / change-this-password — change this immediately.")


if __name__ == "__main__":
    run()
