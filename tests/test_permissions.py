import pytest

from app import create_app
from app.extensions import db
from app.models import User, Course
from app.decorators import role_required, is_owner


@pytest.fixture
def app():
    app = create_app()

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SECRET_KEY="test-secret-key",
    )

    with app.app_context():
        db.create_all()

        @app.route("/admin-only")
        @role_required("admin")
        def admin_only():
            return "OK"

        @app.route("/teacher-only")
        @role_required("teacher")
        def teacher_only():
            return "OK"

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_ids(app):
    with app.app_context():
        admin = User(
    first_name="Admin",
    last_name="Test",
    email="admin@test.com",
    password_hash="test",
    role="admin",
)

        teacher = User(
    first_name="Teacher",
    last_name="Test",
    email="teacher@test.com",
    password_hash="test",
    role="teacher",
)

        other_teacher = User(
    first_name="Other",
    last_name="Teacher",
    email="other@test.com",
    password_hash="test",
    role="teacher",
)

        student = User(
    first_name="Student",
    last_name="Test",
    email="student@test.com",
    password_hash="test",
    role="student",
)

        db.session.add_all([
            admin,
            teacher,
            other_teacher,
            student,
        ])

        db.session.commit()

        return {
            "admin": admin.id,
            "teacher": teacher.id,
            "other_teacher": other_teacher.id,
            "student": student.id,
        }


def login_user(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def test_admin_can_access_admin_route(client, user_ids):
    login_user(client, user_ids["admin"])

    response = client.get("/admin-only")

    assert response.status_code == 200
    assert response.data == b"OK"


def test_student_cannot_access_admin_route(client, user_ids):
    login_user(client, user_ids["student"])

    response = client.get("/admin-only")

    assert response.status_code == 403


def test_teacher_can_access_teacher_route(client, user_ids):
    login_user(client, user_ids["teacher"])

    response = client.get("/teacher-only")

    assert response.status_code == 200
    assert response.data == b"OK"


def test_is_owner_returns_true_for_owner(app, user_ids):
    with app.app_context():
        teacher = db.session.get(User, user_ids["teacher"])

        course = Course(
            name="Test Course",
            description="Test",
            teacher_id=teacher.id,
        )

        db.session.add(course)
        db.session.commit()

        assert is_owner(course, teacher) is True


def test_is_owner_returns_false_for_other_teacher(app, user_ids):
    with app.app_context():
        teacher = db.session.get(User, user_ids["teacher"])
        other_teacher = db.session.get(
            User,
            user_ids["other_teacher"],
        )

        course = Course(
            name="Test Course",
            description="Test",
            teacher_id=teacher.id,
        )

        db.session.add(course)
        db.session.commit()

        assert is_owner(course, other_teacher) is False