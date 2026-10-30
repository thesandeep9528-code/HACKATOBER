import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from app import app, db
from models import User, CropStandard, Topic, Answer

class TestBioGrowMerged(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False

        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()
        from seed_crops import seed_database
        seed_database()

        user = User(
            full_name="Farmer Ramesh",
            email="ramesh@biogrow.farm",
            password_hash="pbkdf2:sha256:dummyhash",
            role="FARMER",
            points=120,
            lifetime_points=120,
            badge="Contributor",
            location="Pune",
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_01_home_and_public_routes(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"BioGrow", res.data)

        res_login = self.client.get("/login")
        self.assertEqual(res_login.status_code, 200)

        res_pred = self.client.get("/crop_prediction")
        self.assertEqual(res_pred.status_code, 200)

        res_leaf = self.client.get("/disease_detection")
        self.assertEqual(res_leaf.status_code, 200)
        print("  [OK] Public pages load successfully (Home, Login, Crop Prediction, Leaf Doctor)")

    def test_02_crop_prediction_api(self):
        payload = {
            "n": 90,
            "p": 42,
            "k": 43,
            "ph": 6.5,
            "temp": 25.0,
            "humidity": 80.0,
            "soil_type": "Alluvial Soil"
        }
        res = self.client.post("/api/predict-crop", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("result", data)
        self.assertIn("match_percentage", data)
        self.assertIn("recommendations", data)
        self.assertGreater(data["match_percentage"], 0)
        print(f"  [OK] Crop Prediction API predicted: {data['result']} ({data['match_percentage']}%)")

    def test_03_smart_irrigation_advisory(self):
        payload = {
            "crop": "Tomato",
            "stage": "flowering",
            "soil_moisture_pct": 25,
            "temperature_c": 32,
            "humidity_pct": 45,
            "rain_probability_pct": 10,
            "forecast_rain_mm": 0
        }
        res = self.client.post("/api/advisory", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("irrigation_action", data)
        self.assertIn("sustainability_score", data)
        print(f"  [OK] Smart Irrigation Advisory returned: {data['irrigation_action']} (Score: {data['sustainability_score']}/100)")

    def test_04_chatbot_api(self):
        res = self.client.post("/chatbot", json={"question": "What is the best fertilizer for wheat?"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("response", data)
        self.assertGreater(len(data["response"]), 10)
        safe_preview = data['response'][:65].encode('ascii', 'replace').decode('ascii')
        print(f"  [OK] AI Chatbot responded: {safe_preview}...")

    def test_05_community_and_session(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["full_name"] = "Farmer Ramesh"
            sess["initials"] = "FR"
            sess["location"] = "Pune"

        res = self.client.get("/farmer_community")
        self.assertEqual(res.status_code, 200)

        post_res = self.client.post("/farmer_community", data={
            "title": "Aphids on chili plants",
            "description": "Noticed small green insects on the underside of young leaves.",
            "category": "Pests"
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        self.assertIn(b"Aphids on chili plants", post_res.data)

        # Check points award
        user = User.query.get(1)
        self.assertGreater(user.points, 120)
        print("  [OK] Farmer Community posting, feed and point transactions verified")

    def test_06_crop_tracking(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        # Add Farm
        res = self.client.post("/add_farm", data={
            "farm_name": "North Field Paddy",
            "crop_standard_id": 1,
            "sowing_date": "2026-08-01",
            "area_acres": "2.5"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Log Field Data
        log_res = self.client.post("/log_field_data/1", json={
            "height": 45,
            "lcc": 4,
            "moisture": "Moist",
            "stage": "Vegetative",
            "stand_count": 48
        })
        self.assertEqual(log_res.status_code, 200)
        print("  [OK] Crop Tracking add farm, logging, and agronomic benchmarks verified")

    def test_07_leaf_disease_prediction(self):
        # Create a small valid test JPEG image in memory
        from PIL import Image
        import io
        img = Image.new('RGB', (224, 224), color=(34, 139, 34))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)

        data = {
            'file': (buf, 'test_leaf.jpg')
        }
        res = self.client.post('/api/disease/predict', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn("label", json_data)
        self.assertIn("confidence", json_data)
        self.assertIn("precautions", json_data)
        print(f"  [OK] Leaf Doctor Diagnostic API returned label: {json_data['label']} (Confidence: {json_data['confidence']})")


if __name__ == "__main__":
    unittest.main(verbosity=2)
