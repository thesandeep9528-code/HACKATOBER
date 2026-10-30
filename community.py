import json
import os
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from sqlalchemy import func

from extensions import db
from models import Topic, Answer, User, PointTransaction, AnswerLike, AnswerComment, TopicImage
from utils.answer_validator import validate_answer_with_ai

community_bp = Blueprint("community", __name__)

# ---------------- BADGE ----------------
def calculate_badge(lifetime_points):
    if lifetime_points >= 300:
        return "Expert Farmer"
    elif lifetime_points >= 150:
        return "Trusted Farmer"
    elif lifetime_points >= 50:
        return "Contributor"
    else:
        return "Beginner"


# ---------------- POINTS ----------------
def award_points(user_id, points, reason):
    user = User.query.get(user_id)
    if not user:
        return
    user.points += points               # wallet
    user.lifetime_points += points      # reputation
    user.badge = calculate_badge(user.lifetime_points)

    db.session.add(
        PointTransaction(
            user_id=user_id,
            points=points,
            transaction_type="CREDIT",
            reason=reason
        )
    )
    db.session.commit()


# ---------------- DAILY BONUS ----------------
def give_daily_bonus(user_id):
    today = datetime.now().date()

    already_given = PointTransaction.query.filter(
        PointTransaction.user_id == user_id,
        PointTransaction.reason == "Daily participation bonus",
        func.date(PointTransaction.created_at) == today
    ).first()

    if already_given:
        return

    award_points(user_id, 5, "Daily participation bonus")


