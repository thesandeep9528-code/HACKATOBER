import random
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash

from extensions import db
from models import User, Otp
from utils.mailer import send_otp_email

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email address is not registered.", "danger")
            return render_template("Auth/forgot_password.html")

        # Invalidate old OTPs
        Otp.query.filter_by(
            user_id=user.user_id,
            is_used=False
        ).update({"is_used": True})

        generated_otp = str(random.randint(100000, 999999))
        otp = Otp(
            user_id=user.user_id,
            otp_code=generated_otp,
            expires_at=datetime.now() + timedelta(minutes=10),
            is_used=False
        )

        db.session.add(otp)
        db.session.commit()

        if not send_otp_email(user.email, generated_otp, user.full_name):
            return render_template(
                "Auth/forgot_password.html",
                error="Could not send the OTP email. Check Gmail SMTP settings in .env and the server logs, then try again."
            )
        flash("A verification OTP has been sent to your email 📧", "info")
        return redirect(url_for("auth.reset_password_otp", user_id=user.user_id))

    return render_template("Auth/forgot_password.html")


@auth_bp.route("/reset_password_otp/<int:user_id>", methods=["GET", "POST"])
def reset_password_otp(user_id):
    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        now = datetime.now()

        otp_record = (
            Otp.query
            .filter(
                Otp.user_id == user_id,
                Otp.is_used == False
            )
            .order_by(Otp.created_at.desc())
            .first()
        )

        if not otp_record or otp_record.otp_code != entered_otp:
            return render_template(
                "Auth/reset_password_otp.html",
                error="Invalid OTP code entered.",
                user_id=user_id
            )

        if otp_record.expires_at < now:
            return render_template(
                "Auth/reset_password_otp.html",
                error="OTP has expired. Please request a new one.",
                user_id=user_id
            )

        otp_record.is_used = True
        db.session.commit()

        session["reset_allowed"] = True
        return redirect(url_for("auth.reset_password", user_id=user_id))

    return render_template("Auth/reset_password_otp.html", user_id=user_id)


@auth_bp.route("/reset_password/<int:user_id>", methods=["GET", "POST"])
def reset_password(user_id):
    if not session.get("reset_allowed"):
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            return render_template(
                "Auth/reset_password.html",
                error="Passwords do not match.",
                user_id=user_id
            )

        user = User.query.get(user_id)
        if user:
            user.password_hash = generate_password_hash(password)
            db.session.commit()

        session.pop("reset_allowed", None)
        flash("Password reset successful! Please log in with your new password.", "success")
        return redirect(url_for("login"))

    return render_template("Auth/reset_password.html", user_id=user_id)
