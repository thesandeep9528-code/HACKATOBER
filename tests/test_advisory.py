import unittest

from fastapi.testclient import TestClient

from fieldguard.main import app
from fieldguard.schemas import SensorContext
from fieldguard.services.advisory import irrigation_advice, sustainability_score


class AdvisoryTests(unittest.TestCase):
    def test_rain_prevents_automatic_irrigation(self):
        context = SensorContext(crop="Tomato", soil_moisture_pct=20, temperature_c=29, humidity_pct=65, rain_probability_pct=80, forecast_rain_mm=8)
        action, _, trace = irrigation_advice(context)
        self.assertEqual(action, "CHECK_AGAIN_SOON")
        self.assertTrue(trace)

    def test_score_is_bounded(self):
        context = SensorContext(crop="Corn", soil_moisture_pct=100, temperature_c=50, humidity_pct=5)
        score = sustainability_score(context, "MONITOR")
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_esp32_rejects_non_private_host(self):
        response = TestClient(app).post("/api/esp32/capture", json={"host": "8.8.8.8"})
        self.assertEqual(response.status_code, 422)

    def test_rejects_non_plant_image(self):
        import io
        from PIL import Image
        blue_img = Image.new("RGB", (224, 224), (30, 80, 220))
        buf = io.BytesIO()
        blue_img.save(buf, format="JPEG")
        response = TestClient(app).post("/api/predict", files={"file": ("blue.jpg", buf.getvalue(), "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["label"], "Non-Plant / Unrecognized Image")
        self.assertEqual(data["confidence"], 0.0)
        self.assertTrue(len(data["quality_warnings"]) > 0)


if __name__ == "__main__":
    unittest.main()
