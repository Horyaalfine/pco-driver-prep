from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Question, Choice, MODULE_SLUGS, MODULE_LABELS

admin_bp = Blueprint("admin", __name__)


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
