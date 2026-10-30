import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if db_url:
    try:
        import psycopg2
    except ImportError:
        db_url = db_url.replace("postgresql+psycopg2://", "postgresql+pg8000://")
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+pg8000://")

class Config:
    # Database URL: uses PostgreSQL if configured, otherwise falls back to local SQLite database
    SQLALCHEMY_DATABASE_URI = db_url or "sqlite:///biogrow.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "biogrow-secret-key-2026-secure-session")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))

    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")  # Required by Flask-Mail
