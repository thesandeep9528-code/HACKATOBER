import json
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash

from extensions import db
from models import User, UserCrop, CropLog, Topic, Answer, AnswerLike

def seed_demo_platform():
    # 1. Create or update Demo Users
    demo_user = User.query.filter_by(email="demo@agrismart.ai").first()
    if not demo_user:
        demo_user = User(
            full_name="Sandip Patel (Team Lead)",
            email="demo@agrismart.ai",
            password_hash=generate_password_hash("demo123"),
            role="FARMER",
            points=420,
            lifetime_points=420,
            badge="Expert Farmer",
            location="Ahmedabad, Gujarat",
            mobile="9876543210",
            is_verified=True,
            created_at=datetime.now() - timedelta(days=60)
        )
        db.session.add(demo_user)
        db.session.commit()
    else:
        demo_user.is_verified = True
        demo_user.points = 420
        demo_user.badge = "Expert Farmer"
        db.session.commit()

    farmer2 = User.query.filter_by(email="kuldeep@agrismart.ai").first()
    if not farmer2:
        farmer2 = User(
            full_name="Kuldeep Sharma",
            email="kuldeep@agrismart.ai",
            password_hash=generate_password_hash("demo123"),
            role="FARMER",
            points=180,
            lifetime_points=180,
            badge="Trusted Farmer",
            location="Mehsana, Gujarat",
            mobile="9812345678",
            is_verified=True,
            created_at=datetime.now() - timedelta(days=45)
        )
        db.session.add(farmer2)
        db.session.commit()

    # 2. Populate Active Farms for Demo User if none exist
    user_farms = UserCrop.query.filter_by(user_id=demo_user.user_id).all()
    if len(user_farms) == 0:
        # Farm 1: Tomato
        farm_tomato = UserCrop(
            user_id=demo_user.user_id,
            crop_standard_id=27, # Tomato
            farm_name="North Field — Tomato (Hybrid Roma)",
            sowing_date=date.today() - timedelta(days=28),
            area_acres=2.5,
            status="active",
            created_at=datetime.now() - timedelta(days=28)
        )
        # Farm 2: Rice
        farm_rice = UserCrop(
            user_id=demo_user.user_id,
            crop_standard_id=1, # Rice
            farm_name="East Plot — Basmati Rice (Paddy)",
            sowing_date=date.today() - timedelta(days=14),
            area_acres=5.0,
            status="active",
            created_at=datetime.now() - timedelta(days=14)
        )
        # Farm 3: Cotton
        farm_cotton = UserCrop(
            user_id=demo_user.user_id,
            crop_standard_id=23, # Cotton
            farm_name="South Parcel — Bt Cotton Hybrid",
            sowing_date=date.today() - timedelta(days=42),
            area_acres=3.5,
            status="active",
            created_at=datetime.now() - timedelta(days=42)
        )
        db.session.add_all([farm_tomato, farm_rice, farm_cotton])
        db.session.commit()

        # Seed Logs for Farm 1 (Tomato with Late Blight history)
        tomato_precautions = json.dumps([
            "Apply Copper Oxychloride (2.5g/L) or Mancozeb immediately.",
            "Prune infected lower foliage and dispose of safely away from compost.",
            "Switch from overhead sprinkling to drip irrigation to keep canopy dry.",
            "Improve plant aeration by thinning dense foliage."
        ])
        log1 = CropLog(
            user_crop_id=farm_tomato.user_crop_id,
            log_date=date.today() - timedelta(days=14),
            week_number=2,
            soil_moisture="Optimal",
            plant_height_cm=18.5,
            lcc_score=4,
            phenology_stage="Seedling Establishment",
            stand_count=2400,
            disease_status="healthy"
        )
        log2 = CropLog(
            user_crop_id=farm_tomato.user_crop_id,
            log_date=date.today() - timedelta(days=2),
            week_number=4,
            soil_moisture="Low",
            plant_height_cm=36.0,
            lcc_score=3,
            phenology_stage="Vegetative Growth",
            stand_count=2380,
            disease_label="Tomato___Late_blight",
            disease_confidence=0.7732,
            disease_precautions_json=tomato_precautions,
            disease_status="active"
        )

        # Seed Logs for Farm 2 (Rice)
        log_rice = CropLog(
            user_crop_id=farm_rice.user_crop_id,
            log_date=date.today() - timedelta(days=1),
            week_number=2,
            soil_moisture="Optimal",
            plant_height_cm=22.0,
            lcc_score=4,
            phenology_stage="Active Tillering",
            stand_count=5000,
            disease_label="Rice___healthy",
            disease_confidence=0.986,
            disease_status="healthy"
        )
        db.session.add_all([log1, log2, log_rice])
        db.session.commit()

    # 3. Populate Community Topics if empty
    if Topic.query.count() == 0:
        topic1 = Topic(
            user_id=farmer2.user_id,
            title="Urgent: Dark brown concentric target spots on lower tomato leaves",
            description="Noticed brown circular lesions with yellow halos on the lower leaves of my hybrid tomato crop. Humidity has been around 80% with intermittent drizzle. How should I treat this before it spreads to green fruit?",
            category="Crop Disease",
            is_pinned=True,
            pinned_until=datetime.now() + timedelta(days=30),
            created_at=datetime.now() - timedelta(days=3)
        )
        topic2 = Topic(
            user_id=demo_user.user_id,
            title="Drip irrigation cycle timing during 38°C peak summer heat in Gujarat",
            description="Sharing field observation: running drip irrigation between 6:00 AM - 7:30 AM saved 35% water compared to mid-day watering and eliminated root scald in our cotton test block. What schedules are other farmers using?",
            category="Irrigation & Water",
            created_at=datetime.now() - timedelta(days=5)
        )
        topic3 = Topic(
            user_id=farmer2.user_id,
            title="Bio-fertilizer Trichoderma viride application for root rot prevention in rice",
            description="Has anyone used Trichoderma viride seed treatment for Basmati paddy? What is the recommended dosage per kg of seed?",
            category="Bio-Fertilizer",
            created_at=datetime.now() - timedelta(days=1)
        )
        db.session.add_all([topic1, topic2, topic3])
        db.session.commit()

        # Answers
        ans1 = Answer(
            topic_id=topic1.topic_id,
            user_id=demo_user.user_id,
            answer_text="This is classic Alternaria solani (Early Blight). Take these steps immediately:\n1. Prune all symptomatic foliage from bottom 20cm using sanitized shears.\n2. Spray Mancozeb 75 WP (2g/L) or Copper Oxychloride 50 WP (2.5g/L).\n3. Strictly avoid overhead watering — wet leaves accelerate spore germination in under 4 hours.\n4. Apply potassium silicate to strengthen cell walls.",
            is_best_solution=True,
            has_earned_best_points=True,
            created_at=datetime.now() - timedelta(days=2)
        )
        ans2 = Answer(
            topic_id=topic2.topic_id,
            user_id=farmer2.user_id,
            answer_text="Agreed Sandip! Early morning cycles also allow soil to absorb water before solar evaporation peaks. We also installed mulch film which reduced weed competition.",
            is_best_solution=False,
            created_at=datetime.now() - timedelta(days=4)
        )
        ans3 = Answer(
            topic_id=topic3.topic_id,
            user_id=demo_user.user_id,
            answer_text="Use 10 grams of Trichoderma viride talc-based formulation per 1 kg of paddy seed. Mix with 50ml jaggery water as sticker, dry in shade for 30 minutes before broadcasting.",
            is_best_solution=True,
            has_earned_best_points=True,
            created_at=datetime.now() - timedelta(hours=8)
        )
        db.session.add_all([ans1, ans2, ans3])
        db.session.commit()

        # Add some likes
        like1 = AnswerLike(answer_id=ans1.answer_id, user_id=farmer2.user_id)
        db.session.add(like1)
        db.session.commit()

    print("[BioGrow Demo] Seeded Demo Farmer, Active Farms, Crop Logs, and Community Discussions!")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        seed_demo_platform()
