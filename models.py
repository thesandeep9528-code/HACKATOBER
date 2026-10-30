from datetime import datetime, date
from extensions import db


# ================= USER =================
class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

    role = db.Column(db.String(20), default="FARMER")
    points = db.Column(db.Integer, default=0, nullable=False)
    badge = db.Column(db.String(50), default="Beginner", nullable=False)

    location = db.Column(db.String(100))
    dob = db.Column(db.Date)
    mobile = db.Column(db.String(15))
    is_verified = db.Column(db.Boolean, default=False)
    lifetime_points = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now)


# ================= OTP =================
class Otp(db.Model):
    __tablename__ = "otp"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    otp_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


# ================= TOPIC =================
class Topic(db.Model):
    __tablename__ = "topics"

    topic_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    images = db.relationship(
        "TopicImage",
        backref="topic",
        cascade="all,delete-orphan",
        lazy=True
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))

    is_pinned = db.Column(db.Boolean, default=False)
    pinned_until = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship("User", backref="topics")


# ================= ANSWER =================
class Answer(db.Model):
    __tablename__ = "answers"

    answer_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(
        db.Integer,
        db.ForeignKey("topics.topic_id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    answer_text = db.Column(db.Text, nullable=False)
    is_best_solution = db.Column(db.Boolean, default=False)
    has_earned_best_points = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User")
    topic = db.relationship("Topic", backref="answers")

    comments = db.relationship(
        "AnswerComment",
        order_by="AnswerComment.created_at.asc()",
        cascade="all, delete-orphan"
    )
    likes = db.relationship(
        "AnswerLike",
        cascade="all, delete-orphan"
    )


# ================= CROP STANDARD =================
class CropStandard(db.Model):
    __tablename__ = 'crop_standards'

    crop_standard_id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    growth_config = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


# ================= USER CROP (FARM) =================
class UserCrop(db.Model):
    __tablename__ = 'user_crops'

    user_crop_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    crop_standard_id = db.Column(db.Integer, db.ForeignKey('crop_standards.crop_standard_id'), nullable=False)
    farm_name = db.Column(db.String(100))
    sowing_date = db.Column(db.Date, nullable=False)
    area_acres = db.Column(db.Float, default=1.0)
    status = db.Column(db.String(20), default='active')  # 'active', 'harvested'
    created_at = db.Column(db.DateTime, default=datetime.now)

    standard = db.relationship('CropStandard', backref='farms')


# ================= CROP LOG =================
class CropLog(db.Model):
    __tablename__ = 'crop_logs'

    crop_log_id = db.Column(db.Integer, primary_key=True)
    user_crop_id = db.Column(db.Integer, db.ForeignKey('user_crops.user_crop_id', ondelete='CASCADE'), nullable=False)
    log_date = db.Column(db.Date, default=date.today, nullable=False)
    week_number = db.Column(db.Integer, nullable=True)
    soil_moisture = db.Column(db.String(20), nullable=True)
    plant_height_cm = db.Column(db.Float, nullable=True)
    lcc_score = db.Column(db.Integer, nullable=True)  # 1-6 Scale
    phenology_stage = db.Column(db.String(50), nullable=True)
    stand_count = db.Column(db.Integer, nullable=True)
    disease_label = db.Column(db.String(100), nullable=True)
    disease_confidence = db.Column(db.Float, nullable=True)
    disease_precautions_json = db.Column(db.Text, nullable=True)
    disease_status = db.Column(db.String(50), default="active")  # 'active', 'treated', 'healthy'

    crop = db.relationship('UserCrop', backref=db.backref('logs', cascade="all, delete-orphan"))


# ================= POINT TRANSACTION =================
class PointTransaction(db.Model):
    __tablename__ = "point_transactions"

    transaction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    points = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # CREDIT / DEBIT
    reason = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship("User", backref="point_transactions")


# ================= ANSWER COMMENT =================
class AnswerComment(db.Model):
    __tablename__ = "answer_comments"

    comment_id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(
        db.Integer,
        db.ForeignKey("answers.answer_id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User")


# ================= ANSWER LIKE =================
class AnswerLike(db.Model):
    __tablename__ = "answer_likes"

    like_id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(
        db.Integer,
        db.ForeignKey("answers.answer_id", ondelete="CASCADE"),
        nullable=False
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("answer_id", "user_id", name="unique_answer_like"),
    )


# ================= PREDICTION REPORT =================
class PredictionReport(db.Model):
    __tablename__ = "prediction_reports"

    report_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Inputs
    n = db.Column(db.Float)
    p = db.Column(db.Float)
    k = db.Column(db.Float)
    ph = db.Column(db.Float)
    humidity = db.Column(db.Float)
    temperature = db.Column(db.Float)
    soil_type = db.Column(db.String(50))

    # Outputs
    crop_name = db.Column(db.String(50))
    match_percentage = db.Column(db.Float)
    water_req = db.Column(db.String(50))
    harvest_duration = db.Column(db.String(50))

    recommendations_json = db.Column(db.Text)


# ================= TOPIC IMAGE =================
class TopicImage(db.Model):
    __tablename__ = "topic_images"

    image_id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(
        db.Integer,
        db.ForeignKey("topics.topic_id", ondelete="CASCADE"),
        nullable=False
    )
    image_path = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
