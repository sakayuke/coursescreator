import pytest

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import User


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'href="/" class="logo"' in response.data
    assert b"Home" in response.data


def test_student_navigation_links_to_home_courses_and_profile(client, app):
    with app.app_context():
        user = User(
            first_name="Student",
            last_name="Test",
            email="navigation@test.com",
            password_hash="unused",
            role="student",
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True

    response = client.get("/courses")
    assert response.status_code == 200
    assert b'href="/"' in response.data
    assert b'href="/courses"' in response.data
    assert b'href="/profile"' in response.data
    assert b'href="/admin"' not in response.data


def test_create_app_rejects_short_secret_key(monkeypatch):
    monkeypatch.setattr(Config, "SECRET_KEY", "too-short")

    with pytest.raises(RuntimeError, match="SECRET_KEY must be at least 32 characters"):
        create_app()
    