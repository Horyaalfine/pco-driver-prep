"""
Sample question bank + admin bootstrap, shared by:
- seed_data.py (CLI, for local dev)
- app/admin.py's one-time /admin/seed route (for seeding a live database
  where there's no shell access, e.g. Railway)

Replace/expand the real question bank via the admin UI — this is just a
realistic starting shape, not the final content.
"""
from app.extensions import db
from app.models import Question, Choice, User

SEED_QUESTIONS = {
    "elr": [
        {
            "topic": "Reading comprehension",
            "prompt": "A passenger says: 'Could you drop me a bit further down, just past the lights?' What does the passenger want?",
            "choices": [
                ("To stop before the traffic lights", False),
                ("To stop a short distance after the traffic lights", True),
                ("To turn around at the lights", False),
                ("To wait at the lights", False),
            ],
            "explanation": "'Further down, just past the lights' means a short distance beyond the lights, in the direction of travel.",
        },
        {
            "topic": "Writing",
            "prompt": "Which sentence is grammatically correct?",
            "choices": [
                ("I have drove this route many times.", False),
                ("I have driven this route many times.", True),
                ("I has driven this route many times.", False),
                ("I driving this route many times.", False),
            ],
            "explanation": "'Driven' is the correct past participle of 'drive', used with 'have'.",
        },
    ],
    "seru": [
        {
            "topic": "Safeguarding",
            "prompt": "A passenger appears to be a lone child under 16 travelling without an adult late at night. What should you do?",
            "choices": [
                ("Carry the journey as normal and say nothing", False),
                ("Refuse the booking outright with no explanation", False),
                ("Follow your operator's safeguarding procedure and raise any concerns appropriately", True),
                ("Ask the child for personal details to post online", False),
            ],
            "explanation": "Drivers are expected to be alert to safeguarding concerns and to follow their operator's procedure, in line with TfL's safeguarding awareness training.",
        },
        {
            "topic": "Equality",
            "prompt": "A passenger asks you to carry their guide dog. Under the Equality Act 2010, you must:",
            "choices": [
                ("Refuse if you have a personal allergy", False),
                ("Carry the passenger and their guide dog unless you hold a valid medical exemption certificate", True),
                ("Charge an extra fee for the dog", False),
                ("Ask the passenger to leave the dog behind", False),
            ],
            "explanation": "Private hire drivers must carry assistance dogs at no extra charge unless they hold a valid, displayed medical exemption certificate.",
        },
        {
            "topic": "Licensing requirements",
            "prompt": "As a London private hire driver, you may only accept bookings that:",
            "choices": [
                ("Are pre-booked through a licensed operator", True),
                ("You pick up by being hailed in the street", False),
                ("Come from any unlicensed app", False),
                ("Are agreed verbally with no booking record", False),
            ],
            "explanation": "Private hire vehicles cannot ply for hire — every journey must be pre-booked through a licensed operator.",
        },
    ],
    "topographical": [
        {
            "topic": "Compass directions",
            "prompt": "If you are travelling north and need to turn to face east, which way do you turn?",
            "choices": [
                ("Left", False),
                ("Right", True),
                ("Continue straight", False),
                ("U-turn", False),
            ],
            "explanation": "Facing north, east is a 90-degree turn to the right.",
        },
        {
            "topic": "Map symbols",
            "prompt": "On a standard London street atlas, a one-way street is typically shown by:",
            "choices": [
                ("A dotted line", False),
                ("An arrow along the road showing the direction of travel", True),
                ("A red circle", False),
                ("A green triangle", False),
            ],
            "explanation": "One-way streets are marked with directional arrows showing the only legal direction of travel.",
        },
        {
            "topic": "Route planning",
            "prompt": "When planning the most direct legal route between two points, you should prioritise:",
            "choices": [
                ("The shortest distance regardless of road restrictions", False),
                ("The route that is both direct and complies with road signs and restrictions", True),
                ("Whichever route avoids all traffic lights", False),
                ("The route your satnav suggests, without checking it", False),
            ],
            "explanation": "The assessment tests your ability to plan a route that is both direct and legally compliant, not simply the shortest on a map.",
        },
    ],
}


def run_seed():
    """Must be called with an app context already active (CLI pushes one
    itself via `with app.app_context()`; the admin route runs inside a
    normal Flask request, which already has one)."""
    summary = []
    for module_slug, questions in SEED_QUESTIONS.items():
        added = 0
        for item in questions:
            existing = Question.query.filter_by(
                module_slug=module_slug, prompt=item["prompt"]
            ).first()
            if existing:
                continue
            question = Question(
                module_slug=module_slug,
                topic=item["topic"],
                prompt=item["prompt"],
                explanation=item["explanation"],
            )
            db.session.add(question)
            for text, is_correct in item["choices"]:
                db.session.add(Choice(question=question, text=text, is_correct=is_correct))
            added += 1
        summary.append(f"{module_slug}: {added} new question(s) added")
    db.session.commit()

    admin_email = "admin@example.com"
    admin_created = False
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, full_name="Admin", is_admin=True)
        admin.set_password("change-this-password")
        db.session.add(admin)
        db.session.commit()
        admin_created = True

    return summary, admin_created
