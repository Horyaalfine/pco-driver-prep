import random
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request, abort, session, jsonify, Response
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Question,
    Attempt,
    AttemptAnswer,
    RouteScenario,
    RouteAttempt,
    SpeakingPrompt,
    SpeakingGrade,
    MODULE_SLUGS,
    MODULE_LABELS,
)
from app.routing import score_route
from app import ai_grading

learning_bp = Blueprint("learning", __name__)

MOCK_EXAM_SIZE = 30
MOCK_EXAM_MINUTES = {"elr": 20, "seru": 45, "topographical": 25}
PRACTICE_BATCH_SIZE = 10
PASS_MARK_PERCENT = 60

# The real SERU paper is ~37 questions in 45 minutes: roughly 18
# multiple-choice, 17 fill-in-the-blank/sentence-completion, and 2 reading
# & understanding passages. Every other module still uses the generic
# flat MOCK_EXAM_SIZE-random-questions composition below.
EXAM_COMPOSITION = {
    "seru": {"mcq": 18, "fill_blank": 17, "reading": 2},
}


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


def _latest_answer_correctness(module_slug):
    """Map of question_id -> is_correct, from the current user's most recent
    answer to that question in this module (practice and mock exams both
    count). Powers both mistake-review and the spaced-repetition weighting
    in practice mode."""
    answers = (
        db.session.query(AttemptAnswer.question_id, AttemptAnswer.is_correct)
        .join(Attempt, AttemptAnswer.attempt_id == Attempt.id)
        .filter(Attempt.user_id == current_user.id, Attempt.module_slug == module_slug)
        .order_by(AttemptAnswer.id.desc())
        .all()
    )
    latest = {}
    for question_id, is_correct in answers:
        # Results are ordered newest-first, so the first time we see a given
        # question_id is its most recent answer — skip any older ones.
        if question_id not in latest:
            latest[question_id] = is_correct
    return latest


def _wrong_question_ids(module_slug):
    """Questions whose most recent answer (if any) was incorrect — once the
    learner answers one correctly again, it naturally drops off this list."""
    return [qid for qid, correct in _latest_answer_correctness(module_slug).items() if not correct]


def _readiness_data(module_slug):
    """Mock-exam score history (for a trend) and a per-topic accuracy
    breakdown (for 'what's actually weak'), both driven by data already
    captured via Attempt/AttemptAnswer — no new tables needed. This is what
    turns 'I did some practice' into a concrete signal of exam readiness,
    and gives a real reason to keep going if the continuation is offered."""
    mock_attempts = (
        Attempt.query.filter_by(user_id=current_user.id, module_slug=module_slug, is_mock_exam=True)
        .filter(Attempt.finished_at.isnot(None))
        .order_by(Attempt.finished_at.asc())
        .all()
    )
    history = [
        {
            "finished_at": a.finished_at,
            "score_percent": a.score_percent,
            "passed": (a.score_percent or 0) >= PASS_MARK_PERCENT,
        }
        for a in mock_attempts
    ]

    trend = None
    if len(history) >= 2:
        delta = history[-1]["score_percent"] - history[0]["score_percent"]
        trend = round(delta, 1)

    # Per-topic accuracy from each question's most recent answer, so a
    # question re-attempted several times only counts once, at its latest
    # result — consistent with how the mistake list works.
    latest = _latest_answer_correctness(module_slug)
    topic_by_question = dict(
        db.session.query(Question.id, Question.topic).filter_by(module_slug=module_slug).all()
    )
    topic_totals = {}
    for question_id, is_correct in latest.items():
        topic = topic_by_question.get(question_id)
        if not topic:
            continue
        stats = topic_totals.setdefault(topic, {"correct": 0, "total": 0})
        stats["total"] += 1
        if is_correct:
            stats["correct"] += 1

    topic_breakdown = [
        {
            "topic": topic,
            "accuracy_percent": round(100 * stats["correct"] / stats["total"]),
            "attempted": stats["total"],
        }
        for topic, stats in topic_totals.items()
    ]
    topic_breakdown.sort(key=lambda row: row["accuracy_percent"])

    return {
        "history": history,
        "trend": trend,
        "best_score": max((h["score_percent"] for h in history), default=None),
        "latest_score": history[-1]["score_percent"] if history else None,
        "topic_breakdown": topic_breakdown,
    }


def _weighted_sample(questions, latest_correctness, k):
    """Weighted sampling without replacement (A-ES algorithm): a question
    never attempted or last answered wrong gets weight 3, one last answered
    correctly gets weight 1 — biases practice toward what the learner
    hasn't mastered yet, without ever fully hiding mastered questions (so
    they still get occasional spaced revisiting)."""
    keyed = []
    for q in questions:
        correct = latest_correctness.get(q.id)
        weight = 1 if correct is True else 3
        key = random.random() ** (1.0 / weight)
        keyed.append((key, q))
    keyed.sort(key=lambda pair: pair[0], reverse=True)
    return [q for _, q in keyed[:k]]


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
        mistake_count=len(_wrong_question_ids(module_slug)),
    )


