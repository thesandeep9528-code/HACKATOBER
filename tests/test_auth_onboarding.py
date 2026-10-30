import os
import sys
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Otp, User
from werkzeug.security import generate_password_hash


class TestAuthOnboarding(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_registration_signs_in_without_otp_and_starts_tour_once(self):
        response = self.client.post(
            "/register",
            data={
                "full_name": "New Farmer",
                "email": "new-farmer@example.com",
                "password": "FarmerPassword123!",
                "location": "Ahmedabad, Gujarat",
                "dob": "1990-01-01",
                "mobile": "9876543210",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/dashboard")
        user = User.query.filter_by(email="new-farmer@example.com").one()
        self.assertTrue(user.is_verified)
        self.assertEqual(Otp.query.filter_by(user_id=user.user_id).count(), 0)

        first_dashboard = self.client.get("/dashboard")
        self.assertEqual(first_dashboard.status_code, 200)
        self.assertIn(b'data-tour-new-user="true"', first_dashboard.data)

        refreshed_dashboard = self.client.get("/dashboard")
        self.assertEqual(refreshed_dashboard.status_code, 200)
        self.assertIn(b'data-tour-new-user="false"', refreshed_dashboard.data)

    def test_existing_unverified_account_can_log_in_without_otp(self):
        user = User(
            full_name="Returning Farmer",
            email="returning-farmer@example.com",
            password_hash=generate_password_hash("FarmerPassword123!"),
            location="Ahmedabad, Gujarat",
            is_verified=False,
        )
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            "/login",
            data={"email": user.email, "password": "FarmerPassword123!"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-tour-new-user="false"', response.data)
        self.assertTrue(user.is_verified)
        self.assertNotIn(b"Verify OTP", response.data)
        self.assertEqual(Otp.query.filter_by(user_id=user.user_id).count(), 0)


if __name__ == "__main__":
    unittest.main()
