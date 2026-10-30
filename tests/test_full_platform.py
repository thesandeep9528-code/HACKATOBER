import io
import json
import os
import sys
import unittest
from datetime import date
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, CropStandard, UserCrop, CropLog, Topic, Answer, PredictionReport

class TestFullPlatformIntegration(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False

        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()
        from seed_crops import seed_database
        seed_database()

        # Create verified test user
        self.user = User(
            full_name="BinaryBrains Farmer",
            email="farmer@binarybrains.ai",
            password_hash="pbkdf2:sha256:dummyhash",
            role="FARMER",
            points=50,
            lifetime_points=50,
            badge="Contributor",
            location="Ahmedabad",
            is_verified=True
        )
        db.session.add(self.user)
        db.session.commit()

        self.client = app.test_client()
        # Set session
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.user_id
            sess["full_name"] = self.user.full_name
            sess["location"] = self.user.location
            sess["badge"] = self.user.badge
            sess["initials"] = "BF"

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_01_crop_prediction_and_add_to_farm(self):
        """Test Crop Prediction ML, Report generation, and 1-Click Add to Farms."""
        payload = {
            "n": 90, "p": 42, "k": 43,
            "ph": 6.5, "temp": 25.0, "humidity": 80.0,
            "soil_type": "Alluvial Soil"
        }
        res = self.client.post("/api/predict-crop", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("result", data)
        self.assertIn("report_id", data)
        crop_name = data["result"]
        report_id = data["report_id"]

        # Add to My Farms from prediction
        add_farm_res = self.client.post("/api/create_farm_from_prediction", json={
            "crop_name": crop_name,
            "farm_name": f"North Plot {crop_name}",
            "area_acres": 2.5
        })
        self.assertEqual(add_farm_res.status_code, 200)
        farm_data = add_farm_res.get_json()
        self.assertTrue(farm_data["success"])
        self.assertIn("user_crop_id", farm_data)

        # Verify farm in DB
        farm = UserCrop.query.get(farm_data["user_crop_id"])
        self.assertIsNotNone(farm)
        self.assertEqual(farm.farm_name, f"North Plot {crop_name}")
        self.assertEqual(farm.area_acres, 2.5)
        print(f"  [PASS] Crop Recommendation ({crop_name}) -> 1-Click Added to Farm (ID: {farm.user_crop_id})")

    def test_02_disease_diagnosis_and_save_to_farm_log(self):
        """Test Leaf Diagnosis and seamless recording into the Farm's health timeline."""
        # 1. Register a test farm
        standard = CropStandard.query.first()
        farm = UserCrop(
            user_id=self.user.user_id,
            crop_standard_id=standard.crop_standard_id,
            farm_name="East Tomato Field",
            sowing_date=date.today(),
            area_acres=1.5,
            status="active"
        )
        db.session.add(farm)
        db.session.commit()

        # 2. Disease Detection UI loads with connected farms
        page_res = self.client.get("/disease_detection")
        self.assertEqual(page_res.status_code, 200)
        self.assertIn(b"East Tomato Field", page_res.data)

        # 3. Simulate leaf diagnosis upload
        img = Image.new("RGB", (224, 224), (50, 150, 60)) # green foliage
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        predict_res = self.client.post("/api/disease/predict", data={
            "file": (io.BytesIO(buf.getvalue()), "leaf.jpg")
        }, content_type="multipart/form-data")
        self.assertEqual(predict_res.status_code, 200)
        diag_data = predict_res.get_json()
        self.assertIn("label", diag_data)

        # 4. Save diagnosis to farm health record
        save_res = self.client.post("/api/disease/save_to_farm", json={
            "user_crop_id": farm.user_crop_id,
            "disease_label": diag_data["label"],
            "confidence": diag_data.get("confidence", 0.85),
            "precautions": diag_data.get("precautions", ["Isolate affected leaves"])
        })
        self.assertEqual(save_res.status_code, 200)
        save_json = save_res.get_json()
        self.assertTrue(save_json["success"])

        # 5. Verify that crop_standards API includes latest_disease
        standards_res = self.client.get(f"/api/crop_standards/{farm.user_crop_id}")
        self.assertEqual(standards_res.status_code, 200)
        standards_data = standards_res.get_json()
        self.assertIsNotNone(standards_data.get("latest_disease"))
        self.assertEqual(standards_data["latest_disease"]["label"], diag_data["label"])
        print(f"  [PASS] Leaf Doctor Diagnostic -> Saved to Farm Log ({diag_data['label']}) -> Verified in Crop Tracking")

    def test_03_smart_irrigation_advisory(self):
        """Verify decoupled environmental irrigation advisory with sustainability scoring."""
        payload = {
            "crop": "Tomato",
            "stage": "flowering",
            "soil_moisture_pct": 22,
            "temperature_c": 31.5,
            "humidity_pct": 50,
            "rain_probability_pct": 15,
            "forecast_rain_mm": 0
        }
        res = self.client.post("/api/advisory", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("irrigation_action", data)
        self.assertIn("sustainability_score", data)
        self.assertIn("trace", data)
        self.assertGreaterEqual(data["sustainability_score"], 0)
        self.assertLessEqual(data["sustainability_score"], 100)
        print(f"  [PASS] Smart Irrigation Advisory: {data['irrigation_action']} (Score: {data['sustainability_score']}/100)")

    def test_04_farmer_community_and_ai_chat(self):
        """Test Community Q&A forum and AI chatbot assistant."""
        # Create topic
        post_res = self.client.post("/farmer_community", data={
            "title": "Preventing early blight in rainy weather",
            "description": "How should we handle heavy downpours with susceptible crops?",
            "category": "Pest & Disease"
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        topic = Topic.query.filter_by(title="Preventing early blight in rainy weather").first()
        self.assertIsNotNone(topic)

        # AI Chatbot consultation
        chat_res = self.client.post("/chatbot", json={"question": "How to prevent fungal leaf rot?"})
        self.assertEqual(chat_res.status_code, 200)
        chat_data = chat_res.get_json()
        self.assertIn("response", chat_data)
        self.assertGreater(len(chat_data["response"]), 10)
        print("  [PASS] Farmer Community Q&A and 24/7 AI Chatbot Consultation verified")

    def test_05_crop_conditioning_and_smart_disambiguation(self):
        """Test Differential Crop Focus, conditioned inference, and cross-crop disambiguation."""
        # Use an existing sample image from validation set
        sample_path = "data/val/Apple___Apple_scab/0395b847-2c73-4674-826f-33a6afb5b4fe___FREC_Scab 3287.JPG"
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                img_data = f.read()

            # 1. Conditioned on Apple
            res_apple = self.client.post("/api/disease/predict", data={
                "file": (io.BytesIO(img_data), "apple_leaf.jpg"),
                "crop_filter": "apple"
            }, content_type="multipart/form-data")
            self.assertEqual(res_apple.status_code, 200)
            data_apple = res_apple.get_json()
            self.assertEqual(data_apple.get("crop_filter_applied"), "Apple")
            self.assertTrue(data_apple["label"].startswith("Apple___"))

            # 2. Conditioned on Tomato
            res_tomato = self.client.post("/api/disease/predict", data={
                "file": (io.BytesIO(img_data), "leaf.jpg"),
                "crop_filter": "tomato"
            }, content_type="multipart/form-data")
            self.assertEqual(res_tomato.status_code, 200)
            data_tomato = res_tomato.get_json()
            self.assertEqual(data_tomato.get("crop_filter_applied"), "Tomato")
            self.assertTrue(data_tomato["label"].startswith("Tomato___"))
            print("  [PASS] Differential Crop Focus & Conditioning successfully verified")


if __name__ == "__main__":
    unittest.main()
