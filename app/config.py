import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "app.db")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Fallback to local SQLite if DATABASE_URL is not set
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Automatically translate 'dbo' schema for SQLite so it runs out-of-the-box
    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "execution_options": {
                "schema_translate_map": {
                    "dbo": None,
                }
            }
        }

    # Security: File upload limits (prevent Denial of Service / Disk exhaustion)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max per request

    # Security: Cookie protections against XSS & CSRF
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_QUERY_VALUE_LENGTH = 100
    MAX_FORM_FIELD_LENGTH = 5000
    INPUT_FIELD_LIMITS = {
        "first_name": 100,
        "last_name": 100,
        "email": 255,
        "password": 255,
        "password_confirm": 255,
        "current_password": 255,
        "new_password": 255,
        "new_password_confirm": 255,
        "name": 150,
        "title": 150,
        "file_path": 255,
        "file_type": 50,
        "status": 50,
        "role": 20,
        "grade": 20,
        "feedback": 5000,
        "content": 10000,
    }
