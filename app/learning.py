import random
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Question,
    Attempt,
    AttemptAnswer,
    RouteScenario,
    RouteAttempt,
    MODULE_SLUGS,
    MODULE_LABELS,
)
from app.routing import score_route

learning_bp = Blueprint("learning", __name__)

MOCK_EXAM_SIZE = 30
MOCK_EXAM_MINUTES = {"elr": 20, "seru": 25, "topographical": 25}
PRACTICE_BATCH_SIZE = 10


def requires_access(view):
    """Gate on User.has_access rather than on login alone — a logged-in user
    whose initial access has lapsed and hasn't opted into the £5/month
    continuation should be bounced to the pricing page, not the content."""

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.has_access:
            flash("Your access has ended. Choose an option below to carry on.", "info")
            return redirect(url_for("billing.pricing"))
        return view(*args, **kwargs)

    return wrapped


def _valid_module_or_404(module_slug: str) -> str:
    if module_slug not in MODULE_SLUGS:
        abort(404)
    return module_slug


@learning_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("learning.dashboard"))
    return render_template("learning/landing.html", modules=MODULE_LABELS)


@learning_bp.route("/dashboard")
@login_required
def dashboard():
    progress = {slug: current_user.progress_for(slug) for slug in MODULE_SLUGS}
    return render_template(
        "learning/dashboard.html",
        modules=MODULE_LABELS,
        progress=progress,
        has_access=current_user.has_access,
    )


@learning_bp.route("/module/<module_slug>")
@requires_access
def module_home(module_slug):
    module_slug = _valid_module_or_404(module_slug)
    topics = (
        db.session.query(Question.topic)
        .filter_by(module_slug=module_slug, is_active=True)
        .distinct()
        .all()
    )
    topics = [t[0] for t in topics if t[0]]
    question_count = Question.query.filter_by(module_slug=module_slug, is_active=True).count()
    return render_template(
        "learning/module_home.html",
        module_slug=module_slug,
        module_label=MODULE_LABELS[module_slug],
        topics=topics,
        question_count=question_count,
        progress=current_user.progress_for(module_slug),
    )


# ---------------------------------------------------------------------------
# Practice mode: untimed, immediate feedback after each question, not scored
# towards the dashboard's "best mock score" (keeps that number meaningful as
# a measure of exam-readiness rather than casual revision).
# ---------------------------------------------------------------------------

@learning_bp.route("/module/<module_slug>/practice")
@requires_access
def practice(module_slug):
    module_slug = _valid_module_or_404(module_slug)
    query = Question.query.filter_by(module_slug=module_slug, is_active=True)
    topic = request.args.get("topic")
    if topic:
        query = query.filter_by(topic=topic)
    questions = query.all()
    if not questions:
        flash("No questions available for this topic yet.", "info")
        return redirect(url_for("learning.module_home", module_slug=module_slug))

    random.shuffle(questions)
    questions = questions[:PRACTICE_BATCH_SIZE]
    attempt = Attempt(user_id=current_user.id, module_slug=module_slug, is_mock_exam=False)
    db.session.add(attempt)
    db.session.commit()

    return render_template(
        "learning/practice.html",
        module_slug=module_slug,
        module_label=MODULE_LABELS[module_slug],
        questions=questions,
        attempt_id=attempt.id,
    )


@learning_bp.route("/practice/<int:attempt_id>/answer", methods=["POST"])
@requires_access
def practice_answer(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)

    question_id = int(request.form["question_id"])
    choice_id = request.form.get("choice_id")
    question = Question.query.get_or_404(question_id)
    choice = None
    is_correct = False
    if choice_id:
        choice = next((c for c in question.choices if c.id == int(choice_id)), None)
        is_correct = bool(choice and choice.is_correct)

    db.session.add(
        AttemptAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            choice_id=choice.id if choice else None,
            is_correct=is_correct,
        )
    )
    db.session.commit()

    return render_template(
        "learning/_answer_feedback.html",
        question=question,
        is_correct=is_correct,
        correct_choice=question.correct_choice,
    )


# ---------------------------------------------------------------------------
# Mock exam: fixed-size, timed, scored — this is what feeds the dashboard's
# "best score" and is meant to mirror the real TfL assessment experience as
# closely as a question bank can.
# ---------------------------------------------------------------------------

@learning_bp.route("/module/<module_slug>/mock-exam/start", methods=["POST"])
@requires_access
def start_mock_exam(module_slug):
    module_slug = _valid_module_or_404(module_slug)
    questions = Question.query.filter_by(module_slug=module_slug, is_active=True).all()
    if len(questions) < 5:
        flash("Not enough questions loaded for a mock exam yet.", "info")
        return redirect(url_for("learning.module_home", module_slug=module_slug))

    random.shuffle(questions)
    chosen = questions[:MOCK_EXAM_SIZE]

    attempt = Attempt(user_id=current_user.id, module_slug=module_slug, is_mock_exam=True)
    db.session.add(attempt)
    db.session.commit()

    # Store the question order server-side (session) so a page refresh doesn't
    # reshuffle mid-exam.
    session[f"mock_exam_{attempt.id}"] = [q.id for q in chosen]

    return redirect(url_for("learning.mock_exam", attempt_id=attempt.id))


