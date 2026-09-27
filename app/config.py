import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_QUERY_VALUE_LENGTH = 100
    MAX_FORM_FIELD_LENGTH = 5000
    INPUT_FIELD_LIMITS = {
        "first_name": 100,
        "last_name": 100,
        "email": 255,
        "password": 255,
        "password_confirm": 255,
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