# ---------------- COMMUNITY FEED ----------------
@community_bp.route("/farmer_community", methods=["GET", "POST"])
def farmer_community():
    if "user_id" not in session:
        flash("Please log in to access the farmer community.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "General")

        if not title or not description:
            flash("Title and description are required.", "warning")
            return redirect(url_for("community.farmer_community"))

        topic = Topic(
            user_id=session["user_id"],
            title=title,
            description=description,
            category=category,
            created_at=datetime.now(),
            is_pinned=False
        )
        db.session.add(topic)
        db.session.commit()

        # Handle image uploads
        files = request.files.getlist("image")
        upload_dir = os.path.join(os.path.dirname(__file__), "static", "images")
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            if file and file.filename != "":
                safe_name = secure_filename(file.filename)
                unique_filename = f"{topic.topic_id}_{int(datetime.now().timestamp())}_{safe_name}"
                filepath = os.path.join(upload_dir, unique_filename)
                file.save(filepath)

                image = TopicImage(
                    topic_id=topic.topic_id,
                    image_path=f"images/{unique_filename}"
                )
                db.session.add(image)

        award_points(session["user_id"], 2, "Created a community topic")
        db.session.commit()
        flash("Your topic has been posted successfully!", "success")
        return redirect(url_for("community.farmer_community"))

    # AUTO UNPIN EXPIRED TOPICS
    Topic.query.filter(
        Topic.is_pinned == True,
        Topic.pinned_until < datetime.now()
    ).update(
        {Topic.is_pinned: False, Topic.pinned_until: None},
        synchronize_session=False
    )
    db.session.commit()

    # Query topics with optional category or search filters
    category_filter = request.args.get("category")
    search_query = request.args.get("q")

    query = Topic.query
    if category_filter and category_filter != "All":
        query = query.filter(Topic.category == category_filter)
    if search_query:
        query = query.filter(
            (Topic.title.ilike(f"%{search_query}%")) |
            (Topic.description.ilike(f"%{search_query}%"))
        )

    topics = query.order_by(
        Topic.is_pinned.desc(),
        Topic.created_at.desc()
    ).all()

    top_contributors = (
        User.query.order_by(User.lifetime_points.desc()).limit(5).all()
    )

    current_user = User.query.get(session["user_id"])

    return render_template(
        "Farmer_Community/farmer_community.html",
        topics=topics,
        current_user=current_user,
        top_contributors=top_contributors
    )


# ---------------- TOPIC DETAIL ----------------
@community_bp.route("/topic/<int:topic_id>", methods=["GET", "POST"])
def view_topic(topic_id):
    if "user_id" not in session:
        flash("Please log in to view this topic.", "warning")
        return redirect(url_for("login"))

    topic = Topic.query.get_or_404(topic_id)

    if request.method == "POST":
        answer_text = request.form.get("answer_text", "").strip()
        if answer_text:
            answer = Answer(
                topic_id=topic_id,
                user_id=session["user_id"],
                answer_text=answer_text,
                created_at=datetime.now()
            )
            db.session.add(answer)
            db.session.commit()
            flash("Your response has been submitted.", "success")
        return redirect(url_for("community.view_topic", topic_id=topic_id))

    answers = (
        Answer.query
        .filter_by(topic_id=topic_id)
        .order_by(
            Answer.is_best_solution.desc(),
            Answer.created_at.desc()
        )
        .all()
    )

    return render_template(
        "Farmer_Community/topic_detail.html",
        topic=topic,
        answers=answers
    )


# ---------------- MARK BEST SOLUTION ----------------
@community_bp.route("/mark-best/<int:answer_id>")
def mark_best_answer(answer_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    answer = Answer.query.get_or_404(answer_id)
    topic = Topic.query.get_or_404(answer.topic_id)

    # Only question owner can mark best
    if topic.user_id != session["user_id"]:
        flash("Only the question owner can mark the best answer.", "danger")
        return redirect(url_for("community.view_topic", topic_id=topic.topic_id))

    if answer.is_best_solution:
        return redirect(url_for("community.view_topic", topic_id=topic.topic_id))

    # Anti-duplication check
    other_answers = Answer.query.filter(
        Answer.topic_id == topic.topic_id,
        Answer.answer_id != answer.answer_id
    ).all()

    for other in other_answers:
        similarity = SequenceMatcher(
            None,
            answer.answer_text.lower().strip(),
            other.answer_text.lower().strip()
        ).ratio()

        if similarity >= 0.85:
            flash("This answer is too similar to an existing response.", "warning")
            return redirect(url_for("community.view_topic", topic_id=topic.topic_id))

    # AI validation
    try:
        raw_result = validate_answer_with_ai(
            topic.title + ". " + topic.description,
            answer.answer_text
        )
        ai_result = json.loads(raw_result)
    except Exception:
        ai_result = {"is_valid": True, "confidence": 75}

    if not ai_result.get("is_valid") or ai_result.get("confidence", 0) < 50:
        flash(ai_result.get("reason", "The answer did not pass quality validation."), "warning")
        return redirect(url_for("community.view_topic", topic_id=topic.topic_id))

    # Single best answer per topic
    Answer.query.filter_by(
        topic_id=topic.topic_id,
        is_best_solution=True
    ).update({"is_best_solution": False})

    answer.is_best_solution = True

    # Award points to author
    if not answer.has_earned_best_points:
        award_points(answer.user_id, 20, "Best answer selected")
        answer.has_earned_best_points = True

    db.session.commit()
    flash("Marked as best solution! 20 reputation points awarded.", "success")

    return redirect(url_for("community.view_topic", topic_id=topic.topic_id))


# ---------------- COMMENTS ----------------
@community_bp.route("/answer/<int:answer_id>/comment", methods=["POST"])
def add_answer_comment(answer_id):
    if "user_id" not in session:
        flash("Please log in to add a comment.", "warning")
        return redirect(url_for("login"))

    text = request.form.get("comment_text", "").strip()
    if text:
        comment = AnswerComment(
            answer_id=answer_id,
            user_id=session["user_id"],
            comment_text=text
        )
        db.session.add(comment)
        db.session.commit()

    return redirect(request.referrer or url_for("community.farmer_community"))


# ---------------- LIKES ----------------
@community_bp.route("/answer/<int:answer_id>/like", methods=["POST"])
def like_answer(answer_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    existing = AnswerLike.query.filter_by(
        answer_id=answer_id,
        user_id=session["user_id"]
    ).first()

    if existing:
        db.session.delete(existing)
    else:
        db.session.add(
            AnswerLike(
                answer_id=answer_id,
                user_id=session["user_id"]
            )
        )

    db.session.commit()
    return redirect(request.referrer or url_for("community.farmer_community"))


# ---------------- PRIORITY PINNING ----------------
@community_bp.route("/topic/<int:topic_id>/pin", methods=["POST"])
def pin_topic(topic_id):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    topic = Topic.query.get_or_404(topic_id)
    user = User.query.get(session["user_id"])

    if topic.user_id != user.user_id:
        flash("You can only pin your own questions.", "danger")
        return redirect(request.referrer or url_for("community.farmer_community"))

    if topic.is_pinned:
        topic.is_pinned = False
        topic.pinned_until = None
        db.session.commit()
        flash("Topic unpinned successfully.", "info")
        return redirect(request.referrer or url_for("community.farmer_community"))

    PIN_COST = 100
    if user.points < PIN_COST:
        flash(f"Not enough points to pin this topic. You need {PIN_COST} points (current: {user.points}).", "warning")
        return redirect(request.referrer or url_for("community.farmer_community"))

    user.points -= PIN_COST
    db.session.add(
        PointTransaction(
            user_id=user.user_id,
            points=PIN_COST,
            transaction_type="DEBIT",
            reason="Pinned community topic"
        )
    )

    topic.is_pinned = True
    topic.pinned_until = datetime.now() + timedelta(days=7)
    db.session.commit()

    flash("📌 Topic pinned for 7 days! 100 points deducted.", "success")
    return redirect(request.referrer or url_for("community.farmer_community"))