@learning_bp.route("/module/<module_slug>/readiness")
@requires_access
def readiness(module_slug):
    module_slug = _valid_module_or_404(module_slug)
    data = _readiness_data(module_slug)
    return render_template(
        "learning/readiness.html",
        module_slug=module_slug,
        module_label=MODULE_LABELS[module_slug],
        pass_mark=PASS_MARK_PERCENT,
        **data,
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

    # Spaced-repetition-style weighting: questions the learner hasn't seen or
    # last got wrong come up more often than ones they've already nailed.
    latest_correctness = _latest_answer_correctness(module_slug)
    questions = _weighted_sample(questions, latest_correctness, PRACTICE_BATCH_SIZE)
    attempt = Attempt(user_id=current_user.id, module_slug=module_slug, is_mock_exam=False)
    db.session.add(attempt)
    db.session.commit()

    return render_template(
        "learning/practice.html",
        module_slug=module_slug,
        module_label=MODULE_LABELS[module_slug],
        questions=questions,
        attempt_id=attempt.id,
        review_mode=False,
    )


@learning_bp.route("/module/<module_slug>/review-mistakes")
@requires_access
def review_mistakes(module_slug):
    """Every question in this module whose most recent answer was wrong —
    the single most direct way to turn practice time into pass-readiness,
    since it targets exactly what the learner hasn't mastered yet rather
    than drawing from the whole bank at random."""
    module_slug = _valid_module_or_404(module_slug)
    wrong_ids = _wrong_question_ids(module_slug)
    if not wrong_ids:
        flash(
            "No mistakes to review here right now — either you haven't practised "
            "this module yet, or your most recent answer to everything you've "
            "tried was correct.",
            "info",
        )
        return redirect(url_for("learning.module_home", module_slug=module_slug))

    questions = Question.query.filter(
        Question.id.in_(wrong_ids), Question.is_active == True  # noqa: E712
    ).all()
    random.shuffle(questions)

    attempt = Attempt(user_id=current_user.id, module_slug=module_slug, is_mock_exam=False)
    db.session.add(attempt)
    db.session.commit()

    return render_template(
        "learning/practice.html",
        module_slug=module_slug,
        module_label=MODULE_LABELS[module_slug],
        questions=questions,
        attempt_id=attempt.id,
        review_mode=True,
    )


def _grade_answer(question, choice_id, text_answer):
    """Shared grading for both mcq/reading (choice-based) and fill_blank
    (text-based) questions. Returns (choice_or_None, is_correct)."""
    if question.question_type == "fill_blank":
        is_correct = question.grade_text_answer(text_answer)
        return None, is_correct
    choice = None
    is_correct = False
    if choice_id:
        choice = next((c for c in question.choices if c.id == int(choice_id)), None)
        is_correct = bool(choice and choice.is_correct)
    return choice, is_correct


@learning_bp.route("/practice/<int:attempt_id>/answer", methods=["POST"])
@requires_access
def practice_answer(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)

    question_id = int(request.form["question_id"])
    question = Question.query.get_or_404(question_id)
    choice, is_correct = _grade_answer(
        question, request.form.get("choice_id"), request.form.get("text_answer")
    )

    db.session.add(
        AttemptAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            choice_id=choice.id if choice else None,
            text_answer=request.form.get("text_answer") if question.question_type == "fill_blank" else None,
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

def _choose_mock_exam_questions(module_slug):
    """Picks the question set for a mock exam. SERU mirrors the real paper's
    composition (mcq/fill_blank/reading counts); every other module just
    takes MOCK_EXAM_SIZE random active questions, as before."""
    composition = EXAM_COMPOSITION.get(module_slug)
    if not composition:
        questions = Question.query.filter_by(module_slug=module_slug, is_active=True).all()
        random.shuffle(questions)
        return questions[:MOCK_EXAM_SIZE]

    chosen = []
    for q_type, count in composition.items():
        pool = Question.query.filter_by(
            module_slug=module_slug, is_active=True, question_type=q_type
        ).all()
        random.shuffle(pool)
        # Take as many as are available, up to the real exam's count for that
        # type — lets the exam still run (at a reduced size) while the bank
        # for a given type is still being built out, rather than blocking.
        chosen.extend(pool[: min(count, len(pool))])
    random.shuffle(chosen)
    return chosen


@learning_bp.route("/module/<module_slug>/mock-exam/start", methods=["POST"])
@requires_access
def start_mock_exam(module_slug):
    module_slug = _valid_module_or_404(module_slug)
    chosen = _choose_mock_exam_questions(module_slug)
    if len(chosen) < 5:
        flash("Not enough questions loaded for a mock exam yet.", "info")
        return redirect(url_for("learning.module_home", module_slug=module_slug))

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
        pass_mark=PASS_MARK_PERCENT,
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
        text_answer = request.form.get(f"q_{question_id}_text")
        choice, is_correct = _grade_answer(
            question, request.form.get(f"q_{question_id}"), text_answer
        )
        db.session.add(
            AttemptAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                choice_id=choice.id if choice else None,
                text_answer=text_answer if question.question_type == "fill_blank" else None,
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
        pass_mark=PASS_MARK_PERCENT,
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


# ---------------------------------------------------------------------------
# ELR speaking practice. The real ELR test is a live speaking & listening
# interview, not a written test — these are self-rehearsal prompts (study
# the model answer and tips, then practise speaking your own answer out
# loud), not a graded exercise. See app/models.py's SpeakingPrompt docstring.
# ---------------------------------------------------------------------------

@learning_bp.route("/module/elr/speaking")
@requires_access
def speaking_practice_list():
    prompts = (
        SpeakingPrompt.query.filter_by(module_slug="elr", is_active=True)
        .order_by(SpeakingPrompt.topic, SpeakingPrompt.id)
        .all()
    )
    return render_template(
        "learning/speaking_list.html",
        module_label=MODULE_LABELS["elr"],
        prompts=prompts,
    )


@learning_bp.route("/module/elr/speaking/<int:prompt_id>")
@requires_access
def speaking_practice_detail(prompt_id):
    prompt = SpeakingPrompt.query.get_or_404(prompt_id)
    all_prompts = (
        SpeakingPrompt.query.filter_by(module_slug="elr", is_active=True)
        .order_by(SpeakingPrompt.topic, SpeakingPrompt.id)
        .all()
    )
    ids = [p.id for p in all_prompts]
    idx = ids.index(prompt.id) if prompt.id in ids else -1
    next_id = ids[idx + 1] if 0 <= idx < len(ids) - 1 else None
    return render_template(
        "learning/speaking_detail.html",
        module_label=MODULE_LABELS["elr"],
        prompt=prompt,
        next_id=next_id,
    )


@learning_bp.route("/module/elr/speaking/<int:prompt_id>/question-audio")
@requires_access
def speaking_practice_question_audio(prompt_id):
    """Serve the examiner reading this prompt's question aloud, so practice
    matches the real interview's listen-then-speak format. Generated once via
    the OpenAI API and cached on the prompt row (SpeakingPrompt.question_audio)
    — every later request for the same prompt is served straight from the
    database with no further API calls, since the question text never changes."""
    prompt = SpeakingPrompt.query.get_or_404(prompt_id)

    if not prompt.question_audio:
        api_key = current_app.config["OPENAI_API_KEY"]
        tts_model = current_app.config["OPENAI_TTS_MODEL"]
        tts_voice = current_app.config["OPENAI_TTS_VOICE"]
        try:
            prompt.question_audio = ai_grading.synthesize_speech(
                api_key, tts_model, tts_voice, prompt.prompt_text
            )
        except ai_grading.GradingError as exc:
            return jsonify({"error": str(exc)}), 502
        db.session.commit()

    return Response(
        prompt.question_audio,
        mimetype="audio/mpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@learning_bp.route("/module/elr/speaking/<int:prompt_id>/grade", methods=["POST"])
@requires_access
def speaking_practice_grade(prompt_id):
    """Transcribe + grade one recorded answer via the OpenAI API. Explicit,
    per-recording opt-in from the learner — never triggered automatically.
    Returns JSON; errors come back as {"error": "<safe-to-show message>"}
    with a 4xx/5xx status rather than a page, since this is called via fetch()."""
    prompt = SpeakingPrompt.query.get_or_404(prompt_id)

    daily_limit = current_app.config["SPEAKING_GRADING_DAILY_LIMIT"]
    since = datetime.utcnow() - timedelta(days=1)
    recent_count = SpeakingGrade.query.filter(
        SpeakingGrade.user_id == current_user.id, SpeakingGrade.created_at >= since
    ).count()
    if recent_count >= daily_limit:
        return jsonify({
            "error": f"You've reached today's limit of {daily_limit} AI-graded recordings. "
                     "Please try again tomorrow, or keep rehearsing with self-review in the meantime."
        }), 429

    audio_file = request.files.get("audio")
    if not audio_file:
        return jsonify({"error": "No recording was received — please record an answer first."}), 400

    api_key = current_app.config["OPENAI_API_KEY"]
    transcribe_model = current_app.config["OPENAI_TRANSCRIBE_MODEL"]
    grading_model = current_app.config["OPENAI_GRADING_MODEL"]

    try:
        transcript = ai_grading.transcribe_audio(
            api_key, transcribe_model, audio_file.read(), audio_file.filename
        )
        result = ai_grading.grade_transcript(api_key, grading_model, prompt.prompt_text, transcript)
    except ai_grading.GradingError as exc:
        return jsonify({"error": str(exc)}), 502

    grade = SpeakingGrade(
        user_id=current_user.id,
        prompt_id=prompt.id,
        transcript=transcript,
        score=result["score"],
        feedback=result["feedback"],
    )
    db.session.add(grade)
    db.session.commit()

    return jsonify({"transcript": transcript, "score": result["score"], "feedback": result["feedback"]})
