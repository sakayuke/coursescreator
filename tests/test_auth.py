from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import User


def test_register_page_loads(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_successful_registration(client, app):
    payload = {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": "jankowalski@test.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
    }
    response = client.post("/register", data=payload)
    # Redirects to login page
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # Verify user was written to the database
    with app.app_context():
        user = User.query.filter_by(email="jankowalski@test.com").first()
        assert user is not None
        assert user.first_name == "Jan"
        assert user.role == "student"


def test_registration_password_mismatch(client):
    payload = {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": "mismatch@test.com",
        "password": "Password123!",
        "password_confirm": "DifferentPassword123!",
    }
    response = client.post("/register", data=payload)
    # Re-renders register template instead of redirecting
    assert response.status_code == 200


def test_registration_weak_password(client):
    payload = {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": "weak@test.com",
        "password": "weak",
        "password_confirm": "weak",
    }
    response = client.post("/register", data=payload)
    assert response.status_code == 200


def test_registration_duplicate_email(client, app):
    with app.app_context():
        existing = User(
            first_name="Existing",
            last_name="User",
            email="duplicate@test.com",
            password_hash=generate_password_hash("Password123!"),
            role="student",
        )
        db.session.add(existing)
        db.session.commit()

    payload = {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": "duplicate@test.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
    }
    response = client.post("/register", data=payload)
    assert response.status_code == 200


def test_successful_student_login(client, app):
    with app.app_context():
        user = User(
            first_name="Login",
            last_name="Test",
            email="login@test.com",
            password_hash=generate_password_hash("Password123!"),
            role="student",
        )
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={"email": "login@test.com", "password": "Password123!"},
    )
    assert response.status_code == 302
    assert "/courses" in response.headers["Location"]


def test_login_invalid_password(client, app):
    with app.app_context():
        user = User(
            first_name="Login",
            last_name="Test",
            email="login_invalid@test.com",
            password_hash=generate_password_hash("Password123!"),
            role="student",
        )
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login",
        data={"email": "login_invalid@test.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_logout(client):
    response = client.get("/logout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]