@learning_bp.route("/mock-exam/<int:attempt_id>")
@requires_access
def mock_exam(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)
    if attempt.finished_at:
        return redirect(url_for("learning.mock_exam_result", attempt_id=attempt.id))

    question_ids = session.get(f"mock_exam_{attempt.id}")
    if not question_ids:
        flash("That exam session has expired. Please start again.", "info")
        return redirect(url_for("learning.module_home", module_slug=attempt.module_slug))

    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    by_id = {q.id: q for q in questions}
    ordered = [by_id[i] for i in question_ids if i in by_id]

    minutes = MOCK_EXAM_MINUTES.get(attempt.module_slug, 25)
    return render_template(
        "learning/mock_exam.html",
        module_label=MODULE_LABELS[attempt.module_slug],
        attempt=attempt,
        questions=ordered,
        minutes=minutes,
    )


@learning_bp.route("/mock-exam/<int:attempt_id>/submit", methods=["POST"])
@requires_access
def submit_mock_exam(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)
    if attempt.finished_at:
        return redirect(url_for("learning.mock_exam_result", attempt_id=attempt.id))

    question_ids = session.pop(f"mock_exam_{attempt.id}", [])
    for question_id in question_ids:
        question = Question.query.get(question_id)
        if not question:
            continue
        choice_id = request.form.get(f"q_{question_id}")
        choice = None
        is_correct = False
        if choice_id:
            choice = next((c for c in question.choices if c.id == int(choice_id)), None)
            is_correct = bool(choice and choice.is_correct)
        db.session.add(
            AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                choice_id=choice.id if choice else None,
                is_correct=is_correct,
            )
        )

    attempt.finalise()
    db.session.commit()
    return redirect(url_for("learning.mock_exam_result", attempt_id=attempt.id))


@learning_bp.route("/mock-exam/<int:attempt_id>/result")
@requires_access
def mock_exam_result(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)
    return render_template(
        "learning/mock_exam_result.html",
        module_label=MODULE_LABELS[attempt.module_slug],
        attempt=attempt,
    )


# ---------------------------------------------------------------------------
# Topographical route-planning exercises. The real assessment weights its 4
# route-planning questions at 75% of the total score, so this gets its own
# exercise type (interactive map, not multiple-choice) rather than living in
# the Question/Choice tables above. See app/models.py and app/routing.py.
# ---------------------------------------------------------------------------

@learning_bp.route("/module/topographical/route-planning")
@requires_access
def route_planning_list():
    scenarios = (
        RouteScenario.query.filter_by(module_slug="topographical", is_active=True)
        .order_by(RouteScenario.id)
        .all()
    )
    best_scores = {}
    for scenario in scenarios:
        best = (
            RouteAttempt.query.filter_by(user_id=current_user.id, scenario_id=scenario.id)
            .order_by(RouteAttempt.score_percent.desc())
            .first()
        )
        best_scores[scenario.id] = best.score_percent if best else None
    return render_template(
        "learning/route_planning_list.html",
        module_label=MODULE_LABELS["topographical"],
        scenarios=scenarios,
        best_scores=best_scores,
    )


@learning_bp.route("/module/topographical/route-planning/<int:scenario_id>")
@requires_access
def route_scenario(scenario_id):
    scenario = RouteScenario.query.get_or_404(scenario_id)
    route_map = scenario.route_map
    return render_template(
        "learning/route_scenario.html",
        module_label=MODULE_LABELS["topographical"],
        scenario=scenario,
        route_map=route_map,
    )


@learning_bp.route("/module/topographical/route-planning/<int:scenario_id>/submit", methods=["POST"])
@requires_access
def route_scenario_submit(scenario_id):
    scenario = RouteScenario.query.get_or_404(scenario_id)
    route_map = scenario.route_map

    payload = request.get_json(silent=True) or {}
    submitted_path = payload.get("path")
    if not isinstance(submitted_path, list) or not all(isinstance(n, str) for n in submitted_path):
        return {"error": "Invalid path."}, 400

    result = score_route(route_map.data, scenario.start_node, scenario.end_node, submitted_path)

    db.session.add(
        RouteAttempt(
            user_id=current_user.id,
            scenario_id=scenario.id,
            submitted_path=submitted_path,
            is_legal=result["is_legal"],
            is_optimal=result["is_optimal"],
            score_percent=result["score_percent"],
        )
    )
    db.session.commit()

    return result, 200
